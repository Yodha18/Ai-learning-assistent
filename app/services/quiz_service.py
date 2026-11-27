from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
import logging
from app.models.document import Document, DocumentChunk
from app.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer
from app.models.topic import Topic
from app.models.subject import Subject
from app.schemas.quiz import (
    QuizCreate, QuizGenerateRequest, QuizAttemptCreate,
    QuizWithQuestions, QuizAttemptWithDetails
)
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service
from datetime import datetime

logger = logging.getLogger(__name__)


def create_quiz(db: Session, quiz_data: QuizCreate, user_id: int) -> Quiz:
    """Create a new quiz."""
    db_quiz = Quiz(
        title=quiz_data.title,
        subject_id=quiz_data.subject_id,
        topic_id=quiz_data.topic_id,
        user_id=user_id,
        difficulty=quiz_data.difficulty,
        number_of_questions=quiz_data.number_of_questions
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz


def generate_ai_quiz(
    db: Session,
    request: QuizGenerateRequest,
    user_id: int
) -> QuizWithQuestions:
    """Generate a quiz using AI."""
    
    # Resolve selected topics and subjects within the current user's data.
    topic_name = request.topic_name
    subject_id = request.subject_id
    if request.topic_id:
        topic = db.query(Topic).join(Subject).filter(
            Topic.id == request.topic_id,
            Subject.user_id == user_id,
        ).first()
        if topic is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        topic_name = topic.name
        subject_id = topic.subject_id
    
    # Prefer the user's uploaded notes for the selected subject.
    context = None
    if subject_id is not None:
        subject = db.query(Subject).filter(
            Subject.id == subject_id,
            Subject.user_id == user_id,
        ).first()
        if subject is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        chunks = db.query(DocumentChunk).join(Document).filter(
            Document.user_id == user_id,
            Document.subject_id == subject_id,
        ).order_by(DocumentChunk.document_id, DocumentChunk.chunk_index).limit(10).all()
        if chunks:
            context = "\n".join(chunk.chunk_text for chunk in chunks)[:8000]
        topic_name = topic_name or subject.name
    elif topic_name:
        try:
            relevant_chunks = rag_service.search_similar_chunks(
                user_id,
                topic_name,
                top_k=3,
                db=db,
            )
            if relevant_chunks:
                context = "\n".join(chunk["chunk_text"] for chunk in relevant_chunks)
        except Exception:
            logger.warning("Could not retrieve quiz context for topic %s", topic_name, exc_info=True)
    
    # Generate questions using AI
    try:
        questions_data = ai_service.generate_quiz(
            topic=topic_name or "General Knowledge",
            difficulty=request.difficulty,
            num_questions=request.number_of_questions,
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )
    
    # Create quiz
    quiz_title = f"{topic_name or 'General'} Quiz ({request.difficulty})"
    db_quiz = Quiz(
        title=quiz_title,
        subject_id=request.subject_id,
        topic_id=request.topic_id,
        user_id=user_id,
        difficulty=request.difficulty,
        number_of_questions=len(questions_data)
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    # Create questions
    for q_data in questions_data:
        question = Question(
            quiz_id=db_quiz.id,
            question_text=q_data['question_text'],
            options=q_data['options'],
            correct_answer=q_data['correct_answer'],
            explanation=q_data['explanation'],
            topic=q_data['topic']
        )
        db.add(question)
    
    db.commit()
    db.refresh(db_quiz)
    
    return db_quiz


def get_user_quizzes(db: Session, user_id: int, subject_id: Optional[int] = None) -> List[Quiz]:
    """Get all quizzes for a user, optionally filtered by subject."""
    query = db.query(Quiz).filter(Quiz.user_id == user_id)
    
    if subject_id:
        query = query.filter(Quiz.subject_id == subject_id)
    
    return query.order_by(Quiz.created_at.desc()).all()


def get_quiz_with_questions(db: Session, quiz_id: int, user_id: int) -> QuizWithQuestions:
    """Get a quiz with its questions."""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz


def submit_quiz_attempt(
    db: Session,
    attempt_data: QuizAttemptCreate,
    user_id: int
) -> QuizAttemptWithDetails:
    """Submit a quiz attempt and calculate score."""
    
    # Get quiz
    quiz = db.query(Quiz).filter(
        Quiz.id == attempt_data.quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get all questions for the quiz
    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    question_map = {q.id: q for q in questions}
    
    # Calculate score
    correct_count = 0
    total_questions = len(questions)
    
    # Create quiz attempt
    db_attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user_id,
        score=0.0,  # Will be updated
        accuracy=0.0,  # Will be updated
        time_taken=attempt_data.time_taken
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    
    # Process answers
    for answer_data in attempt_data.answers:
        question = question_map.get(answer_data.question_id)
        if not question:
            continue
        
        is_correct = 1 if answer_data.selected_answer == question.correct_answer else 0
        if is_correct:
            correct_count += 1
        
        quiz_answer = QuizAnswer(
            attempt_id=db_attempt.id,
            question_id=answer_data.question_id,
            selected_answer=answer_data.selected_answer,
            is_correct=is_correct
        )
        db.add(quiz_answer)
    
    # Calculate final score and accuracy
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    accuracy = score  # Same as score for now
    
    db_attempt.score = score
    db_attempt.accuracy = accuracy
    
    db.commit()
    db.refresh(db_attempt)
    
    # Update topic mastery if applicable
    if quiz.topic_id:
        update_topic_mastery(db, quiz.topic_id, user_id, accuracy)
    
    return db_attempt


def update_topic_mastery(db: Session, topic_id: int, user_id: int, accuracy: float) -> None:
    """Update topic mastery based on quiz performance."""
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == user_id
    ).first()
    
    if not topic:
        return
    
    # Get all attempts for this topic
    attempts = db.query(QuizAttempt).join(Quiz).filter(
        Quiz.topic_id == topic_id,
        Quiz.user_id == user_id
    ).all()
    
    if not attempts:
        return
    
    # Calculate average accuracy
    avg_accuracy = sum(attempt.accuracy for attempt in attempts) / len(attempts)
    
    # Update mastery score (weighted average with previous score)
    topic.mastery_score = (topic.mastery_score * 0.7) + (avg_accuracy * 0.3)
    topic.last_practiced = datetime.utcnow()
    
    db.commit()


def get_quiz_attempts(db: Session, user_id: int, quiz_id: Optional[int] = None) -> List[QuizAttempt]:
    """Get quiz attempts for a user."""
    query = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)
    
    if quiz_id:
        query = query.filter(QuizAttempt.quiz_id == quiz_id)
    
    return query.order_by(QuizAttempt.completion_date.desc()).all()


def get_quiz_attempt_with_details(db: Session, attempt_id: int, user_id: int) -> QuizAttemptWithDetails:
    """Get a quiz attempt with all details."""
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.user_id == user_id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )
    
    return attempt


def delete_quiz(db: Session, quiz_id: int, user_id: int) -> None:
    """Delete a quiz."""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    db.delete(quiz)
    db.commit()
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.user import User
from app.models.subject import Subject
from app.models.topic import Topic
from app.services.ai_service import ai_service


def generate_interview_question(
    db: Session,
    user_id: int,
    subject_id: int = None,
    topic_id: int = None,
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """Generate an interview question using AI."""
    
    # Get subject and topic names
    subject_name = "General"
    topic_name = "General"
    
    if subject_id:
        subject = db.query(Subject).filter(
            Subject.id == subject_id,
            Subject.user_id == user_id
        ).first()
        if subject:
            subject_name = subject.name
    
    if topic_id:
        topic = db.query(Topic).join(Subject).filter(
            Topic.id == topic_id,
            Subject.user_id == user_id
        ).first()
        if topic:
            topic_name = topic.name
            subject_name = topic.subject.name
    
    # Generate question using AI
    try:
        interview_data = ai_service.generate_interview_question(
            subject=subject_name,
            topic=topic_name,
            difficulty=difficulty
        )
        
        return {
            'subject': subject_name,
            'topic': topic_name,
            'difficulty': difficulty,
            'question': interview_data['question'],
            'what_looking_for': interview_data['what_looking_for'],
            'key_points': interview_data['key_points']
        }
        
    except Exception as e:
        raise Exception(f"Failed to generate interview question: {str(e)}")


def evaluate_interview_answer(
    db: Session,
    user_id: int,
    question: str,
    answer: str,
    key_points: list
) -> Dict[str, Any]:
    """Evaluate an interview answer using AI."""
    
    try:
        evaluation = ai_service.evaluate_interview_answer(
            question=question,
            answer=answer,
            key_points=key_points
        )
        
        return evaluation
        
    except Exception as e:
        raise Exception(f"Failed to evaluate answer: {str(e)}")
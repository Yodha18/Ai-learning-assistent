from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.user import User
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.quiz import QuizAttempt, Quiz
from app.models.study_session import StudySession
from app.schemas.progress import (
    OverallProgress, SubjectProgress, TopicProgress, WeakTopic
)


def calculate_overall_progress(db: Session, user_id: int) -> OverallProgress:
    """Calculate overall progress for a user."""
    
    # Get all subjects
    subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    total_subjects = len(subjects)
    
    # Get all topics
    topics = db.query(Topic).join(Subject).filter(Subject.user_id == user_id).all()
    total_topics = len(topics)
    
    # Calculate topics mastered (mastery_score >= 75)
    topics_mastered = sum(1 for t in topics if t.mastery_score >= 75)
    
    # Calculate overall progress
    overall_progress = 0.0
    if total_topics > 0:
        overall_progress = sum(t.mastery_score for t in topics) / total_topics
    
    # Get quiz attempts
    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
    
    # Calculate quiz accuracy
    quiz_accuracy = 0.0
    if attempts:
        quiz_accuracy = sum(attempt.accuracy for attempt in attempts) / len(attempts)
    
    # Calculate total study time (from quiz attempts)
    total_study_time = sum(attempt.time_taken or 0 for attempt in attempts) // 60  # Convert to minutes
    
    # Calculate study streak (simplified - consecutive days with activity)
    study_streak = calculate_study_streak(db, user_id)
    
    # Calculate subjects completed (all topics in subject mastered)
    subjects_completed = 0
    for subject in subjects:
        subject_topics = db.query(Topic).filter(Topic.subject_id == subject.id).all()
        if subject_topics and all(t.mastery_score >= 75 for t in subject_topics):
            subjects_completed += 1
    
    return OverallProgress(
        overall_progress=round(overall_progress, 2),
        total_study_time=total_study_time,
        study_streak=study_streak,
        quiz_accuracy=round(quiz_accuracy, 2),
        subjects_completed=subjects_completed,
        total_subjects=total_subjects,
        topics_mastered=topics_mastered,
        total_topics=total_topics
    )


def calculate_subject_progress(db: Session, user_id: int, subject_id: int) -> SubjectProgress:
    """Calculate progress for a specific subject."""
    
    # Get subject
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        return None
    
    # Get topics for subject
    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    total_topics = len(topics)
    
    # Calculate topics mastered
    topics_mastered = sum(1 for t in topics if t.mastery_score >= 75)
    
    # Calculate subject progress
    progress_percentage = 0.0
    if total_topics > 0:
        progress_percentage = sum(t.mastery_score for t in topics) / total_topics
    
    # Get quiz attempts for this subject
    attempts = db.query(QuizAttempt).join(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.subject_id == subject_id
    ).all()
    
    # Calculate quiz accuracy
    quiz_accuracy = 0.0
    if attempts:
        quiz_accuracy = sum(attempt.accuracy for attempt in attempts) / len(attempts)
    
    # Get last studied date
    last_studied = None
    if topics:
        last_studied = max((t.last_practiced for t in topics if t.last_practiced), default=None)
    
    return SubjectProgress(
        subject_id=subject.id,
        subject_name=subject.name,
        progress_percentage=round(progress_percentage, 2),
        topics_mastered=topics_mastered,
        total_topics=total_topics,
        quiz_accuracy=round(quiz_accuracy, 2),
        last_studied=last_studied
    )


def calculate_all_subjects_progress(db: Session, user_id: int) -> List[SubjectProgress]:
    """Calculate progress for all subjects."""
    subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    return [calculate_subject_progress(db, user_id, subject.id) for subject in subjects]


def calculate_topic_progress(db: Session, user_id: int, topic_id: int) -> TopicProgress:
    """Calculate progress for a specific topic."""
    
    # Get topic
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == user_id
    ).first()
    
    if not topic:
        return None
    
    # Get quiz attempts for this topic
    attempts = db.query(QuizAttempt).join(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.topic_id == topic_id
    ).all()
    
    # Calculate quiz accuracy
    quiz_accuracy = 0.0
    if attempts:
        quiz_accuracy = sum(attempt.accuracy for attempt in attempts) / len(attempts)
    
    return TopicProgress(
        topic_id=topic.id,
        topic_name=topic.name,
        subject_name=topic.subject.name,
        mastery_score=round(topic.mastery_score, 2),
        difficulty=topic.difficulty,
        quiz_attempts=len(attempts),
        accuracy=round(quiz_accuracy, 2),
        last_practiced=topic.last_practiced
    )


def calculate_all_topics_progress(db: Session, user_id: int) -> List[TopicProgress]:
    """Calculate progress for all topics."""
    topics = db.query(Topic).join(Subject).filter(Subject.user_id == user_id).all()
    return [calculate_topic_progress(db, user_id, topic.id) for topic in topics]


def calculate_study_streak(db: Session, user_id: int) -> int:
    """Calculate study streak based on recent activity."""
    
    # Get recent quiz attempts (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.completion_date >= thirty_days_ago
    ).order_by(QuizAttempt.completion_date.desc()).all()
    
    if not attempts:
        return 0
    
    # Group by date
    dates = set()
    for attempt in attempts:
        dates.add(attempt.completion_date.date())
    
    # Calculate streak
    today = datetime.utcnow().date()
    streak = 0
    
    if today in dates:
        streak = 1
        check_date = today - timedelta(days=1)
        
        while check_date in dates:
            streak += 1
            check_date -= timedelta(days=1)
    
    return streak


def detect_weak_topics(db: Session, user_id: int) -> List[WeakTopic]:
    """Detect weak topics based on quiz performance."""
    
    # Get all topics with attempts
    topics = db.query(Topic).join(Subject).filter(Subject.user_id == user_id).all()
    
    weak_topics = []
    
    for topic in topics:
        # Get quiz attempts for this topic
        attempts = db.query(QuizAttempt).join(Quiz).filter(
            Quiz.user_id == user_id,
            Quiz.topic_id == topic.id
        ).all()
        
        # Need at least 3 attempts
        if len(attempts) < 3:
            continue
        
        # Calculate accuracy
        accuracy = sum(attempt.accuracy for attempt in attempts) / len(attempts)
        
        # Weak if accuracy below 60%
        if accuracy < 60:
            # Determine priority
            if accuracy < 50:
                priority = "high"
                reason = f"Your accuracy is {accuracy:.1f}% across {len(attempts)} attempts."
            else:
                priority = "medium"
                reason = f"Your accuracy is {accuracy:.1f}% across {len(attempts)} attempts."
            
            weak_topics.append(WeakTopic(
                topic_id=topic.id,
                topic_name=topic.name,
                subject_name=topic.subject.name,
                accuracy=round(accuracy, 2),
                attempts=len(attempts),
                reason=reason,
                priority=priority
            ))
    
    # Sort by priority (high first) and accuracy (lowest first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    weak_topics.sort(key=lambda x: (priority_order[x.priority], x.accuracy))
    
    return weak_topics
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.models.notification import Notification, NotificationType
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str
) -> Notification:
    """Create a new notification for a user."""
    
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=0
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False
) -> List[Notification]:
    """Get notifications for a user."""
    
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == 0)
    
    return query.order_by(Notification.created_at.desc()).all()


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification:
    """Mark a notification as read."""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return None
    
    notification.is_read = 1
    db.commit()
    db.refresh(notification)
    
    return notification


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read for a user."""
    
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == 0
    ).update({"is_read": 1})
    
    db.commit()
    
    return count


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Delete a notification."""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return False
    
    db.delete(notification)
    db.commit()
    
    return True


def get_unread_count(db: Session, user_id: int) -> int:
    """Get count of unread notifications."""
    
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == 0
    ).count()
    
    return count


def create_study_reminder(db: Session, user_id: int, message: str) -> Notification:
    """Create a study reminder notification."""
    return create_notification(
        db,
        user_id,
        NotificationType.STUDY_REMINDER,
        "Study Reminder",
        message
    )


def create_weak_topic_notification(db: Session, user_id: int, topic_name: str) -> Notification:
    """Create a weak topic notification."""
    return create_notification(
        db,
        user_id,
        NotificationType.WEAK_TOPIC,
        "Weak Topic Detected",
        f"Your performance in {topic_name} needs improvement. Consider reviewing this topic."
    )


def create_quiz_improvement_notification(db: Session, user_id: int, subject: str) -> Notification:
    """Create a quiz improvement notification."""
    return create_notification(
        db,
        user_id,
        NotificationType.QUIZ_IMPROVEMENT,
        "Quiz Improvement",
        f"Great job! Your quiz performance in {subject} has improved."
    )


def create_document_ready_notification(db: Session, user_id: int, document_name: str) -> Notification:
    """Create a document ready notification."""
    return create_notification(
        db,
        user_id,
        NotificationType.DOCUMENT_READY,
        "Document Ready",
        f"Your document '{document_name}' has been processed and is ready for use."
    )


def create_study_plan_ready_notification(db: Session, user_id: int) -> Notification:
    """Create a study plan ready notification."""
    return create_notification(
        db,
        user_id,
        NotificationType.STUDY_PLAN_READY,
        "Study Plan Ready",
        "Your personalized study plan for today has been generated."
    )
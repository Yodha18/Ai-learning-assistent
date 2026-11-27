from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.models.recommendation import Recommendation, Priority
from app.models.user import User
from app.models.topic import Topic
from app.schemas.recommendation import RecommendationCreate
from app.services.progress_service import detect_weak_topics


def generate_recommendations(db: Session, user_id: int) -> List[Recommendation]:
    """Generate personalized recommendations based on user performance."""
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # Get weak topics
    weak_topics = detect_weak_topics(db, user_id)
    
    # Clear existing recommendations
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete()
    db.commit()
    
    recommendations = []
    
    # Generate recommendations for weak topics
    for weak_topic in weak_topics[:5]:  # Limit to top 5 weak topics
        priority = Priority.HIGH if weak_topic.priority == "high" else Priority.MEDIUM
        
        # Determine recommended action
        if weak_topic.accuracy < 50:
            action = "Review fundamentals and take practice quiz"
            difficulty = "easy"
            study_time = 30
        else:
            action = "Study and take practice quiz"
            difficulty = "medium"
            study_time = 20
        
        recommendation = Recommendation(
            user_id=user_id,
            subject=weak_topic.subject_name,
            topic=weak_topic.topic_name,
            reason=weak_topic.reason,
            priority=priority,
            difficulty=difficulty,
            estimated_study_time=study_time,
            recommended_action=action
        )
        
        db.add(recommendation)
        recommendations.append(recommendation)
    
    # Add general recommendations if no weak topics
    if not weak_topics:
        # Get topics not practiced recently
        week_ago = datetime.utcnow() - timedelta(days=7)
        from app.models.subject import Subject
        stale_topics = db.query(Topic).join(Subject).filter(
            Subject.user_id == user_id,
            Topic.last_practiced < week_ago
        ).limit(3).all()
        
        for topic in stale_topics:
            recommendation = Recommendation(
                user_id=user_id,
                subject=topic.subject.name,
                topic=topic.name,
                reason=f"You haven't practiced this topic in over a week.",
                priority=Priority.LOW,
                difficulty=topic.difficulty,
                estimated_study_time=15,
                recommended_action="Quick revision session"
            )
            
            db.add(recommendation)
            recommendations.append(recommendation)
    
    db.commit()
    
    return recommendations


def get_user_recommendations(db: Session, user_id: int) -> List[Recommendation]:
    """Get all recommendations for a user."""
    recommendations = db.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.is_completed == 0
    ).order_by(
        Recommendation.priority.asc(),
        Recommendation.created_at.desc()
    ).all()
    
    return recommendations


def mark_recommendation_completed(db: Session, recommendation_id: int, user_id: int) -> Recommendation:
    """Mark a recommendation as completed."""
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.user_id == user_id
    ).first()
    
    if not recommendation:
        return None
    
    recommendation.is_completed = 1
    db.commit()
    db.refresh(recommendation)
    
    return recommendation


def mark_all_recommendations_completed(db: Session, user_id: int) -> None:
    """Mark all recommendations as completed for a user."""
    db.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.is_completed == 0
    ).update({"is_completed": 1})
    db.commit()


def regenerate_recommendations(db: Session, user_id: int) -> List[Recommendation]:
    """Regenerate recommendations for a user."""
    return generate_recommendations(db, user_id)
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.models.study_plan import StudyPlan, StudyTask, TaskStatus
from app.models.user import User
from app.schemas.study_plan import StudyPlanCreate, StudyPlanGenerateRequest
from app.services.recommendation_service import get_user_recommendations
from app.services.progress_service import detect_weak_topics


def generate_study_plan(db: Session, user_id: int, daily_study_time: int) -> StudyPlan:
    """Generate a personalized study plan for the day."""
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Get weak topics
    weak_topics = detect_weak_topics(db, user_id)
    
    # Get recommendations
    recommendations = get_user_recommendations(db, user_id)
    
    # Create study plan for today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if plan already exists for today
    existing_plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.date >= today,
        StudyPlan.date < today + timedelta(days=1)
    ).first()
    
    if existing_plan:
        return existing_plan
    
    # Create new plan
    study_plan = StudyPlan(
        user_id=user_id,
        date=today,
        total_study_time=daily_study_time
    )
    db.add(study_plan)
    db.commit()
    db.refresh(study_plan)
    
    # Allocate time to tasks
    time_remaining = daily_study_time
    task_order = 0
    
    # Priority 1: Weak topics (high priority)
    high_priority_topics = [t for t in weak_topics if t.priority == "high"]
    for topic in high_priority_topics[:2]:  # Max 2 high priority topics
        task_time = min(30, time_remaining)  # 30 minutes each
        if task_time <= 0:
            break
        
        task = StudyTask(
            study_plan_id=study_plan.id,
            subject=topic.subject_name,
            topic=topic.topic_name,
            task_type="study",
            duration_minutes=task_time,
            status=TaskStatus.PENDING,
            order=task_order
        )
        db.add(task)
        time_remaining -= task_time
        task_order += 1
    
    # Priority 2: Medium priority weak topics
    medium_priority_topics = [t for t in weak_topics if t.priority == "medium"]
    for topic in medium_priority_topics[:2]:  # Max 2 medium priority topics
        task_time = min(20, time_remaining)  # 20 minutes each
        if task_time <= 0:
            break
        
        task = StudyTask(
            study_plan_id=study_plan.id,
            subject=topic.subject_name,
            topic=topic.topic_name,
            task_type="study",
            duration_minutes=task_time,
            status=TaskStatus.PENDING,
            order=task_order
        )
        db.add(task)
        time_remaining -= task_time
        task_order += 1
    
    # Priority 3: Quiz practice
    if time_remaining >= 15:
        quiz_time = min(20, time_remaining)
        task = StudyTask(
            study_plan_id=study_plan.id,
            subject="General",
            topic="Quiz Practice",
            task_type="quiz",
            duration_minutes=quiz_time,
            status=TaskStatus.PENDING,
            order=task_order
        )
        db.add(task)
        time_remaining -= quiz_time
        task_order += 1
    
    # Priority 4: Revision
    if time_remaining >= 10:
        revision_time = time_remaining
        task = StudyTask(
            study_plan_id=study_plan.id,
            subject="General",
            topic="Revision",
            task_type="revision",
            duration_minutes=revision_time,
            status=TaskStatus.PENDING,
            order=task_order
        )
        db.add(task)
    
    db.commit()
    db.refresh(study_plan)
    
    return study_plan


def get_user_study_plan(db: Session, user_id: int, date: datetime = None) -> StudyPlan:
    """Get study plan for a user for a specific date."""
    if not date:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.date >= date,
        StudyPlan.date < date + timedelta(days=1)
    ).first()
    
    return plan


def get_study_plans(db: Session, user_id: int, limit: int = 7) -> List[StudyPlan]:
    """Get recent study plans for a user."""
    plans = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id
    ).order_by(StudyPlan.date.desc()).limit(limit).all()
    
    return plans


def complete_task(db: Session, task_id: int, user_id: int) -> StudyTask:
    """Mark a study task as completed."""
    task = db.query(StudyTask).join(StudyPlan).filter(
        StudyTask.id == task_id,
        StudyPlan.user_id == user_id
    ).first()
    
    if not task:
        return None
    
    task.status = TaskStatus.COMPLETED
    db.commit()
    db.refresh(task)
    
    return task


def skip_task(db: Session, task_id: int, user_id: int) -> StudyTask:
    """Skip a study task."""
    task = db.query(StudyTask).join(StudyPlan).filter(
        StudyTask.id == task_id,
        StudyPlan.user_id == user_id
    ).first()
    
    if not task:
        return None
    
    task.status = TaskStatus.SKIPPED
    db.commit()
    db.refresh(task)
    
    return task


def regenerate_study_plan(db: Session, user_id: int, daily_study_time: int) -> StudyPlan:
    """Regenerate study plan for today."""
    # Delete existing plan for today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.date >= today,
        StudyPlan.date < today + timedelta(days=1)
    ).delete()
    db.commit()
    
    # Generate new plan
    return generate_study_plan(db, user_id, daily_study_time)
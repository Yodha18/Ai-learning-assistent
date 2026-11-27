from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import Optional, List

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.progress_service import (
    calculate_overall_progress,
    calculate_all_subjects_progress,
    detect_weak_topics
)
from app.services.recommendation_service import get_user_recommendations
from app.services.study_plan_service import get_user_study_plan
from app.services.notification_service import get_unread_count

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def dashboard_health():
    """Health check endpoint for dashboard service."""
    return {
        "status": "healthy",
        "service": "dashboard"
    }


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview data."""
    try:
        # Get overall progress
        overall_progress = calculate_overall_progress(db, current_user.id)
        
        # Get subject progress
        subjects_progress = calculate_all_subjects_progress(db, current_user.id)
        
        # Get weak topics
        weak_topics = detect_weak_topics(db, current_user.id)
        
        # Get recommendations
        recommendations = get_user_recommendations(db, current_user.id)
        
        # Get today's study plan
        study_plan = get_user_study_plan(db, current_user.id)
        
        # Get unread notification count
        unread_count = get_unread_count(db, current_user.id)
        
        return {
            "user": {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "email": current_user.email,
                "course": current_user.course,
                "semester": current_user.semester
            },
            "overall_progress": overall_progress,
            "subjects_progress": subjects_progress[:5],  # Limit to top 5
            "weak_topics": weak_topics[:3],  # Limit to top 3
            "recommendations": recommendations[:3],  # Limit to top 3
            "study_plan": study_plan,
            "unread_notifications": unread_count
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get quick statistics for dashboard."""
    try:
        overall_progress = calculate_overall_progress(db, current_user.id)
        return {
            "overall_progress": overall_progress.overall_progress,
            "study_streak": overall_progress.study_streak,
            "quiz_accuracy": overall_progress.quiz_accuracy,
            "total_study_time": overall_progress.total_study_time,
            "subjects_completed": overall_progress.subjects_completed,
            "total_subjects": overall_progress.total_subjects,
            "topics_mastered": overall_progress.topics_mastered,
            "total_topics": overall_progress.total_topics
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )


@router.get("/subjects")
async def get_subject_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress for all subjects."""
    try:
        subjects_progress = calculate_all_subjects_progress(db, current_user.id)
        return {
            "subjects": subjects_progress
        }
    except Exception as e:
        logger.error(f"Error fetching subject progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subject progress"
        )


@router.get("/weak-topics")
async def get_weak_topics_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get list of weak topics for improvement."""
    try:
        weak_topics = detect_weak_topics(db, current_user.id)
        return {
            "weak_topics": weak_topics[:limit]
        }
    except Exception as e:
        logger.error(f"Error fetching weak topics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch weak topics"
        )


@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 5
):
    """Get personalized recommendations."""
    try:
        recommendations = get_user_recommendations(db, current_user.id)
        return {
            "recommendations": recommendations[:limit]
        }
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recommendations"
        )


@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count."""
    try:
        unread_count = get_unread_count(db, current_user.id)
        return {
            "unread_count": unread_count
        }
    except Exception as e:
        logger.error(f"Error fetching notification count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )
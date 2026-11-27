from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.progress import (
    OverallProgress, SubjectProgress, TopicProgress, WeakTopic
)
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.progress_service import (
    calculate_overall_progress,
    calculate_all_subjects_progress,
    calculate_all_topics_progress,
    detect_weak_topics,
    calculate_subject_progress,
    calculate_topic_progress
)

router = APIRouter()


@router.get("/overall", response_model=OverallProgress)
async def get_overall_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get overall progress for the current user."""
    progress = calculate_overall_progress(db, current_user.id)
    return progress


@router.get("/subjects", response_model=List[SubjectProgress])
async def get_subjects_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress for all subjects."""
    progress = calculate_all_subjects_progress(db, current_user.id)
    return progress


@router.get("/subjects/{subject_id}", response_model=SubjectProgress)
async def get_subject_progress(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress for a specific subject."""
    progress = calculate_subject_progress(db, current_user.id, subject_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return progress


@router.get("/topics", response_model=List[TopicProgress])
async def get_topics_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress for all topics."""
    progress = calculate_all_topics_progress(db, current_user.id)
    return progress


@router.get("/topics/{topic_id}", response_model=TopicProgress)
async def get_topic_progress(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress for a specific topic."""
    progress = calculate_topic_progress(db, current_user.id, topic_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    return progress


@router.get("/weak-topics", response_model=List[WeakTopic])
async def get_weak_topics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get weak topics that need improvement."""
    weak_topics = detect_weak_topics(db, current_user.id)
    return weak_topics
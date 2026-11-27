from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.schemas.study_plan import (
    StudyPlanResponse, StudyPlanWithTasks, StudyPlanGenerateRequest,
    StudyTaskResponse
)
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.study_plan_service import (
    generate_study_plan,
    get_user_study_plan,
    get_study_plans,
    complete_task,
    skip_task,
    regenerate_study_plan
)

router = APIRouter()


@router.get("/today", response_model=StudyPlanWithTasks)
async def get_today_plan(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get today's study plan."""
    plan = get_user_study_plan(db, current_user.id)
    
    if not plan:
        # Generate a plan if none exists
        plan = generate_study_plan(db, current_user.id, current_user.daily_study_time)
    
    return plan


@router.post("/generate", response_model=StudyPlanWithTasks)
async def generate_new_plan(
    request: StudyPlanGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a new study plan for today."""
    if request.regenerate:
        plan = regenerate_study_plan(db, current_user.id, request.daily_study_time)
    else:
        plan = generate_study_plan(db, current_user.id, request.daily_study_time)
    
    return plan


@router.get("/", response_model=List[StudyPlanResponse])
async def get_study_plans_route(
    limit: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent study plans."""
    plans = get_study_plans(db, current_user.id, limit)
    return plans


@router.get("/{plan_id}", response_model=StudyPlanWithTasks)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific study plan."""
    from app.models.study_plan import StudyPlan
    plan = db.query(StudyPlan).filter(
        StudyPlan.id == plan_id,
        StudyPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study plan not found"
        )
    
    return plan


@router.post("/tasks/{task_id}/complete", response_model=StudyTaskResponse)
async def complete_task_route(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a task as completed."""
    task = complete_task(db, task_id, current_user.id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.post("/tasks/{task_id}/skip", response_model=StudyTaskResponse)
async def skip_task_route(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Skip a task."""
    task = skip_task(db, task_id, current_user.id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.recommendation import RecommendationResponse
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.recommendation_service import (
    generate_recommendations,
    get_user_recommendations,
    mark_recommendation_completed,
    mark_all_recommendations_completed,
    regenerate_recommendations
)

router = APIRouter()


@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all recommendations for the current user."""
    recommendations = get_user_recommendations(db, current_user.id)
    return recommendations


@router.post("/generate", response_model=List[RecommendationResponse])
async def generate_new_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate new recommendations based on current performance."""
    recommendations = generate_recommendations(db, current_user.id)
    return recommendations


@router.post("/regenerate", response_model=List[RecommendationResponse])
async def regenerate_user_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate recommendations for the current user."""
    recommendations = regenerate_recommendations(db, current_user.id)
    return recommendations


@router.post("/{recommendation_id}/complete", response_model=RecommendationResponse)
async def complete_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a recommendation as completed."""
    recommendation = mark_recommendation_completed(db, recommendation_id, current_user.id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    return recommendation


@router.post("/complete-all", status_code=status.HTTP_204_NO_CONTENT)
async def complete_all_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all recommendations as completed."""
    mark_all_recommendations_completed(db, current_user.id)
    return None
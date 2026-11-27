from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.recommendation import Priority


class RecommendationBase(BaseModel):
    subject: str
    topic: str
    reason: str
    priority: Priority
    difficulty: str
    estimated_study_time: int  # in minutes
    recommended_action: str


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
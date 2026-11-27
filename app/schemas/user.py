from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import LearningGoal, ExplanationStyle, Difficulty


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    semester: Optional[int] = None
    learning_goal: Optional[LearningGoal] = None
    daily_study_time: Optional[int] = None
    preferred_difficulty: Optional[Difficulty] = None
    explanation_style: Optional[ExplanationStyle] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    course: str
    university: Optional[str]
    semester: Optional[int]
    learning_goal: LearningGoal
    daily_study_time: int
    preferred_difficulty: Difficulty
    explanation_style: ExplanationStyle
    full_access: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

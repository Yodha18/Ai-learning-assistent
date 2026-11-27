from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.models.user import LearningGoal, ExplanationStyle, Difficulty


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    course: str = Field(..., min_length=1)
    university: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=8)
    learning_goal: Optional[LearningGoal] = LearningGoal.GENERAL
    daily_study_time: Optional[int] = Field(120, ge=30, le=360)  # in minutes
    preferred_difficulty: Optional[Difficulty] = Difficulty.MEDIUM
    explanation_style: Optional[ExplanationStyle] = ExplanationStyle.SIMPLE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
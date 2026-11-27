from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.interview_service import (
    generate_interview_question,
    evaluate_interview_answer
)

router = APIRouter()


class InterviewQuestionRequest(BaseModel):
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: str = "medium"


class InterviewAnswerRequest(BaseModel):
    question: str
    answer: str
    key_points: list


@router.post("/generate-question")
async def generate_question(
    request: InterviewQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a technical interview question."""
    try:
        question_data = generate_interview_question(
            db,
            current_user.id,
            request.subject_id,
            request.topic_id,
            request.difficulty
        )
        return question_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/evaluate-answer")
async def evaluate_answer(
    request: InterviewAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evaluate an interview answer."""
    try:
        evaluation = evaluate_interview_answer(
            db,
            current_user.id,
            request.question,
            request.answer,
            request.key_points
        )
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
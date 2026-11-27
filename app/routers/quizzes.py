from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.quiz import (
    QuizCreate, QuizGenerateRequest, QuizAttemptCreate,
    QuizResponse, QuizWithQuestions, QuizAttemptResponse,
    QuizAttemptWithDetails
)
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.quiz_service import (
    create_quiz, generate_ai_quiz, get_user_quizzes,
    get_quiz_with_questions, submit_quiz_attempt,
    get_quiz_attempts, get_quiz_attempt_with_details,
    delete_quiz
)

router = APIRouter()


@router.post("/generate", response_model=QuizWithQuestions, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a quiz using AI."""
    quiz = generate_ai_quiz(db, request, current_user.id)
    return quiz


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz_endpoint(
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new quiz manually."""
    quiz = create_quiz(db, quiz_data, current_user.id)
    return quiz


@router.get("/", response_model=List[QuizResponse])
async def get_quizzes(
    subject_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all quizzes for the current user."""
    quizzes = get_user_quizzes(db, current_user.id, subject_id)
    return quizzes


@router.get("/{quiz_id}", response_model=QuizWithQuestions)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz with its questions."""
    quiz = get_quiz_with_questions(db, quiz_id, current_user.id)
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizAttemptWithDetails, status_code=status.HTTP_201_CREATED)
async def submit_quiz(
    quiz_id: int,
    attempt_data: QuizAttemptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a quiz attempt."""
    attempt_data.quiz_id = quiz_id
    attempt = submit_quiz_attempt(db, attempt_data, current_user.id)
    return attempt


@router.get("/attempts/", response_model=List[QuizAttemptResponse])
async def get_all_attempts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all quiz attempts for the current user."""
    attempts = get_quiz_attempts(db, current_user.id)
    return attempts


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptWithDetails)
async def get_quiz_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz attempt with details."""
    attempt = get_quiz_attempt_with_details(db, attempt_id, current_user.id)
    return attempt


@router.get("/{quiz_id}/attempts", response_model=List[QuizAttemptResponse])
async def get_quiz_attempts_route(
    quiz_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all attempts for a specific quiz."""
    attempts = get_quiz_attempts(db, current_user.id, quiz_id)
    return attempts


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz_route(
    quiz_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a quiz."""
    delete_quiz(db, quiz_id, current_user.id)
    return None
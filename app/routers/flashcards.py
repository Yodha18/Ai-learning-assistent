from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.flashcard import FlashcardFeedback
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.flashcard_service import (
    create_flashcard,
    generate_flashcards_from_content,
    get_user_flashcards,
    submit_flashcard_feedback,
    delete_flashcard as delete_flashcard_service,
    get_due_flashcards_count
)

router = APIRouter()


class FlashcardCreate(BaseModel):
    front: str
    back: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: str = "medium"


class FlashcardGenerateRequest(BaseModel):
    content: str
    topic: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    num_flashcards: int = 5


class FlashcardFeedbackRequest(BaseModel):
    feedback: FlashcardFeedback


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_flashcard_endpoint(
    flashcard_data: FlashcardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new flashcard."""
    flashcard = create_flashcard(
        db,
        current_user.id,
        flashcard_data.front,
        flashcard_data.back,
        flashcard_data.subject_id,
        flashcard_data.topic_id,
        flashcard_data.difficulty
    )
    return flashcard


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate flashcards from content."""
    try:
        flashcards = generate_flashcards_from_content(
            db,
            current_user.id,
            request.content,
            request.topic,
            request.subject_id,
            request.topic_id,
            request.num_flashcards
        )
        return flashcards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
async def get_flashcards(
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    due_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get flashcards for the current user."""
    flashcards = get_user_flashcards(
        db,
        current_user.id,
        subject_id,
        topic_id,
        due_only
    )
    return flashcards


@router.get("/due-count")
async def get_due_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get count of flashcards due for review."""
    count = get_due_flashcards_count(db, current_user.id)
    return {"due_count": count}


@router.post("/{flashcard_id}/feedback")
async def submit_feedback(
    flashcard_id: int,
    request: FlashcardFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a flashcard."""
    flashcard = submit_flashcard_feedback(
        db,
        flashcard_id,
        current_user.id,
        request.feedback
    )
    
    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )
    
    return flashcard


@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard_route(
    flashcard_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a flashcard."""
    success = delete_flashcard_service(db, flashcard_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )
    
    return None
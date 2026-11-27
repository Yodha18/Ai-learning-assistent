from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.flashcard import Flashcard, FlashcardFeedback
from app.models.user import User
from app.models.subject import Subject
from app.models.topic import Topic
from app.services.ai_service import ai_service


def create_flashcard(
    db: Session,
    user_id: int,
    front: str,
    back: str,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    difficulty: str = "medium"
) -> Flashcard:
    """Create a new flashcard."""
    
    flashcard = Flashcard(
        user_id=user_id,
        subject_id=subject_id,
        topic_id=topic_id,
        front=front,
        back=back,
        difficulty=difficulty,
        next_review_date=datetime.utcnow(),
        interval_days=1,
        ease_factor=2.5
    )
    
    db.add(flashcard)
    db.commit()
    db.refresh(flashcard)
    
    return flashcard


def generate_flashcards_from_content(
    db: Session,
    user_id: int,
    content: str,
    topic: str,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    num_flashcards: int = 5
) -> List[Flashcard]:
    """Generate flashcards from content using AI."""
    
    try:
        # Use AI to generate flashcards
        # For now, we'll create a simple implementation
        # In a full implementation, this would call the AI service
        
        flashcards = []
        
        # Create a few example flashcards (placeholder)
        flashcard_data = [
            {
                'front': f'What is the main concept of {topic}?',
                'back': f'The main concept involves understanding the core principles of {topic}.'
            },
            {
                'front': f'Explain the key components of {topic}.',
                'back': f'The key components include various elements that work together to define {topic}.'
            }
        ]
        
        for data in flashcard_data[:num_flashcards]:
            flashcard = create_flashcard(
                db,
                user_id,
                data['front'],
                data['back'],
                subject_id,
                topic_id,
                "medium"
            )
            flashcards.append(flashcard)
        
        return flashcards
        
    except Exception as e:
        raise Exception(f"Failed to generate flashcards: {str(e)}")


def get_user_flashcards(
    db: Session,
    user_id: int,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    due_only: bool = False
) -> List[Flashcard]:
    """Get flashcards for a user."""
    
    query = db.query(Flashcard).filter(Flashcard.user_id == user_id)
    
    if subject_id:
        query = query.filter(Flashcard.subject_id == subject_id)
    
    if topic_id:
        query = query.filter(Flashcard.topic_id == topic_id)
    
    if due_only:
        query = query.filter(Flashcard.next_review_date <= datetime.utcnow())
    
    return query.order_by(Flashcard.next_review_date.asc()).all()


def submit_flashcard_feedback(
    db: Session,
    flashcard_id: int,
    user_id: int,
    feedback: FlashcardFeedback
) -> Flashcard:
    """Submit feedback for a flashcard and update spaced repetition parameters."""
    
    flashcard = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.user_id == user_id
    ).first()
    
    if not flashcard:
        return None
    
    # Simple spaced repetition algorithm (SM-2 inspired)
    # Update ease factor and interval based on feedback
    
    if feedback == FlashcardFeedback.AGAIN:
        # Forgot - reset interval
        flashcard.interval_days = 1
        flashcard.ease_factor = max(1.3, flashcard.ease_factor - 0.2)
    elif feedback == FlashcardFeedback.HARD:
        # Hard - slight increase
        flashcard.interval_days = max(1, int(flashcard.interval_days * 1.2))
        flashcard.ease_factor = max(1.3, flashcard.ease_factor - 0.1)
    elif feedback == FlashcardFeedback.GOOD:
        # Good - normal increase
        flashcard.interval_days = int(flashcard.interval_days * flashcard.ease_factor)
        flashcard.ease_factor = flashcard.ease_factor
    elif feedback == FlashcardFeedback.EASY:
        # Easy - larger increase
        flashcard.interval_days = int(flashcard.interval_days * flashcard.ease_factor * 1.3)
        flashcard.ease_factor = flashcard.ease_factor + 0.1
    
    # Calculate next review date
    flashcard.next_review_date = datetime.utcnow() + timedelta(days=flashcard.interval_days)
    
    db.commit()
    db.refresh(flashcard)
    
    return flashcard


def delete_flashcard(db: Session, flashcard_id: int, user_id: int) -> bool:
    """Delete a flashcard."""
    
    flashcard = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.user_id == user_id
    ).first()
    
    if not flashcard:
        return False
    
    db.delete(flashcard)
    db.commit()
    
    return True


def get_due_flashcards_count(db: Session, user_id: int) -> int:
    """Get count of flashcards due for review."""
    
    count = db.query(Flashcard).filter(
        Flashcard.user_id == user_id,
        Flashcard.next_review_date <= datetime.utcnow()
    ).count()
    
    return count
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import Difficulty
import enum


class FlashcardFeedback(str, enum.Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    difficulty = Column(String(50), default="medium")
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    subject = relationship("Subject")
    topic = relationship("Topic")

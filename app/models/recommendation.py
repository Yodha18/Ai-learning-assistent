from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import Difficulty
import enum


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=True)
    topic = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    difficulty = Column(String(50), default="medium")
    estimated_study_time = Column(Integer, nullable=True)  # in minutes
    recommended_action = Column(String(255), nullable=False)
    is_completed = Column(Integer, default=0)  # 0 for not completed, 1 for completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="recommendations")

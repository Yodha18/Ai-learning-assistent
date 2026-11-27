from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import Difficulty


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), default="medium")
    mastery_score = Column(Float, default=0.0)
    last_practiced = Column(DateTime(timezone=True), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subject = relationship("Subject", back_populates="topics")
    quizzes = relationship("Quiz", back_populates="topic")

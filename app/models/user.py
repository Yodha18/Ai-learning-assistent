from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class LearningGoal(str, enum.Enum):
    EXAMS = "exams"
    COMPETITIVE_PROGRAMMING = "competitive_programming"
    PLACEMENTS = "placements"
    INTERVIEW_PREP = "interview_prep"
    GENERAL = "general"


class ExplanationStyle(str, enum.Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    PRACTICAL = "practical"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    course = Column(String(255), nullable=False)
    university = Column(String(255), nullable=True)
    semester = Column(Integer, nullable=True)
    learning_goal = Column(Enum(LearningGoal), default=LearningGoal.GENERAL)
    daily_study_time = Column(Integer, default=120)  # in minutes
    preferred_difficulty = Column(Enum(Difficulty), default=Difficulty.MEDIUM)
    explanation_style = Column(Enum(ExplanationStyle), default=ExplanationStyle.SIMPLE)
    full_access = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subjects = relationship("Subject", back_populates="user")
    documents = relationship("Document", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    chat_conversations = relationship("ChatConversation", back_populates="user")
    study_plans = relationship("StudyPlan", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

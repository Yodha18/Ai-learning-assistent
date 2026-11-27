from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SubjectProgress(BaseModel):
    subject_id: int
    subject_name: str
    progress_percentage: float
    topics_mastered: int
    total_topics: int
    quiz_accuracy: float
    last_studied: Optional[datetime]


class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    subject_name: str
    mastery_score: float
    difficulty: str
    quiz_attempts: int
    accuracy: float
    last_practiced: Optional[datetime]


class OverallProgress(BaseModel):
    overall_progress: float
    total_study_time: int  # in minutes
    study_streak: int
    quiz_accuracy: float
    subjects_completed: int
    total_subjects: int
    topics_mastered: int
    total_topics: int


class WeakTopic(BaseModel):
    topic_id: int
    topic_name: str
    subject_name: str
    accuracy: float
    attempts: int
    reason: str
    priority: str  # high, medium, low
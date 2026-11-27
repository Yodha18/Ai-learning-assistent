from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestionBase(BaseModel):
    question_text: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: int = Field(..., ge=0, le=3)
    explanation: Optional[str] = None
    topic: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    title: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: str = "medium"
    number_of_questions: int = Field(..., gt=0)


class QuizCreate(QuizBase):
    pass


class QuizGenerateRequest(BaseModel):
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    difficulty: str = "medium"
    number_of_questions: int = Field(..., gt=0, le=20)


class QuizResponse(QuizBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class QuizWithQuestions(QuizResponse):
    questions: List[QuestionResponse]


class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_answer: int


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: List[QuizAnswerSubmit]
    time_taken: Optional[int] = None


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    accuracy: float
    time_taken: Optional[int]
    completion_date: datetime

    class Config:
        from_attributes = True


class QuizAnswerResponse(BaseModel):
    id: int
    attempt_id: int
    question_id: int
    selected_answer: int
    is_correct: int

    class Config:
        from_attributes = True


class QuizAttemptWithDetails(QuizAttemptResponse):
    answers: List[QuizAnswerResponse]
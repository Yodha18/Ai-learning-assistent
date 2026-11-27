from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime


class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty: str = "medium"


class TopicCreate(TopicBase):
    subject_id: int


class TopicUpdate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int
    subject_id: int
    mastery_score: float
    last_practiced: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubjectWithTopics(SubjectResponse):
    topics: List[TopicResponse]
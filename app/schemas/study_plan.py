from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.study_plan import TaskStatus


class StudyTaskBase(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None
    task_type: str  # study, quiz, revision, etc.
    duration_minutes: int
    status: TaskStatus = TaskStatus.PENDING
    order: int


class StudyTaskCreate(StudyTaskBase):
    pass


class StudyTaskResponse(StudyTaskBase):
    id: int
    study_plan_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class StudyPlanBase(BaseModel):
    date: datetime
    total_study_time: int  # in minutes


class StudyPlanCreate(StudyPlanBase):
    pass


class StudyPlanResponse(StudyPlanBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StudyPlanWithTasks(StudyPlanResponse):
    tasks: List[StudyTaskResponse]


class StudyPlanGenerateRequest(BaseModel):
    daily_study_time: int  # in minutes
    regenerate: bool = False
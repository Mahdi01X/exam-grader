from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.exam import ExamStatus


class ExamCreate(BaseModel):
    title: str
    subject: str = ""


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[ExamStatus] = None


class ExamOut(BaseModel):
    id: int
    title: str
    subject: str
    status: ExamStatus
    owner_id: int
    rubric_source_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

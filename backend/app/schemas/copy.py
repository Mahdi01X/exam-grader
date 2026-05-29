from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.copy import CopyStatus


class CopyOut(BaseModel):
    id: int
    exam_id: int
    student_identifier: str
    file_path: str
    page_count: int
    status: CopyStatus
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradeOut(BaseModel):
    id: int
    copy_id: int
    rubric_item_id: int
    applied_policy_id: Optional[int]
    extracted_text: str
    proposed_points: float
    applied_fraction: float
    justification: str
    confidence: float
    needs_human_review: bool
    final_points: Optional[float]
    validated_by: Optional[int]
    validated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GradeOverride(BaseModel):
    final_points: float
    applied_policy_id: Optional[int] = None
    justification: Optional[str] = None


class CopyDetailOut(CopyOut):
    grades: List[GradeOut]

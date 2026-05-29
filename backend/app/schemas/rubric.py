from typing import Optional, List
from pydantic import BaseModel


class RubricItemIn(BaseModel):
    question_number: str
    intitule: str = ""
    expected_answer: str = ""
    points_max: float = 0.0
    ordre: int = 0


class RubricItemOut(RubricItemIn):
    id: int
    exam_id: int

    class Config:
        from_attributes = True


class RubricItemUpdate(BaseModel):
    question_number: Optional[str] = None
    intitule: Optional[str] = None
    expected_answer: Optional[str] = None
    points_max: Optional[float] = None
    ordre: Optional[int] = None


class RubricBulkReplace(BaseModel):
    items: List[RubricItemIn]

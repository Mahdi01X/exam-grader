from typing import Optional
from pydantic import BaseModel, Field


class PolicyIn(BaseModel):
    name: str
    condition_description: str = ""
    fraction_points: float = Field(ge=0.0, le=1.0)


class PolicyOut(PolicyIn):
    id: int
    exam_id: int

    class Config:
        from_attributes = True


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    condition_description: Optional[str] = None
    fraction_points: Optional[float] = Field(default=None, ge=0.0, le=1.0)

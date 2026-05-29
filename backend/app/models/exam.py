import enum
from typing import List
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class ExamStatus(str, enum.Enum):
    draft = "draft"
    rubric_pending = "rubric_pending"
    rubric_ready = "rubric_ready"
    grading = "grading"
    closed = "closed"


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ExamStatus] = mapped_column(
        SAEnum(ExamStatus, name="exam_status"), default=ExamStatus.draft, nullable=False
    )
    rubric_source_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    rubric_items: Mapped[List["RubricItem"]] = relationship(  # noqa: F821
        back_populates="exam", cascade="all, delete-orphan", order_by="RubricItem.ordre"
    )
    policies: Mapped[List["GradingPolicy"]] = relationship(  # noqa: F821
        back_populates="exam", cascade="all, delete-orphan"
    )
    copies: Mapped[List["StudentCopy"]] = relationship(  # noqa: F821
        back_populates="exam", cascade="all, delete-orphan"
    )

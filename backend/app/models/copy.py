import enum
from typing import List
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class CopyStatus(str, enum.Enum):
    uploaded = "uploaded"
    extracted = "extracted"
    graded = "graded"
    reviewed = "reviewed"
    failed = "failed"


class StudentCopy(Base, TimestampMixin):
    __tablename__ = "student_copies"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    page_count: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[CopyStatus] = mapped_column(
        SAEnum(CopyStatus, name="copy_status"),
        default=CopyStatus.uploaded,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    exam = relationship("Exam", back_populates="copies")
    grades: Mapped[List["QuestionGrade"]] = relationship(  # noqa: F821
        back_populates="copy", cascade="all, delete-orphan"
    )

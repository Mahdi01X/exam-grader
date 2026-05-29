from sqlalchemy import String, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class RubricItem(Base, TimestampMixin):
    __tablename__ = "rubric_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_number: Mapped[str] = mapped_column(String(32), nullable=False)
    intitule: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    points_max: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="rubric_items")

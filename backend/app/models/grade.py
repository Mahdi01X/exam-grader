from datetime import datetime
from sqlalchemy import Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class QuestionGrade(Base, TimestampMixin):
    """Note proposée par le pipeline pour une question d'une copie.

    Si le prof valide ou modifie : `final_points` et `validated_by` sont remplis.
    Tant que `validated_at` est nul, c'est une proposition non validée.
    """

    __tablename__ = "question_grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    copy_id: Mapped[int] = mapped_column(
        ForeignKey("student_copies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rubric_item_id: Mapped[int] = mapped_column(
        ForeignKey("rubric_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    applied_policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("grading_policies.id", ondelete="SET NULL"), nullable=True
    )

    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    proposed_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    applied_fraction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    justification: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    final_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    copy = relationship("StudentCopy", back_populates="grades")
    rubric_item = relationship("RubricItem")
    applied_policy = relationship("GradingPolicy")

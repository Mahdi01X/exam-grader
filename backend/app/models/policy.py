from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class GradingPolicy(Base, TimestampMixin):
    """Règles de notation partielle attachées à un examen.

    Le moteur Python applique ces règles (pas le LLM) pour garantir reproductibilité
    et auditabilité du calcul final.
    """

    __tablename__ = "grading_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fraction_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    exam = relationship("Exam", back_populates="policies")


DEFAULT_POLICIES: list[dict] = [
    {
        "name": "Réponse correcte et justifiée",
        "condition_description": "La réponse est correcte et la démarche/justification est complète.",
        "fraction_points": 1.0,
    },
    {
        "name": "Bonne démarche, résultat faux",
        "condition_description": "La démarche est correcte mais le résultat final est erroné (ex. erreur de calcul, de signe).",
        "fraction_points": 0.5,
    },
    {
        "name": "Résultat correct sans justification",
        "condition_description": "Le résultat est correct mais la justification est absente ou insuffisante.",
        "fraction_points": 0.5,
    },
    {
        "name": "Réponse partielle",
        "condition_description": "Une partie de la réponse est correcte mais incomplète. Pondération à ajuster.",
        "fraction_points": 0.25,
    },
    {
        "name": "Hors sujet / vide",
        "condition_description": "Pas de réponse, ou réponse sans rapport avec la question.",
        "fraction_points": 0.0,
    },
]

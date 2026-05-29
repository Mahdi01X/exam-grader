"""Moteur de notation côté Python.

Ce module prend les évaluations brutes produites par la vision et calcule la
note finale en appliquant les GradingPolicy de l'examen. Il ne fait AUCUN appel
au LLM : c'est volontaire, pour garantir reproductibilité et auditabilité.

Le LLM suggère une règle ; le Python décide laquelle appliquer (en validant que
la règle existe bien) et calcule points = points_max * fraction. Si la règle
suggérée n'existe pas, on retombe sur "Hors sujet / vide" et on force la revue.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.models.policy import GradingPolicy
from app.models.rubric import RubricItem


@dataclass
class ScoringResult:
    rubric_item_id: int
    extracted_text: str
    proposed_points: float
    applied_fraction: float
    applied_policy_id: Optional[int]
    justification: str
    confidence: float
    needs_human_review: bool


def _norm(s: str) -> str:
    return " ".join(s.lower().strip().split())


def find_policy(policies: list[GradingPolicy], suggested_name: str) -> Optional[GradingPolicy]:
    """Apparie le nom suggéré par le LLM à une policy connue.

    On compare insensiblement à la casse et aux espaces multiples. Si rien ne
    correspond exactement, on tente un préfixe — sinon None.
    """
    target = _norm(suggested_name)
    by_norm = {_norm(p.name): p for p in policies}
    if target in by_norm:
        return by_norm[target]
    # tolérance : préfixe
    for n, p in by_norm.items():
        if n.startswith(target) or target.startswith(n):
            return p
    return None


def fallback_zero_policy(policies: list[GradingPolicy]) -> Optional[GradingPolicy]:
    for p in policies:
        if p.fraction_points == 0.0:
            return p
    return None


def score_one(
    *,
    rubric_item: RubricItem,
    policies: list[GradingPolicy],
    transcription: str,
    suggested_policy_name: str,
    suggested_fraction: float,
    justification: str,
    confidence: float,
    found: bool,
) -> ScoringResult:
    """Calcule la note proposée pour une question, à partir des règles connues.

    - On ne croit jamais aveuglément le LLM sur le nombre de points : on applique
      points_max * fraction_de_la_policy_choisie.
    - Si la confiance est sous le seuil, ou si la copie ne contenait pas la
      réponse (found=False), needs_human_review=True.
    - Si la policy suggérée est inconnue, on tombe sur policy zéro + revue forcée.
    """
    settings = get_settings()
    threshold = settings.confidence_review_threshold

    policy = find_policy(policies, suggested_policy_name) if found else fallback_zero_policy(policies)
    forced_review = False
    if found and policy is None:
        policy = fallback_zero_policy(policies)
        forced_review = True
        justification = (
            f"[Règle suggérée '{suggested_policy_name}' introuvable. "
            f"Note remise à 0 et revue forcée.] {justification}"
        )

    fraction = policy.fraction_points if policy else 0.0
    points = round(rubric_item.points_max * fraction, 4)
    needs_review = (
        forced_review
        or confidence < threshold
        or not found
    )
    return ScoringResult(
        rubric_item_id=rubric_item.id,
        extracted_text=transcription,
        proposed_points=points,
        applied_fraction=fraction,
        applied_policy_id=policy.id if policy else None,
        justification=justification.strip(),
        confidence=max(0.0, min(1.0, confidence)),
        needs_human_review=needs_review,
    )

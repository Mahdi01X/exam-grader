"""Tests du moteur de notation.

Ces tests garantissent que :
- les points finaux sont = points_max * fraction de la règle appliquée (pas une
  invention du LLM),
- une règle inconnue déclenche une revue humaine et une note de 0,
- une confiance basse déclenche une revue humaine,
- une réponse non trouvée → 0 + revue.
"""
from dataclasses import dataclass

from app.grading.scorer import find_policy, score_one


@dataclass
class P:
    id: int
    name: str
    fraction_points: float


@dataclass
class R:
    id: int
    points_max: float


POLS = [
    P(id=1, name="Réponse correcte et justifiée", fraction_points=1.0),
    P(id=2, name="Bonne démarche, résultat faux", fraction_points=0.5),
    P(id=3, name="Hors sujet / vide", fraction_points=0.0),
]


def test_find_policy_exact_and_case_insensitive():
    assert find_policy(POLS, "Réponse correcte et justifiée").id == 1
    assert find_policy(POLS, "réponse correcte et justifiée").id == 1
    assert find_policy(POLS, "Bonne démarche, résultat faux").id == 2


def test_find_policy_unknown_returns_none():
    assert find_policy(POLS, "Excellent travail brillant") is None


def test_score_one_correct_full_points():
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="dérivée correcte",
        suggested_policy_name="Réponse correcte et justifiée",
        suggested_fraction=1.0,
        justification="ok",
        confidence=0.95,
        found=True,
    )
    assert result.proposed_points == 4.0
    assert result.applied_fraction == 1.0
    assert result.applied_policy_id == 1
    assert result.needs_human_review is False


def test_score_one_partial_credit_uses_policy_fraction_not_llm_value():
    """Le LLM peut suggérer fraction_suggeree=0.7 — on n'en tient PAS compte.
    Seule la fraction de la GradingPolicy choisie est utilisée."""
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="démarche ok mais erreur de signe",
        suggested_policy_name="Bonne démarche, résultat faux",
        suggested_fraction=0.7,  # ignoré
        justification="erreur de signe",
        confidence=0.9,
        found=True,
    )
    assert result.proposed_points == 2.0  # 4.0 * 0.5, pas * 0.7
    assert result.applied_fraction == 0.5
    assert result.needs_human_review is False


def test_score_one_unknown_policy_falls_to_zero_and_forces_review():
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="qqch",
        suggested_policy_name="Politique inventée par le LLM",
        suggested_fraction=0.8,
        justification="...",
        confidence=0.95,
        found=True,
    )
    assert result.proposed_points == 0.0
    assert result.needs_human_review is True
    assert "introuvable" in result.justification.lower()


def test_score_one_low_confidence_forces_review():
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="hésitation",
        suggested_policy_name="Réponse correcte et justifiée",
        suggested_fraction=1.0,
        justification="manuscrit difficile",
        confidence=0.5,
        found=True,
    )
    assert result.needs_human_review is True


def test_score_one_not_found_is_zero_and_review():
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="",
        suggested_policy_name="Hors sujet / vide",
        suggested_fraction=0.0,
        justification="absente",
        confidence=0.9,
        found=False,
    )
    assert result.proposed_points == 0.0
    assert result.applied_policy_id == 3
    assert result.needs_human_review is True


def test_score_clamps_confidence():
    result = score_one(
        rubric_item=R(id=10, points_max=4.0),
        policies=POLS,
        transcription="x",
        suggested_policy_name="Réponse correcte et justifiée",
        suggested_fraction=1.0,
        justification="",
        confidence=1.7,  # hors borne
        found=True,
    )
    assert result.confidence == 1.0

"""Tests du parsing de la sortie d'extraction de barème.

On vérifie que ExtractedRubric tolère les variations communes (champs
manquants par défaut, ordre des clés, etc.).
"""
from app.grading.rubric_extraction import ExtractedRubric


def test_full_payload():
    payload = {
        "items": [
            {
                "question_number": "1",
                "intitule": "Énoncé Q1",
                "expected_answer": "Réponse attendue",
                "points_max": 4.0,
                "ordre": 0,
            }
        ]
    }
    r = ExtractedRubric.model_validate(payload)
    assert len(r.items) == 1
    assert r.items[0].points_max == 4.0


def test_missing_optional_fields_default():
    payload = {"items": [{"question_number": "Q1"}]}
    r = ExtractedRubric.model_validate(payload)
    assert r.items[0].intitule == ""
    assert r.items[0].expected_answer == ""
    assert r.items[0].points_max == 0.0


def test_empty_items_list_is_valid():
    r = ExtractedRubric.model_validate({"items": []})
    assert r.items == []


def test_missing_items_key_defaults_to_empty():
    r = ExtractedRubric.model_validate({})
    assert r.items == []

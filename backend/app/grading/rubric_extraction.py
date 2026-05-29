"""Extraction du barème à partir du corrigé fourni par le prof.

NB : la sortie est TOUJOURS soumise à validation par le prof avant utilisation.
On ne fait pas confiance à l'extraction en silence.
"""
from __future__ import annotations
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from app.grading.vision import call_vision_json


RUBRIC_SYSTEM = """Tu es un assistant qui extrait le barème d'un corrigé d'examen universitaire.

Tu reçois une ou plusieurs images d'un corrigé. Tu dois identifier chaque question
(et sous-question le cas échéant), la réponse attendue, et le nombre de points.

Tu réponds UNIQUEMENT avec du JSON valide. PAS de markdown. PAS d'explication
hors JSON. Le format est strict :

{
  "items": [
    {
      "question_number": "1" | "1.a" | "Q2" ...,
      "intitule": "énoncé court de la question",
      "expected_answer": "réponse attendue, complète et précise",
      "points_max": 2.5,
      "ordre": 0
    }
  ]
}

Règles :
- Si tu n'es pas sûr du nombre de points d'une question, mets 0 et le prof corrigera.
- N'invente JAMAIS de question. Si tu ne vois rien clairement, retourne items vide.
- expected_answer doit être autosuffisant — le scoring s'en servira directement.
- Conserve l'ordre des questions dans le champ "ordre" (0, 1, 2, ...).
"""


class ExtractedRubricItem(BaseModel):
    question_number: str
    intitule: str = ""
    expected_answer: str = ""
    points_max: float = 0.0
    ordre: int = 0


class ExtractedRubric(BaseModel):
    items: List[ExtractedRubricItem] = Field(default_factory=list)


def extract_rubric(image_paths: list[Path]) -> ExtractedRubric:
    user_text = (
        "Voici le corrigé. Extrais le barème dans le format JSON demandé. "
        "Pas de prose, uniquement le JSON."
    )
    raw = call_vision_json(RUBRIC_SYSTEM, user_text, image_paths)
    return ExtractedRubric.model_validate(raw)

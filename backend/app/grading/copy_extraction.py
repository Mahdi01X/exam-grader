"""Transcription d'une copie étudiant + appariement aux questions du barème.

Pour chaque question du barème, on demande à la vision de :
1. retrouver la réponse correspondante dans la copie (manuscrite ou tapée),
2. la transcrire fidèlement,
3. suggérer la règle de notation la plus adaptée parmi celles fournies,
4. fournir une justification et un niveau de confiance.

Le SCORING (calcul des points) est ensuite fait côté Python à partir des
GradingPolicy — cf. app/grading/scorer.py.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from app.grading.vision import call_vision_json


GRADING_SYSTEM = """Tu es un assistant-correcteur pour un professeur d'université.

Tu reçois :
- les images d'une copie d'étudiant (manuscrite ou tapée),
- le barème (questions, réponses attendues, points max),
- la liste des règles de notation partielle disponibles.

Pour chaque question du barème, tu retournes une évaluation. Tu réponds
UNIQUEMENT avec du JSON valide, sans markdown ni préambule.

Format strict :

{
  "answers": [
    {
      "question_number": "1",
      "transcription": "transcription fidèle de la réponse de l'étudiant pour cette question (vide si introuvable)",
      "found": true | false,
      "regle_suggeree": "<nom exact d'une règle fournie>",
      "fraction_suggeree": 0.5,
      "justification": "explication concise : ce que l'étudiant a fait, en quoi cela correspond à la règle choisie",
      "confiance": 0.85
    }
  ]
}

Règles importantes :
- Tu ne calcules PAS le nombre de points final — ne retourne JAMAIS de "points".
  Le backend Python s'en charge à partir de la règle et de points_max.
- "regle_suggeree" DOIT correspondre exactement à un nom dans la liste fournie.
  Si vraiment aucune ne s'applique, mets "Hors sujet / vide" et fraction 0.
- "confiance" entre 0 et 1 : 1 = certain, 0 = aucune idée. Sois honnête : si la
  copie est illisible ou ambiguë, mets une confiance faible (< 0.6) — le prof
  relira ces cas. Mieux vaut une note proposée incertaine qu'une fausse certitude.
- Si la question est absente de la copie, found=false, transcription="",
  regle_suggeree="Hors sujet / vide", confiance reflète ta certitude de l'absence.
- Pour les copies manuscrites : transcris ce que tu déchiffres. Si tu hésites
  entre deux interprétations, choisis la plus probable et baisse la confiance.
"""


class CopyAnswer(BaseModel):
    question_number: str
    transcription: str = ""
    found: bool = False
    regle_suggeree: str = ""
    fraction_suggeree: float = 0.0
    justification: str = ""
    confiance: float = 0.0


class ExtractedCopy(BaseModel):
    answers: List[CopyAnswer] = Field(default_factory=list)


def extract_copy_answers(
    image_paths: list[Path],
    rubric_items: list[dict],
    policies: list[dict],
) -> ExtractedCopy:
    """rubric_items et policies sont passés sous forme de dicts simples."""
    user_payload = {
        "rubric": rubric_items,
        "policies": [{"name": p["name"], "fraction": p["fraction_points"], "desc": p["condition_description"]} for p in policies],
    }
    user_text = (
        "Voici le barème et les règles de notation. Évalue la copie ci-dessus "
        "question par question. Réponds uniquement avec le JSON demandé.\n\n"
        f"{json.dumps(user_payload, ensure_ascii=False)}"
    )
    raw = call_vision_json(GRADING_SYSTEM, user_text, image_paths)
    return ExtractedCopy.model_validate(raw)

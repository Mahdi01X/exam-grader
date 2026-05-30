"""Extraction du barème à partir du corrigé fourni par le prof.

NB : la sortie est TOUJOURS soumise à validation par le prof avant utilisation.
On ne fait pas confiance à l'extraction en silence.
"""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any, List

from pydantic import BaseModel, Field

from app.grading.vision import call_vision_json

logger = logging.getLogger(__name__)


RUBRIC_SYSTEM = """Tu es un assistant qui extrait le barème d'un corrigé d'examen universitaire.

Tu reçois une ou plusieurs images d'un corrigé (souvent une PHOTO manuscrite,
parfois mal cadrée, avec ombres : déchiffre du mieux possible).

Tu dois identifier chaque question (et sous-question le cas échéant), la réponse
attendue, et le nombre de points.

Tu réponds UNIQUEMENT avec du JSON valide. PAS de markdown. PAS d'explication
hors JSON. Le format est strict :

{
  "items": [
    {
      "question_number": "1",
      "intitule": "énoncé court de la question (ou le symbole/label si c'est une simple liste de résultats)",
      "expected_answer": "réponse attendue, complète et précise",
      "points_max": 2.5,
      "ordre": 0
    }
  ]
}

Règles :
- TOUJOURS renseigner "question_number". S'il n'y a pas de numéro explicite dans
  le corrigé, numérote séquentiellement : "1", "2", "3"…
- Si le corrigé est une simple LISTE DE RÉSULTATS (ex. « Pv1 = 321 Pa »,
  « gv = 1,536e-8 »), crée UN item par résultat : mets le symbole/label dans
  "intitule" et la valeur dans "expected_answer". N'abandonne pas.
- Si tu n'es pas sûr du nombre de points, mets 0 (le prof corrigera).
- N'invente JAMAIS de contenu. Si une image est totalement illisible, retourne
  "items": [] — mais essaie d'abord vraiment de lire.
- expected_answer doit être autosuffisant — le scoring s'en servira directement.
- Conserve l'ordre dans "ordre" (0, 1, 2, ...).
"""


class ExtractedRubricItem(BaseModel):
    question_number: str
    intitule: str = ""
    expected_answer: str = ""
    points_max: float = 0.0
    ordre: int = 0


class ExtractedRubric(BaseModel):
    items: List[ExtractedRubricItem] = Field(default_factory=list)


def _to_float(value: Any) -> float:
    """Convertit « 2,5 », « 2.5 pts », 2, None… en float (0.0 si rien d'exploitable)."""
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value))
    return float(m.group().replace(",", ".")) if m else 0.0


def _first_str(item: dict, keys: tuple[str, ...]) -> str:
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return str(v)
    return ""


def _extract_items_list(raw: Any) -> list:
    """Retrouve la liste d'items quelle que soit la forme renvoyée par le modèle.

    Le modèle peut répondre {"items": [...]}, une liste nue, {"barème": [...]},
    {"questions": [...]}, ou un dict mono-item. On encaisse tout.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("items", "questions", "barème", "bareme", "rubric", "data", "result"):
            val = raw.get(key)
            if isinstance(val, list):
                return val
        # Un dict de dicts (ex. {"1": {...}, "2": {...}}) → on prend les valeurs.
        if raw and all(isinstance(v, dict) for v in raw.values()):
            return list(raw.values())
        # Un dict qui EST déjà un item unique.
        if any(k in raw for k in ("question_number", "intitule", "expected_answer", "points_max")):
            return [raw]
    return []


def _normalize(raw: Any) -> ExtractedRubric:
    """Construit un barème valide à partir d'une sortie modèle imparfaite.

    Tolère les champs manquants/mal nommés (notamment l'absence de
    "question_number" sur un corrigé manuscrit sans numéros) au lieu de lever
    une ValidationError (qui se traduisait par une 500 opaque à l'import).
    """
    items_data = _extract_items_list(raw)
    out: list[ExtractedRubricItem] = []
    for i, it in enumerate(items_data):
        if not isinstance(it, dict):
            continue
        qn = _first_str(it, ("question_number", "number", "num", "q", "id"))
        if not qn:
            qn = str(i + 1)  # numérotation séquentielle si absente
        out.append(
            ExtractedRubricItem(
                question_number=qn,
                intitule=_first_str(it, ("intitule", "question", "label", "libelle", "title")),
                expected_answer=_first_str(
                    it, ("expected_answer", "answer", "reponse", "réponse", "solution", "value")
                ),
                points_max=_to_float(
                    it.get("points_max", it.get("points", it.get("bareme", it.get("barème"))))
                ),
                ordre=i,
            )
        )
    return ExtractedRubric(items=out)


def extract_rubric(image_paths: list[Path]) -> ExtractedRubric:
    user_text = (
        "Voici le corrigé. Extrais le barème dans le format JSON demandé. "
        "Pas de prose, uniquement le JSON."
    )
    raw = call_vision_json(RUBRIC_SYSTEM, user_text, image_paths)
    rubric = _normalize(raw)
    logger.info("rubric extraction: %d item(s)", len(rubric.items))
    return rubric

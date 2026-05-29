"""Wrapper minimal autour de l'API OpenAI (vision), optimisé pour notre usage.

Principes :
- Sortie JSON stricte (response_format json_object). Le prompt l'exige aussi, et on
  parse défensivement.
- Température basse (configurée), max_tokens raisonnable → reproductibilité.
- Retry exponentiel sur erreurs transitoires.
- Pas de PII dans les logs.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Iterable, List

from openai import OpenAI, APIError, APIStatusError

from app.core.config import get_settings
from app.services.documents import resize_for_vision

logger = logging.getLogger(__name__)


class VisionError(RuntimeError):
    pass


class VisionUnavailable(VisionError):
    """L'API est indisponible — l'UI doit afficher le mode dégradé."""


def _client() -> OpenAI:
    s = get_settings()
    if not s.openai_api_key:
        raise VisionUnavailable(
            "OPENAI_API_KEY missing — set it in .env before running grading"
        )
    return OpenAI(api_key=s.openai_api_key)


def _image_content(paths: Iterable[Path]) -> list[dict]:
    """Construit les blocs image au format OpenAI (data URI base64)."""
    out: list[dict] = []
    for p in paths:
        b64, media_type = resize_for_vision(p)
        out.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{b64}"},
            }
        )
    return out


def _strip_json(text: str) -> str:
    """Extrait un objet JSON même si le modèle ajoute des fences markdown."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text.startswith("{") and "{" in text:
        text = text[text.index("{") :]
    if not text.endswith("}") and "}" in text:
        text = text[: text.rindex("}") + 1]
    return text


def call_vision_json(
    system: str,
    user_text: str,
    image_paths: List[Path],
    *,
    max_retries: int = 3,
) -> dict:
    """Appelle le modèle vision OpenAI et retourne un dict JSON.

    Lève VisionError si le JSON ne peut pas être parsé après retries.
    """
    s = get_settings()
    client = _client()

    user_content: list[dict] = _image_content(image_paths)
    user_content.append({"type": "text", "text": user_text})
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=s.openai_model,
                max_tokens=s.openai_max_tokens,
                temperature=s.openai_temperature,
                response_format={"type": "json_object"},
                messages=messages,
            )
            raw = resp.choices[0].message.content or ""
            cleaned = _strip_json(raw)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "vision returned non-JSON (attempt %d): %s", attempt + 1, exc
                )
                last_exc = exc
        except APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            logger.warning(
                "vision API status error (attempt %d): %s", attempt + 1, status_code
            )
            last_exc = exc
            # Erreurs client (4xx) non transitoires : inutile de réessayer (sauf 429).
            if status_code and 400 <= status_code < 500 and status_code != 429:
                raise VisionError(f"vision API client error {status_code}") from exc
        except APIError as exc:
            logger.warning("vision API error (attempt %d): %s", attempt + 1, exc)
            last_exc = exc
        time.sleep(2 ** attempt)

    raise VisionError(f"vision call failed after {max_retries} attempts: {last_exc}")

"""Conversion PDF → images haute résolution pour la vision (OpenAI).

On rend les pages à 300 DPI par défaut (configurable). Sortie en PNG pour
préserver la lisibilité du manuscrit.
"""
from __future__ import annotations
import base64
import io
import logging
from pathlib import Path
from typing import List, Tuple

from PIL import Image
from pdf2image import convert_from_path
from pypdf import PdfReader

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def count_pdf_pages(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def render_pdf_to_pngs(path: Path, output_dir: Path, dpi: int | None = None) -> List[Path]:
    """Rend chaque page d'un PDF en PNG dans output_dir/page-XXX.png."""
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    dpi = dpi or settings.pdf_render_dpi
    # poppler_path vide => on s'appuie sur le PATH (cas Docker/Linux).
    poppler_path = settings.poppler_path or None
    pages = convert_from_path(str(path), dpi=dpi, fmt="png", poppler_path=poppler_path)
    out: List[Path] = []
    for idx, img in enumerate(pages, start=1):
        dst = output_dir / f"page-{idx:03d}.png"
        img.save(dst, "PNG", optimize=True)
        out.append(dst)
    logger.info("rendered %d pages from %s at %d DPI", len(out), path.name, dpi)
    return out


def resize_for_vision(img_path: Path, max_long_side: int = 1568) -> Tuple[str, str]:
    """Redimensionne pour rester sous la limite de l'API vision.

    Retourne (base64_data, media_type) prêts à passer dans le payload vision.
    Le côté le plus long est plafonné — bonne lisibilité du manuscrit conservée.
    """
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        long_side = max(w, h)
        if long_side > max_long_side:
            ratio = max_long_side / long_side
            im = im.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii"), "image/png"


def get_page_images(file_path: Path, output_dir: Path) -> List[Path]:
    """Retourne la liste des PNG à passer à la vision.

    Si l'entrée est un PDF, on rend. Sinon (image), on la copie en page unique.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return render_pdf_to_pngs(file_path, output_dir)
    if suffix in (".png", ".jpg", ".jpeg", ".webp"):
        output_dir.mkdir(parents=True, exist_ok=True)
        dst = output_dir / "page-001.png"
        with Image.open(file_path) as im:
            im.convert("RGB").save(dst, "PNG", optimize=True)
        return [dst]
    raise ValueError(f"unsupported file type: {suffix}")

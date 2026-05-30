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

# Support optionnel des photos iPhone (HEIC/HEIF). Si pillow-heif est présent,
# Pillow saura ouvrir ces fichiers ; sinon on l'ignore (les autres formats
# continuent de fonctionner).
try:  # pragma: no cover - dépend de l'environnement
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
    _HEIC_OK = True
except Exception:  # noqa: BLE001
    _HEIC_OK = False

# Formats image acceptés (Pillow gère nativement bmp/gif/tiff ; HEIC via pillow-heif).
IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif",
}
# Tout ce qu'on accepte à l'upload (corrigé ou copie) : PDF + images.
ALLOWED_UPLOAD_SUFFIXES = {".pdf"} | IMAGE_SUFFIXES


def count_pdf_pages(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def render_pdf_to_pngs(path: Path, output_dir: Path, dpi: int | None = None) -> List[Path]:
    """Rend chaque page d'un PDF en PNG dans output_dir/page-XXX.png.

    Rendu PAGE PAR PAGE : `convert_from_path` chargerait sinon toutes les pages
    en RAM simultanément (≈25 Mo/page à 300 DPI), ce qui fait sauter les petites
    instances cloud (512 Mo). On borne la mémoire à une page à la fois.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    dpi = dpi or settings.pdf_render_dpi
    # poppler_path vide => on s'appuie sur le PATH (cas Docker/Linux).
    poppler_path = settings.poppler_path or None
    total = count_pdf_pages(path)
    out: List[Path] = []
    for i in range(1, total + 1):
        imgs = convert_from_path(
            str(path),
            dpi=dpi,
            fmt="png",
            first_page=i,
            last_page=i,
            poppler_path=poppler_path,
        )
        if imgs:
            dst = output_dir / f"page-{i:03d}.png"
            imgs[0].save(dst, "PNG", optimize=True)
            out.append(dst)
            del imgs  # libère la mémoire de la page avant la suivante
    logger.info("rendered %d pages from %s at %d DPI (page-by-page)", len(out), path.name, dpi)
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
    if suffix in IMAGE_SUFFIXES:
        if suffix in (".heic", ".heif") and not _HEIC_OK:
            raise ValueError(
                "format HEIC non pris en charge sur ce serveur — convertissez la "
                "photo en JPG/PNG, ou installez pillow-heif"
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        dst = output_dir / "page-001.png"
        with Image.open(file_path) as im:
            # GIF/TIFF multi-frames : la 1re image suffit. convert('RGB') gère le
            # mode (P, RGBA, CMYK…) sans planter à l'enregistrement PNG.
            im.convert("RGB").save(dst, "PNG", optimize=True)
        return [dst]
    raise ValueError(f"format de fichier non supporté : {suffix}")

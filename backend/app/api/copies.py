from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import current_user
from app.models.exam import Exam
from app.models.copy import StudentCopy, CopyStatus
from app.models.grade import QuestionGrade
from app.models.user import User, UserRole
from app.schemas.copy import CopyOut, CopyDetailOut
from app.services import audit
from app.services.documents import count_pdf_pages, get_page_images
from app.storage import get_storage

router = APIRouter(prefix="/api/exams/{exam_id}/copies", tags=["copies"])


def _exam_or_403(db: Session, exam_id: int, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role != UserRole.admin and exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return exam


ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


@router.post("", response_model=CopyOut, status_code=status.HTTP_201_CREATED)
async def upload_copy(
    exam_id: int,
    student_identifier: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unsupported file type {suffix}")

    storage = get_storage()
    rel = f"exam-{exam_id}/copies/{student_identifier}/source{suffix}"
    abs_path = storage.absolute(rel)
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    limit = settings.max_upload_mb * 1024 * 1024
    with open(abs_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > limit:
                out.close()
                abs_path.unlink(missing_ok=True)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    f"file exceeds {settings.max_upload_mb} MB",
                )
            out.write(chunk)

    page_count = 1
    if suffix == ".pdf":
        try:
            page_count = count_pdf_pages(abs_path)
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid pdf: {e}")

    pages_dir = storage.absolute(f"exam-{exam_id}/copies/{student_identifier}/pages")
    try:
        get_page_images(abs_path, pages_dir)
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"render failed: {e}")

    copy = StudentCopy(
        exam_id=exam_id,
        student_identifier=student_identifier,
        file_path=rel,
        page_count=page_count,
        status=CopyStatus.uploaded,
    )
    db.add(copy)
    db.flush()
    audit.log_action(
        db, entity="student_copy", entity_id=copy.id, action="upload",
        user_id=user.id, new_value={"student": student_identifier, "pages": page_count},
    )
    db.commit()
    db.refresh(copy)
    return copy


@router.get("", response_model=List[CopyOut])
def list_copies(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    _exam_or_403(db, exam_id, user)
    return (
        db.query(StudentCopy)
        .filter(StudentCopy.exam_id == exam_id)
        .order_by(StudentCopy.created_at.desc())
        .all()
    )


@router.get("/{copy_id}", response_model=CopyDetailOut)
def get_copy(
    exam_id: int,
    copy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    grades = db.query(QuestionGrade).filter(QuestionGrade.copy_id == copy.id).all()
    return CopyDetailOut(
        **CopyOut.model_validate(copy).model_dump(),
        grades=grades,
    )


@router.get("/{copy_id}/pages/{page_number}")
def get_page_image(
    exam_id: int,
    copy_id: int,
    page_number: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    storage = get_storage()
    pages_dir = storage.absolute(f"exam-{exam_id}/copies/{copy.student_identifier}/pages")
    path = pages_dir / f"page-{page_number:03d}.png"
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "page not found")
    return FileResponse(path, media_type="image/png")


@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_copy(
    exam_id: int,
    copy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Suppression de la copie et de ses fichiers (RGPD)."""
    _exam_or_403(db, exam_id, user)
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    storage = get_storage()
    # Supprime fichiers
    base = storage.absolute(f"exam-{exam_id}/copies/{copy.student_identifier}")
    if base.exists():
        import shutil
        shutil.rmtree(base, ignore_errors=True)
    audit.log_action(
        db, entity="student_copy", entity_id=copy.id, action="delete",
        user_id=user.id, old_value={"student": copy.student_identifier},
    )
    db.delete(copy)
    db.commit()

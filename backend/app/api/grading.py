from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import current_user
from app.grading.rubric_extraction import extract_rubric
from app.grading.vision import VisionError, VisionUnavailable
from app.models.copy import StudentCopy, CopyStatus
from app.models.exam import Exam, ExamStatus
from app.models.grade import QuestionGrade
from app.models.user import User, UserRole
from app.schemas.copy import GradeOut, GradeOverride
from app.schemas.rubric import RubricItemIn
from app.services import audit
from app.services.documents import get_page_images
from app.services.grading import grade_copy, override_grade
from app.storage import get_storage

router = APIRouter(prefix="/api/exams/{exam_id}", tags=["grading"])


def _exam_or_403(db: Session, exam_id: int, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role != UserRole.admin and exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return exam


@router.post("/rubric/extract", response_model=list[RubricItemIn])
def extract_rubric_endpoint(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Le prof dépose le corrigé. On rend les pages, on extrait via vision,
    puis on retourne une PROPOSITION de barème — qu'il devra valider via
    PUT /rubric/bulk avant de continuer.

    Endpoint synchrone (`def`) : le rendu PDF→PNG et l'appel vision (bloquants)
    s'exécutent dans le threadpool FastAPI, jamais sur l'event loop — sinon ils
    gèlent le health-check de l'instance Render (→ 502 perçu comme erreur CORS).
    """
    exam = _exam_or_403(db, exam_id, user)
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unsupported file type {suffix}")

    storage = get_storage()
    rel = f"exam-{exam_id}/rubric/source{suffix}"
    abs_path = storage.absolute(rel)
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    limit = settings.max_upload_mb * 1024 * 1024
    with open(abs_path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > limit:
                out.close()
                abs_path.unlink(missing_ok=True)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    f"file exceeds {settings.max_upload_mb} MB",
                )
            out.write(chunk)

    pages_dir = storage.absolute(f"exam-{exam_id}/rubric/pages")
    try:
        pages = get_page_images(abs_path, pages_dir)
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"render failed: {e}")

    try:
        extracted = extract_rubric(pages)
    except VisionUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except VisionError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"vision failed: {e}")

    exam.rubric_source_path = rel
    exam.status = ExamStatus.rubric_pending
    audit.log_action(
        db, entity="exam", entity_id=exam.id, action="rubric_extract",
        user_id=user.id, new_value={"items": len(extracted.items)},
    )
    db.commit()

    # On retourne la proposition — la persistance définitive passe par bulk_replace
    return [RubricItemIn(**i.model_dump()) for i in extracted.items]


@router.post("/copies/{copy_id}/grade", response_model=list[GradeOut])
def grade_copy_endpoint(
    exam_id: int,
    copy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exam = _exam_or_403(db, exam_id, user)
    if exam.status != ExamStatus.rubric_ready and exam.status != ExamStatus.grading:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "rubric must be validated (status=rubric_ready) before grading",
        )
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    try:
        grade_copy(db, copy, user_id=user.id)
    except VisionUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except VisionError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"vision failed: {e}")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    if exam.status == ExamStatus.rubric_ready:
        exam.status = ExamStatus.grading
        db.commit()

    grades = db.query(QuestionGrade).filter(QuestionGrade.copy_id == copy.id).all()
    return grades


@router.post(
    "/copies/{copy_id}/grades/{grade_id}/override",
    response_model=GradeOut,
)
def override_grade_endpoint(
    exam_id: int,
    copy_id: int,
    grade_id: int,
    payload: GradeOverride,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    grade = db.get(QuestionGrade, grade_id)
    if not grade or grade.copy_id != copy_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    rubric = grade.rubric_item
    if payload.final_points < 0 or payload.final_points > rubric.points_max:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"points must be between 0 and {rubric.points_max}",
        )
    return override_grade(
        db,
        grade,
        final_points=payload.final_points,
        user_id=user.id,
        applied_policy_id=payload.applied_policy_id,
        justification=payload.justification,
    )


@router.post("/copies/{copy_id}/finalize", status_code=status.HTTP_204_NO_CONTENT)
def finalize_copy(
    exam_id: int,
    copy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Marque la copie comme `reviewed` : toutes les notes doivent avoir un
    `final_points` ou être explicitement validées comme conformes à la
    proposition. Les notes non touchées sont auto-validées à proposed_points.
    """
    _exam_or_403(db, exam_id, user)
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    from datetime import datetime, timezone

    grades = db.query(QuestionGrade).filter(QuestionGrade.copy_id == copy.id).all()
    for g in grades:
        if g.final_points is None:
            g.final_points = g.proposed_points
            g.validated_by = user.id
            g.validated_at = datetime.now(timezone.utc)
            g.needs_human_review = False
    copy.status = CopyStatus.reviewed
    audit.log_action(
        db, entity="student_copy", entity_id=copy.id, action="finalize",
        user_id=user.id, new_value={"grades": len(grades)},
    )
    db.commit()

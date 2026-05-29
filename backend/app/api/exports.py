from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import current_user
from app.models.copy import StudentCopy
from app.models.exam import Exam
from app.models.grade import QuestionGrade
from app.models.rubric import RubricItem
from app.models.user import User, UserRole
from app.services.exports import annotated_pdf, class_xlsx

router = APIRouter(prefix="/api/exams/{exam_id}/export", tags=["exports"])


def _exam_or_403(db: Session, exam_id: int, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role != UserRole.admin and exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return exam


@router.get("/class.xlsx")
def export_class_xlsx(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    exam = _exam_or_403(db, exam_id, user)
    rubric = (
        db.query(RubricItem).filter(RubricItem.exam_id == exam_id).order_by(RubricItem.ordre).all()
    )
    copies = (
        db.query(StudentCopy).filter(StudentCopy.exam_id == exam_id).order_by(StudentCopy.student_identifier).all()
    )
    grades = db.query(QuestionGrade).filter(
        QuestionGrade.copy_id.in_([c.id for c in copies])
    ).all()
    by_copy: dict[int, list[QuestionGrade]] = defaultdict(list)
    for g in grades:
        by_copy[g.copy_id].append(g)
    data = class_xlsx(exam, rubric, copies, by_copy)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="exam-{exam_id}-notes.xlsx"'},
    )


@router.get("/copy/{copy_id}.pdf")
def export_copy_pdf(
    exam_id: int,
    copy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exam = _exam_or_403(db, exam_id, user)
    copy = db.get(StudentCopy, copy_id)
    if not copy or copy.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    rubric = (
        db.query(RubricItem).filter(RubricItem.exam_id == exam_id).order_by(RubricItem.ordre).all()
    )
    grades = db.query(QuestionGrade).filter(QuestionGrade.copy_id == copy.id).all()
    data = annotated_pdf(exam, copy, rubric, grades)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="copy-{copy.student_identifier}.pdf"'},
    )


@router.get("/dashboard")
def dashboard(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    _exam_or_403(db, exam_id, user)
    rubric = db.query(RubricItem).filter(RubricItem.exam_id == exam_id).all()
    total_max = sum(r.points_max for r in rubric)
    copies = db.query(StudentCopy).filter(StudentCopy.exam_id == exam_id).all()
    grades = db.query(QuestionGrade).filter(
        QuestionGrade.copy_id.in_([c.id for c in copies])
    ).all()
    by_copy: dict[int, list[QuestionGrade]] = {}
    for g in grades:
        by_copy.setdefault(g.copy_id, []).append(g)

    totals: list[float] = []
    per_copy = []
    pending_review = 0
    for c in copies:
        gs = by_copy.get(c.id, [])
        total = sum(
            (g.final_points if g.final_points is not None else g.proposed_points) for g in gs
        )
        totals.append(total)
        review_for_this = sum(1 for g in gs if g.needs_human_review)
        pending_review += review_for_this
        per_copy.append({
            "copy_id": c.id,
            "student_identifier": c.student_identifier,
            "total": round(total, 2),
            "status": c.status.value,
            "needs_review_count": review_for_this,
        })

    avg = round(sum(totals) / len(totals), 2) if totals else 0
    sorted_totals = sorted(totals)
    median = round(sorted_totals[len(sorted_totals) // 2], 2) if sorted_totals else 0
    # distribution par tranches de 10% du total_max
    buckets = [0] * 10
    if total_max > 0:
        for t in totals:
            idx = min(int((t / total_max) * 10), 9)
            buckets[idx] += 1

    return {
        "total_max": round(total_max, 2),
        "copies_count": len(copies),
        "pending_review_count": pending_review,
        "average": avg,
        "median": median,
        "distribution": buckets,
        "per_copy": per_copy,
    }

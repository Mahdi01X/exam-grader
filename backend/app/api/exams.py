from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import current_user
from app.models.exam import Exam, ExamStatus
from app.models.user import User, UserRole
from app.schemas.exam import ExamCreate, ExamOut, ExamUpdate
from app.services import audit
from app.services.exam import create_exam

router = APIRouter(prefix="/api/exams", tags=["exams"])


def _check_access(exam: Exam, user: User) -> None:
    if user.role == UserRole.admin:
        return
    if exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not your exam")


@router.get("", response_model=List[ExamOut])
def list_exams(db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Exam)
    if user.role != UserRole.admin:
        q = q.filter(Exam.owner_id == user.id)
    return q.order_by(Exam.created_at.desc()).all()


@router.post("", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return create_exam(db, payload, owner_id=user.id)


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    _check_access(exam, user)
    return exam


@router.patch("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    _check_access(exam, user)
    old = {"title": exam.title, "subject": exam.subject, "status": exam.status.value}
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and isinstance(data["status"], ExamStatus):
        data["status"] = data["status"]
    for k, v in data.items():
        setattr(exam, k, v)
    audit.log_action(
        db, entity="exam", entity_id=exam.id, action="update",
        user_id=user.id, old_value=old, new_value=data,
    )
    db.commit()
    db.refresh(exam)
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    _check_access(exam, user)
    audit.log_action(
        db, entity="exam", entity_id=exam.id, action="delete", user_id=user.id,
        old_value={"title": exam.title},
    )
    db.delete(exam)
    db.commit()

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import current_user
from app.models.exam import Exam
from app.models.policy import GradingPolicy
from app.models.user import User, UserRole
from app.schemas.policy import PolicyIn, PolicyOut, PolicyUpdate
from app.services import audit

router = APIRouter(prefix="/api/exams/{exam_id}/policies", tags=["policies"])


def _exam_or_403(db: Session, exam_id: int, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role != UserRole.admin and exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return exam


@router.get("", response_model=List[PolicyOut])
def list_policies(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    _exam_or_403(db, exam_id, user)
    return db.query(GradingPolicy).filter(GradingPolicy.exam_id == exam_id).all()


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    exam_id: int,
    payload: PolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    p = GradingPolicy(exam_id=exam_id, **payload.model_dump())
    db.add(p)
    db.flush()
    audit.log_action(
        db, entity="grading_policy", entity_id=p.id, action="create",
        user_id=user.id, new_value=payload.model_dump(),
    )
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(
    exam_id: int,
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    p = db.get(GradingPolicy, policy_id)
    if not p or p.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    old = {"name": p.name, "fraction_points": p.fraction_points}
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    audit.log_action(
        db, entity="grading_policy", entity_id=p.id, action="update",
        user_id=user.id, old_value=old, new_value=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    exam_id: int,
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    p = db.get(GradingPolicy, policy_id)
    if not p or p.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    audit.log_action(
        db, entity="grading_policy", entity_id=p.id, action="delete",
        user_id=user.id, old_value={"name": p.name},
    )
    db.delete(p)
    db.commit()

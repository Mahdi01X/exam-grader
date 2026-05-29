from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import current_user
from app.models.exam import Exam, ExamStatus
from app.models.rubric import RubricItem
from app.models.user import User, UserRole
from app.schemas.rubric import (
    RubricItemIn,
    RubricItemOut,
    RubricItemUpdate,
    RubricBulkReplace,
)
from app.services import audit

router = APIRouter(prefix="/api/exams/{exam_id}/rubric", tags=["rubric"])


def _exam_or_403(db: Session, exam_id: int, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role != UserRole.admin and exam.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return exam


@router.get("", response_model=List[RubricItemOut])
def list_items(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    return (
        db.query(RubricItem)
        .filter(RubricItem.exam_id == exam_id)
        .order_by(RubricItem.ordre, RubricItem.id)
        .all()
    )


@router.post("", response_model=RubricItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    exam_id: int,
    payload: RubricItemIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    item = RubricItem(exam_id=exam_id, **payload.model_dump())
    db.add(item)
    db.flush()
    audit.log_action(
        db, entity="rubric_item", entity_id=item.id, action="create",
        user_id=user.id, new_value=payload.model_dump(),
    )
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=RubricItemOut)
def update_item(
    exam_id: int,
    item_id: int,
    payload: RubricItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    item = db.get(RubricItem, item_id)
    if not item or item.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    old = {
        "question_number": item.question_number,
        "intitule": item.intitule,
        "expected_answer": item.expected_answer,
        "points_max": item.points_max,
    }
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    audit.log_action(
        db, entity="rubric_item", entity_id=item.id, action="update",
        user_id=user.id, old_value=old, new_value=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    exam_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _exam_or_403(db, exam_id, user)
    item = db.get(RubricItem, item_id)
    if not item or item.exam_id != exam_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    audit.log_action(
        db, entity="rubric_item", entity_id=item.id, action="delete",
        user_id=user.id, old_value={"question_number": item.question_number},
    )
    db.delete(item)
    db.commit()


@router.put("/bulk", response_model=List[RubricItemOut])
def bulk_replace(
    exam_id: int,
    payload: RubricBulkReplace,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Remplace tous les items du barème par la nouvelle liste.

    Utilisé par l'écran de validation après extraction vision : le prof relit,
    corrige, puis enregistre. Cela passe l'examen en `rubric_ready`.
    """
    exam = _exam_or_403(db, exam_id, user)
    db.query(RubricItem).filter(RubricItem.exam_id == exam_id).delete()
    new_items = []
    for idx, it in enumerate(payload.items):
        ri = RubricItem(
            exam_id=exam_id,
            question_number=it.question_number,
            intitule=it.intitule,
            expected_answer=it.expected_answer,
            points_max=it.points_max,
            ordre=it.ordre or idx,
        )
        db.add(ri)
        new_items.append(ri)
    exam.status = ExamStatus.rubric_ready
    audit.log_action(
        db, entity="exam", entity_id=exam.id, action="rubric_validate",
        user_id=user.id, new_value={"count": len(new_items)},
    )
    db.commit()
    for item in new_items:
        db.refresh(item)
    return new_items

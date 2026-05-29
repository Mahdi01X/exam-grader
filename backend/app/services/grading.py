"""Orchestration : extraction copie → scoring Python → persistance."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.grading.copy_extraction import extract_copy_answers, CopyAnswer
from app.grading.scorer import score_one
from app.grading.vision import VisionError
from app.models.copy import StudentCopy, CopyStatus
from app.models.exam import Exam
from app.models.grade import QuestionGrade
from app.models.policy import GradingPolicy
from app.models.rubric import RubricItem
from app.services import audit
from app.services.documents import get_page_images
from app.storage import get_storage

logger = logging.getLogger(__name__)


def _page_paths(copy: StudentCopy) -> list[Path]:
    storage = get_storage()
    pages_dir = storage.absolute(
        f"exam-{copy.exam_id}/copies/{copy.student_identifier}/pages"
    )
    return sorted(pages_dir.glob("page-*.png"))


def ensure_copy_pages(copy: StudentCopy) -> list[Path]:
    """Garantit que les PNG des pages existent, en les rendant si besoin.

    Le rendu PDF→PNG est volontairement déporté ici (hors de l'upload) : il est
    lourd et bloquant, et le faire pendant la requête d'upload faisait tomber la
    petite instance Render (→ 502). Ici on est appelé depuis la notation, un
    endpoint synchrone exécuté dans le threadpool : l'event loop reste libre.
    """
    pages = _page_paths(copy)
    if pages:
        return pages
    storage = get_storage()
    source = storage.absolute(copy.file_path)
    if not source.exists():
        raise ValueError(
            "fichier source de la copie introuvable — le stockage éphémère a "
            "peut-être été purgé (redéploiement) ; redéposez la copie"
        )
    pages_dir = storage.absolute(
        f"exam-{copy.exam_id}/copies/{copy.student_identifier}/pages"
    )
    return get_page_images(source, pages_dir)


def _by_qnum(answers: list[CopyAnswer]) -> dict[str, CopyAnswer]:
    return {a.question_number.strip(): a for a in answers}


def grade_copy(db: Session, copy: StudentCopy, user_id: Optional[int] = None) -> StudentCopy:
    """Pipeline complet : extraction copie + scoring + persistance.

    Idempotent : si des QuestionGrade existent déjà pour cette copie, ils sont
    remplacés (sauf ceux validés par le prof, qu'on préserve).
    """
    exam: Exam = db.get(Exam, copy.exam_id)
    rubric = (
        db.query(RubricItem)
        .filter(RubricItem.exam_id == exam.id)
        .order_by(RubricItem.ordre)
        .all()
    )
    if not rubric:
        raise ValueError("rubric is empty — validate the rubric before grading")
    policies = db.query(GradingPolicy).filter(GradingPolicy.exam_id == exam.id).all()
    if not policies:
        raise ValueError("no grading policies configured for this exam")

    pages = ensure_copy_pages(copy)
    if not pages:
        raise ValueError("no rendered pages found for copy")

    rubric_payload = [
        {
            "question_number": r.question_number,
            "intitule": r.intitule,
            "expected_answer": r.expected_answer,
            "points_max": r.points_max,
        }
        for r in rubric
    ]
    policy_payload = [
        {
            "name": p.name,
            "fraction_points": p.fraction_points,
            "condition_description": p.condition_description,
        }
        for p in policies
    ]

    try:
        extracted = extract_copy_answers(pages, rubric_payload, policy_payload)
    except VisionError as exc:
        copy.status = CopyStatus.failed
        copy.error_message = f"vision: {exc}"
        audit.log_action(
            db, entity="student_copy", entity_id=copy.id, action="grade_failed",
            user_id=user_id, new_value={"error": str(exc)},
        )
        db.commit()
        raise

    answers_by_q = _by_qnum(extracted.answers)

    # Préserve les notes déjà validées
    validated_ids = {
        g.rubric_item_id
        for g in db.query(QuestionGrade)
        .filter(QuestionGrade.copy_id == copy.id, QuestionGrade.validated_at.is_not(None))
        .all()
    }

    # Supprime uniquement les notes non validées
    (
        db.query(QuestionGrade)
        .filter(
            QuestionGrade.copy_id == copy.id,
            QuestionGrade.validated_at.is_(None),
        )
        .delete()
    )

    for item in rubric:
        if item.id in validated_ids:
            continue
        ans = answers_by_q.get(item.question_number.strip())
        if ans is None:
            # Question non vue par le LLM : note 0 + revue
            ans = CopyAnswer(
                question_number=item.question_number,
                transcription="",
                found=False,
                regle_suggeree="Hors sujet / vide",
                fraction_suggeree=0.0,
                justification="Aucune réponse identifiée par l'extraction.",
                confiance=0.0,
            )
        result = score_one(
            rubric_item=item,
            policies=policies,
            transcription=ans.transcription,
            suggested_policy_name=ans.regle_suggeree,
            suggested_fraction=ans.fraction_suggeree,
            justification=ans.justification,
            confidence=ans.confiance,
            found=ans.found,
        )
        db.add(
            QuestionGrade(
                copy_id=copy.id,
                rubric_item_id=item.id,
                applied_policy_id=result.applied_policy_id,
                extracted_text=result.extracted_text,
                proposed_points=result.proposed_points,
                applied_fraction=result.applied_fraction,
                justification=result.justification,
                confidence=result.confidence,
                needs_human_review=result.needs_human_review,
            )
        )

    copy.status = CopyStatus.graded
    copy.error_message = None
    audit.log_action(
        db, entity="student_copy", entity_id=copy.id, action="graded",
        user_id=user_id,
        new_value={"questions": len(rubric), "preserved_validated": len(validated_ids)},
    )
    db.commit()
    db.refresh(copy)
    return copy


def override_grade(
    db: Session,
    grade: QuestionGrade,
    *,
    final_points: float,
    user_id: int,
    applied_policy_id: Optional[int] = None,
    justification: Optional[str] = None,
) -> QuestionGrade:
    old = {
        "proposed_points": grade.proposed_points,
        "final_points": grade.final_points,
        "applied_policy_id": grade.applied_policy_id,
        "justification": grade.justification,
    }
    grade.final_points = final_points
    if applied_policy_id is not None:
        grade.applied_policy_id = applied_policy_id
    if justification is not None:
        grade.justification = justification
    grade.validated_by = user_id
    grade.validated_at = datetime.now(timezone.utc)
    grade.needs_human_review = False

    audit.log_action(
        db, entity="question_grade", entity_id=grade.id, action="override",
        user_id=user_id, old_value=old,
        new_value={"final_points": final_points, "applied_policy_id": grade.applied_policy_id},
    )
    db.commit()
    db.refresh(grade)
    return grade

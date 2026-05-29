from sqlalchemy.orm import Session
from app.models.exam import Exam, ExamStatus
from app.models.policy import GradingPolicy, DEFAULT_POLICIES
from app.schemas.exam import ExamCreate
from app.services import audit


def create_exam(db: Session, payload: ExamCreate, owner_id: int) -> Exam:
    exam = Exam(
        title=payload.title,
        subject=payload.subject,
        owner_id=owner_id,
        status=ExamStatus.draft,
    )
    db.add(exam)
    db.flush()

    for p in DEFAULT_POLICIES:
        db.add(GradingPolicy(exam_id=exam.id, **p))

    audit.log_action(
        db,
        entity="exam",
        entity_id=exam.id,
        action="create",
        user_id=owner_id,
        new_value={"title": exam.title, "subject": exam.subject},
    )
    db.commit()
    db.refresh(exam)
    return exam

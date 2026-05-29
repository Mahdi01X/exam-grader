import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return str(value)


def log_action(
    db: Session,
    *,
    entity: str,
    entity_id: int,
    action: str,
    user_id: Optional[int] = None,
    old_value: Any = None,
    new_value: Any = None,
) -> AuditLog:
    entry = AuditLog(
        entity=entity,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        old_value=_to_str(old_value),
        new_value=_to_str(new_value),
    )
    db.add(entry)
    db.flush()
    return entry

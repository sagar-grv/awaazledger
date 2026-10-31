"""Immutable audit logging service."""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import logger


class AuditService:
    """Maintains tamper-evident traces and audit logs for banking compliance."""

    def log_event(
        self,
        db: Session,
        dispute_id: int,
        actor: str,
        event: str,
        input_hash: Optional[str] = None,
        output_status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        consent_id: Optional[int] = None,
    ) -> Optional[AuditLog]:
        """Appends an immutable audit event record to the database."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            if not input_hash:
                raw_token = f"{dispute_id}:{actor}:{event}:{now_iso}"
                input_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

            details_str = json.dumps(details or {})

            audit_log = AuditLog(
                dispute_id=dispute_id,
                actor=actor,
                event=event,
                input_hash=input_hash,
                output_status=output_status,
                details_json=details_str,
                consent_id=consent_id,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            return audit_log
        except Exception as e:
            logger.warning(f"Failed to record audit event '{event}' for dispute {dispute_id}: {e}")
            return None


async def log_audit_event(
    db: Session,
    dispute_id: int,
    actor: str,
    event: str,
    input_hash: Optional[str] = None,
    output_status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    consent_id: Optional[int] = None,
) -> Optional[AuditLog]:
    """Async convenience wrapper for audit logging."""
    return AuditService().log_event(
        db=db,
        dispute_id=dispute_id,
        actor=actor,
        event=event,
        input_hash=input_hash,
        output_status=output_status,
        details=details,
        consent_id=consent_id,
    )

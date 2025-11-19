from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from . import models, schemas


def create_audit_event(db: Session, event: schemas.AuditEventCreate) -> models.AuditEvent:
    """Create a new audit event."""
    db_event = models.AuditEvent(
        user_id=event.user_id,
        event_type=event.event_type,
        event_description=event.event_description,
        ip_address=event.ip_address,
        user_agent=event.user_agent,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        details=event.details,
        severity=event.severity
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_audit_event(db: Session, event_id: int) -> Optional[models.AuditEvent]:
    """Get an audit event by ID."""
    return db.query(models.AuditEvent).filter(models.AuditEvent.id == event_id).first()


def get_audit_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[models.AuditEvent]:
    """Get audit events with optional filtering."""
    query = db.query(models.AuditEvent).filter(models.AuditEvent.gdpr_deleted.is_(None))

    if user_id is not None:
        query = query.filter(models.AuditEvent.user_id == user_id)

    if event_type:
        query = query.filter(models.AuditEvent.event_type == event_type)

    if start_date:
        query = query.filter(models.AuditEvent.timestamp >= start_date)

    if end_date:
        query = query.filter(models.AuditEvent.timestamp <= end_date)

    return query.order_by(models.AuditEvent.timestamp.desc()).offset(skip).limit(limit).all()


def get_audit_summary(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> schemas.AuditSummary:
    """Get audit event summary statistics."""
    # Total events
    total_events = db.query(func.count(models.AuditEvent.id)).filter(
        and_(
            models.AuditEvent.timestamp >= start_date,
            models.AuditEvent.timestamp <= end_date,
            models.AuditEvent.gdpr_deleted.is_(None)
        )
    ).scalar()

    # Events by type
    events_by_type = db.query(
        models.AuditEvent.event_type,
        func.count(models.AuditEvent.id)
    ).filter(
        and_(
            models.AuditEvent.timestamp >= start_date,
            models.AuditEvent.timestamp <= end_date,
            models.AuditEvent.gdpr_deleted.is_(None)
        )
    ).group_by(models.AuditEvent.event_type).all()

    # Events by severity
    events_by_severity = db.query(
        models.AuditEvent.severity,
        func.count(models.AuditEvent.id)
    ).filter(
        and_(
            models.AuditEvent.timestamp >= start_date,
            models.AuditEvent.timestamp <= end_date,
            models.AuditEvent.gdpr_deleted.is_(None)
        )
    ).group_by(models.AuditEvent.severity).all()

    # Events by user
    events_by_user = db.query(
        models.AuditEvent.user_id,
        func.count(models.AuditEvent.id)
    ).filter(
        and_(
            models.AuditEvent.timestamp >= start_date,
            models.AuditEvent.timestamp <= end_date,
            models.AuditEvent.gdpr_deleted.is_(None),
            models.AuditEvent.user_id.isnot(None)
        )
    ).group_by(models.AuditEvent.user_id).all()

    # Recent events (last 10)
    recent_events = get_audit_events(db, limit=10, start_date=start_date, end_date=end_date)

    return schemas.AuditSummary(
        total_events=total_events,
        events_by_type=dict(events_by_type),
        events_by_severity=dict(events_by_severity),
        events_by_user={str(uid): count for uid, count in events_by_user},
        recent_events=recent_events,
        time_range={"start": start_date, "end": end_date}
    )


def delete_audit_event(db: Session, event_id: int) -> bool:
    """Mark an audit event as deleted (GDPR compliance)."""
    event = db.query(models.AuditEvent).filter(models.AuditEvent.id == event_id).first()
    if event:
        event.gdpr_deleted = datetime.utcnow()
        db.commit()
        return True
    return False


def bulk_delete_audit_events(
    db: Session,
    user_id: Optional[int] = None,
    event_types: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> int:
    """Bulk delete audit events (GDPR compliance)."""
    query = db.query(models.AuditEvent).filter(models.AuditEvent.gdpr_deleted.is_(None))

    if user_id is not None:
        query = query.filter(models.AuditEvent.user_id == user_id)

    if event_types:
        query = query.filter(models.AuditEvent.event_type.in_(event_types))

    if start_date:
        query = query.filter(models.AuditEvent.timestamp >= start_date)

    if end_date:
        query = query.filter(models.AuditEvent.timestamp <= end_date)

    # Mark as deleted instead of actually deleting
    count = query.update({"gdpr_deleted": datetime.utcnow()})
    db.commit()
    return count


def cleanup_expired_events(db: Session) -> int:
    """Permanently delete events that have exceeded their retention period."""
    cutoff_date = datetime.utcnow() - timedelta(days=2555)  # 7 years

    count = db.query(models.AuditEvent).filter(
        and_(
            models.AuditEvent.timestamp < cutoff_date,
            models.AuditEvent.retention_days > 0
        )
    ).delete()

    db.commit()
    return count
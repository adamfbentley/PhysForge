from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditEventBase(BaseModel):
    user_id: Optional[int] = None
    event_type: str
    event_description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "INFO"


class AuditEventCreate(AuditEventBase):
    pass


class AuditEvent(AuditEventBase):
    id: int
    timestamp: datetime
    retention_days: int = 2555  # 7 years
    gdpr_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditEventBulkDelete(BaseModel):
    user_id: Optional[int] = None
    event_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditSummary(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_user: Dict[str, int]  # user_id -> count
    recent_events: List[AuditEvent]
    time_range: Dict[str, datetime]
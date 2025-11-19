from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # None for anonymous events
    event_type = Column(String, nullable=False, index=True)
    event_description = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    resource_type = Column(String, nullable=True)  # e.g., "dataset", "job", "user"
    resource_id = Column(String, nullable=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # Additional event-specific data
    severity = Column(String, default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # GDPR compliance fields
    retention_days = Column(Integer, default=2555)  # 7 years default
    gdpr_deleted = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AuditEvent(id={self.id}, event_type='{self.event_type}', user_id={self.user_id})>"
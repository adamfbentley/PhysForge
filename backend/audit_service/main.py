"""
Audit Logging Service
Provides centralized audit logging for security events and user actions.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from . import crud, models, schemas
from .database import SessionLocal, engine
from .security import get_current_active_admin_user
from ..shared.security.audit_logging import init_audit_logger, get_audit_logger

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize audit logger for self-auditing
init_audit_logger("audit_service")

app = FastAPI(
    title="PhysForge Audit Service",
    description="Centralized audit logging for security events and user actions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "audit_service"}

@app.post("/audit/events/", response_model=schemas.AuditEvent)
async def create_audit_event(
    event: schemas.AuditEventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new audit event.
    This endpoint is called by other services to log events.
    """
    try:
        audit_event = crud.create_audit_event(db=db, event=event)

        # Log the audit event creation itself
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            "AUDIT_EVENT_CREATED",
            event.user_id,
            {"event_type": event.event_type, "event_id": audit_event.id},
            None,  # No request object available
            event.ip_address,
            event.user_agent
        )

        return audit_event
    except Exception as e:
        # Log the error
        audit_logger = get_audit_logger()
        audit_logger.logger.error(f"Failed to create audit event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create audit event")

@app.get("/audit/events/", response_model=List[schemas.AuditEvent])
async def get_audit_events(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)
):
    """
    Retrieve audit events with filtering.
    Admin access required.
    """
    events = crud.get_audit_events(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date
    )
    return events

@app.get("/audit/events/{event_id}", response_model=schemas.AuditEvent)
async def get_audit_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)
):
    """
    Get a specific audit event by ID.
    Admin access required.
    """
    event = crud.get_audit_event(db=db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return event

@app.get("/audit/events/summary/")
async def get_audit_summary(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)
):
    """
    Get audit event summary statistics.
    Admin access required.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    summary = crud.get_audit_summary(db=db, start_date=start_date, end_date=end_date)
    return summary

@app.delete("/audit/events/{event_id}")
async def delete_audit_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)
):
    """
    Delete an audit event (for GDPR compliance).
    Admin access required.
    """
    success = crud.delete_audit_event(db=db, event_id=event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audit event not found")

    # Log the deletion
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        "AUDIT_EVENT_DELETED",
        current_user.id,
        {"deleted_event_id": event_id},
        None
    )

    return {"message": "Audit event deleted successfully"}

@app.post("/audit/events/bulk-delete/")
async def bulk_delete_audit_events(
    delete_request: schemas.AuditEventBulkDelete,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)
):
    """
    Bulk delete audit events (for GDPR compliance).
    Admin access required.
    """
    deleted_count = crud.bulk_delete_audit_events(
        db=db,
        user_id=delete_request.user_id,
        event_types=delete_request.event_types,
        start_date=delete_request.start_date,
        end_date=delete_request.end_date
    )

    # Log the bulk deletion
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        "AUDIT_EVENTS_BULK_DELETED",
        current_user.id,
        {
            "deleted_count": deleted_count,
            "user_id": delete_request.user_id,
            "event_types": delete_request.event_types
        },
        None
    )

    return {"message": f"Deleted {deleted_count} audit events"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    print("Audit Service started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
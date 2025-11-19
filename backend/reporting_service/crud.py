from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_report(db: Session, report_create: schemas.ReportCreate) -> models.Report:
    db_report = models.Report(
        job_id=report_create.job_id,
        owner_id=report_create.owner_id,
        report_type=report_create.report_type,
        report_path=report_create.report_path,
        status=report_create.status,
        metadata=report_create.metadata
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report_by_id(db: Session, report_id: int) -> Optional[models.Report]:
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def get_reports_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[models.Report]:
    return db.query(models.Report).filter(models.Report.owner_id == owner_id).offset(skip).limit(limit).all()

def update_report_status(db: Session, report_id: int, status_update: schemas.ReportStatusUpdate) -> Optional[models.Report]:
    db_report = get_report_by_id(db, report_id)
    if not db_report:
        return None

    update_data = status_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)
    
    db_report.updated_at = datetime.now()
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

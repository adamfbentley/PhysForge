from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# --- JWT related schemas (from Auth Service) ---
class TokenData(BaseModel):
    email: Optional[str] = None

class RoleBase(BaseModel):
    name: str

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    roles: List[Role] = []
    token: str # Original JWT token for authenticating with other services
    class Config:
        from_attributes = True

# --- Reporting Service Schemas (STORY-703, STORY-704, STORY-705) ---
class ReportGenerationConfig(BaseModel):
    job_id: int = Field(..., description="ID of the completed PDE discovery job to generate a report for.")
    report_type: Literal["json_summary", "jupyter_notebook"] = Field(..., description="Type of report to generate.")
    output_name: str = Field(..., description="A name for the output report/notebook file.")

class ReportCreate(BaseModel):
    job_id: int
    owner_id: int
    report_type: str
    report_path: str
    status: str = "PENDING"
    metadata: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    id: int
    job_id: int
    owner_id: int
    report_type: str
    report_path: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    generated_at: datetime
    updated_at: Optional[datetime] = None
    download_url: Optional[str] = None # Added for GET endpoint

    class Config:
        from_attributes = True

class ReportStatusUpdate(BaseModel):
    status: str
    report_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

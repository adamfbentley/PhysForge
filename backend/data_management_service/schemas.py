from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Schemas for JWT token validation (from Auth Service)
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
    class Config:
        from_attributes = True

# Schemas for Data Management Service

class MetadataSchema(BaseModel):
    filename: str
    size_bytes: int
    mime_type: str
    extracted_data: Dict[str, Any] = {}

class DatasetVersionBase(BaseModel):
    version_number: int
    storage_path: str
    metadata: Optional[Dict[str, Any]] = None
    uploader_id: int

class DatasetVersionCreate(DatasetVersionBase):
    pass

class DatasetVersionResponse(DatasetVersionBase):
    id: int
    dataset_id: int
    uploaded_at: datetime
    is_latest: bool

    class Config:
        from_attributes = True

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetCreate(DatasetBase):
    pass

class DatasetResponse(DatasetBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    latest_version: Optional[DatasetVersionResponse] = None # Include latest version info

    class Config:
        from_attributes = True

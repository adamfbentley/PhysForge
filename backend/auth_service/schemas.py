from pydantic import BaseModel, EmailStr
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    # CQ-002: Added optional roles for user creation
    roles: Optional[List[str]] = None

class UserLogin(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    roles: List[Role] = []

    class Config:
        from_attributes = True

# CQ-003: New schema for assigning roles
class RoleAssign(BaseModel):
    role_names: List[str]

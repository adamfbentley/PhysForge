from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..security import (create_access_token, get_current_active_user,
                        verify_password, get_current_active_admin_user, get_current_user) # Import new dependency
from ..config import settings

router = APIRouter()

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

# CQ-003: New API endpoints for role management

@router.post("/roles/", response_model=schemas.Role, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(get_current_active_admin_user)], # Protect with admin role
             summary="Create a new role (Admin only)")
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    db_role = crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role with this name already exists")
    return crud.create_role(db=db, role=role)

@router.get("/roles/", response_model=List[schemas.Role],
            dependencies=[Depends(get_current_active_admin_user)], # Protect with admin role
            summary="Retrieve all roles (Admin only)")
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/users/{user_id}/roles/", response_model=schemas.User,
             dependencies=[Depends(get_current_active_admin_user)], # Protect with admin role
             summary="Assign roles to a user (Admin only)")
def assign_roles_to_user(
    user_id: int = Path(..., description="The ID of the user to assign roles to"),
    role_assign: schemas.RoleAssign,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if all roles exist
    for role_name in role_assign.role_names:
        if not crud.get_role_by_name(db, role_name):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_name}' not found")

    return crud.assign_roles_to_user(db, user, role_assign.role_names)

@router.get("/users/{user_id}/roles/", response_model=List[schemas.Role],
            dependencies=[Depends(get_current_active_admin_user)], # Protect with admin role
            summary="Retrieve roles for a specific user (Admin only)")
def get_user_roles(
    user_id: int = Path(..., description="The ID of the user to retrieve roles for"),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user.roles

# Optional: Add endpoint to remove roles from a user
@router.delete("/users/{user_id}/roles/", response_model=schemas.User,
              dependencies=[Depends(get_current_active_admin_user)], # Protect with admin role
              summary="Remove roles from a user (Admin only)")
def remove_roles_from_user(
    user_id: int = Path(..., description="The ID of the user to remove roles from"),
    role_assign: schemas.RoleAssign,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if all roles exist and are currently assigned
    current_role_names = {role.name for role in user.roles}
    for role_name in role_assign.role_names:
        if role_name not in current_role_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{role_name}' is not assigned to user {user_id}")

    return crud.remove_roles_from_user(db, user, role_assign.role_names)

# API Gateway verification endpoint
@router.get("/verify")
async def verify_token(current_user: schemas.User = Depends(get_current_user)):
    """
    Endpoint for API Gateway to verify JWT tokens.
    Returns user information in headers for downstream services.
    """
    return {
        "status": "valid",
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "roles": [role.name for role in current_user.roles]
    }

from sqlalchemy.orm import Session
from . import models, schemas
from .security import get_password_hash
from typing import List, Optional

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# CQ-003: Added get_user_by_id for role assignment endpoints
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# CQ-002: Modified create_user to accept optional roles
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)

    if user.roles:
        for role_name in user.roles:
            role = get_role_by_name(db, role_name)
            if role:
                db_user.roles.append(role)
            # else: Handle case where role doesn't exist? For now, just skip.
            # In a real app, might raise an error or create the role.

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: schemas.RoleCreate):
    db_role = models.Role(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_by_name(db: Session, name: str):
    return db.query(models.Role).filter(models.Role.name == name).first()

# CQ-003: New functions for role management
def assign_roles_to_user(db: Session, user: models.User, role_names: List[str]):
    for role_name in role_names:
        role = get_role_by_name(db, role_name)
        if role and role not in user.roles:
            user.roles.append(role)
    db.commit()
    db.refresh(user)
    return user

def remove_roles_from_user(db: Session, user: models.User, role_names: List[str]):
    roles_to_remove = [role for role in user.roles if role.name in role_names]
    for role in roles_to_remove:
        user.roles.remove(role)
    db.commit()
    db.refresh(user)
    return user

def get_user_roles(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        return user.roles
    return []

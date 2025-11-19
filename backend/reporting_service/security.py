from datetime import datetime, timedelta, timezone
from typing import Optional, List

from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from .config import settings
from . import schemas
from .database import get_report_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Point to Auth Service login

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_report_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.encode('utf-8'), algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # The Auth Service is expected to include 'user_id' in the JWT payload.
    # This service relies on 'user_id' for report ownership checks.
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # Construct a minimal User object for this service's needs
    current_user = schemas.User(id=user_id, email=email, is_active=True, roles=[], token=token)
    return current_user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

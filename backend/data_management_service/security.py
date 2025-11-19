from datetime import datetime, timedelta, timezone
from typing import Optional, List

from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from .config import settings
from . import schemas
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Point to Auth Service login

# This service only needs to validate tokens, not create them or hash passwords.
# The SECRET_KEY and ALGORITHM must match the Auth Service's configuration.

async def get_current_user(token: str = Depends(oAuth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # CQ-DMS-001: The Auth Service is expected to include 'user_id' in the JWT payload.
    # This service relies on 'user_id' for data ownership checks.
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        # If user_id is not in the token, it indicates a misconfiguration or an invalid token
        # from the Auth Service, which is a critical security and functional issue.
        raise credentials_exception

    # Construct a minimal User object for this service's needs
    current_user = schemas.User(id=user_id, email=email, is_active=True, roles=[]) # Roles not needed for data ownership check
    return current_user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

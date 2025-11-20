from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()

class User(BaseModel):
    """User model from auth service"""
    id: str
    username: str
    email: str
    role: str

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Validate JWT token with auth service and return current user.
    
    This makes a request to the auth service to validate the token
    and retrieve user information.
    """
    token = credentials.credentials
    
    try:
        # Call auth service to validate token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://auth_service:8000/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_data = response.json()
            return User(**user_data)
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def require_role(required_role: str):
    """
    Dependency to check if user has required role.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return user
    
    return role_checker

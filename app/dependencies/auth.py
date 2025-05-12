from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.db.database import get_db
from app.models.database import User
from app.services.firebase_auth import FirebaseAuthService
from app.core.settings import settings

logger = logging.getLogger(__name__)

# Security scheme for Firebase authentication
firebase_auth_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from Firebase ID token or return demo user in development.
    
    Args:
        authorization: HTTP Authorization header
        db: Database session
        
    Returns:
        User database object
        
    Raises:
        HTTPException: If authentication fails in production mode
    """
    # Always use demo user in development mode
    if settings.APP_ENV == "development":
        logger.info("Using demo user for development environment")
        return FirebaseAuthService.create_demo_user(db)
    
    # Production mode requires valid authentication
    if not authorization:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify Firebase token
        user = await FirebaseAuthService.get_user_by_token(db, token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    
    Args:
        current_user: User from token authentication
        
    Returns:
        User database object if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
    
# For backwards compatibility with API keys
async def validate_api_key(api_key: str, db: Session) -> User:
    """Validate API key and return user."""
    logger.info("API key validation requested - using demo user in development mode")
    if settings.APP_ENV == "development":
        return FirebaseAuthService.create_demo_user(db)
    
    # In production, try to validate the API key
    # This is a placeholder - you'd need to implement actual validation
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )
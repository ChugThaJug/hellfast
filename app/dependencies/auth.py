# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.db.database import get_db
from app.models.database import User
from app.core.settings import settings

logger = logging.getLogger(__name__)

# Development-friendly authentication
class DevAuthService:
    @staticmethod
    def create_demo_user(db: Session) -> User:
        """Create a demo user for development."""
        from datetime import datetime
        
        # Check if demo user exists
        demo_user = db.query(User).filter(User.username == "demo").first()
        if demo_user:
            return demo_user
                
        # Create a new demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add optional fields if they exist
        if hasattr(User, 'firebase_uid'):
            demo_user.firebase_uid = "demo_firebase_uid"
        if hasattr(User, 'display_name'):
            demo_user.display_name = "Demo User"
        if hasattr(User, 'photo_url'):
            demo_user.photo_url = "https://ui-avatars.com/api/?name=Demo+User"
        if hasattr(User, 'google_id'):
            demo_user.google_id = "demo_google_id"
                
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        return demo_user

# Try to import real Firebase, fall back to development version
try:
    from app.services.firebase_auth import FirebaseAuthService
    firebase_service = FirebaseAuthService
    logger.info("Using real Firebase Authentication service")
except ImportError:
    logger.warning("Firebase not available, using development service")
    firebase_service = DevAuthService

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from Firebase ID token or return demo user in development.
    """
    # Always use demo user in development mode
    if settings.APP_ENV == "development":
        logger.info("Using demo user for development environment")
        return firebase_service.create_demo_user(db)
    
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
        
        # Verify Firebase token (only in production)
        user = await firebase_service.get_user_by_token(db, token)
        
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
        return firebase_service.create_demo_user(db)
    
    # In production, try to validate the API key
    # This is a placeholder - you'd need to implement actual validation
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )
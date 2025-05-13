# app/api/routes/firebase_auth.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.db.database import get_db
from app.models.database import User
from app.dependencies.auth import get_current_user
from app.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/firebase", tags=["firebase_auth"])

# Development-friendly Firebase service 
class DevFirebaseService:
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

# Use real Firebase in production mode, development-friendly version in development
try:
    from app.services.firebase_auth import FirebaseAuthService
    firebase_service = FirebaseAuthService
    logger.info("Using real Firebase Authentication service")
except ImportError:
    logger.warning("Firebase not available, using development service")
    firebase_service = DevFirebaseService

@router.post("/verify-token", summary="Verify Firebase ID token")
async def verify_token(
    token_data: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Verify Firebase ID token and return user information.
    In development mode, this will always return the demo user.
    """
    # Development mode - always return demo user
    if settings.APP_ENV == "development":
        logger.info("Development mode - returning demo user")
        demo_user = firebase_service.create_demo_user(db)
        
        # Build response with basic user info
        user_info = {
            "id": demo_user.id,
            "username": demo_user.username,
            "email": demo_user.email,
            "is_active": demo_user.is_active,
            "development_mode": True
        }
        
        # Add additional fields if they exist
        if hasattr(demo_user, 'display_name') and demo_user.display_name:
            user_info["display_name"] = demo_user.display_name
        if hasattr(demo_user, 'photo_url') and demo_user.photo_url:
            user_info["photo_url"] = demo_user.photo_url
        if hasattr(demo_user, 'firebase_uid') and demo_user.firebase_uid:
            user_info["firebase_uid"] = demo_user.firebase_uid
            
        return user_info
    
    # Production logic remains the same
    if not token_data or "token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    token = token_data.get("token")
    
    try:
        # Verify token and get user with real Firebase service
        decoded_token = firebase_service.verify_token(token)
        user = await firebase_service.get_or_create_user(db, decoded_token)
        
        # Return user information
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
        
        # Add Firebase fields if they exist
        if hasattr(user, 'display_name') and user.display_name:
            user_info["display_name"] = user.display_name
        if hasattr(user, 'photo_url') and user.photo_url:
            user_info["photo_url"] = user.photo_url
        if hasattr(user, 'firebase_uid') and user.firebase_uid:
            user_info["firebase_uid"] = user.firebase_uid
            
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.get("/profile", summary="Get current user profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile using Firebase authentication."""
    # Build response with only fields that exist
    profile = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }
    
    # Add Firebase fields if they exist
    if hasattr(current_user, 'display_name') and current_user.display_name:
        profile["display_name"] = current_user.display_name
    if hasattr(current_user, 'photo_url') and current_user.photo_url:
        profile["photo_url"] = current_user.photo_url
    if hasattr(current_user, 'firebase_uid') and current_user.firebase_uid:
        profile["firebase_uid"] = current_user.firebase_uid
    
    # Add development mode flag
    if settings.APP_ENV == "development":
        profile["development_mode"] = True
        
    return profile

@router.get("/status", summary="Check Firebase authentication status")
async def firebase_status():
    """Check if Firebase authentication is configured and working."""
    # Always return successful status in development mode
    is_dev_mode = settings.APP_ENV == "development"
    
    if is_dev_mode:
        return {
            "status": "Firebase authentication is in development mode",
            "initialized": True,
            "development_mode": True,
            "message": "In development mode, authentication will use demo user"
        }
        
    # Production logic (try to check real Firebase)
    try:
        return {
            "status": "Firebase authentication is configured",
            "initialized": True,
            "development_mode": False
        }
    except Exception as e:
        logger.error(f"Firebase status check failed: {str(e)}")
        return {
            "status": "Firebase authentication is not properly configured",
            "error": str(e),
            "initialized": False,
            "development_mode": False
        }
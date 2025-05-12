from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import firebase_admin

from app.db.database import get_db
from app.models.database import User
from app.dependencies.auth import get_current_user
from app.services.firebase_auth import FirebaseAuthService, initialize_firebase_admin
from app.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/firebase", tags=["firebase_auth"])

@router.post("/verify-token", summary="Verify Firebase ID token")
async def verify_token(
    token_data: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Verify Firebase ID token and return user information.
    In development mode, this will always return the demo user.
    
    Args:
        token_data: Object containing Firebase ID token (optional in dev mode)
        db: Database session
        
    Returns:
        User information if token is valid
    """
    # Development mode - always return demo user
    if settings.APP_ENV == "development":
        logger.info("Development mode - returning demo user")
        demo_user = FirebaseAuthService.create_demo_user(db)
        
        # Build response with basic user info
        user_info = {
            "id": demo_user.id,
            "username": demo_user.username,
            "email": demo_user.email,
            "is_active": demo_user.is_active,
            "development_mode": True
        }
        
        # Add Firebase fields if they exist
        if hasattr(demo_user, 'display_name') and demo_user.display_name:
            user_info["display_name"] = demo_user.display_name
        if hasattr(demo_user, 'photo_url') and demo_user.photo_url:
            user_info["photo_url"] = demo_user.photo_url
        if hasattr(demo_user, 'firebase_uid') and demo_user.firebase_uid:
            user_info["firebase_uid"] = demo_user.firebase_uid
            
        return user_info
    
    # Production mode - verify token
    if not token_data or "token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    token = token_data.get("token")
    
    try:
        # Verify token and get user
        decoded_token = FirebaseAuthService.verify_token(token)
        user = await FirebaseAuthService.get_or_create_user(db, decoded_token)
        
        # Return user information - only include fields that exist
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
    """
    Get current user profile using Firebase authentication.
    
    Args:
        current_user: User from Firebase authentication
        
    Returns:
        User profile information
    """
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
    try:
        # Add development mode info
        is_dev_mode = settings.APP_ENV == "development"
        
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            return {
                "status": "Firebase authentication is configured and working",
                "initialized": True,
                "development_mode": is_dev_mode
            }
        
        # Try to initialize Firebase
        success = initialize_firebase_admin()
        if success:
            return {
                "status": "Firebase authentication is configured and working",
                "initialized": True,
                "development_mode": is_dev_mode
            }
        else:
            return {
                "status": "Firebase authentication is not properly configured",
                "initialized": False,
                "development_mode": is_dev_mode,
                "message": "In development mode, authentication will use demo user"
            }
    except Exception as e:
        logger.error(f"Firebase status check failed: {str(e)}")
        return {
            "status": "Firebase authentication is not properly configured",
            "error": str(e),
            "initialized": False,
            "development_mode": settings.APP_ENV == "development",
            "message": "In development mode, authentication will use demo user"
        }
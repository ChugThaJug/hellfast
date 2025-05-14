# app/api/routes/auth_api.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import jwt
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.database import User
from app.dependencies.auth import get_current_user
from app.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/verify-token", summary="Verify JWT token")
async def verify_token(
    token_data: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Verify JWT token and return user information.
    """
    # Always require a token
    if not token_data or "token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    token = token_data.get("token")
    
    try:
        # Verify token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not email and not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token content"
            )
            
        # Get user from database
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
        else:
            user = db.query(User).filter(User.email == email).first()
            
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Return user information
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
        
        # Add optional fields if they exist
        if hasattr(user, 'display_name') and user.display_name:
            user_info["display_name"] = user.display_name
        if hasattr(user, 'photo_url') and user.photo_url:
            user_info["photo_url"] = user.photo_url
            
        return user_info
    except jwt.PyJWTError as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
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
    """Get current user profile."""
    # Build response with only fields that exist
    profile = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }
    
    # Add optional fields if they exist
    if hasattr(current_user, 'display_name') and current_user.display_name:
        profile["display_name"] = current_user.display_name
    if hasattr(current_user, 'photo_url') and current_user.photo_url:
        profile["photo_url"] = current_user.photo_url
        
    return profile

@router.get("/status", summary="Check authentication status")
async def auth_status():
    """Check if authentication is configured and working."""
    return {
        "status": "Authentication is configured",
        "initialized": True,
        "oauth_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    }
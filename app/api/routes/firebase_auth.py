from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import firebase_admin

from app.db.database import get_db
from app.models.database import User
from app.dependencies.auth import get_current_user
from app.services.firebase_auth import FirebaseAuthService, initialize_firebase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/firebase", tags=["firebase_auth"])

@router.post("/verify-token", summary="Verify Firebase ID token")
async def verify_token(
    token_data: Dict[str, Any] = Body(..., examples={"example1": {"summary": "Example token", "value": {"token": "firebase_id_token_here"}}}),
    db: Session = Depends(get_db)
):
    """
    Verify Firebase ID token and return user information.
    
    Args:
        token_data: Object containing Firebase ID token
        db: Database session
        
    Returns:
        User information if token is valid
    """
    token = token_data.get("token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    try:
        # Verify token and get user
        decoded_token = FirebaseAuthService.verify_token(token)
        user = await FirebaseAuthService.get_or_create_user(db, decoded_token)
        
        # Return user information
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "firebase_uid": user.firebase_uid,
            "is_active": user.is_active
        }
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
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "photo_url": current_user.photo_url,
        "firebase_uid": current_user.firebase_uid,
        "is_active": current_user.is_active
    }

@router.get("/status", summary="Check Firebase authentication status")
async def firebase_status():
    """Check if Firebase authentication is configured and working."""
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            return {
                "status": "Firebase authentication is configured and working",
                "initialized": True
            }
        
        # Try to initialize Firebase
        initialize_firebase_admin()
        return {
            "status": "Firebase authentication is configured and working",
            "initialized": True
        }
    except Exception as e:
        logger.error(f"Firebase status check failed: {str(e)}")
        return {
            "status": "Firebase authentication is not properly configured",
            "error": str(e),
            "initialized": False
        }
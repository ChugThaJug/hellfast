# app/api/routes/oauth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.db.database import get_db
from app.core.settings import settings
from app.services.oauth import GoogleOAuthService

logger = logging.getLogger(__name__)

# Change the prefix to avoid conflicts with auth router
router = APIRouter(prefix="/oauth", tags=["oauth"])

@router.get("/google/login", summary="Start Google OAuth flow")
async def google_login():
    """
    Generates a Google OAuth login URL and redirects the user to Google's authentication page.
    
    Returns:
        A redirect response to Google's authentication page
    """
    try:
        auth_url = await GoogleOAuthService.get_authorization_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"OAuth error: {str(e)}"}
        )

@router.get("/google/callback", summary="Handle Google OAuth callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handles the Google OAuth callback after user authentication.
    
    This endpoint is called by Google after the user grants permission.
    
    Args:
        code: Authorization code provided by Google
        
    Returns:
        A redirect response to the frontend with the access token
    """
    try:
        # Log the received code for debugging
        logger.info("Received OAuth callback with code")
        
        # Use the same redirect URI that was used in the authorization request
        redirect_uri = "http://localhost:8000/oauth/google/callback"
        
        # Exchange code for token using the redirect URI
        result = await GoogleOAuthService.handle_oauth_callback(db, code, redirect_uri)
        
        if not result.get("success"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": result.get("message", "Authentication failed")}
            )
        
        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/auth/oauth-success"
        redirect_url = f"{frontend_url}?access_token={result['access_token']}&token_type={result['token_type']}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"OAuth error: {str(e)}"}
        )

@router.get("/google/mobile-callback", summary="Handle Google OAuth for mobile")
async def google_mobile_callback(code: str, db: Session = Depends(get_db)):
    """
    Handles Google OAuth callback for mobile apps.
    
    Returns JSON instead of redirecting, for mobile app integration.
    
    Args:
        code: Authorization code provided by Google
        
    Returns:
        JSON response with the access token and user information
    """
    try:
        # Use the same redirect URI that was used in the authorization request
        redirect_uri = "http://localhost:8000/oauth/google/callback"
        
        result = await GoogleOAuthService.handle_oauth_callback(db, code, redirect_uri)
        
        if not result.get("success"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": result.get("message", "Authentication failed")}
            )
        
        # Return token in JSON response for mobile apps
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": result["user"]
        }
        
    except Exception as e:
        logger.error(f"OAuth error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"OAuth error: {str(e)}"}
        )

@router.get("/status", summary="Check OAuth status")
async def oauth_status():
    """
    Check if OAuth routes are working and properly configured.
    
    Returns:
        Status information about the OAuth configuration
    """
    is_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {
        "status": "OAuth routes are working",
        "google_oauth_configured": is_configured,
        "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(settings.GOOGLE_CLIENT_SECRET),
        "redirect_url": "http://localhost:8000/oauth/google/callback"
    }
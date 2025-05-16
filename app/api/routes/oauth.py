# app/api/routes/oauth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.core.settings import settings
from app.services.oauth_service import OAuthService
from app.models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Map to store state parameters for CSRF protection
oauth_states = {}

@router.get("/google/login", summary="Start Google OAuth flow")
async def google_login():
    """
    Generates a Google OAuth login URL and redirects the user to Google's authentication page.
    """
    try:
        auth_url, state = await OAuthService.get_authorization_url()
        
        # Store state for verification on callback
        oauth_states[state] = True
        
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"OAuth error: {str(e)}"}
        )

@router.get("/google/callback", summary="Handle Google OAuth callback")
async def google_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    """
    Handles the Google OAuth callback after user authentication.
    """
    try:
        logger.info("Received OAuth callback with code")
        
        # Verify state parameter to prevent CSRF attacks
        if state and state not in oauth_states:
            logger.warning("Invalid OAuth state parameter")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid state parameter"}
            )
            
        # Clean up state after use
        if state:
            oauth_states.pop(state, None)
            
        # Exchange code for token
        tokens = await OAuthService.exchange_code_for_token(code)
        if not tokens:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Failed to exchange authorization code for tokens"}
            )
        
        # Get user info with the access token
        access_token = tokens.get("access_token")
        if not access_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "No access token received"}
            )
        
        user_info = await OAuthService.get_user_info(access_token)
        if not user_info:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Failed to get user info"}
            )
        
        # Create or update user
        user = await OAuthService.create_or_update_user(db, user_info)
        
        # Create JWT token
        token = OAuthService.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"Successfully authenticated user: {user.email}")
        
        # Redirect to frontend with token
        frontend_url = settings.FRONTEND_URL
        redirect_url = f"{frontend_url}/auth/oauth-success?access_token={token}&token_type=bearer"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"OAuth error: {str(e)}"}
        )

@router.get("/status", summary="Check OAuth status")
async def oauth_status():
    """
    Check if OAuth routes are working and properly configured.
    """
    is_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {
        "status": "OAuth routes are working",
        "google_oauth_configured": is_configured,
        "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(settings.GOOGLE_CLIENT_SECRET),
        "redirect_url": settings.OAUTH_REDIRECT_URL
    }
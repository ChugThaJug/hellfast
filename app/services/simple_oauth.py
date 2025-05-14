# app/services/simple_oauth.py
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import jwt

from app.core.settings import settings
from app.models.database import User

logger = logging.getLogger(__name__)

class SimpleOAuthService:
    """Basic OAuth service for Google authentication."""
    
    # In app/services/simple_oauth.py
    @staticmethod
    async def get_authorization_url() -> str:
        """Get the Google authorization URL."""
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        scope = "email profile openid"
        
        # Get the redirect URI
        redirect_uri = settings.OAUTH_REDIRECT_URL or "http://localhost:8000/oauth/google/callback"
        
        # Log the exact redirect URI being used
        logger.info(f"Using OAuth redirect URI: {redirect_uri}")
        
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account"
        }
        
        # Build the URL
        url_parts = []
        for key, value in params.items():
            url_parts.append(f"{key}={value}")
        
        final_url = f"{auth_url}?{'&'.join(url_parts)}"
        logger.info(f"Complete OAuth URL: {final_url}")
        
        return final_url
    
    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        # Use the provided redirect URI or default
        if not redirect_uri:
            redirect_uri = settings.OAUTH_REDIRECT_URL or "http://localhost:8000/oauth/google/callback"
        
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code != 200:
                    logger.error(f"Error exchanging code for token: {response.text}")
                    return {}
                
                return response.json()
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return {}
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google using the access token."""
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting user info: {response.text}")
                    return {}
                
                return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {}
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for our application."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
            
        to_encode.update({"exp": expire})
        secret_key = getattr(settings, "SECRET_KEY", "development-secret-key-change-in-production")
        algorithm = getattr(settings, "ALGORITHM", "HS256")
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt


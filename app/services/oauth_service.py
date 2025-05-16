# app/services/oauth_service.py
import httpx
import jwt
import logging
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import User

logger = logging.getLogger(__name__)

class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    @staticmethod
    async def get_authorization_url() -> Tuple[str, str]:
        """Get the Google authorization URL and state parameter."""
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        scope = "email profile openid"
        
        # Always use backend URL for redirect
        redirect_uri = settings.OAUTH_REDIRECT_URL
        if not redirect_uri:
            raise ValueError("OAUTH_REDIRECT_URL must be configured")
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account",
            "state": state
        }
        
        # Build the URL
        url_parts = []
        for key, value in params.items():
            url_parts.append(f"{key}={value}")
        
        final_url = f"{auth_url}?{'&'.join(url_parts)}"
        logger.info(f"Generated OAuth URL: {final_url}")
        
        return final_url, state
    
    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        # Use the provided redirect URI or default
        if not redirect_uri:
            redirect_uri = settings.OAUTH_REDIRECT_URL
            if not redirect_uri:
                raise ValueError("OAUTH_REDIRECT_URL must be configured")
        
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials must be configured")
            
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
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY must be configured")
            
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM or "HS256"
        )
        return encoded_jwt
    
    @staticmethod
    async def create_or_update_user(db: Session, user_info: Dict[str, Any]) -> User:
        """Create or update user from OAuth user info."""
        if not user_info:
            raise ValueError("User info is required")
        
        # Extract user information
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        if not google_id or not email:
            raise ValueError("Google ID and email are required")
        
        # Try to find user by google_id or email
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Try to find by email
            user = db.query(User).filter(User.email == email).first()
        
        now = datetime.now(timezone.utc)
        
        if user:
            # Update existing user
            user.google_id = google_id
            
            # Update optional fields if they exist on the model
            if hasattr(user, 'display_name'):
                user.display_name = name
            if hasattr(user, 'photo_url'):
                user.photo_url = picture
            if hasattr(user, 'updated_at'):
                user.updated_at = now
                
            db.commit()
            db.refresh(user)
            return user
        
        # Create new user
        username = email.split('@')[0]
        
        # Make username unique if needed
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            import uuid
            username = f"{username}_{str(uuid.uuid4())[:8]}"
            
        # Create user
        user = User(
            username=username,
            email=email,
            google_id=google_id,
            is_active=True,
            created_at=now
        )
        
        # Add optional fields if they exist
        if hasattr(user, 'display_name'):
            user.display_name = name
        if hasattr(user, 'photo_url'):
            user.photo_url = picture
        if hasattr(user, 'updated_at'):
            user.updated_at = now
            
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
import httpx
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import User
from app.services.auth import get_password_hash, create_access_token

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    @staticmethod
    async def get_authorization_url() -> str:
        """Get the Google authorization URL."""
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        scope = "email profile openid"
        
        # Update redirect URL to match new route path
        redirect_uri = settings.OAUTH_REDIRECT_URL
        if "/auth/google/callback" in redirect_uri:
            redirect_uri = redirect_uri.replace("/auth/google/callback", "/oauth/google/callback")
        
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
        
        return f"{auth_url}?{'&'.join(url_parts)}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        # Update redirect URL to match new route path
        redirect_uri = settings.OAUTH_REDIRECT_URL
        if "/auth/google/callback" in redirect_uri:
            redirect_uri = redirect_uri.replace("/auth/google/callback", "/oauth/google/callback")
        
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code != 200:
                logger.error(f"Error exchanging code for token: {response.text}")
                return {}
            
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google using the access token."""
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                logger.error(f"Error getting user info: {response.text}")
                return {}
            
            return response.json()
    
    @staticmethod
    async def authenticate_google_user(db: Session, user_info: Dict[str, Any]) -> Optional[User]:
        """Authenticate a user with Google OAuth."""
        if not user_info:
            return None
        
        # Extract user information
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        
        if not google_id or not email:
            logger.error("Google ID or email missing from user info")
            return None
        
        # Check if user already exists with this email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # User exists, update Google ID if not set
            if not hasattr(user, 'google_id') or not user.google_id:
                # Add google_id dynamically if it doesn't exist in the model
                # FIXME: Ideally, the User model should have a google_id field
                # Add it to app/models/database.py
                setattr(user, 'google_id', google_id)
                db.commit()
            return user
        else:
            # Create new user
            # Generate username from email
            username = email.split('@')[0]
            # Generate a random password
            import secrets
            random_password = secrets.token_urlsafe(16)
            hashed_password = get_password_hash(random_password)
            
            try:
                # Check if User model has google_id field
                # FIXME: Add google_id to User model in app/models/database.py
                has_google_id = hasattr(User, 'google_id')
                
                if has_google_id:
                    new_user = User(
                        email=email,
                        username=username,
                        hashed_password=hashed_password,
                        google_id=google_id,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                else:
                    # Create user without google_id field
                    new_user = User(
                        email=email,
                        username=username,
                        hashed_password=hashed_password,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    # Try to add google_id dynamically
                    setattr(new_user, 'google_id', google_id)
                    
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user
            except Exception as e:
                db.rollback()
                logger.error(f"Error creating new user from Google OAuth: {str(e)}")
                return None
    
    @staticmethod
    async def handle_oauth_callback(db: Session, code: str) -> Dict[str, Any]:
        """Handle the OAuth callback."""
        oauth_service = GoogleOAuthService()
        
        # Get tokens
        tokens = await oauth_service.exchange_code_for_token(code)
        if not tokens:
            return {"success": False, "message": "Failed to exchange authorization code for tokens"}
        
        # Get user info
        access_token = tokens.get("access_token")
        if not access_token:
            return {"success": False, "message": "No access token received"}
        
        user_info = await oauth_service.get_user_info(access_token)
        if not user_info:
            return {"success": False, "message": "Failed to get user info"}
        
        # Authenticate or create user
        user = await oauth_service.authenticate_google_user(db, user_info)
        if not user:
            return {"success": False, "message": "Failed to authenticate user"}
        
        # Create access token
        token = create_access_token(data={"sub": user.username})
        
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
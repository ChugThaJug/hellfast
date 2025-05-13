# app/services/oauth.py
import httpx
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import User
from app.services.auth import create_access_token

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    @staticmethod
    async def get_authorization_url() -> str:
        """Get the Google authorization URL."""
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        scope = "email profile openid"
        
        # Always use backend URL for redirect
        redirect_uri = "http://localhost:8000/oauth/google/callback"  # Hardcoded for reliability
        
        # Debug logging
        print(f"OAuth Redirect URI: {redirect_uri}")
        logger.info(f"OAuth Redirect URI: {redirect_uri}")
        
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
    async def exchange_code_for_token(code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        # Use the provided redirect URI or default
        if not redirect_uri:
            redirect_uri = "http://localhost:8000/oauth/google/callback"
        
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
        picture = user_info.get("picture")
        
        if not google_id or not email:
            logger.error("Google ID or email missing from user info")
            return None
        
        # Check if user already exists with this email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # User exists, update Google ID if not set
            if hasattr(user, 'google_id') and not user.google_id:
                # Add google_id dynamically if it doesn't exist in the model
                setattr(user, 'google_id', google_id)
                
            # Update display name and photo
            if hasattr(user, 'display_name') and name:
                user.display_name = name
            if hasattr(user, 'photo_url') and picture:
                user.photo_url = picture
                
            # Update Firebase UID if it exists and not set
            if hasattr(user, 'firebase_uid') and not user.firebase_uid:
                setattr(user, 'firebase_uid', google_id)
                
            db.commit()
            return user
        else:
            # Create new user
            # Generate username from email
            username = email.split('@')[0]
            
            # Check if username exists and make it unique if needed
            existing_username = db.query(User).filter(User.username == username).first()
            if existing_username:
                import uuid
                username = f"{username}_{str(uuid.uuid4())[:8]}"
            
            try:
                # Create user with basic fields
                new_user = User(
                    email=email,
                    username=username,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Add optional fields if they exist in model
                if hasattr(User, 'google_id'):
                    new_user.google_id = google_id
                if hasattr(User, 'display_name'):
                    new_user.display_name = name
                if hasattr(User, 'photo_url'):
                    new_user.photo_url = picture
                if hasattr(User, 'firebase_uid'):
                    new_user.firebase_uid = google_id
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user
            except Exception as e:
                db.rollback()
                logger.error(f"Error creating new user from Google OAuth: {str(e)}")
                raise
    
    @staticmethod
    async def handle_oauth_callback(db: Session, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Handle the OAuth callback."""
        try:
            # Get tokens
            tokens = await GoogleOAuthService.exchange_code_for_token(code, redirect_uri)
            if not tokens:
                return {"success": False, "message": "Failed to exchange authorization code for tokens"}
            
            # Get user info
            access_token = tokens.get("access_token")
            if not access_token:
                return {"success": False, "message": "No access token received"}
            
            user_info = await GoogleOAuthService.get_user_info(access_token)
            if not user_info:
                return {"success": False, "message": "Failed to get user info"}
            
            # Authenticate or create user
            user = await GoogleOAuthService.authenticate_google_user(db, user_info)
            if not user:
                return {"success": False, "message": "Failed to authenticate user"}
            
            # Create JWT token for your application
            # This assumes you have a create_access_token function
            from app.services.auth import create_access_token
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
        except Exception as e:
            logger.error(f"OAuth error: {str(e)}")
            return {"success": False, "message": f"OAuth error: {str(e)}"}
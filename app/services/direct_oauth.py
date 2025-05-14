# app/services/direct_oauth.py
import httpx
import jwt
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import User

logger = logging.getLogger(__name__)

class DirectOAuthService:
    """Service for handling direct OAuth authentication without Firebase."""
    
    @staticmethod
    async def get_authorization_url() -> str:
        """Get the Google authorization URL."""
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        scope = "email profile openid"
        
        # Always use backend URL for redirect
        redirect_uri = settings.OAUTH_REDIRECT_URL
        
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
            redirect_uri = settings.OAUTH_REDIRECT_URL
        
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
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for our application."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def authenticate_user(db: Session, user_info: Dict[str, Any]) -> Optional[User]:
        """Authenticate a user with OAuth user info."""
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
        
        # Check if user already exists by google_id
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if user:
            # Update user info if needed
            user.display_name = name or user.display_name
            user.photo_url = picture or user.photo_url
            user.updated_at = datetime.utcnow()
            db.commit()
            return user
        
        # Check if user exists by email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update user with Google ID
            user.google_id = google_id
            user.display_name = name or user.display_name
            user.photo_url = picture or user.photo_url
            user.updated_at = datetime.utcnow()
            db.commit()
            return user
        
        # Create new user
        # Generate username from email
        username = email.split('@')[0]
        
        # Make username unique if needed
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            import uuid
            username = f"{username}_{str(uuid.uuid4())[:8]}"
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            google_id=google_id,
            display_name=name,
            photo_url=picture,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    @staticmethod
    async def handle_oauth_callback(db: Session, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Process the complete OAuth callback."""
        try:
            # Exchange code for tokens
            tokens = await DirectOAuthService.exchange_code_for_token(code, redirect_uri)
            if not tokens:
                return {"success": False, "message": "Failed to exchange authorization code for tokens"}
            
            # Get user info with the access token
            access_token = tokens.get("access_token")
            if not access_token:
                return {"success": False, "message": "No access token received"}
            
            user_info = await DirectOAuthService.get_user_info(access_token)
            if not user_info:
                return {"success": False, "message": "Failed to get user info"}
            
            # Authenticate or create user
            user = await DirectOAuthService.authenticate_user(db, user_info)
            if not user:
                return {"success": False, "message": "Failed to authenticate user"}
            
            # Create JWT token for the application
            token = DirectOAuthService.create_access_token(
                data={"sub": user.email, "user_id": user.id}
            )
            
            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": user.display_name,
                    "photo_url": user.photo_url
                }
            }
        except Exception as e:
            logger.error(f"OAuth error: {str(e)}")
            return {"success": False, "message": f"OAuth error: {str(e)}"}
    
    @staticmethod
    def create_demo_user(db: Session) -> User:
        """Create a demo user for development."""
        demo_user = db.query(User).filter(User.username == "demo").first()
        if demo_user:
            return demo_user
            
        # Create a new demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            google_id="demo_google_id",
            display_name="Demo User",
            photo_url="https://ui-avatars.com/api/?name=Demo+User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
            
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        return demo_user
    
    @staticmethod
    async def verify_token(token: str, db: Session) -> Optional[User]:
        """Verify JWT token and get user."""
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            user_id = payload.get("user_id")
            
            if not email:
                return None
                
            # Development mode - always return demo user
            if settings.APP_ENV == "development":
                return DirectOAuthService.create_demo_user(db)
                
            # Get user from database
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).filter(User.email == email).first()
                
            return user
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import jwt
import firebase_admin
from firebase_admin import credentials, auth
from app.core.settings import settings
from app.models.database import User

logger = logging.getLogger(__name__)

# Define the function at module level to make it directly importable
def initialize_firebase_admin():
    """Initialize Firebase Admin SDK with credentials."""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Check if service account key is provided as a file path
            if settings.FIREBASE_SERVICE_ACCOUNT_KEY and os.path.isfile(settings.FIREBASE_SERVICE_ACCOUNT_KEY):
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
            # Or if it's provided as JSON string in environment variable
            elif settings.FIREBASE_SERVICE_ACCOUNT_KEY and settings.FIREBASE_SERVICE_ACCOUNT_KEY.startswith('{'):
                service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                cred = credentials.Certificate(service_account_info)
            else:
                # Use application default credentials or initialize with just project ID
                if settings.FIREBASE_PROJECT_ID:
                    cred = credentials.ApplicationDefault()
                else:
                    logger.warning("Firebase credentials not provided. Some features may not work.")
                    return False
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
            })
            logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        # Don't raise exception - let application continue with limited functionality
        return False

# Try to initialize Firebase at module import
try:
    initialize_firebase_admin()
except Exception as e:
    logger.warning(f"Firebase initialization deferred: {str(e)}")

# For compatibility with old auth system
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token for compatibility with old auth system."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

class FirebaseAuthService:
    """Service for handling Firebase Authentication."""
    
    @staticmethod
    def initialize_firebase():
        """Initialize Firebase Admin SDK (wrapper for the module function)."""
        return initialize_firebase_admin()
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded token.
        
        Args:
            token: Firebase ID token
            
        Returns:
            Decoded token with user information
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def get_or_create_user(db: Session, firebase_user: Dict[str, Any]) -> User:
        """
        Get existing user or create a new one based on Firebase user data.
        
        Args:
            db: Database session
            firebase_user: Firebase user data from decoded token
            
        Returns:
            User database object
        """
        uid = firebase_user.get("uid")
        email = firebase_user.get("email")
        name = firebase_user.get("name")
        photo_url = firebase_user.get("picture")
        
        if not uid:
            raise ValueError("Firebase user ID (uid) is missing")
        
        if not email:
            # Try to get email from Firebase directly
            try:
                user_record = auth.get_user(uid)
                email = user_record.email
            except Exception as e:
                logger.error(f"Failed to get user email from Firebase: {str(e)}")
                # Generate a placeholder email if still not available
                email = f"{uid}@firebase.example.com"
        
        # Check if user exists by Firebase UID
        try:
            user = db.query(User).filter(User.firebase_uid == uid).first()
        except Exception as e:
            logger.error(f"Error querying by firebase_uid: {e}")
            # The column might not exist yet
            user = None
        
        if user:
            # Update user info if needed
            if name and hasattr(user, 'display_name') and user.display_name != name:
                user.display_name = name
            if photo_url and hasattr(user, 'photo_url') and user.photo_url != photo_url:
                user.photo_url = photo_url
            if email and user.email != email:
                user.email = email
            
            # Update timestamp if it exists
            if hasattr(user, 'updated_at'):
                user.updated_at = datetime.utcnow()
            
            db.commit()
            return user
        
        # Check if user exists by email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Link existing user with Firebase if the column exists
            try:
                user.firebase_uid = uid
                if hasattr(user, 'display_name') and name:
                    user.display_name = name
                if hasattr(user, 'photo_url') and photo_url:
                    user.photo_url = photo_url
                if hasattr(user, 'updated_at'):
                    user.updated_at = datetime.utcnow()
                
                db.commit()
            except Exception as e:
                logger.error(f"Error updating user with Firebase info: {e}")
                db.rollback()
            
            return user
        
        # Create new user
        username = email.split('@')[0]
        
        # Check if username exists and make it unique if needed
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            import uuid
            username = f"{username}_{str(uuid.uuid4())[:8]}"
        
        # Build user with attributes that definitely exist
        user_data = {
            "email": email,
            "username": username,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        
        # Add optional fields if they exist in model
        try:
            # Try to create a user including firebase fields
            new_user = User(
                **user_data,
                firebase_uid=uid,
                display_name=name,
                photo_url=photo_url,
                updated_at=datetime.utcnow()
            )
        except TypeError:
            # If the firebase fields don't exist, create without them
            new_user = User(**user_data)
        
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating new user from Firebase OAuth: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_by_token(db: Session, token: str) -> Optional[User]:
        """
        Get user by Firebase ID token.
        
        Args:
            db: Database session
            token: Firebase ID token
            
        Returns:
            User database object or None if not found
        """
        try:
            # Verify the token
            decoded_token = FirebaseAuthService.verify_token(token)
            
            # Get or create user
            user = await FirebaseAuthService.get_or_create_user(db, decoded_token)
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user by token: {str(e)}")
            return None
            
    @staticmethod
    def create_demo_user(db: Session) -> User:
        """Create a demo user for development purposes."""
        try:
            # Check if demo user exists
            demo_user = db.query(User).filter(User.username == "demo").first()
            if demo_user:
                return demo_user
                
            # Create a new demo user with default values
            demo_user = User(
                username="demo",
                email="demo@example.com",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Add firebase fields if they exist
            if hasattr(User, 'firebase_uid'):
                demo_user.firebase_uid = "demo_firebase_uid"
            if hasattr(User, 'display_name'):
                demo_user.display_name = "Demo User"
            if hasattr(User, 'updated_at'):
                demo_user.updated_at = datetime.utcnow()
                
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            return demo_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating demo user: {str(e)}")
            # Try to get demo user if it exists despite error
            demo_user = db.query(User).filter(User.username == "demo").first()
            if demo_user:
                return demo_user
            raise
    
    @staticmethod
    def get_firebase_user(uid: str) -> Dict[str, Any]:
        """
        Get Firebase user information by UID.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            Firebase user information
        """
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "email_verified": user.email_verified,
                "disabled": user.disabled
            }
        except Exception as e:
            logger.error(f"Failed to get Firebase user: {str(e)}")
            raise
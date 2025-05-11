import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
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
            if os.path.isfile(settings.FIREBASE_SERVICE_ACCOUNT_KEY):
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
            # Or if it's provided as JSON string in environment variable
            elif settings.FIREBASE_SERVICE_ACCOUNT_KEY.startswith('{'):
                service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                cred = credentials.Certificate(service_account_info)
            else:
                # Default to application default credentials
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
            })
            logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise

# Try to initialize Firebase at module import
try:
    initialize_firebase_admin()
except Exception as e:
    logger.warning(f"Firebase initialization deferred: {str(e)}")

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
        user = db.query(User).filter(User.firebase_uid == uid).first()
        
        if user:
            # Update user info if needed
            if name and user.display_name != name:
                user.display_name = name
            if photo_url and user.photo_url != photo_url:
                user.photo_url = photo_url
            if email and user.email != email:
                user.email = email
            
            user.updated_at = datetime.utcnow()
            db.commit()
            return user
        
        # Check if user exists by email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Link existing user with Firebase
            user.firebase_uid = uid
            if name:
                user.display_name = name
            if photo_url:
                user.photo_url = photo_url
            
            user.updated_at = datetime.utcnow()
            db.commit()
            return user
        
        # Create new user
        username = email.split('@')[0]
        
        # Check if username exists and make it unique if needed
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            import uuid
            username = f"{username}_{str(uuid.uuid4())[:8]}"
        
        new_user = User(
            email=email,
            username=username,
            firebase_uid=uid,
            display_name=name,
            photo_url=photo_url,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def get_user_by_token(db: Session, token: str) -> Optional[User]:
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
            user = FirebaseAuthService.get_or_create_user(db, decoded_token)
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user by token: {str(e)}")
            return None
    
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
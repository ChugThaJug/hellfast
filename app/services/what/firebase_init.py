# app/services/firebase_init.py
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Flag to track if Firebase was successfully initialized
firebase_initialized = False

# Try to initialize Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    
    def initialize_firebase_admin():
        """Initialize Firebase Admin SDK with credentials."""
        global firebase_initialized
        
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                from app.core.settings import settings
                
                # If we have service account credentials
                if settings.FIREBASE_SERVICE_ACCOUNT_KEY:
                    try:
                        if os.path.isfile(settings.FIREBASE_SERVICE_ACCOUNT_KEY):
                            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                        else:
                            import json
                            service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                            cred = credentials.Certificate(service_account_info)
                        
                        firebase_admin.initialize_app(cred, {
                            'projectId': settings.FIREBASE_PROJECT_ID,
                        })
                        firebase_initialized = True
                        logger.info("Firebase Admin SDK initialized successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to initialize Firebase with credentials: {str(e)}")
                
                # Try application default
                if not firebase_initialized:
                    try:
                        from app.core.settings import settings
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred, {
                            'projectId': settings.FIREBASE_PROJECT_ID,
                        })
                        firebase_initialized = True
                        logger.info("Firebase Admin SDK initialized successfully with default credentials")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to initialize Firebase with application default: {str(e)}")
                
                if not firebase_initialized:
                    logger.warning("Firebase credentials not provided. Using development mode fallback.")
                    return False
            else:
                firebase_initialized = True
                return True
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            return False
        
        return firebase_initialized
    
    class FirebaseAuthService:
        """Service for handling Firebase Authentication."""
        
        @staticmethod
        def verify_token(token: str) -> Dict[str, Any]:
            """Verify Firebase ID token and return decoded token."""
            try:
                # Verify the ID token
                decoded_token = auth.verify_id_token(token)
                return decoded_token
            except Exception as e:
                logger.error(f"Token verification failed: {str(e)}")
                raise Exception(f"Invalid authentication credentials: {str(e)}")
        
        @staticmethod
        async def get_user_by_token(db: Session, token: str) -> Optional["User"]:
            """Get user by Firebase ID token."""
            try:
                from app.models.database import User
                
                # Verify the token
                decoded_token = FirebaseAuthService.verify_token(token)
                
                # Get or create user
                user = await FirebaseAuthService.get_or_create_user(db, decoded_token)
                return user
            except Exception as e:
                logger.error(f"Failed to get user by token: {str(e)}")
                return None
                
        @staticmethod
        async def get_or_create_user(db: Session, firebase_user: Dict[str, Any]):
            """Get existing user or create a new one based on Firebase user data."""
            from app.models.database import User
            
            uid = firebase_user.get("uid")
            email = firebase_user.get("email")
            name = firebase_user.get("name")
            photo_url = firebase_user.get("picture")
            
            # First try to find user by Firebase UID
            user = None
            try:
                user = db.query(User).filter(User.firebase_uid == uid).first()
            except:
                pass
            
            if user:
                return user
            
            # Try by email
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    # Update Firebase uid if needed
                    if hasattr(user, 'firebase_uid') and not user.firebase_uid:
                        user.firebase_uid = uid
                    db.commit()
                    return user
            
            # Create new user
            username = email.split('@')[0] if email else f"user_{uid[:8]}"
            
            # Make username unique if needed
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                import uuid
                username = f"{username}_{str(uuid.uuid4())[:8]}"
            
            # Create user
            user = User(
                username=username,
                email=email or f"{uid}@firebase.example.com",
                firebase_uid=uid,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add optional fields if they exist
            if hasattr(user, 'display_name') and name:
                user.display_name = name
            if hasattr(user, 'photo_url') and photo_url:
                user.photo_url = photo_url
            if hasattr(user, 'google_id') and uid:
                user.google_id = uid
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        
        @staticmethod
        def create_demo_user(db: Session):
            """Create a demo user for development purposes."""
            from app.models.database import User
            
            # Check if demo user exists
            demo_user = db.query(User).filter(User.username == "demo").first()
            if demo_user:
                return demo_user
                
            # Create a new demo user with default values
            demo_user = User(
                username="demo",
                email="demo@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add firebase fields if they exist
            if hasattr(User, 'firebase_uid'):
                demo_user.firebase_uid = "demo_firebase_uid"
            if hasattr(User, 'display_name'):
                demo_user.display_name = "Demo User"
            if hasattr(User, 'photo_url'):
                demo_user.photo_url = "https://ui-avatars.com/api/?name=Demo+User"
            if hasattr(User, 'google_id'):
                demo_user.google_id = "demo_google_id"
                
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            return demo_user

except ImportError:
    # Create fallback implementation if Firebase Admin is not available
    logger.warning("Firebase Admin SDK not available, using development mode fallback")
    
    def initialize_firebase_admin():
        """Fallback initialization that always returns False."""
        logger.warning("Using Firebase fallback - this is only suitable for development")
        return False
    
    class FirebaseAuthService:
        """Fallback service that only supports development mode."""
        
        @staticmethod
        def verify_token(token: str) -> Dict[str, Any]:
            """Fallback token verification."""
            raise Exception("Firebase Admin SDK not available, cannot verify tokens")
        
        @staticmethod
        async def get_user_by_token(db: Session, token: str) -> Optional["User"]:
            """Fallback that always returns None."""
            return None
        
        @staticmethod
        async def get_or_create_user(db: Session, firebase_user: Dict[str, Any]):
            """Fallback that returns None."""
            return None
        
        @staticmethod
        def create_demo_user(db: Session):
            """Create a demo user for development purposes."""
            from app.models.database import User
            
            # Check if demo user exists
            demo_user = db.query(User).filter(User.username == "demo").first()
            if demo_user:
                return demo_user
                
            # Create a new demo user with default values
            demo_user = User(
                username="demo",
                email="demo@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add firebase fields if they exist
            if hasattr(User, 'firebase_uid'):
                demo_user.firebase_uid = "demo_firebase_uid"
            if hasattr(User, 'display_name'):
                demo_user.display_name = "Demo User"
            if hasattr(User, 'photo_url'):
                demo_user.photo_url = "https://ui-avatars.com/api/?name=Demo+User"
            if hasattr(User, 'google_id'):
                demo_user.google_id = "demo_google_id"
                
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            return demo_user
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
import logging
import secrets

from app.core.settings import settings
from app.models.database import User, ApiKey
from app.db.database import get_db

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password, hashed_password):
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password for storage."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Make sure SECRET_KEY and ALGORITHM are defined in settings
    secret_key = getattr(settings, "SECRET_KEY", "development-secret-key")
    algorithm = getattr(settings, "ALGORITHM", "HS256")
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user."""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_user(db: Session, email: str, username: str, password: str):
    """Create a new user."""
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Created new user: {username}")
    return db_user

# For development, we'll use a simplified token validation
# that doesn't require an actual JWT token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """For development: always return a demo user without checking the token."""
    # Create a demo user if it doesn't exist
    demo_user = db.query(User).filter(User.username == "demo").first()
    if not demo_user:
        demo_user = User(
            id=1,
            username="demo",
            email="demo@example.com",
            hashed_password=get_password_hash("password"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    
    return demo_user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user."""
    return current_user

async def validate_api_key(api_key: str, db: Session) -> User:
    """Validate API key and return the associated user."""
    # Check if API key exists
    db_api_key = db.query(ApiKey).filter(ApiKey.api_key == api_key, ApiKey.is_active == True).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Update last used timestamp
    db_api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    # Get user
    user = db.query(User).filter(User.id == db_api_key.user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def create_api_key(db: Session, user_id: int, name: str = "Default API Key") -> str:
    """Create a new API key for a user."""
    # Generate a unique API key
    api_key = f"{settings.API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    
    # Create API key in database
    db_api_key = ApiKey(
        user_id=user_id,
        api_key=api_key,
        name=name,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_api_key)
    db.commit()
    
    return api_key
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from app.db.database import get_db
from app.models.database import User, ApiKey
from app.services.auth import (
    authenticate_user, create_access_token, create_user, get_password_hash,
    get_current_active_user, create_api_key
)
from app.core.settings import settings

# Define Pydantic models for request/response
from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        orm_mode = True

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class ApiKeyResponse(BaseModel):
    name: str
    api_key: str
    created_at: str

    class Config:
        orm_mode = True

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Get access token using username and password."""
    # Define a default expiry time to use if the setting is missing
    try:
        access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    except AttributeError:
        # Default to 30 minutes if the setting is missing
        access_token_expire_minutes = 30
    
    access_token_expires = timedelta(minutes=access_token_expire_minutes)
    
    # For development, we'll always return a token
    access_token = create_access_token(
        data={"sub": "demo"},  # Always use "demo" user for development
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Always create a new user for development (no duplicate checks)
    new_user = create_user(
        db, 
        user_data.email,
        user_data.username,
        user_data.password
    )
    
    # Create a response object
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=True
    )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )

@router.post("/api-key", response_model=ApiKeyResponse)
async def create_new_api_key(
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new API key for the current user."""
    api_key = await create_api_key(db, current_user.id, key_data.name)
    
    return ApiKeyResponse(
        name=key_data.name,
        api_key=api_key,
        created_at=db.query(ApiKey).filter(ApiKey.api_key == api_key).first().created_at.isoformat()
    )

@router.get("/status")
async def auth_status():
    return {"status": "Auth routes are working"}
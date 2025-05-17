import os
from pydantic_settings import BaseSettings
from typing import Dict, List, Any, Optional, ClassVar, Union

# Setup environment variables
class Settings(BaseSettings):
    # Add ClassVar type annotations for all class variables
    VERCEL_URL: ClassVar[str] = ''
    FRONTEND_URL: ClassVar[str] = 'http://localhost:5173'
    
    # Add missing APP_TITLE attribute
    APP_TITLE: str = "Hellfast API"
    
    # App settings
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Add the missing LOG_LEVEL attribute
    LOG_LEVEL: str = "INFO"
    
    # API settings
    API_V1_PREFIX: ClassVar[str] = "/api/v1"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:4173"]
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: ClassVar[str] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Model settings
    MODEL: str = "gpt-3.5-turbo"
    
    # Paddle settings
    PADDLE_API_KEY: str = ""
    PADDLE_WEBHOOK_SECRET: str = ""
    PADDLE_SANDBOX: bool = True
    
    # Plan IDs
    PADDLE_PRO_PLAN_ID: str = ""
    PADDLE_PRO_YEARLY_PLAN_ID: str = ""
    PADDLE_MAX_PLAN_ID: str = ""
    PADDLE_MAX_YEARLY_PLAN_ID: str = ""
    
    # Paddle checkout URLs
    PADDLE_CHECKOUT_SUCCESS_URL: str = ""
    PADDLE_CHECKOUT_CANCEL_URL: str = ""
    
    # Add missing fields from the .env file
    OPENAI_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URL: str = "http://localhost:8000/oauth/google/callback"
    REPLICATE_API_TOKEN: str = ""
    
    # Uploads and temporary directories
    UPLOADS_DIR: str = "uploads"
    TEMP_DIR: str = "temp"
    
    # Subscription plans configuration
    SUBSCRIPTION_PLANS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "free": {
            "name": "Free",
            "price": 0.00,
            "monthly_quota": 5,
            "features": ["5 videos per month", "3 minutes max length", "Basic editing tools"],
            "max_video_length": 180,  # 3 minutes in seconds
        },
        "pro": {
            "name": "Pro",
            "price": 29.00,
            "yearly_price": 290.00,  # 10 months for the price of 12
            "monthly_quota": 50,
            "features": ["50 videos per month", "10 minutes max length", "Advanced editing tools", "Priority support"],
            "max_video_length": 600,  # 10 minutes in seconds
            "paddle_plan_id": "",
            "paddle_yearly_plan_id": "",
        },
        "max": {
            "name": "Max",
            "price": 79.00,
            "yearly_price": 790.00,  # 10 months for the price of 12
            "monthly_quota": 200,
            "features": ["200 videos per month", "Unlimited video length", "All editing tools", "Priority support", "Custom templates"],
            "max_video_length": 3600,  # 60 minutes in seconds
            "paddle_plan_id": "",
            "paddle_yearly_plan_id": "",
        }
    }

    class Config:
        env_file = ".env"
        
        # Allow extra fields from environment, preventing validation errors
        extra = "ignore"
        
        # Add this config to ignore non-field class variables
        model_config = {
            "ignored_types": (ClassVar,)
        }

# Create a global settings instance
settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOADS_DIR, settings.TEMP_DIR]:
    if directory:
        os.makedirs(directory, exist_ok=True)
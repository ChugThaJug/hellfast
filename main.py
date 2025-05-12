from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os

from app.core.settings import settings
from app.db.database import create_tables, get_db
from app.models.database import User
from app.services.firebase_auth import initialize_firebase_admin
from app.dependencies.auth import get_current_active_user

# IMPORTANT: Force development mode
os.environ["APP_ENV"] = "development"
settings.APP_ENV = "development"

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Print development mode status
logger.info(f"Running in {settings.APP_ENV} mode")
logger.info(f"Development mode enabled: {settings.APP_ENV == 'development'}")

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables and initialize Firebase
    try:
        create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize Firebase Admin SDK
        try:
            initialize_firebase_admin()
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            logger.info("In development mode, this is not a critical error")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Import routers - do this AFTER app is created
from app.api.routes import youtube, subscription, firebase_auth

# Include routers - only import what we need
app.include_router(youtube.router)
app.include_router(subscription.router)
app.include_router(firebase_auth.router)  # Add Firebase auth routes

# Root endpoint
@app.get("/")
async def root():
    return {
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.APP_ENV
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

# User profile endpoint
@app.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from app.services.subscription import SubscriptionService
    
    # Get subscription features
    subscription_features = await SubscriptionService.get_subscription_features(db, current_user.id)
    
    # Build response with only fields that exist
    profile = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "subscription": {
            "plan": subscription_features["plan"],
            "quota": subscription_features["quota"],
            "features": subscription_features["features"]
        },
        "development_mode": settings.APP_ENV == "development"
    }
    
    # Add Firebase fields if they exist
    if hasattr(current_user, 'display_name') and current_user.display_name:
        profile["display_name"] = current_user.display_name
    if hasattr(current_user, 'photo_url') and current_user.photo_url:
        profile["photo_url"] = current_user.photo_url
    if hasattr(current_user, 'firebase_uid') and current_user.firebase_uid:
        profile["firebase_uid"] = current_user.firebase_uid
    
    return profile

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting YouTube Processing API...")
    logger.info(f"Running in {settings.APP_ENV} mode")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
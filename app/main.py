from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.database import create_tables, get_db
from app.api.routes import auth, youtube, subscription
from app.models.database import User
from app.dependencies.auth import get_current_active_user
# Try to use the real Firebase, fall back to stub implementation
try:
    from app.services.firebase_auth import initialize_firebase_admin
except ImportError:
    from app.services.init_firebase import initialize_firebase_admin
    
from app.dependencies.auth import get_current_active_user
# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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

# Import Firebase router after defining main app
from app.api.routes import firebase_auth

# Include routers
app.include_router(auth.router)  # Keep for backward compatibility
app.include_router(youtube.router)
app.include_router(subscription.router)
app.include_router(firebase_auth.router)  # Add Firebase auth routes

# Root endpoint
@app.get("/")
async def root():
    return {
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_version": settings.APP_VERSION
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
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": getattr(current_user, "display_name", None),
        "photo_url": getattr(current_user, "photo_url", None),
        "created_at": current_user.created_at.isoformat(),
        "subscription": {
            "plan": subscription_features["plan"],
            "quota": subscription_features["quota"],
            "features": subscription_features["features"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting YouTube Processing API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
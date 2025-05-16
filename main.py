# app/main.py
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
from app.dependencies.auth import get_current_active_user

# Configure environment - Use environment variable
app_env = os.getenv("APP_ENV", "development")
settings.APP_ENV = app_env

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Print environment status
logger.info(f"Running in {settings.APP_ENV} mode")

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
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

# Add CORS middleware - Make sure frontend URL is included
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # SvelteKit default dev port
        "http://localhost:4173",  # SvelteKit preview
        "http://localhost:3000",  # Alternative dev port
        *settings.CORS_ORIGINS,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Special handling for webhook routes to get raw body
    path = request.url.path
    if "/webhooks/" in path:
        # Store the body before processing
        body = await request.body()
        # Create a new request with the same body
        request = Request(scope=request.scope, receive=request._receive)
        # Define a custom receive function that returns the stored body
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
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


# Add this debug endpoint after your other endpoints (before if __name__ == "__main__")
@app.get("/debug/settings", include_in_schema=settings.APP_ENV == "development")
async def debug_settings():
    """Debug endpoint to check settings (only available in development mode)."""
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints only available in development mode"
        )
    
    subscription_plans = {}
    for plan_id, plan_data in settings.SUBSCRIPTION_PLANS.items():
        # Create a copy to avoid modifying the original
        plan_info = dict(plan_data)
        # Add paddle IDs specifically for debugging
        if plan_id == "pro":
            plan_info["debug_paddle_id"] = settings.PADDLE_PRO_PLAN_ID
            plan_info["debug_paddle_yearly_id"] = settings.PADDLE_PRO_YEARLY_PLAN_ID
        elif plan_id == "max":
            plan_info["debug_paddle_id"] = settings.PADDLE_MAX_PLAN_ID
            plan_info["debug_paddle_yearly_id"] = settings.PADDLE_MAX_YEARLY_PLAN_ID
        subscription_plans[plan_id] = plan_info
    
    return {
        "app_env": settings.APP_ENV,
        "paddle_sandbox": settings.PADDLE_SANDBOX,
        "paddle_api_key_configured": bool(settings.PADDLE_API_KEY),
        "paddle_webhook_secret_configured": bool(settings.PADDLE_WEBHOOK_SECRET),
        "paddle_plan_ids": {
            "pro": settings.PADDLE_PRO_PLAN_ID,
            "pro_yearly": settings.PADDLE_PRO_YEARLY_PLAN_ID,
            "max": settings.PADDLE_MAX_PLAN_ID,
            "max_yearly": settings.PADDLE_MAX_YEARLY_PLAN_ID
        },
        "subscription_plans": subscription_plans
    }

# Import routers - do this AFTER app is created
from app.api.routes import youtube, subscription, oauth, webhook
from app.api.routes.auth_api import router as auth_router

# Include routers
app.include_router(youtube.router)
app.include_router(subscription.router)
app.include_router(oauth.router)
app.include_router(auth_router)
app.include_router(webhook.router)  # Add webhook router

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
    from app.services.subscription_service import SubscriptionService
    
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
    
    # Add optional fields if they exist
    if hasattr(current_user, 'display_name') and current_user.display_name:
        profile["display_name"] = current_user.display_name
    if hasattr(current_user, 'photo_url') and current_user.photo_url:
        profile["photo_url"] = current_user.photo_url
    
    return profile



if __name__ == "__main__":
    import uvicorn
    logger.info("Starting YouTube Processing API...")
    logger.info(f"Running in {settings.APP_ENV} mode")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
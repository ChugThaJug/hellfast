# app/api/routes/subscription.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging

from app.db.database import get_db
from app.models.database import User, Subscription
from app.dependencies.auth import get_current_active_user
from app.services.subscription_service import SubscriptionService
from app.services.paddle_direct import PaddleDirectService
from app.core.settings import settings

# Define Pydantic models for request/response
from pydantic import BaseModel, Field, validator
from fastapi.responses import JSONResponse

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    yearly_price: Optional[float] = None
    monthly_quota: int
    features: List[str]
    max_video_length: Optional[int] = None

class SubscriptionStatus(BaseModel):
    plan_id: str
    status: str
    current_period_end: str
    monthly_quota: int
    used_quota: int
    features: List[str]
    max_video_length: Optional[int] = None

class PlanRequest(BaseModel):
    plan_id: str = Field(..., description="Plan ID must be 'pro' or 'max'")
    billing_cycle: str = Field(..., description="Billing cycle must be 'monthly' or 'yearly'")
    
    @validator('plan_id')
    def validate_plan_id(cls, v):
        if v not in ['pro', 'max']:
            raise ValueError("Plan ID must be 'pro' or 'max'")
        return v
    
    @validator('billing_cycle')
    def validate_billing_cycle(cls, v):
        if v not in ['monthly', 'yearly']:
            raise ValueError("Billing cycle must be 'monthly' or 'yearly'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "plan_id": "pro",
                "billing_cycle": "monthly"
            }
        }

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans():
    """Get all available subscription plans."""
    plans = []
    for plan_id, plan_data in settings.SUBSCRIPTION_PLANS.items():
        plan_dict = {
            "id": plan_id,
            "name": plan_data["name"],
            "price": plan_data["price"],
            "monthly_quota": plan_data["monthly_quota"],
            "features": plan_data["features"],
            "max_video_length": plan_data.get("max_video_length")
        }
        
        # Add yearly price if available
        if "yearly_price" in plan_data:
            plan_dict["yearly_price"] = plan_data["yearly_price"]
            
        plans.append(plan_dict)
        
    return plans

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subscription status for current user."""
    # Get subscription
    subscription = SubscriptionService.get_subscription(db, current_user.id)
    
    if not subscription:
        # Return free tier info
        free_plan = settings.SUBSCRIPTION_PLANS["free"]
        return {
            "plan_id": "free",
            "status": "active",
            "current_period_end": "-",
            "monthly_quota": free_plan["monthly_quota"],
            "used_quota": 0,
            "features": free_plan["features"],
            "max_video_length": free_plan.get("max_video_length")
        }
    
    # Get subscription features
    features_data = await SubscriptionService.get_subscription_features(db, current_user.id)
    
    # Get plan data
    plan_data = settings.SUBSCRIPTION_PLANS.get(subscription.plan_id, settings.SUBSCRIPTION_PLANS["free"])
    
    return {
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end.isoformat(),
        "monthly_quota": subscription.monthly_quota,
        "used_quota": subscription.used_quota,
        "features": features_data["features"],
        "max_video_length": plan_data.get("max_video_length")
    }

@router.post("/create")
async def create_checkout_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a checkout session for subscription."""
    try:
        # First try to parse the raw request to see what's being sent
        body = await request.json()
        logger.info(f"Received subscription request: {body}")
        
        # Handle the client sending {"plan_id": "pro", "yearly": false} format
        # Convert to our expected {"plan_id": "pro", "billing_cycle": "monthly"|"yearly"} format
        if "yearly" in body and "billing_cycle" not in body:
            yearly = body.pop("yearly")
            body["billing_cycle"] = "yearly" if yearly else "monthly"
            logger.info(f"Converted request format to: {body}")
        
        # Now try to validate the data with our model
        try:
            plan_data = PlanRequest(**body)
        except Exception as validation_error:
            logger.error(f"Invalid subscription request data: {validation_error}")
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Invalid request format",
                    "expected_format": {"plan_id": "pro or max", "billing_cycle": "monthly or yearly"},
                    "errors": str(validation_error),
                    "received": body
                }
            )
        
        # Log the received request data
        logger.info(f"Creating checkout session for plan: {plan_data.plan_id}, billing cycle: {plan_data.billing_cycle}")
        
        # Get the price ID based on the plan and billing cycle
        price_id = None
        if plan_data.plan_id == "pro":
            price_id = settings.PADDLE_PRO_YEARLY_PLAN_ID if plan_data.billing_cycle == "yearly" else settings.PADDLE_PRO_PLAN_ID
        elif plan_data.plan_id == "max":
            price_id = settings.PADDLE_MAX_YEARLY_PLAN_ID if plan_data.billing_cycle == "yearly" else settings.PADDLE_MAX_PLAN_ID
        else:
            raise HTTPException(status_code=400, detail="Invalid plan ID")
        
        # Validate price ID
        if not price_id:
            logger.error(f"Price ID not found for plan: {plan_data.plan_id}, billing cycle: {plan_data.billing_cycle}")
            raise HTTPException(status_code=400, detail="Plan configuration error. Please contact support.")
        
        # Check if price ID exists in Paddle before trying to create checkout
        price_exists = await PaddleDirectService.check_price_exists(price_id)
        if not price_exists:
            logger.error(f"Price ID {price_id} does not exist in Paddle account")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": f"Price ID {price_id} not found in Paddle. Please check your subscription plans configuration.",
                    "error_code": "price_not_found",
                }
            )
        
        # Create checkout session using the correct parameters
        try:
            checkout_data = await PaddleDirectService.create_checkout(
                price_id=price_id,
                email=current_user.email,
                customer_id=current_user.id
            )
            
            # Check if there was an error
            if isinstance(checkout_data, dict) and checkout_data.get("error"):
                error_details = checkout_data.get("details", {})
                error_message = error_details.get("error", {}).get("message", checkout_data.get("message", "Unknown error"))
                logger.error(f"Paddle checkout creation error: {error_message}")
                raise HTTPException(status_code=400, detail=f"Payment provider error: {error_message}")
                
            return checkout_data
            
        except ValueError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the checkout")

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel the current subscription."""
    subscription = SubscriptionService.get_subscription(db, current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Cancel subscription
    success = await SubscriptionService.cancel_subscription(db, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
        
    return {
        "message": "Subscription cancelled successfully. You have been downgraded to the free plan."
    }

@router.post("/debug", include_in_schema=settings.APP_ENV == "development")
async def debug_subscription_request(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Debug endpoint to echo back the received request body."""
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=404, detail="Not Found")
        
    try:
        body = await request.json()
        return {
            "received": body,
            "expected_format": {
                "plan_id": "pro or max",
                "billing_cycle": "monthly or yearly"
            },
            "user_id": current_user.id,
            "user_email": current_user.email
        }
    except Exception as e:
        return {
            "error": "Could not parse JSON body",
            "expected_format": {
                "plan_id": "pro or max",
                "billing_cycle": "monthly or yearly"
            },
            "exception": str(e)
        }

@router.get("/checkout-data/{plan_id}")
async def get_checkout_data(
    plan_id: str,
    yearly: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """Get checkout data for initializing Paddle.js on the frontend."""
    try:
        # Validate the plan ID
        if plan_id not in ["pro", "max"]:
            raise HTTPException(status_code=400, detail="Invalid plan ID. Must be 'pro' or 'max'")
        
        # Get checkout data from the Paddle service
        checkout_data = await PaddleDirectService.get_checkout_data_for_frontend(
            plan_id=plan_id,
            is_yearly=yearly,
            user_id=current_user.id,
            email=current_user.email
        )
        
        return checkout_data
        
    except ValueError as e:
        logger.error(f"Error generating checkout data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating checkout data: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating checkout data")

@router.get("/paddle/prices")
async def list_paddle_prices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available Paddle prices (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        prices = await PaddleDirectService.list_available_prices()
        return prices
    except Exception as e:
        logger.exception(f"Error listing Paddle prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list Paddle prices")

@router.post("/debug-prices")
async def debug_paddle_prices(
    current_user: User = Depends(get_current_active_user)
):
    """Debug Paddle price IDs from settings."""
    try:
        # Get configured price IDs
        configured_prices = {
            "PADDLE_PRO_PLAN_ID": settings.PADDLE_PRO_PLAN_ID,
            "PADDLE_PRO_YEARLY_PLAN_ID": settings.PADDLE_PRO_YEARLY_PLAN_ID,
            "PADDLE_MAX_PLAN_ID": settings.PADDLE_MAX_PLAN_ID,
            "PADDLE_MAX_YEARLY_PLAN_ID": settings.PADDLE_MAX_YEARLY_PLAN_ID
        }
        
        # Check existence of each price ID
        results = {}
        for name, price_id in configured_prices.items():
            if not price_id:
                results[name] = {"exists": False, "reason": "Not configured (empty)"}
                continue
                
            try:
                exists = await PaddleDirectService.check_price_exists(price_id)
                results[name] = {"exists": exists, "price_id": price_id}
            except Exception as e:
                results[name] = {"exists": False, "price_id": price_id, "error": str(e)}
        
        return {
            "sandbox_mode": settings.PADDLE_SANDBOX,
            "configured_prices": results
        }
    except Exception as e:
        logger.exception(f"Error debugging prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to debug price IDs")

@router.get("/paddle-config", include_in_schema=settings.APP_ENV == "development")
async def get_paddle_config(
    current_user: User = Depends(get_current_active_user)
):
    """Get Paddle configuration for debugging (development only)."""
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=404, detail="Not found")
        
    # Return configuration information (sanitized for security)
    return {
        "environment": "sandbox" if settings.PADDLE_SANDBOX else "production",
        "frontend_url": settings.FRONTEND_URL,
        "paddle_checkout_success_url": getattr(settings, "PADDLE_CHECKOUT_SUCCESS_URL", 
                                             f"{settings.FRONTEND_URL}/subscription/success"),
        "paddle_checkout_cancel_url": getattr(settings, "PADDLE_CHECKOUT_CANCEL_URL", 
                                            f"{settings.FRONTEND_URL}/subscription/cancel"),
        "api_key_valid": PaddleDirectService.is_api_key_configured(),
        "webhook_secret_configured": bool(settings.PADDLE_WEBHOOK_SECRET),
        "plan_ids": {
            "pro": {
                "monthly": settings.PADDLE_PRO_PLAN_ID[:10] + "..." if settings.PADDLE_PRO_PLAN_ID else None,
                "yearly": settings.PADDLE_PRO_YEARLY_PLAN_ID[:10] + "..." if settings.PADDLE_PRO_YEARLY_PLAN_ID else None,
            },
            "max": {
                "monthly": settings.PADDLE_MAX_PLAN_ID[:10] + "..." if settings.PADDLE_MAX_PLAN_ID else None,
                "yearly": settings.PADDLE_MAX_YEARLY_PLAN_ID[:10] + "..." if settings.PADDLE_MAX_YEARLY_PLAN_ID else None,
            }
        },
        "recommendation": """
        For proper Paddle integration:
        1. Register a domain with HTTPS (or use a service like ngrok)
        2. Configure this domain in your Paddle dashboard
        3. Update FRONTEND_URL in your .env file
        4. Set your PADDLE_CHECKOUT_SUCCESS_URL and PADDLE_CHECKOUT_CANCEL_URL
        """
    }
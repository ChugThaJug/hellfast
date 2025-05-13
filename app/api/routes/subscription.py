# app/api/routes/subscription.py
# Add/update routes for Paddle

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
import logging

from app.db.database import get_db
from app.models.database import User, Subscription
from app.services.auth import get_current_active_user
from app.services.subscription import SubscriptionService
from app.services.paddle import PaddleService
from app.core.settings import settings

# Define Pydantic models for request/response
from pydantic import BaseModel

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

class SubscriptionCreate(BaseModel):
    plan_id: str
    yearly: bool = False

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

@router.post("/create", response_model=Dict)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update a subscription."""
    if subscription_data.plan_id not in settings.SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID"
        )
    
    # For free plan, just create subscription without payment
    if subscription_data.plan_id == "free":
        subscription = await SubscriptionService.create_subscription(
            db, current_user.id, "free"
        )
        return {
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat(),
            "message": "Free subscription activated successfully"
        }
    
    # For paid plans, create checkout URL
    success_url = f"{settings.FRONTEND_URL}/subscription/success?plan_id={subscription_data.plan_id}"
    cancel_url = f"{settings.FRONTEND_URL}/subscription/cancel"
    
    # Create Paddle checkout
    checkout_url = await PaddleService.create_checkout(
        plan_id=subscription_data.plan_id,
        user_id=current_user.id,
        user_email=current_user.email,
        is_yearly=subscription_data.yearly,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if not checkout_url:
        # In development mode, activate subscription directly
        if settings.APP_ENV == "development":
            subscription = await SubscriptionService.create_subscription(
                db, current_user.id, subscription_data.plan_id
            )
            return {
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end.isoformat(),
                "message": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} subscription activated successfully (development mode)"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
    
    # Return checkout URL for redirection
    return {
        "checkout_url": checkout_url
    }

@router.post("/paddle-webhook", include_in_schema=False)
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paddle webhook events."""
    try:
        # Parse webhook data
        data = await request.json()
        
        # Get signature from header (if provided)
        signature = request.headers.get("Paddle-Signature", "")
        
        # Verify signature if in production
        if settings.APP_ENV != "development" and signature:
            if not PaddleService.verify_webhook_signature(data, signature):
                logger.warning("Invalid Paddle webhook signature")
                return {"status": "invalid_signature"}
        
        # Get alert name and data
        alert_name = data.get("alert_name")
        logger.info(f"Received Paddle webhook: {alert_name}")
        
        # Process different webhook events
        if alert_name == "subscription_created":
            # Extract data
            subscription_id = data.get("subscription_id")
            user_id = None
            plan_id = None
            
            # Extract user_id and plan_id from passthrough
            try:
                passthrough = json.loads(data.get("passthrough", "{}"))
                user_id = passthrough.get("user_id")
                plan_id = passthrough.get("plan_id")
            except:
                logger.error("Failed to parse passthrough data")
            
            if user_id and plan_id and subscription_id:
                # Get status and next bill date
                status = data.get("status", "active")
                next_bill_date = data.get("next_bill_date", "")
                
                # Create or update subscription
                await PaddleService.handle_subscription_created(
                    db, 
                    int(user_id), 
                    subscription_id, 
                    plan_id, 
                    status, 
                    next_bill_date
                )
        
        # Handle cancellation
        elif alert_name == "subscription_cancelled":
            subscription_id = data.get("subscription_id")
            if subscription_id:
                await PaddleService.handle_subscription_cancelled(db, subscription_id)
        
        # Handle updates
        elif alert_name == "subscription_updated":
            subscription_id = data.get("subscription_id")
            if subscription_id:
                status = data.get("status", "active")
                next_bill_date = data.get("next_bill_date", "")
                
                # Plan ID from passthrough if available
                plan_id = None
                try:
                    passthrough = json.loads(data.get("passthrough", "{}"))
                    plan_id = passthrough.get("plan_id")
                except:
                    pass
                
                await PaddleService.handle_subscription_updated(
                    db, subscription_id, status, plan_id, next_bill_date
                )
        
        # Payment succeeded event - update quota if it's a renewal
        elif alert_name == "payment_succeeded":
            subscription_id = data.get("subscription_id")
            if subscription_id:
                # Find subscription
                subscription = db.query(Subscription).filter(
                    Subscription.paddle_subscription_id == subscription_id
                ).first()
                
                if subscription:
                    # Reset quota for new billing period
                    subscription.used_quota = 0
                    db.commit()
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

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
    
    # Update subscription in database
    subscription.status = "cancelled"
    db.commit()
    
    # Create free subscription
    free_subscription = await SubscriptionService.create_subscription(
        db, 
        current_user.id, 
        "free"
    )
    
    return {
        "message": "Subscription cancelled successfully. You have been downgraded to the free plan."
    }
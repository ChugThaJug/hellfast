from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from typing import Dict, Optional, List

from app.core.settings import settings
from app.models.database import User, Subscription, Video, OutputFormat, ProcessingMode

logger = logging.getLogger(__name__)

# Try to import Stripe if available
try:
    import stripe
    stripe.api_key = settings.STRIPE_API_KEY
    HAS_STRIPE = True
except (ImportError, AttributeError):
    HAS_STRIPE = False
    logger.warning("Stripe not configured. Payment features will be limited.")


class SubscriptionService:
    @staticmethod
    def get_subscription(db: Session, user_id: int) -> Subscription:
        """Get user's subscription."""
        return db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
    @staticmethod
    def create_free_subscription(db: Session, user_id: int) -> Subscription:
        """Create a free subscription for a new user."""
        # Set period to one month from now
        current_time = datetime.utcnow()
        period_end = current_time + timedelta(days=30)
        
        subscription = Subscription(
            user_id=user_id,
            plan_id="free",
            status="active",
            current_period_start=current_time,
            current_period_end=period_end,
            monthly_quota=settings.SUBSCRIPTION_PLANS["free"]["monthly_quota"],
            used_quota=0
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created free subscription for user {user_id}")
        return subscription
    
# In app/services/subscription.py
# Method for creating a new subscription

    @staticmethod
    async def create_subscription(db: Session, user_id: int, plan_id: str, stripe_customer_id: Optional[str] = None) -> Subscription:
        """Create or update a subscription."""
        if plan_id not in settings.SUBSCRIPTION_PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan ID")
            
        # Get existing subscription if any
        existing = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        # Set period to one month from now
        current_time = datetime.utcnow()
        period_end = current_time + timedelta(days=30)
        
        if existing:
            # Update existing subscription
            existing.plan_id = plan_id
            existing.status = "active"
            existing.current_period_start = current_time
            existing.current_period_end = period_end
            existing.monthly_quota = settings.SUBSCRIPTION_PLANS[plan_id]["monthly_quota"]
            existing.updated_at = current_time
            
            if stripe_customer_id:
                existing.stripe_customer_id = stripe_customer_id
                
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated subscription for user {user_id} to {plan_id}")
            return existing
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                stripe_customer_id=stripe_customer_id,
                status="active",
                current_period_start=current_time,
                current_period_end=period_end,
                monthly_quota=settings.SUBSCRIPTION_PLANS[plan_id]["monthly_quota"],
                used_quota=0
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Created subscription for user {user_id} with plan {plan_id}")
            return subscription
    
    @staticmethod
    async def get_subscription_features(db: Session, user_id: int) -> Dict:
        """Get features available for a user's subscription."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription or subscription.status != "active":
            # Return free tier features
            return {
                "plan": "free",
                "features": settings.SUBSCRIPTION_PLANS["free"]["features"],
                "quota": {
                    "monthly": settings.SUBSCRIPTION_PLANS["free"]["monthly_quota"],
                    "used": 0,
                    "remaining": settings.SUBSCRIPTION_PLANS["free"]["monthly_quota"]
                }
            }
        
        plan_id = subscription.plan_id
        plan_features = settings.SUBSCRIPTION_PLANS.get(plan_id, settings.SUBSCRIPTION_PLANS["free"])
        
        return {
            "plan": plan_id,
            "features": plan_features["features"],
            "quota": {
                "monthly": subscription.monthly_quota,
                "used": subscription.used_quota,
                "remaining": subscription.monthly_quota - subscription.used_quota
            }
        }
    
    @staticmethod
    async def can_process_video(db: Session, user_id: int) -> bool:
        """Check if user can process more videos."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription:
            # Create free subscription if none exists
            subscription = SubscriptionService.create_free_subscription(db, user_id)
        
        # Check subscription status
        if subscription.status != "active":
            return False
        
        # Check quota
        if subscription.used_quota >= subscription.monthly_quota:
            return False
            
        return True
    
    @staticmethod
    async def increment_usage(db: Session, user_id: int) -> None:
        """Increment the user's quota usage."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription:
            # Create free subscription if none exists
            subscription = SubscriptionService.create_free_subscription(db, user_id)
        
        subscription.used_quota += 1
        db.commit()
    
    @staticmethod
    async def reset_monthly_quota(db: Session) -> None:
        """Reset monthly quota for subscriptions at period end."""
        current_time = datetime.utcnow()
        
        # Get subscriptions that need resetting
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.current_period_end <= current_time,
            Subscription.status == "active"
        ).all()
        
        for subscription in expired_subscriptions:
            # Reset quota
            subscription.used_quota = 0
            
            # Set new period
            subscription.current_period_start = current_time
            subscription.current_period_end = current_time + timedelta(days=30)
            
            logger.info(f"Reset quota for subscription {subscription.id}")
            
        db.commit()
    
    @staticmethod
    async def check_feature_access(db: Session, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        features = (await SubscriptionService.get_subscription_features(db, user_id))["features"]
        return feature in features
    
    @staticmethod
    async def validate_processing_request(
        db: Session, 
        user_id: int, 
        mode: ProcessingMode, 
        output_format: OutputFormat
    ) -> bool:
        """Validate if the user can use the requested processing options."""
        # Check quota first
        if not await SubscriptionService.can_process_video(db, user_id):
            raise HTTPException(
                status_code=403, 
                detail="Monthly quota exceeded. Please upgrade your subscription."
            )
        
        # Get user's features
        features = (await SubscriptionService.get_subscription_features(db, user_id))["features"]
        
        # Check mode access
        if mode == ProcessingMode.DETAILED and "detailed_mode" not in features:
            raise HTTPException(
                status_code=403,
                detail="Your current subscription does not include access to detailed mode. Please upgrade."
            )
        
        # Check output format access
        format_feature_map = {
            OutputFormat.BULLET_POINTS: "bullet_points",
            OutputFormat.SUMMARY: "summary",
            OutputFormat.STEP_BY_STEP: "step_by_step",
            OutputFormat.PODCAST_ARTICLE: "podcast_article"
        }
        
        if format_feature_map[output_format] not in features:
            raise HTTPException(
                status_code=403,
                detail=f"Your current subscription does not include access to {output_format.value} format. Please upgrade."
            )
        
        return True
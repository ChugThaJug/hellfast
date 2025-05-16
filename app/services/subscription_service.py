# app/services/subscription_service.py
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
import json

from app.core.settings import settings
from app.models.database import User, Subscription, OutputFormat, ProcessingMode
from app.services.paddle_direct import PaddleDirectService

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Comprehensive service for managing user subscriptions."""
    
    @staticmethod
    def get_subscription(db: Session, user_id: int) -> Optional[Subscription]:
        """Get a user's subscription"""
        return db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
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
    async def create_subscription(
        db: Session, 
        user_id: int, 
        plan_id: str, 
        paddle_subscription_id: Optional[str] = None
    ) -> Subscription:
        """Create or update a subscription."""
        if plan_id not in settings.SUBSCRIPTION_PLANS:
            raise ValueError(f"Invalid plan ID: {plan_id}")
        
        # Get existing subscription if any
        existing = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        # Set period to one month from now
        current_time = datetime.now(timezone.utc)
        period_end = current_time + timedelta(days=30)
        
        if existing:
            # Update existing subscription
            existing.plan_id = plan_id
            existing.status = "active"
            existing.current_period_start = current_time
            existing.current_period_end = period_end
            existing.monthly_quota = settings.SUBSCRIPTION_PLANS[plan_id]["monthly_quota"]
            existing.updated_at = current_time
            
            if paddle_subscription_id:
                existing.paddle_subscription_id = paddle_subscription_id
                
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated subscription for user {user_id} to {plan_id}")
            return existing
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                paddle_subscription_id=paddle_subscription_id,
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
    async def cancel_subscription(db: Session, user_id: int) -> bool:
        """Cancel a user's subscription and downgrade to free plan."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription:
            logger.warning(f"No subscription found for user {user_id}")
            return False
            
        try:
            # If subscription has a Paddle ID, cancel it through Paddle API
            if subscription.paddle_subscription_id:
                logger.info(f"Cancelling Paddle subscription: {subscription.paddle_subscription_id}")
                
                # Call Paddle API to cancel the subscription
                # Note: In a real implementation, we would make an API call to Paddle
                # to cancel the subscription, but for simplicity we'll just update our database
                
                # Update subscription status
                subscription.status = "cancelled"
                db.commit()
                
                # Create free subscription
                await SubscriptionService.create_subscription(
                    db, user_id, "free"
                )
                
                return True
            else:
                logger.warning(f"No Paddle subscription ID for user {user_id}")
                
                # Just downgrade to free plan
                await SubscriptionService.create_subscription(
                    db, user_id, "free"
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    @staticmethod
    async def increment_usage(db: Session, user_id: int) -> bool:
        """Increment a user's quota usage."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription:
            # Create free subscription if none exists
            subscription = await SubscriptionService.create_subscription(
                db, user_id, "free"
            )
        
        # Increment usage
        subscription.used_quota += 1
        db.commit()
        
        logger.info(f"Incremented usage for user {user_id}. New usage: {subscription.used_quota}/{subscription.monthly_quota}")
        return True
    
    @staticmethod
    async def can_process_video(db: Session, user_id: int) -> bool:
        """Check if a user can process more videos."""
        subscription = SubscriptionService.get_subscription(db, user_id)
        
        if not subscription:
            # Create free subscription if none exists
            subscription = await SubscriptionService.create_subscription(
                db, user_id, "free"
            )
        
        # Check subscription status
        if subscription.status != "active":
            return False
        
        # Check quota
        if subscription.used_quota >= subscription.monthly_quota:
            return False
            
        return True
    
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
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Monthly quota exceeded. Please upgrade your subscription."
            )
        
        # Get user's features
        features = (await SubscriptionService.get_subscription_features(db, user_id))["features"]
        
        # Check mode access
        if mode == ProcessingMode.DETAILED and "detailed_mode" not in features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your current subscription does not include access to {output_format.value} format. Please upgrade."
            )
        
        return True
    
    @staticmethod
    async def reset_monthly_quota(db: Session) -> int:
        """Reset monthly quota for subscriptions at period end. Return count of reset subscriptions."""
        current_time = datetime.now(timezone.utc)
        
        # Get subscriptions that need resetting
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.current_period_end <= current_time,
            Subscription.status == "active"
        ).all()
        
        count = 0
        for subscription in expired_subscriptions:
            # Reset quota
            subscription.used_quota = 0
            
            # Set new period
            subscription.current_period_start = current_time
            subscription.current_period_end = current_time + timedelta(days=30)
            
            logger.info(f"Reset quota for subscription {subscription.id} (user {subscription.user_id})")
            count += 1
            
        db.commit()
        return count
    
    @staticmethod
    async def handle_webhook_event(db: Session, event_data: Dict[str, Any]) -> bool:
        """Process a webhook event from Paddle."""
        try:
            event_type = event_data.get("event_type", "")
            logger.info(f"Processing Paddle webhook event: {event_type}")
            
            # Extract data
            data = event_data.get("data", {})
            
            # Handle different event types
            if "subscription.created" in event_type or "subscription.updated" in event_type:
                # Extract subscription data
                subscription_id = data.get("id")
                status = data.get("status", "").lower()
                custom_data = data.get("custom_data", {})
                
                # Extract user_id and plan_id from custom_data
                user_id = None
                plan_id = "free"
                
                if isinstance(custom_data, dict):
                    user_id = custom_data.get("user_id")
                    if user_id:
                        try:
                            user_id = int(user_id)
                        except (ValueError, TypeError):
                            user_id = None
                    plan_id = custom_data.get("plan_id", "free")
                elif isinstance(custom_data, str):
                    # Try to parse JSON string
                    try:
                        custom_data_dict = json.loads(custom_data)
                        user_id = custom_data_dict.get("user_id")
                        if user_id:
                            try:
                                user_id = int(user_id)
                            except (ValueError, TypeError):
                                user_id = None
                        plan_id = custom_data_dict.get("plan_id", "free")
                    except json.JSONDecodeError:
                        pass
                
                if not user_id or not subscription_id:
                    logger.error(f"Missing required data in webhook event: user_id={user_id}, subscription_id={subscription_id}")
                    return False
                
                # Get or create subscription
                subscription = SubscriptionService.get_subscription(db, user_id)
                if not subscription:
                    subscription = await SubscriptionService.create_subscription(
                        db, user_id, plan_id, subscription_id
                    )
                else:
                    # Update subscription
                    subscription.paddle_subscription_id = subscription_id
                    subscription.plan_id = plan_id
                    subscription.status = status
                    
                    # Update period
                    current_time = datetime.now(timezone.utc)
                    subscription.current_period_start = current_time
                    
                    # Default to 30 days
                    subscription.current_period_end = current_time + timedelta(days=30)
                    
                    # Try to extract billing period if available
                    billing_period = data.get("current_billing_period", {})
                    if billing_period:
                        ends_at = billing_period.get("ends_at")
                        if ends_at:
                            try:
                                ends_at_dt = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
                                subscription.current_period_end = ends_at_dt
                            except:
                                # Use default if parsing fails
                                pass
                    
                    # Update quota based on plan
                    plan_data = settings.SUBSCRIPTION_PLANS.get(plan_id)
                    if plan_data:
                        subscription.monthly_quota = plan_data.get("monthly_quota", 3)
                    
                    db.commit()
                
                logger.info(f"Processed subscription event for user {user_id} with plan {plan_id}")
                return True
                
            elif "subscription.cancelled" in event_type or "subscription.canceled" in event_type:
                # Extract subscription ID
                subscription_id = data.get("id")
                
                if not subscription_id:
                    logger.error("No subscription ID found in event data")
                    return False
                
                # Find subscription
                subscription = db.query(Subscription).filter(
                    Subscription.paddle_subscription_id == subscription_id
                ).first()
                
                if not subscription:
                    logger.warning(f"Subscription not found for cancellation: {subscription_id}")
                    return False
                    
                # Update status
                subscription.status = "cancelled"
                db.commit()
                
                logger.info(f"Marked subscription {subscription_id} as cancelled")
                
                # Create free tier subscription
                await SubscriptionService.create_subscription(
                    db,
                    subscription.user_id,
                    "free"
                )
                
                return True
                
            elif "transaction.completed" in event_type:
                # Handle transaction completed event
                subscription_id = data.get("subscription_id")
                
                if not subscription_id:
                    # Not subscription-related transaction
                    return True
                
                # Find subscription
                subscription = db.query(Subscription).filter(
                    Subscription.paddle_subscription_id == subscription_id
                ).first()
                
                if not subscription:
                    logger.warning(f"Subscription not found for transaction: {subscription_id}")
                    return False
                    
                # Reset usage quota for new billing period
                subscription.used_quota = 0
                db.commit()
                
                logger.info(f"Reset usage quota for subscription {subscription_id}")
                
                return True
                
            # For any other event, just return success
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            return False
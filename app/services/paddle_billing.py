# app/services/paddle_billing.py
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import Subscription, User
from paddle_billing import Client, Environment, Options

logger = logging.getLogger(__name__)

class PaddleBillingService:
    """Service for Paddle Billing API integration."""
    
    @staticmethod
    def get_client():
        """Get Paddle client instance."""
        try:
            # Initialize Paddle client with settings
            env = Environment.SANDBOX if settings.PADDLE_SANDBOX else Environment.PRODUCTION
            client = Client(settings.PADDLE_API_KEY, options=Options(env))
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Paddle client: {str(e)}")
            return None
    
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
        """
        Verify Paddle webhook signature using SDK.
        """
        if not settings.PADDLE_WEBHOOK_SECRET:
            logger.warning("No Paddle webhook secret configured for verification")
            return False
        
        try:
            client = PaddleBillingService.get_client()
            if not client:
                return False
                
            # Use Paddle SDK to verify webhook
            return client.webhooks.verify(
                raw_body.decode('utf-8'), 
                signature
            )
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    @staticmethod
    async def create_checkout(
        plan_id: str,
        user_id: int,
        user_email: str,
        is_yearly: bool = False,
        success_url: str = None,
        cancel_url: str = None
    ) -> Optional[str]:
        """
        Create a Paddle checkout session.
        """
        try:
            # Get the appropriate plan data
            plan_data = None
            for plan_key, plan_info in settings.SUBSCRIPTION_PLANS.items():
                if plan_id == plan_key:
                    plan_data = plan_info
                    break
                    
            if not plan_data:
                logger.error(f"Invalid plan ID: {plan_id}")
                return None
                
            # Get the Paddle price ID
            price_id = None
            if is_yearly and "paddle_yearly_plan_id" in plan_data:
                price_id = plan_data["paddle_yearly_plan_id"]
            elif "paddle_plan_id" in plan_data:
                price_id = plan_data["paddle_plan_id"]
            
            if not price_id:
                logger.error(f"No Paddle price ID configured for {plan_id}")
                # In development mode, use mock checkout
                if settings.APP_ENV == "development":
                    return f"https://checkout.paddle.com/checkout/custom/dev-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
                return None
            
            # If in development mode with no API key, return mock URL
            if settings.APP_ENV == "development" and not settings.PADDLE_API_KEY:
                return f"https://checkout.paddle.com/checkout/custom/dev-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
            
            # Create checkout with Paddle SDK
            client = PaddleBillingService.get_client()
            if not client:
                logger.error("Failed to initialize Paddle client")
                return None
                
            logger.info(f"Creating checkout for price_id: {price_id}, email: {user_email}")
            
            # Build checkout data
            checkout_data = {
                "items": [
                    {
                        "price_id": price_id,
                        "quantity": 1
                    }
                ],
                "customer_email": user_email,
                "custom_data": {
                    "user_id": str(user_id),
                    "plan_id": plan_id
                }
            }
            
            # Add success and cancel URLs if provided
            if success_url:
                checkout_data["success_url"] = success_url
            
            if cancel_url:
                checkout_data["cancel_url"] = cancel_url
                
            # Create checkout
            checkout = client.checkout.create(**checkout_data)
            
            logger.info(f"Created checkout: {checkout.url}")
            return checkout.url
            
        except Exception as e:
            logger.error(f"Error creating Paddle checkout: {str(e)}")
            # Fallback for development
            if settings.APP_ENV == "development":
                return f"https://checkout.paddle.com/checkout/custom/dev-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
            return None
    
    @staticmethod
    async def handle_subscription_created(
        db: Session, 
        event_data: Dict[str, Any]
    ) -> Subscription:
        """
        Handle subscription created event.
        """
        try:
            # Extract data from event
            subscription_data = event_data.get("data", {})
            subscription_id = subscription_data.get("id")
            custom_data = subscription_data.get("custom_data", {})
            
            # Parse user_id and plan_id from custom_data
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
                    data = json.loads(custom_data)
                    user_id = data.get("user_id")
                    if user_id:
                        try:
                            user_id = int(user_id)
                        except (ValueError, TypeError):
                            user_id = None
                    plan_id = data.get("plan_id", "free")
                except json.JSONDecodeError:
                    pass
            
            status = subscription_data.get("status", "").lower()
            
            if not user_id or not subscription_id:
                logger.error(f"Missing required data in subscription event: user_id={user_id}, subscription_id={subscription_id}")
                return None
            
            # Get existing subscription or create new one
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if not subscription:
                subscription = Subscription(user_id=user_id)
                
            # Update subscription details
            subscription.paddle_subscription_id = subscription_id
            subscription.plan_id = plan_id
            subscription.status = status
            
            # Update period
            current_time = datetime.utcnow()
            subscription.current_period_start = current_time
            
            # Set end date to 30 days from now (default)
            subscription.current_period_end = current_time + timedelta(days=30)
            
            # Try to extract billing period if available
            billing_period = subscription_data.get("current_billing_period", {})
            if billing_period:
                ends_at = billing_period.get("ends_at")
                if ends_at:
                    try:
                        ends_at_dt = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
                        subscription.current_period_end = ends_at_dt
                    except:
                        # Use default 30 days if parsing fails
                        pass
                
            # Set monthly quota based on plan
            plan_data = settings.SUBSCRIPTION_PLANS.get(plan_id)
            if plan_data:
                subscription.monthly_quota = plan_data.get("monthly_quota", 3)
                subscription.used_quota = 0
                
            # Save to database
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error handling subscription created: {str(e)}")
            return None
            
    @staticmethod
    async def get_subscription(subscription_id: str):
        """
        Get subscription details from Paddle.
        """
        try:
            client = PaddleBillingService.get_client()
            if not client:
                return None
                
            return client.subscriptions.get(subscription_id)
        except Exception as e:
            logger.error(f"Error getting subscription {subscription_id}: {str(e)}")
            return None
    
    @staticmethod
    async def cancel_subscription(subscription_id: str, effective: str = "next_billing_period"):
        """
        Cancel a subscription in Paddle.
        """
        try:
            client = PaddleBillingService.get_client()
            if not client:
                return None
                
            return client.subscriptions.cancel(
                subscription_id,
                effective_from=effective
            )
        except Exception as e:
            logger.error(f"Error canceling subscription {subscription_id}: {str(e)}")
            return None
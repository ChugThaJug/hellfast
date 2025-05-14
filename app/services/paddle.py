# app/services/paddle.py
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import Subscription, User

logger = logging.getLogger(__name__)

class PaddleService:
    """Service for Paddle payment processing and subscription management."""
    
    @staticmethod
    def get_client():
        """Get Paddle client instance."""
        try:
            # Try to import paddle_billing with correct imports
            from paddle_billing import Client, Environment, Options
            
            env = Environment.SANDBOX if settings.PADDLE_SANDBOX else Environment.PRODUCTION
            return Client(settings.PADDLE_API_KEY, options=Options(env))
        except (ImportError, ModuleNotFoundError) as e:
            logger.error(f"Failed to import Paddle SDK: {str(e)}")
            return None
    
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
        """
        Verify Paddle webhook signature using the raw request body.
        
        Args:
            raw_body: The raw body bytes from the request
            signature: The Paddle-Signature header value
            secret: The webhook secret key
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No Paddle webhook secret configured for verification")
            return False
        
        try:
            # Try to import the Paddle verifier
            from paddle_billing.Notifications import Secret, Verifier
            
            # Create a request-like object that matches the Paddle verifier expectations
            class PaddleRequest:
                def __init__(self, body_bytes, sig):
                    self.headers = {"Paddle-Signature": sig}
                    self.body = body_bytes  # Use raw bytes, don't transform
            
            request = PaddleRequest(raw_body, signature)
            return Verifier().verify(request, Secret(secret))
        except ImportError:
            logger.error("Paddle SDK not properly installed")
            # In development mode, return True to allow testing
            return settings.APP_ENV == "development"
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
        if not settings.PADDLE_API_KEY:
            logger.error("Paddle API key not configured")
            return None
            
        # In development mode without real API key, return a mock URL
        if settings.APP_ENV == "development":
            # For development mode, just return a mock checkout URL
            mock_url = f"https://checkout.paddle.com/checkout/custom/dev-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
            logger.info(f"Development mode - using mock checkout URL: {mock_url}")
            return mock_url
            
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
                
            # Get the Paddle plan ID (price ID in Paddle Billing)
            paddle_price_id = plan_data["paddle_yearly_plan_id"] if is_yearly else plan_data["paddle_plan_id"]
            
            if not paddle_price_id:
                logger.error(f"No Paddle price ID configured for {plan_id}")
                return None
            
            # For now, just return a mock URL in development mode
            if settings.APP_ENV == "development":
                return f"https://checkout.paddle.com/checkout/custom/dev-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
            
            logger.error("Paddle SDK not fully implemented. Using mock checkout URL for testing.")
            return f"https://checkout.paddle.com/checkout/custom/mock-checkout?user={user_id}&plan={plan_id}&yearly={is_yearly}"
            
        except Exception as e:
            logger.error(f"Error creating Paddle checkout: {str(e)}")
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
    async def handle_subscription_cancelled(db: Session, event_data: Dict[str, Any]) -> None:
        """
        Handle subscription cancelled event.
        """
        try:
            # Extract subscription ID
            subscription_data = event_data.get("data", {})
            subscription_id = subscription_data.get("id")
            
            if not subscription_id:
                logger.error("No subscription ID found in event data")
                return
            
            # Find subscription
            subscription = db.query(Subscription).filter(
                Subscription.paddle_subscription_id == subscription_id
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found for cancellation: {subscription_id}")
                return
                
            # Update status
            subscription.status = "cancelled"
            db.commit()
            
            # Create free tier subscription
            from app.services.subscription import SubscriptionService
            await SubscriptionService.create_subscription(
                db,
                subscription.user_id,
                "free"
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription cancelled: {str(e)}")
    
    @staticmethod
    async def handle_subscription_updated(db: Session, event_data: Dict[str, Any]) -> None:
        """
        Handle subscription updated event.
        """
        try:
            # Extract subscription data
            subscription_data = event_data.get("data", {})
            subscription_id = subscription_data.get("id")
            status = subscription_data.get("status", "").lower()
            
            if not subscription_id:
                logger.error("No subscription ID found in event data")
                return
            
            # Find subscription
            subscription = db.query(Subscription).filter(
                Subscription.paddle_subscription_id == subscription_id
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found for update: {subscription_id}")
                return
                
            # Update status
            if status:
                subscription.status = status
            
            # Try to extract billing period
            billing_period = subscription_data.get("current_billing_period", {})
            if billing_period:
                ends_at = billing_period.get("ends_at")
                if ends_at:
                    try:
                        ends_at_dt = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
                        subscription.current_period_end = ends_at_dt
                    except:
                        # Ignore parse errors
                        pass
                    
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")
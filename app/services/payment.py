# app/services/payment.py
import hmac
import hashlib
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import Subscription

# Import the subscription service normally here - this is OK since we're not creating a circular import
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for payment processing and subscription management."""
    
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
        """Verify Paddle webhook signature."""
        if not secret and settings.PADDLE_WEBHOOK_SECRET:
            secret = settings.PADDLE_WEBHOOK_SECRET
            
        if not secret:
            logger.warning("No Paddle webhook secret configured for verification")
            return False
        
        try:
            # Parse the signature header
            ts_part, h1_part = signature.split(";")
            var, timestamp = ts_part.split("=")
            var, signature = h1_part.split("=")
            
            signed_payload = ":".join([timestamp, raw_body.decode("utf-8")])
            
            # Paddle generates signatures using HMAC-SHA256
            computed_signature = hmac.new(
                key=secret.encode("utf-8"),
                msg=signed_payload.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)
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
        """Create a Paddle checkout session."""
        if not settings.PADDLE_API_KEY:
            raise ValueError("Paddle API key must be configured")
            
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
            paddle_plan_id = None
            if is_yearly and "paddle_yearly_plan_id" in plan_data:
                paddle_plan_id = plan_data["paddle_yearly_plan_id"]
            elif "paddle_plan_id" in plan_data:
                paddle_plan_id = plan_data["paddle_plan_id"]
            
            if not paddle_plan_id:
                logger.error(f"No Paddle plan ID configured for {plan_id}")
                return None
            
            # Prepare checkout data for Paddle API
            checkout_url = f"https://checkout.paddle.com/checkout/custom/{paddle_plan_id}"
            checkout_params = {
                "email": user_email,
                "custom_data": json.dumps({
                    "user_id": str(user_id),
                    "plan_id": plan_id
                })
            }
            
            # Add success and cancel URLs if provided
            if success_url:
                checkout_params["successCallback"] = success_url
                
            if cancel_url:
                checkout_params["cancelCallback"] = cancel_url
            
            # Construct the checkout URL with parameters
            param_strings = []
            for key, value in checkout_params.items():
                param_strings.append(f"{key}={value}")
                
            final_url = f"{checkout_url}?{'&'.join(param_strings)}"
            
            return final_url
            
        except Exception as e:
            logger.error(f"Error creating Paddle checkout: {str(e)}")
            return None
    
    @staticmethod
    async def handle_subscription_event(
        db: Session, 
        event_data: Dict[str, Any]
    ) -> Optional[Subscription]:
        """Handle subscription created/updated event."""
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
            
            # Create or update subscription via the SubscriptionService
            subscription = await SubscriptionService.create_subscription(db, user_id, plan_id)
            
            # Update paddle-specific details
            subscription.paddle_subscription_id = subscription_id
            subscription.status = status
            
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
            
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Processed subscription event for user {user_id} with plan {plan_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error handling subscription event: {str(e)}")
            return None
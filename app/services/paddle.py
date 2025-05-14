# app/services/paddle.py
import hmac
import hashlib
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import Subscription, User

logger = logging.getLogger(__name__)

# Import the paddle_billing_client if available
try:
    from paddle_billing_client.client import PaddleApiClient
    from paddle_billing_client.errors import VerboseErrorHandler
    from apiclient.authentication_methods import HeaderAuthentication
    from paddle_billing_client.models.transaction import TransactionRequest
    from paddle_billing_client.models.subscription import SubscriptionRequest
    from paddle_billing_client.helpers import validate_webhook_signature
    HAS_PADDLE_CLIENT = True
except ImportError:
    logger.warning("paddle_billing_client not installed. Some features will be limited.")
    HAS_PADDLE_CLIENT = False

class PaddleService:
    """Service for Paddle payment processing and subscription management."""
    
    @classmethod
    def get_client(cls):
        """Get Paddle API client instance."""
        if not HAS_PADDLE_CLIENT:
            logger.error("Paddle client not available")
            return None
            
        if not settings.PADDLE_API_KEY:
            logger.error("Paddle API key not configured")
            return None
            
        try:
            # Initialize client with proper authentication
            base_url = "https://sandbox-api.paddle.com" if settings.PADDLE_SANDBOX else "https://api.paddle.com"
            client = PaddleApiClient(
                base_url=base_url,
                authentication_method=HeaderAuthentication(token=settings.PADDLE_API_KEY),
                error_handler=VerboseErrorHandler
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing Paddle client: {str(e)}")
            return None
    
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
        """
        Verify Paddle webhook signature using the raw request body and HMAC.
        """
        if not secret and settings.PADDLE_WEBHOOK_SECRET:
            secret = settings.PADDLE_WEBHOOK_SECRET
            
        if not secret:
            logger.warning("No Paddle webhook secret configured for verification")
            return False
        
        try:
            # Use helper from paddle_billing_client if available
            if HAS_PADDLE_CLIENT:
                return validate_webhook_signature(
                    signature_header=signature,
                    raw_body=raw_body,
                    secret_key=secret
                )
            
            # Fallback to manual verification
            ts_part, h1_part = signature.split(";")
            var, timestamp = ts_part.split("=")
            var, signature = h1_part.split("=")
            
            signed_payload = ":".join([timestamp, raw_body.decode("utf-8")])
            
            # Paddle generates signatures using a keyed-hash message authentication code (HMAC) with SHA256 and a secret key.
            computed_signature = hmac.new(
                key=secret.encode("utf-8"),
                msg=signed_payload.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Compare the computed signature with the signature extracted from the Paddle-Signature header.
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
        """
        Create a Paddle checkout session.
        """
        if not settings.PADDLE_API_KEY:
            logger.error("Paddle API key not configured")
            return None
            
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
            
            client = PaddleService.get_client()
            if not client:
                logger.error("Failed to initialize Paddle client")
                return None
                
            logger.info(f"Creating checkout for price_id: {paddle_plan_id}, email: {user_email}")
            
            # Create checkout with Paddle API
            checkout_data = {
                "items": [
                    {
                        "price_id": paddle_plan_id,
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
            
            # Create transaction request
            transaction_request = TransactionRequest(**checkout_data)
            
            # Create checkout
            response = client.create_transaction(transaction_request)
            
            # Get checkout URL
            checkout_url = response.data.checkout.url if hasattr(response.data, 'checkout') else None
            
            if checkout_url:
                logger.info(f"Created checkout: {checkout_url}")
                return checkout_url
            else:
                logger.error("No checkout URL returned from Paddle API")
                return None
            
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
            
            logger.info(f"Created/updated subscription for user {user_id} with plan {plan_id}")
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
            
            logger.info(f"Subscription {subscription_id} marked as cancelled")
            
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
            
            # Handle transaction.completed to reset quota
            if event_data.get("event_type") == "transaction.completed":
                # Reset quota for new billing period
                subscription.used_quota = 0
                
            db.commit()
            logger.info(f"Updated subscription {subscription_id} with status {status}")
            
        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")
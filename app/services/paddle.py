# app/services/paddle.py
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.database import Subscription, User

logger = logging.getLogger(__name__)

class PaddleService:
    """Service for Paddle payment processing and subscription management."""
    
    @staticmethod
    def verify_webhook_signature(data: Dict[str, Any], signature: str) -> bool:
        """Verify Paddle webhook signature."""
        if not settings.PADDLE_PUBLIC_KEY:
            logger.warning("No Paddle public key configured for webhook verification")
            return False
            
        # Convert data to JSON string
        data_json = json.dumps(data, separators=(',', ':'))
        
        # Create signature
        h = hmac.new(
            settings.PADDLE_PUBLIC_KEY.encode('utf-8'),
            data_json.encode('utf-8'),
            hashlib.sha256
        )
        digest = h.hexdigest()
        
        # Compare with received signature
        return hmac.compare_digest(digest, signature)
    
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
        
        Args:
            plan_id: The Paddle plan ID
            user_id: User ID for passthrough
            user_email: User email for pre-filling checkout
            is_yearly: Whether to use yearly plan
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancellation
            
        Returns:
            Checkout ID or None if failed
        """
        if not settings.PADDLE_API_KEY:
            logger.error("Paddle API key not configured")
            return None
            
        # Use development mode checkout without API if no real credentials
        if settings.APP_ENV == "development" and not settings.PADDLE_API_KEY:
            return f"dev-checkout-{user_id}-{plan_id}"
        
        # In development, we can create a checkout URL without calling Paddle
        if settings.APP_ENV == "development":
            return f"dev-checkout-{user_id}-{plan_id}"
            
        # In production with Paddle API
        try:
            # Get the appropriate plan ID
            plan_data = None
            for plan_key, plan_info in settings.SUBSCRIPTION_PLANS.items():
                if plan_id == plan_key:
                    plan_data = plan_info
                    break
                    
            if not plan_data:
                logger.error(f"Invalid plan ID: {plan_id}")
                return None
                
            # Get the Paddle plan ID
            paddle_plan_id = plan_data["paddle_yearly_plan_id"] if is_yearly else plan_data["paddle_plan_id"]
            
            if not paddle_plan_id:
                logger.error(f"No Paddle plan ID configured for {plan_id}")
                return None
                
            # Create checkout
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://vendors.paddle.com/api/2.0/product/generate_pay_link",
                    data={
                        "vendor_id": settings.PADDLE_VENDOR_ID,
                        "vendor_auth_code": settings.PADDLE_API_KEY,
                        "product_id": paddle_plan_id,
                        "customer_email": user_email,
                        "passthrough": json.dumps({"user_id": user_id, "plan_id": plan_id}),
                        "return_url": success_url,
                        "cancel_url": cancel_url
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error creating Paddle checkout: {response.text}")
                    return None
                    
                data = response.json()
                if not data.get("success"):
                    logger.error(f"Paddle error: {data.get('error', {}).get('message')}")
                    return None
                    
                return data["response"]["url"]
                
        except Exception as e:
            logger.error(f"Error creating Paddle checkout: {str(e)}")
            return None
    
    @staticmethod
    async def handle_subscription_created(
        db: Session, 
        user_id: int,
        subscription_id: str,
        plan_id: str,
        status: str,
        next_bill_date: str
    ) -> Subscription:
        """
        Handle subscription created event.
        
        Args:
            db: Database session
            user_id: User ID
            subscription_id: Paddle subscription ID
            plan_id: Plan ID (our internal plan ID)
            status: Subscription status
            next_bill_date: Next billing date
            
        Returns:
            Updated subscription
        """
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
        
        # Parse next_bill_date
        try:
            next_bill_date_obj = datetime.strptime(next_bill_date, "%Y-%m-%d")
            subscription.current_period_end = next_bill_date_obj
        except:
            # Fallback to 30 days if date parsing fails
            subscription.current_period_end = current_time + timedelta(days=30)
            
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
    
    @staticmethod
    async def handle_subscription_cancelled(db: Session, subscription_id: str) -> None:
        """
        Handle subscription cancelled event.
        
        Args:
            db: Database session
            subscription_id: Paddle subscription ID
        """
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
        
    @staticmethod
    async def handle_subscription_updated(
        db: Session,
        subscription_id: str,
        status: str,
        plan_id: Optional[str] = None,
        next_bill_date: Optional[str] = None
    ) -> None:
        """
        Handle subscription updated event.
        
        Args:
            db: Database session
            subscription_id: Paddle subscription ID
            status: New status
            plan_id: New plan ID (optional)
            next_bill_date: New billing date (optional)
        """
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.paddle_subscription_id == subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription not found for update: {subscription_id}")
            return
            
        # Update status
        subscription.status = status
        
        # Update plan if provided
        if plan_id:
            subscription.plan_id = plan_id
            
            # Update quota based on new plan
            plan_data = settings.SUBSCRIPTION_PLANS.get(plan_id)
            if plan_data:
                subscription.monthly_quota = plan_data.get("monthly_quota", 3)
                
        # Update next bill date if provided
        if next_bill_date:
            try:
                next_bill_date_obj = datetime.strptime(next_bill_date, "%Y-%m-%d")
                subscription.current_period_end = next_bill_date_obj
            except:
                # Ignore parse errors
                pass
                
        db.commit()
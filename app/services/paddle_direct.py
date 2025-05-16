# app/services/paddle_direct.py
"""
Direct Paddle API integration without using the paddle_billing_client library
"""
import requests
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.settings import settings

logger = logging.getLogger(__name__)

class PaddleDirectService:
    """
    Service for direct Paddle API interaction without using the paddle_billing_client library
    """
    
    @staticmethod
    def get_base_url() -> str:
        """Get the appropriate base URL depending on sandbox setting"""
        return "https://sandbox-api.paddle.com" if settings.PADDLE_SANDBOX else "https://api.paddle.com"
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get the headers required for Paddle API calls"""
        if not settings.PADDLE_API_KEY:
            raise ValueError("PADDLE_API_KEY is not configured")
            
        # Ensure the API key has the correct format (starting with pdl_)
        api_key = settings.PADDLE_API_KEY
        if not api_key.startswith("pdl_"):
            logger.warning("API key doesn't start with 'pdl_'. Paddle API keys should match the format: pdl_sdbx_apikey_XXXX or pdl_live_apikey_XXXX")
            
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    async def list_prices(cls) -> Dict[str, Any]:
        """List all prices from Paddle"""
        try:
            url = f"{cls.get_base_url()}/prices"
            headers = cls.get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error listing prices: {str(e)}")
            raise
    
    @classmethod
    async def create_checkout(
        cls,
        plan_id: str,
        user_id: int,
        user_email: str,
        is_yearly: bool = False,
        success_url: str = None,
        cancel_url: str = None
    ) -> Optional[str]:
        """
        Create a Paddle checkout session directly using the API
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
                raise ValueError(f"Invalid plan ID: {plan_id}")
                
            # Get the Paddle plan ID (price ID in Paddle Billing)
            paddle_plan_id = None
            if is_yearly and "paddle_yearly_plan_id" in plan_data:
                paddle_plan_id = plan_data["paddle_yearly_plan_id"]
            elif "paddle_plan_id" in plan_data:
                paddle_plan_id = plan_data["paddle_plan_id"]
            
            if not paddle_plan_id:
                logger.error(f"No Paddle plan ID configured for {plan_id}")
                raise ValueError(f"No Paddle plan ID configured for {plan_id}")
                
            logger.info(f"Creating checkout for price_id: {paddle_plan_id}, email: {user_email}")
            
            # Create checkout with Paddle API
            url = f"{cls.get_base_url()}/transactions"
            headers = cls.get_headers()
            
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
            
            # Make the request
            response = requests.post(url, headers=headers, json=checkout_data)
            response.raise_for_status()
            
            # Get data from response
            data = response.json()
            
            # Extract checkout URL
            checkout_url = None
            if data.get("data") and data["data"].get("checkout") and data["data"]["checkout"].get("url"):
                checkout_url = data["data"]["checkout"]["url"]
                
            if checkout_url:
                logger.info(f"Created checkout: {checkout_url}")
                return checkout_url
            else:
                logger.error("No checkout URL returned from Paddle API")
                logger.error(f"Response: {json.dumps(data)}")
                raise ValueError("No checkout URL returned from Paddle API")
            
        except Exception as e:
            logger.error(f"Error creating Paddle checkout: {str(e)}")
            raise
    
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
        """
        Verify Paddle webhook signature directly without using helpers
        """
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
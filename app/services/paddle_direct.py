# app/services/paddle_direct.py
"""
Direct Paddle API integration without using the paddle_billing_client library
"""
import requests
import json
import logging
import hmac
import hashlib
import httpx
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
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate Paddle API key format according to documentation."""
        if not api_key:
            return False
        
        # API key should be 69 characters long
        if len(api_key) != 69:
            logger.warning(f"API key length incorrect: got {len(api_key)}, expected 69 characters")
            return False
        
        # Should be prefixed with pdl_
        if not api_key.startswith("pdl_"):
            logger.warning("API key doesn't start with 'pdl_'")
            return False
        
        # Should contain apikey_
        if "apikey_" not in api_key:
            logger.warning("API key doesn't contain 'apikey_'")
            return False
        
        # Should contain sdbx_ or live_ depending on environment
        if "sdbx_" not in api_key and "live_" not in api_key:
            logger.warning("API key doesn't contain environment identifier (sdbx_ or live_)")
            return False
        
        # If sandbox flag is set, should contain sdbx_, otherwise live_
        expected_env = "sdbx_" if settings.PADDLE_SANDBOX else "live_"
        if expected_env not in api_key:
            logger.warning(f"API key environment mismatch: expected {expected_env} for current environment")
            return False
            
        return True
    
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
    async def list_available_prices(cls) -> Dict[str, Any]:
        """List all available prices in the Paddle account."""
        try:
            response = await cls._make_paddle_api_request("GET", "prices?per_page=100")
            logger.info(f"Found {len(response.get('data', []))} prices in Paddle account")
            return response
        except Exception as e:
            logger.error(f"Error listing prices: {str(e)}")
            raise

    @staticmethod
    async def check_price_exists(price_id: str) -> bool:
        """Verify if a price ID exists in the Paddle system."""
        try:
            response = await PaddleDirectService._make_paddle_api_request(
                "GET", 
                f"prices/{price_id}"
            )
            # If we get a response, the price exists
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Price ID {price_id} not found in Paddle system")
                return False
            # For other errors, log but don't fail silently
            logger.error(f"Error checking price: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking price: {str(e)}")
            raise

    @staticmethod
    async def create_checkout(price_id, email, customer_id=None):
        """Create a checkout session with Paddle."""
        logger.info(f"Creating checkout for price_id: {price_id}, email: {email}")
        
        try:
            # First verify that the price ID exists
            price_exists = await PaddleDirectService.check_price_exists(price_id)
            if not price_exists:
                error_msg = f"Price ID {price_id} does not exist in Paddle account"
                logger.error(error_msg)
                return {
                    "error": True, 
                    "message": error_msg,
                    "suggestion": "Please check your PADDLE_PRO_PLAN_ID and PADDLE_MAX_PLAN_ID settings"
                }
            
            # Get frontend URL for success/cancel redirects
            frontend_url = settings.FRONTEND_URL
            success_url = getattr(settings, "PADDLE_CHECKOUT_SUCCESS_URL", f"{frontend_url}/subscription/success")
            cancel_url = getattr(settings, "PADDLE_CHECKOUT_CANCEL_URL", f"{frontend_url}/subscription/cancel")
            
            # Prepare checkout data - using correct field names per Paddle API docs
            checkout_data = {
                "items": [{"price_id": price_id, "quantity": 1}],
                "customer_email": email,
                "success_url": success_url,  # Changed from return_url to success_url
                "cancel_url": cancel_url
            }
            
            # Add customer_id as custom_data as per Paddle API format
            if customer_id:
                checkout_data["custom_data"] = {"customer_id": str(customer_id)}
            
            # Log the payload for debugging
            logger.debug(f"Paddle checkout payload: {checkout_data}")
            
            # Make the API request
            response = await PaddleDirectService._make_paddle_api_request(
                "POST", 
                "transactions", 
                json=checkout_data
            )
            
            # Log full response for debugging
            logger.debug(f"Paddle API response: {response}")
            
            # Extract checkout URL from response
            checkout_url = None
            if response.get("data") and response["data"].get("checkout") and response["data"]["checkout"].get("url"):
                checkout_url = response["data"]["checkout"]["url"]
                logger.info(f"Checkout URL created: {checkout_url}")
                return {"checkout_url": checkout_url}
            else:
                logger.error(f"Unexpected response format from Paddle: {response}")
                return {"error": True, "message": "Unexpected response format from Paddle API"}
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error creating Paddle checkout: {error_message}")
            
            # Extract more detailed error info if available
            if hasattr(e, 'response') and e.response:
                try:
                    error_details = e.response.json()
                    logger.error(f"Paddle API error details: {error_details}")
                    return {"error": True, "message": error_message, "details": error_details}
                except:
                    pass
                    
            raise ValueError(f"Failed to create checkout session: {error_message}")

    @staticmethod
    async def _make_paddle_api_request(method, endpoint, **kwargs):
        """Make a request to the Paddle API with proper authentication."""
        base_url = "https://sandbox-api.paddle.com" if settings.PADDLE_SANDBOX else "https://api.paddle.com"
        url = f"{base_url}/{endpoint}"
        
        # Validate API key
        api_key = settings.PADDLE_API_KEY
        if not api_key:
            raise ValueError("PADDLE_API_KEY not configured")
            
        # Perform detailed validation but continue if fails (with warning)
        PaddleDirectService.validate_api_key(api_key)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Paddle-Version": "1"  # Updated to version 1 as per Paddle docs
        }
        
        try:
            # Log request details at debug level
            logger.debug(f"Paddle API request: {method} {url}")
            logger.debug(f"Headers: {headers}")
            if 'json' in kwargs:
                logger.debug(f"Request body: {kwargs['json']}")
                
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, 
                    url, 
                    headers=headers, 
                    timeout=30,
                    **kwargs
                )
                
                # Log response details
                logger.debug(f"Response status: {response.status_code}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            # Handle common authentication errors with more helpful messages
            if status_code == 401:
                try:
                    error_body = e.response.json()
                    error_type = error_body.get("error", {}).get("type", "")
                    
                    if error_type == "authentication_missing":
                        logger.error("Paddle API Error: Authentication header is missing")
                    elif error_type == "authentication_malformed":
                        logger.error("Paddle API Error: Authentication header is malformed")
                    elif error_type == "invalid_token":
                        logger.error("Paddle API Error: Invalid API key. Check that key is correct and not revoked")
                    else:
                        logger.error(f"Paddle API authentication error: {error_body}")
                except:
                    logger.error("Paddle API authentication error (could not parse response)")
            elif status_code == 403:
                logger.error("Paddle API Error: Forbidden - The API key doesn't have the required permissions")
                
            # Log detailed error info
            try:
                error_body = e.response.json()
                logger.error(f"Paddle API error response: {error_body}")
            except:
                logger.error(f"Paddle API error raw response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Paddle API request error: {str(e)}")
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

    @staticmethod
    async def get_checkout_data_for_frontend(plan_id: str, is_yearly: bool = False, user_id: Optional[int] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate checkout data for frontend Paddle.js integration.
        
        Returns a dictionary with all the necessary information for the frontend
        to initialize a Paddle.js overlay checkout.
        """
        try:
            # Get the Paddle price ID from settings
            price_id = None
            
            if plan_id == "pro":
                price_id = settings.PADDLE_PRO_YEARLY_PLAN_ID if is_yearly else settings.PADDLE_PRO_PLAN_ID
            elif plan_id == "max":
                price_id = settings.PADDLE_MAX_YEARLY_PLAN_ID if is_yearly else settings.PADDLE_MAX_PLAN_ID
            else:
                raise ValueError(f"Invalid plan ID: {plan_id}")
                
            if not price_id:
                raise ValueError(f"No Paddle price ID configured for {plan_id} with yearly={is_yearly}")
            
            # Create the checkout data format needed for Paddle.js
            checkout_data = {
                "items": [
                    {
                        "priceId": price_id,
                        "quantity": 1
                    }
                ],
                "settings": {
                    "displayMode": "overlay",
                    "theme": "light",
                    "locale": "en",
                    "successUrl": f"{settings.FRONTEND_URL}/subscription/success",
                    "cancelUrl": f"{settings.FRONTEND_URL}/subscription/cancel"
                }
            }
            
            # Add customer information if provided
            if email:
                customer_data = {"email": email}
                
                if user_id:
                    customer_data["customData"] = {"customer_id": str(user_id)}
                    
                checkout_data["customer"] = customer_data
                
            # Add sandbox flag if in sandbox mode
            if settings.PADDLE_SANDBOX:
                checkout_data["sandbox"] = True
                
            return checkout_data
            
        except Exception as e:
            logger.error(f"Error generating frontend checkout data: {str(e)}")
            raise ValueError(f"Failed to generate checkout data: {str(e)}")
                
    @staticmethod
    def is_api_key_configured() -> bool:
        """Check if Paddle API key is properly configured."""
        api_key = settings.PADDLE_API_KEY
        if not api_key:
            return False
        return PaddleDirectService.validate_api_key(api_key)
    
    @staticmethod
    def get_environment_status() -> Dict[str, Any]:
        """Get the status of the Paddle integration environment."""
        return {
            "sandbox_mode": settings.PADDLE_SANDBOX,
            "api_key_configured": PaddleDirectService.is_api_key_configured(),
            "webhook_secret_configured": bool(settings.PADDLE_WEBHOOK_SECRET),
            "frontend_url": settings.FRONTEND_URL,
            "client_side_integration": "Paddle.js overlay checkout"
        }
#!/usr/bin/env python
"""
Script to test Paddle integration
"""
import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.core.settings import settings
from app.services.paddle import PaddleService
from app.models.database import Base

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_paddle_client():
    """Test Paddle client initialization and basic API calls"""
    try:
        logger.info("Testing Paddle client initialization...")
        client = PaddleService.get_client()
        
        if not client:
            logger.error("Failed to initialize Paddle client. Check API key and settings.")
            return False
            
        logger.info("Paddle client initialized successfully.")
        
        # Test listing prices
        logger.info("Testing Paddle API by listing prices...")
        response = client.list_prices()
        
        if response and hasattr(response, 'data') and response.data:
            logger.info(f"Successfully fetched prices. Found {len(response.data)} price(s).")
            
            # Print the first price
            if response.data:
                price = response.data[0]
                logger.info(f"Sample price: ID={price.id}, Name={price.name}")
        else:
            logger.warning("No prices found. This might be normal for a new account.")
        
        logger.info("Paddle API connection test completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error testing Paddle client: {str(e)}")
        return False

async def test_create_checkout():
    """Test creating a Paddle checkout"""
    try:
        logger.info("Testing checkout creation...")
        
        # Use test values
        test_user_id = 1
        test_email = "test@example.com"
        test_plan = "pro"
        is_yearly = False
        
        checkout_url = await PaddleService.create_checkout(
            plan_id=test_plan,
            user_id=test_user_id,
            user_email=test_email,
            is_yearly=is_yearly
        )
        
        if checkout_url:
            logger.info(f"Successfully created checkout URL: {checkout_url}")
            return True
        else:
            logger.error("Failed to create checkout URL.")
            return False
    except Exception as e:
        logger.error(f"Error creating checkout: {str(e)}")
        return False

async def test_webhook_verification():
    """Test webhook signature verification"""
    try:
        logger.info("Testing webhook signature verification...")
        
        # Create a sample payload
        sample_payload = {
            "event_type": "subscription.created",
            "data": {
                "id": "sub_01h9wy6c8xxf2z5tejfam6pcz6",
                "status": "active",
                "custom_data": {
                    "user_id": "1",
                    "plan_id": "pro"
                }
            }
        }
        
        # Convert to bytes
        raw_body = json.dumps(sample_payload).encode('utf-8')
        
        # We can't generate a valid signature here, but we can test the function 
        # with a mock signature
        mock_signature = "ts=123456789;h1=invalid_hash"
        
        if not settings.PADDLE_WEBHOOK_SECRET:
            logger.warning("PADDLE_WEBHOOK_SECRET not set. Skipping verification test.")
            return True
            
        result = PaddleService.verify_webhook_signature(
            raw_body=raw_body,
            signature=mock_signature,
            secret=settings.PADDLE_WEBHOOK_SECRET
        )
        
        # This should fail as we used an invalid signature
        if not result:
            logger.info("Webhook signature verification correctly rejected invalid signature.")
            return True
        else:
            logger.error("Webhook signature verification incorrectly accepted invalid signature.")
            return False
    except Exception as e:
        logger.error(f"Error testing webhook verification: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Paddle integration test...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Sandbox mode: {settings.PADDLE_SANDBOX}")
    
    # Check if Paddle API key is set
    if not settings.PADDLE_API_KEY:
        logger.error("PADDLE_API_KEY is not configured. Set it in your .env file.")
        return
        
    # Test client
    client_result = await test_paddle_client()
    
    # If client test passed, test checkout
    if client_result:
        checkout_result = await test_create_checkout()
    else:
        logger.error("Skipping checkout test due to client initialization failure.")
        checkout_result = False
        
    # Always test webhook verification
    webhook_result = await test_webhook_verification()
    
    # Report results
    logger.info("\n========== TEST RESULTS ==========")
    logger.info(f"Paddle client test: {'PASSED' if client_result else 'FAILED'}")
    logger.info(f"Checkout creation test: {'PASSED' if checkout_result else 'FAILED'}")
    logger.info(f"Webhook verification test: {'PASSED' if webhook_result else 'FAILED'}")
    
    # Check subscription plans configuration
    logger.info("\n========== SUBSCRIPTION PLANS ==========")
    for plan_id, plan_data in settings.SUBSCRIPTION_PLANS.items():
        if plan_id != "free":
            paddle_plan_id = plan_data.get("paddle_plan_id", "NOT CONFIGURED")
            paddle_yearly_plan_id = plan_data.get("paddle_yearly_plan_id", "NOT CONFIGURED")
            logger.info(f"Plan: {plan_id}")
            logger.info(f"  Monthly ID: {paddle_plan_id}")
            logger.info(f"  Yearly ID: {paddle_yearly_plan_id}")
    
    logger.info("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(main())
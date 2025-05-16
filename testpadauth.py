#!/usr/bin/env python
"""
Simplified script to test Paddle API authentication
"""
import asyncio
import logging
import os
import requests
import json

from app.core.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_paddle_auth():
    """Test direct authentication with Paddle API"""
    try:
        logger.info("Testing direct authentication with Paddle API...")
        
        # Get API key from settings
        api_key = settings.PADDLE_API_KEY
        
        if not api_key:
            logger.error("PADDLE_API_KEY is not configured")
            return False
            
        # Determine base URL
        base_url = "https://sandbox-api.paddle.com" if settings.PADDLE_SANDBOX else "https://api.paddle.com"
        
        # Setup headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Make a simple request to list prices
        url = f"{base_url}/prices"
        
        # Log the request details
        logger.info(f"Making request to: {url}")
        logger.info(f"With Authorization: Bearer {api_key[:5]}...")
        
        # Make the request
        response = requests.get(url, headers=headers)
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Authentication successful! Found {len(data.get('data', []))} prices")
            if data.get('data'):
                logger.info(f"Sample price ID: {data['data'][0]['id']}")
            return True
        else:
            logger.error(f"Authentication failed with status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing authentication: {str(e)}")
        return False

async def main():
    """Run the authentication test"""
    logger.info("Starting Paddle API authentication test...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Sandbox mode: {settings.PADDLE_SANDBOX}")
    
    # Test authentication
    auth_result = await test_paddle_auth()
    
    logger.info("\n========== TEST RESULT ==========")
    logger.info(f"Paddle API authentication test: {'PASSED' if auth_result else 'FAILED'}")
    
    logger.info("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(main())
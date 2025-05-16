#!/usr/bin/env python
"""
Script to validate Paddle API key format and test API access
"""
import os
import requests
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    """Validate that the API key has the correct format"""
    if not api_key:
        logger.error("API key is missing")
        return False
        
    # Check if it starts with pdl_
    if not api_key.startswith("pdl_"):
        logger.error("API key must start with 'pdl_'")
        return False
        
    # Check if it contains apikey_
    if "apikey_" not in api_key:
        logger.error("API key must contain 'apikey_'")
        return False
        
    # Check if it's a sandbox or live key
    if "sdbx_" not in api_key and "live_" not in api_key:
        logger.error("API key must contain 'sdbx_' (for sandbox) or 'live_' (for production)")
        return False
        
    # Check the length (approximately 69 characters)
    if len(api_key) < 60:
        logger.warning(f"API key length is {len(api_key)}, which is shorter than expected (should be around 69 characters)")
        
    logger.info("API key format appears valid")
    return True

def test_api_access(api_key, sandbox=True):
    """Test API access by making a simple request"""
    # Determine base URL
    base_url = "https://sandbox-api.paddle.com" if sandbox else "https://api.paddle.com"
    
    # Setup headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    endpoints = [
        "/prices",
        "/event-types"
    ]
    
    success = False
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"Testing endpoint: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Success! Endpoint {endpoint} returned status code 200")
                logger.info("Response preview:")
                
                # Get the first 200 characters of the response
                response_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                logger.info(response_text)
                
                success = True
                break
            else:
                logger.error(f"❌ Failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error making request: {str(e)}")
    
    return success

def main():
    """Validate and test the Paddle API key"""
    logger.info("Paddle API Key Validator")
    logger.info("----------------------")
    
    # Get API key from environment
    api_key = os.getenv("PADDLE_API_KEY")
    
    if not api_key:
        logger.error("PADDLE_API_KEY environment variable is not set")
        logger.info("Please set the PADDLE_API_KEY in your .env file or provide it as a parameter")
        
        # Ask for API key if not in environment
        api_key = input("Enter your Paddle API key: ")
        
    # Validate API key format
    logger.info("\nValidating API key format...")
    if not validate_api_key(api_key):
        logger.error("API key format validation failed")
        sys.exit(1)
        
    # Determine environment
    is_sandbox = "sdbx_" in api_key
    env_type = "SANDBOX" if is_sandbox else "PRODUCTION"
    
    logger.info(f"\nAPI key appears to be for {env_type} environment")
    logger.info(f"Testing API access against {env_type.lower()} environment...")
    
    # Test API access
    if test_api_access(api_key, is_sandbox):
        logger.info("\n✅ API ACCESS SUCCESSFUL!")
        logger.info("Your Paddle API key is valid and working correctly.")
    else:
        logger.error("\n❌ API ACCESS FAILED!")
        logger.error("Your Paddle API key failed to authenticate with the API.")
        logger.error("Please check that:")
        logger.error("1. The API key is correct")
        logger.error("2. The key has the necessary permissions")
        logger.error("3. Your account is active")
        sys.exit(1)

if __name__ == "__main__":
    main()
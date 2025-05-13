# oauthtest.py
import os
import asyncio
from app.core.settings import settings

async def test_oauth_config():
    """Test the OAuth configuration"""
    print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
    print(f"GOOGLE_CLIENT_SECRET: {'*****' if settings.GOOGLE_CLIENT_SECRET else 'Not set'}")
    print(f"OAUTH_REDIRECT_URL: {settings.OAUTH_REDIRECT_URL}")
    
    # Check if the critical parts are configured
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        print("\nWARNING: Google OAuth credentials are not configured.")
        print("You need to set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.")
        print("Without these, Google OAuth will not work.")
    else:
        print("\nGoogle OAuth configuration looks good.")

if __name__ == "__main__":
    asyncio.run(test_oauth_config())
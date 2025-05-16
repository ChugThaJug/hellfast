# app/services/paddle_auth.py
"""
Custom authentication helpers for Paddle API
"""
from typing import Dict

class HeaderAuthentication:
    """
    Custom header authentication for Paddle API
    """
    def __init__(self, token=None, headers=None):
        """
        Initialize with either a token or headers dict
        """
        self.token = token
        self.headers = headers or {}
        
        # If token provided but no headers, create Authorization header
        if token and not headers:
            self.headers = {"Authorization": f"Bearer {token}"}
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Return headers for authentication
        """
        return self.headers
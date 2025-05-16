# app/services/init_firebase.py
import logging

logger = logging.getLogger(__name__)

def initialize_firebase_admin():
    """Development-friendly Firebase initialization."""
    logger.warning("Using development-friendly Firebase initialization")
    return True
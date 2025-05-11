# app/utils/cache_cleanup.py
import os
import time
from datetime import datetime, timedelta
import logging
from app.core.settings import settings

logger = logging.getLogger(__name__)

def cleanup_old_cache_files():
    """Remove cache files older than CACHE_RETENTION_DAYS."""
    try:
        current_time = time.time()
        retention_seconds = settings.CACHE_RETENTION_DAYS * 24 * 3600
        
        # Clean cache directory
        for directory in [settings.CACHE_DIR, settings.DOWNLOAD_DIR]:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if current_time - file_time > retention_seconds:
                        os.remove(filepath)
                        logger.info(f"Removed old file: {filename}")
                        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")
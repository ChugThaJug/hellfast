import os
import logging
from app.core.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting YouTube Processing API...")
    logger.info(f"Running in {settings.APP_ENV} mode")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
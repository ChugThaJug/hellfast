
# app/api/routes/webhook.py
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging

from app.db.database import get_db
from app.services.subscription_service import SubscriptionService
from app.services.paddle_direct import PaddleDirectService
from app.core.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/paddle", include_in_schema=True)
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Paddle webhooks for subscription updates and payments.
    
    This endpoint receives webhook events from Paddle when subscriptions
    are created, updated, cancelled, or payments are processed.
    """
    try:
        # Get the raw request body - important for signature verification
        raw_body = await request.body()
        
        # Parse the data from the raw body for processing
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return {"status": "error", "message": "Invalid JSON"}
        
        # Get the Paddle-Signature header
        signature = request.headers.get("Paddle-Signature", "")
        
        # Verify signature in production
        if settings.APP_ENV == "production" and settings.PADDLE_WEBHOOK_SECRET:
            if not signature:
                logger.warning("Missing Paddle signature header in production")
                return {"status": "error", "message": "Missing signature header"}
                
            valid_signature = PaddleDirectService.verify_webhook_signature(
                raw_body,
                signature, 
                settings.PADDLE_WEBHOOK_SECRET
            )
            
            if not valid_signature:
                logger.warning("Invalid Paddle webhook signature")
                return {"status": "invalid_signature"}
        elif not signature and settings.APP_ENV == "production":
            logger.warning("Missing Paddle signature header in production")
            # We still process in production but log the warning
        
        # Log the event
        event_type = data.get("event_type", "")
        logger.info(f"Received Paddle webhook: {event_type}")
        
        # Process the webhook event
        success = await SubscriptionService.handle_webhook_event(db, data)
        
        if success:
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "Failed to process webhook"}
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/status")
async def webhook_status():
    """
    Check if webhook endpoints are configured and functioning.
    """
    return {
        "status": "Webhook endpoints are configured",
        "paddle_webhook_secret_configured": bool(settings.PADDLE_WEBHOOK_SECRET),
        "environment": settings.APP_ENV
    }
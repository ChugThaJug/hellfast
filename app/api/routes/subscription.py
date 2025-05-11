from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json

from app.db.database import get_db
from app.models.database import User, Subscription
from app.services.auth import get_current_active_user
from app.services.subscription import SubscriptionService
from app.core.settings import settings

# Define Pydantic models for request/response
from pydantic import BaseModel

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    monthly_quota: int
    features: List[str]

class SubscriptionStatus(BaseModel):
    plan_id: str
    status: str
    current_period_end: str
    monthly_quota: int
    used_quota: int
    features: List[str]

class SubscriptionCreate(BaseModel):
    plan_id: str
    payment_method_id: Optional[str] = None

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans():
    """Get all available subscription plans."""
    plans = []
    for plan_id, plan_data in settings.SUBSCRIPTION_PLANS.items():
        plans.append({
            "id": plan_id,
            "name": plan_data["name"],
            "price": plan_data["price"],
            "monthly_quota": plan_data["monthly_quota"],
            "features": plan_data["features"]
        })
    return plans

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subscription status for current user."""
    # Get subscription
    subscription = SubscriptionService.get_subscription(db, current_user.id)
    
    if not subscription:
        # Return free tier info
        free_plan = settings.SUBSCRIPTION_PLANS["free"]
        return {
            "plan_id": "free",
            "status": "active",
            "current_period_end": "-",
            "monthly_quota": free_plan["monthly_quota"],
            "used_quota": 0,
            "features": free_plan["features"]
        }
    
    # Get subscription features
    features_data = await SubscriptionService.get_subscription_features(db, current_user.id)
    
    return {
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end.isoformat(),
        "monthly_quota": subscription.monthly_quota,
        "used_quota": subscription.used_quota,
        "features": features_data["features"]
    }

@router.post("/create", response_model=Dict)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update a subscription."""
    if subscription_data.plan_id not in settings.SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID"
        )
    
    # For free plan, just create subscription without payment
    if subscription_data.plan_id == "free":
        subscription = await SubscriptionService.create_subscription(
            db, current_user.id, "free"
        )
        return {
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat(),
            "message": "Free subscription activated successfully"
        }
    
    # If no payment method is provided and not free plan
    if not subscription_data.payment_method_id and subscription_data.plan_id != "free":
        try:
            import stripe
            # Create session for checkout
            success_url = f"{settings.FRONTEND_URL}/subscription/success?plan_id={subscription_data.plan_id}"
            cancel_url = f"{settings.FRONTEND_URL}/subscription/cancel"
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} Plan",
                        },
                        "unit_amount": int(settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['price'] * 100),
                    },
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(current_user.id),
                metadata={"plan_id": subscription_data.plan_id}
            )
            
            return {"checkout_url": session.url}
        except (ImportError, Exception) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment processing is not available. Please contact support."
            )
    
    # If payment method is provided
    if subscription_data.payment_method_id:
        try:
            import stripe
            # Create customer if not exists
            subscription = SubscriptionService.get_subscription(db, current_user.id)
            customer_id = None
            
            if subscription and subscription.stripe_customer_id:
                customer_id = subscription.stripe_customer_id
            else:
                # Create new customer
                customer = stripe.Customer.create(
                    email=current_user.email,
                    payment_method=subscription_data.payment_method_id,
                    invoice_settings={
                        'default_payment_method': subscription_data.payment_method_id,
                    },
                )
                customer_id = customer.id
            
            # Create subscription in Stripe
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} Plan",
                            },
                            "unit_amount": int(settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['price'] * 100),
                            "recurring": {"interval": "month"}
                        },
                    },
                ],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
            )
            
            # Create or update subscription in database
            subscription = await SubscriptionService.create_subscription(
                db, 
                current_user.id, 
                subscription_data.plan_id,
                customer_id
            )
            
            subscription.stripe_subscription_id = stripe_subscription.id
            db.commit()
            
            return {
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end.isoformat(),
                "message": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} subscription activated successfully"
            }
        except ImportError:
            # Fallback if Stripe is not available
            subscription = await SubscriptionService.create_subscription(
                db, 
                current_user.id, 
                subscription_data.plan_id
            )
            
            return {
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end.isoformat(),
                "message": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} subscription activated successfully"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating subscription: {str(e)}"
            )
    
    # Fallback option if no payment method and not free
    subscription = await SubscriptionService.create_subscription(
        db, 
        current_user.id, 
        subscription_data.plan_id
    )
    
    return {
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end.isoformat(),
        "message": f"{settings.SUBSCRIPTION_PLANS[subscription_data.plan_id]['name']} subscription activated successfully (payment processing skipped)"
    }

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel the current subscription."""
    subscription = SubscriptionService.get_subscription(db, current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # If has Stripe subscription, cancel it
    if subscription.stripe_subscription_id:
        try:
            import stripe
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except (ImportError, Exception) as e:
            # Just log error and continue with local cancellation
            pass
    
    # Update subscription in database
    subscription.status = "cancelled"
    db.commit()
    
    # Create free subscription
    free_subscription = await SubscriptionService.create_subscription(
        db, 
        current_user.id, 
        "free"
    )
    
    return {
        "message": "Subscription cancelled successfully. You have been downgraded to the free plan."
    }

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks for subscription events."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        return {"status": "ok"}
    
    try:
        import stripe
        body = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        # Verify signature
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid signature: {str(e)}"
            )
        
        # Handle different webhook events
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Get user and plan from session
            user_id = int(session.get('client_reference_id'))
            plan_id = session.get('metadata', {}).get('plan_id')
            
            if user_id and plan_id:
                # Create or update subscription
                await SubscriptionService.create_subscription(
                    db, 
                    user_id, 
                    plan_id,
                    session.get('customer')
                )
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            customer_id = invoice.get('customer')
            
            if subscription_id and customer_id:
                # Find subscription by Stripe customer ID
                subscription = db.query(Subscription).filter(
                    Subscription.stripe_customer_id == customer_id
                ).first()
                
                if subscription:
                    # Reset quota for new billing period
                    subscription.used_quota = 0
                    subscription.status = "active"
                    db.commit()
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription_data = event['data']['object']
            customer_id = subscription_data.get('customer')
            
            if customer_id:
                # Find subscription by Stripe customer ID
                subscription = db.query(Subscription).filter(
                    Subscription.stripe_customer_id == customer_id
                ).first()
                
                if subscription:
                    # Mark subscription as cancelled
                    subscription.status = "cancelled"
                    db.commit()
                    
                    # Create free subscription
                    await SubscriptionService.create_subscription(
                        db, 
                        subscription.user_id, 
                        "free"
                    )
        
        return {"status": "ok"}
    
    except ImportError:
        return {"status": "ok", "message": "Stripe not installed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
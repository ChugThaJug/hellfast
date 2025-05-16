# debug_settings.py
from app.core.settings import settings

def print_settings():
    """Print settings to console."""
    print(f"App Environment: {settings.APP_ENV}")
    print(f"Paddle Sandbox: {settings.PADDLE_SANDBOX}")
    print("\nPaddle Plan IDs:")
    print(f"  Pro:         {settings.PADDLE_PRO_PLAN_ID}")
    print(f"  Pro Yearly:  {settings.PADDLE_PRO_YEARLY_PLAN_ID}")
    print(f"  Max:         {settings.PADDLE_MAX_PLAN_ID}")
    print(f"  Max Yearly:  {settings.PADDLE_MAX_YEARLY_PLAN_ID}")
    
    print("\nSubscription Plans:")
    for plan_id, plan_data in settings.SUBSCRIPTION_PLANS.items():
        print(f"\n  Plan: {plan_id}")
        for key, value in plan_data.items():
            print(f"    {key}: {value}")

if __name__ == "__main__":
    print_settings()
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # App info
    APP_TITLE: str = "YouTube Processing API"
    APP_DESCRIPTION: str = "API for processing YouTube videos and generating structured content"
    APP_VERSION: str = "1.0.0"

    APP_ENV: str = os.getenv("APP_ENV", "production")  # "development" or "production"

    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/ytprocessing")
    
    # Firebase Authentication
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_WEB_API_KEY: str = os.getenv("FIREBASE_WEB_API_KEY", "")
    FIREBASE_SERVICE_ACCOUNT_KEY: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    
    # Stripe integration
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # API Keys
    API_KEY_PREFIX: str = os.getenv("API_KEY_PREFIX", "ytproc_")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    REPLICATE_API_TOKEN: Optional[str] = os.getenv("REPLICATE_API_TOKEN")

    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")  # SvelteKit default dev port
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",    # SvelteKit dev server
        "http://localhost:4173",    # SvelteKit preview
        "http://localhost:3000",    # Alternative dev port
    ]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Directory settings
    CACHE_DIR: str = "cache"
    DOWNLOAD_DIR: str = "downloads"
    OUTPUT_DIR: str = "processed"
    SCREENSHOTS_DIR: str = "screenshots"
    
    # OpenAI settings
    MODEL: str = "gpt-4o-mini"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    # Token prices (per 1M tokens)
    TOKEN_PRICES: Dict[str, Dict[str, float]] = {
        'gpt-4o': {'input': 5/1000000, 'output': 15/1000000},
        'gpt-4o-mini': {'input': 0.15/1000000, 'output': 0.6/1000000},
    }
    DEFAULT_TOKEN_PRICE: Dict[str, float] = {
        'input': 0.0001,
        'output': 0.0002
    }
    
    # Processing settings
    MAX_CHARS: int = 100000
    CHUNK_SIZE: int = 1000
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    
    # System resource limits
    MAX_CONCURRENT_JOBS: int = 5
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Cache retention (days)
    CACHE_RETENTION_DAYS: int = 7
    
    # Subscription plans
    SUBSCRIPTION_PLANS: Dict[str, Dict] = {
        "free": {
            "name": "Free",
            "price": 0,
            "monthly_quota": 3,
            "features": ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step"]
        },
        "basic": {
            "name": "Basic",
            "price": 9.99,
            "monthly_quota": 20,
            "features": ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step"]
        },
        "premium": {
            "name": "Premium",
            "price": 19.99,
            "monthly_quota": 50,
            "features": ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step", "podcast_article"]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 49.99,
            "monthly_quota": 200,
            "features": ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step", "podcast_article"]
        }
    }
    
    # In app/core/settings.py, update the SYSTEM_PROMPTS section

    SYSTEM_PROMPTS: Dict[str, str] = {
        "bullet_points": """Transform this transcript into concise bullet points.
        Focus on key information, main ideas, and important details.
        Use clear, direct language and standard bullet point formatting.
        Maintain the logical flow of information.
        Ensure bullet points are non-repetitive and build on each other.""",
        
        "summary": """Create a concise summary of this transcript.
        Capture the main ideas and essential information.
        Maintain the original meaning while condensing the content.
        Aim for clarity and brevity.
        Ensure a coherent flow of information throughout the summary.""",
        
        "step_by_step": """Transform this transcript into a detailed, step-by-step guide.
        Organize the content into logical steps or phases.
        Include relevant background information and context.
        Make the guide clear and actionable for someone who wants to follow along.
        Ensure steps are numbered sequentially and build naturally on each other.
        Avoid repeating information across steps.""",
        
        "podcast_article": """Transform this transcript into a well-structured article or podcast script.
        Use engaging, conversational language.
        Organize content with clear paragraphs and smooth transitions.
        Include relevant context and maintain a narrative flow.
        Ensure ideas connect logically from one paragraph to the next."""
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_token_price(self, model: str) -> Dict[str, float]:
        """Get token prices for specified model."""
        return self.TOKEN_PRICES.get(model, self.DEFAULT_TOKEN_PRICE)

    def validate_directories(self):
        """Validate and create required directories."""
        for directory in [self.CACHE_DIR, self.DOWNLOAD_DIR, self.OUTPUT_DIR, self.SCREENSHOTS_DIR]:
            os.makedirs(directory, exist_ok=True)

# Initialize settings
settings = Settings()

# Create necessary directories
settings.validate_directories()
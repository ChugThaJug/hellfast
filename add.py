"""
Script to add the google_id column to the users table.
This should be run once to migrate your database to support Google OAuth.
"""
from sqlalchemy import create_engine, text
from app.core.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_google_id_column():
    """Add the google_id column to the users table if it doesn't exist."""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Check if the column exists
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'google_id'
            """))
            
            if result.fetchone():
                logger.info("google_id column already exists in users table.")
                return
            
            # Add the column
            logger.info("Adding google_id column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR UNIQUE NULL"))
            conn.commit()
            
            logger.info("Successfully added google_id column to users table.")
            
    except Exception as e:
        logger.error(f"Error adding google_id column: {str(e)}")
        raise

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will add a google_id column to your users table. Continue? (yes/no): ")
    
    if confirm.lower() == "yes":
        add_google_id_column()
        print("Database updated successfully.")
    else:
        print("Operation cancelled.")
"""
Script to add Firebase-related columns to the users table.
This should be run once to migrate your database to support Firebase Authentication.
"""
from sqlalchemy import create_engine, text
from app.core.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_firebase_columns():
    """Add Firebase-related columns to the users table if they don't exist."""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                # Check if firebase_uid column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'firebase_uid'
                """))
                
                if not result.fetchone():
                    logger.info("Adding firebase_uid column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN firebase_uid VARCHAR UNIQUE NULL"))
                else:
                    logger.info("firebase_uid column already exists.")
                
                # Check if display_name column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'display_name'
                """))
                
                if not result.fetchone():
                    logger.info("Adding display_name column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR NULL"))
                else:
                    logger.info("display_name column already exists.")
                
                # Check if photo_url column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'photo_url'
                """))
                
                if not result.fetchone():
                    logger.info("Adding photo_url column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN photo_url VARCHAR NULL"))
                else:
                    logger.info("photo_url column already exists.")
                
                # Check if updated_at column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'updated_at'
                """))
                
                if not result.fetchone():
                    logger.info("Adding updated_at column to users table...")
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                else:
                    logger.info("updated_at column already exists.")
            
            logger.info("All Firebase-related columns added successfully.")
            
    except Exception as e:
        logger.error(f"Error adding Firebase columns: {str(e)}")
        raise

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will add Firebase-related columns to your users table. Continue? (yes/no): ")
    
    if confirm.lower() == "yes":
        add_firebase_columns()
        print("Database updated successfully.")
    else:
        print("Operation cancelled.")
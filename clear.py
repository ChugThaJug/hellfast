from sqlalchemy import create_engine, inspect, text
from app.core.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    """
    Clear the entire database or reset it to a clean state.
    USE WITH CAUTION: This will delete all data in the database.
    """
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Get all tables using PostgreSQL's information_schema (case-sensitive)
            result = conn.execute(text(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                """
            ))
            
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Found tables: {tables}")
            
            # Disable foreign key constraints for PostgreSQL
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            
            # Delete all data from each table
            for table in tables:
                try:
                    logger.info(f"Deleting all data from table: {table}")
                    # Use quotes around table name to preserve case
                    conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
                except Exception as e:
                    logger.warning(f"Error truncating table {table}: {str(e)}")
                    # Try alternative approach
                    try:
                        conn.execute(text(f'DELETE FROM "{table}"'))
                        logger.info(f"Deleted data from {table} using DELETE instead of TRUNCATE")
                    except Exception as e2:
                        logger.error(f"Failed to clear table {table}: {str(e2)}")
            
            # Re-enable foreign key constraints
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            
            # Commit the transaction
            conn.commit()
        
        logger.info("Database cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        raise

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will delete ALL data in your database. Are you sure? (yes/no): ")
    
    if confirm.lower() == "yes":
        clear_database()
        print("Database cleared.")
    else:
        print("Operation cancelled.")
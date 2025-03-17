"""
Run Celery worker and beat scheduler for HackRadar
This script provides a reliable way to run both Celery worker and beat.
"""
import os
import logging
import subprocess
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduce verbosity of SQLAlchemy and Celery loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    logger.error("REDIS_URL not set in environment variables!")
    sys.exit(1)

def run_worker():
    """Run Celery worker and beat"""
    logger.info("Starting Celery worker and beat for HackRadar")
    
    # Set environment variable to suppress detailed startup logs
    os.environ["SHOW_STARTUP_LOGS"] = "false"
    
    # Start Celery worker first - make sure it's ready to receive tasks
    worker_cmd = ["celery", "-A", "app.worker", "worker", "--loglevel=WARNING"]
    worker_process = subprocess.Popen(worker_cmd)
    logger.info("Started Celery worker")
    
    # Wait a moment for worker to initialize
    time.sleep(3)
    
    # Start Celery beat
    beat_cmd = ["celery", "-A", "app.worker", "beat", "--loglevel=WARNING"]
    beat_process = subprocess.Popen(beat_cmd)
    logger.info("Started Celery beat scheduler")
    
    try:
        # Keep the processes running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Celery processes...")
        beat_process.terminate()
        worker_process.terminate()
        
        # Wait for processes to terminate
        beat_process.wait()
        worker_process.wait()
        logger.info("Celery processes stopped")
        sys.exit(0)

def trigger_manual_scrape():
    """Trigger manual scraping task"""
    try:
        # Import the task directly
        # We use direct import to ensure the task is registered properly
        from app.services.hackathon_service import scrape_all_sources
        
        logger.info("Manually triggering scrapers...")
        
        # Run the task synchronously for testing/debugging
        logger.info("Running scrapers - this may take a moment...")
        result = scrape_all_sources()
        
        if result:
            # Show only essential information about fetched hackathons
            unstop_count = result.get('unstop', 0)
            devfolio_count = result.get('devfolio', 0)
            devpost_count = result.get('devpost', 0)
            total_new = result.get('total_new', 0)
            
            logger.info(f"Results Summary:")
            logger.info(f"- Unstop: {unstop_count} new hackathons")
            logger.info(f"- Devfolio: {devfolio_count} new hackathons")
            logger.info(f"- Devpost: {devpost_count} new hackathons")
            logger.info(f"- Total new hackathons added: {total_new}")
            
            return True
        else:
            logger.error("Scraping completed but returned no results")
            return False
    except Exception as e:
        logger.error(f"Error triggering scraping task: {str(e)}")
        return False

def test_database_connection():
    """Test function to add a test hackathon to the database"""
    import uuid
    import datetime
    from app.db.database import SessionLocal
    from app.models.hackathon import HackathonModel
    
    # Create a unique test hackathon
    test_id = uuid.uuid4().hex[:8]
    db = SessionLocal()
    
    try:
        logger.info("Testing database connection...")
        
        # Count hackathons before adding
        count_before = db.query(HackathonModel).count()
        
        # Create a test hackathon
        test_hackathon = HackathonModel(
            name=f"Test Hackathon {test_id}",
            description="This is a test hackathon to verify database connectivity",
            start_date=datetime.datetime.now(),
            end_date=datetime.datetime.now() + datetime.timedelta(days=1),
            location="Test Location",
            registration_link=f"https://example.com/test-{test_id}",
            source="Test",
            image_url="https://example.com/image.jpg"
        )
        
        # Add to database
        db.add(test_hackathon)
        db.commit()
        
        # Count hackathons after adding
        count_after = db.query(HackathonModel).count()
        logger.info(f"Database test successful! Added test hackathon (before: {count_before}, after: {count_after})")
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "scrape":
            trigger_manual_scrape()
        elif sys.argv[1] == "test-db":
            test_database_connection()
        else:
            logger.error(f"Unknown command: {sys.argv[1]}")
            logger.info("Available commands: scrape, test-db")
    else:
        run_worker()
from sqlalchemy.orm import Session
from typing import List, Optional
from celery import Celery
import os
from dotenv import load_dotenv
import logging
from ssl import CERT_NONE

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduce verbosity of other loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)

from app.models.hackathon import HackathonModel
from app.scrapers.unstop_scraper import scrape_unstop
from app.scrapers.devfolio_scraper import scrape_devfolio
from app.scrapers.devpost_scraper import scrape_devpost
from app.services.notification_service import notify_new_hackathons
from app.services.last_run_service import update_last_run, should_run_task

# Celery configuration - import the app instance from worker.py
from app.worker import celery_app

# Constants
SCRAPE_TASK_NAME = "hackathon_scraping"
SCRAPE_INTERVAL_HOURS = 24

def get_hackathons(
    db: Session, 
    location: Optional[str] = None, 
    source: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[HackathonModel]:
    """
    Get hackathons from the database with optional filtering.
    """
    query = db.query(HackathonModel)
    
    if location:
        query = query.filter(HackathonModel.location.ilike(f"%{location}%"))
    
    if source:
        query = query.filter(HackathonModel.source == source)
    
    return query.order_by(HackathonModel.start_date.desc()).offset(skip).limit(limit).all()

@celery_app.task(name="app.services.hackathon_service.scrape_all_sources")
def scrape_all_sources():
    """
    Celery task to scrape all hackathon sources.
    """
    logger.info("┌─── Starting hackathon scraping process ───┐")
    
    # Scrape from all sources
    logger.info("├── Fetching hackathons from Unstop...")
    unstop_hackathons = scrape_unstop() or []
    logger.info(f"├── Found {len(unstop_hackathons)} new hackathons from Unstop")
    
    logger.info("├── Fetching hackathons from Devfolio...")
    devfolio_hackathons = scrape_devfolio() or []
    logger.info(f"├── Found {len(devfolio_hackathons)} new hackathons from Devfolio")
    
    logger.info("├── Fetching hackathons from Devpost...")
    devpost_hackathons = scrape_devpost() or []
    logger.info(f"├── Found {len(devpost_hackathons)} new hackathons from Devpost")
    
    # Combine all new hackathons
    all_new_hackathons = unstop_hackathons + devfolio_hackathons + devpost_hackathons
    
    # Send notifications for new hackathons
    if all_new_hackathons:
        logger.info(f"├── Sending notifications for {len(all_new_hackathons)} new hackathons")
        notify_new_hackathons(all_new_hackathons)
    else:
        logger.info("├── No new hackathons found, skipping notifications")
    
    logger.info("└─── Hackathon scraping process completed ───┘")
    
    # Update the last run time
    update_last_run(SCRAPE_TASK_NAME)
    
    return {
        "unstop": len(unstop_hackathons),
        "devfolio": len(devfolio_hackathons),
        "devpost": len(devpost_hackathons),
        "total_new": len(all_new_hackathons)
    }

def trigger_scraping():
    """
    Trigger the scraping task asynchronously using Celery.
    """
    logger.info("Triggering scraping task via Celery...")
    result = scrape_all_sources.delay()
    logger.info(f"Scraping task triggered with ID: {result.id}")
    return result.id

def check_and_run_scraping_if_needed():
    """
    Check if it's time to run the scraping task, and run it if needed.
    This should be called when the application starts.
    """
    if should_run_task(SCRAPE_TASK_NAME, SCRAPE_INTERVAL_HOURS):
        logger.info(f"It's been over {SCRAPE_INTERVAL_HOURS} hours since last scraping, running now...")
        return trigger_scraping()
    else:
        logger.info("Not time to scrape yet, skipping...")
        return None 
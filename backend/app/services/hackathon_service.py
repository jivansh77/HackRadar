from sqlalchemy.orm import Session
from typing import List, Optional
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

from app.models.hackathon import HackathonModel
from app.scrapers.unstop_scraper import scrape_unstop
from app.scrapers.devfolio_scraper import scrape_devfolio
from app.scrapers.devpost_scraper import scrape_devpost
from app.services.notification_service import notify_new_hackathons

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("hackathon_tasks", broker=REDIS_URL)

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

def trigger_scraping():
    """
    Trigger the scraping task asynchronously using Celery.
    """
    scrape_all_sources.delay()

@celery_app.task
def scrape_all_sources():
    """
    Celery task to scrape all hackathon sources.
    """
    # Scrape from all sources
    unstop_hackathons = scrape_unstop()
    devfolio_hackathons = scrape_devfolio()
    devpost_hackathons = scrape_devpost()
    
    # Combine all new hackathons
    all_new_hackathons = unstop_hackathons + devfolio_hackathons + devpost_hackathons
    
    # Send notifications for new hackathons
    if all_new_hackathons:
        notify_new_hackathons(all_new_hackathons)
    
    return {
        "unstop": len(unstop_hackathons),
        "devfolio": len(devfolio_hackathons),
        "devpost": len(devpost_hackathons),
        "total_new": len(all_new_hackathons)
    } 
from celery import Celery
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Redis URL from environment variable or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery("hackathon_tasks", broker=REDIS_URL)

# Import tasks to register them with Celery
from app.services.hackathon_service import scrape_all_sources

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Schedule periodic tasks
    beat_schedule={
        "scrape-hackathons-every-hour": {
            "task": "app.services.hackathon_service.scrape_all_sources",
            "schedule": 7200.0,  # Every 2 hours
        },
    },
)

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.start() 
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.hackathon import Hackathon
from app.services.hackathon_service import get_hackathons, trigger_scraping, SCRAPE_TASK_NAME
from app.services.last_run_service import get_last_run, update_last_run
from app.services.notification_service import send_notification
from firebase_admin import messaging
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/hackathons", response_model=List[Hackathon])
async def read_hackathons(
    db: Session = Depends(get_db),
    location: Optional[str] = Query(None, description="Filter by location"),
    source: Optional[str] = Query(None, description="Filter by source platform"),
    skip: int = 0,
    limit: int = 500
):
    """
    Get all hackathons with optional filtering by location and source.
    """
    return get_hackathons(db, location=location, source=source, skip=skip, limit=limit)

# Notification subscription model
class SubscriptionRequest(BaseModel):
    token: str
    topic: str

@router.post("/notifications/subscribe", status_code=200)
async def subscribe_to_topic(request: SubscriptionRequest):
    """
    Subscribe a device token to a Firebase Cloud Messaging topic.
    """
    try:
        # Register the device to receive notifications for a given topic
        messaging.subscribe_to_topic([request.token], request.topic)
        return {"message": f"Successfully subscribed to {request.topic}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {str(e)}")

@router.post("/scrape", status_code=202)
async def scrape_hackathons():
    """
    Trigger manual scraping of hackathon data from all sources.
    This is an asynchronous operation.
    """
    # Get the last run time
    last_run = get_last_run(SCRAPE_TASK_NAME)
    
    # Start the scraping task
    task_id = trigger_scraping()
    
    response = {
        "message": "Scraping task started",
        "task_id": task_id,
        "last_run": last_run.isoformat() if last_run else None,
    }
    
    # If we have a last run time, include the next scheduled run
    if last_run:
        next_scheduled = last_run + timedelta(hours=24)
        response["next_scheduled_run"] = next_scheduled.isoformat()
    
    return response

@router.get("/scrape/status", status_code=200)
async def get_scrape_status():
    """
    Get information about the last scraping run and when the next one is scheduled.
    """
    last_run = get_last_run(SCRAPE_TASK_NAME)
    
    if not last_run:
        return {
            "last_run": None,
            "next_scheduled_run": None,
            "message": "No scraping has been performed yet"
        }
    
    next_scheduled = last_run + timedelta(hours=24)
    now = datetime.utcnow()
    
    return {
        "last_run": last_run.isoformat(),
        "next_scheduled_run": next_scheduled.isoformat(),
        "time_since_last_run": str(now - last_run).split('.')[0],  # Remove microseconds
        "time_until_next_run": str(next_scheduled - now).split('.')[0] if next_scheduled > now else "Overdue",
    }
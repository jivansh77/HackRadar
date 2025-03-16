from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.hackathon import Hackathon
from app.services.hackathon_service import get_hackathons, trigger_scraping
from app.services.notification_service import send_notification
from firebase_admin import messaging

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
    # Start the scraping task
    trigger_scraping()
    return {"message": "Scraping task started"}
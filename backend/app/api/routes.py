from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.hackathon import Hackathon
from app.services.hackathon_service import get_hackathons, trigger_scraping

router = APIRouter()

@router.get("/hackathons", response_model=List[Hackathon])
async def read_hackathons(
    db: Session = Depends(get_db),
    location: Optional[str] = Query(None, description="Filter by location"),
    source: Optional[str] = Query(None, description="Filter by source platform"),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all hackathons with optional filtering by location and source.
    """
    return get_hackathons(db, location=location, source=source, skip=skip, limit=limit)

@router.post("/scrape", status_code=202)
async def scrape_hackathons():
    """
    Trigger manual scraping of hackathon data from all sources.
    This is an asynchronous operation.
    """
    # Start the scraping task
    trigger_scraping()
    return {"message": "Scraping task started"} 
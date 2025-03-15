import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Any

from app.db.database import SessionLocal
from app.models.hackathon import HackathonModel

logger = logging.getLogger(__name__)

def scrape_devpost() -> List[Dict[str, Any]]:
    """
    Scrape hackathon data from Devpost.
    
    Returns:
        List of hackathon dictionaries with scraped data.
    """
    try:
        # Create a database session
        db = SessionLocal()
        
        # URL for Devpost hackathons
        url = "https://devpost.com/hackathons"
        
        # Send HTTP request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find hackathon listings
        hackathon_cards = soup.select(".hackathon-tile")
        
        hackathons = []
        
        for card in hackathon_cards:
            try:
                # Extract data from each card
                name_elem = card.select_one(".title")
                name = name_elem.text.strip() if name_elem else "Unknown Hackathon"
                
                link_elem = card.select_one("a.tile-link")
                registration_link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                location_elem = card.select_one(".location")
                location = location_elem.text.strip() if location_elem else None
                
                date_elem = card.select_one(".date-range")
                date_text = date_elem.text.strip() if date_elem else ""
                
                # Parse dates (simplified for example)
                start_date = None
                end_date = None
                if date_text:
                    try:
                        # This is a simplified date parsing logic
                        # In a real implementation, you'd need more robust parsing
                        date_parts = date_text.split("-")
                        if len(date_parts) >= 2:
                            start_date = datetime.strptime(date_parts[0].strip(), "%b %d, %Y")
                            end_date = datetime.strptime(date_parts[1].strip(), "%b %d, %Y")
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {date_text}. Error: {str(e)}")
                
                image_elem = card.select_one("img.hackathon-thumbnail")
                image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
                
                # Create hackathon dictionary
                hackathon = {
                    "name": name,
                    "description": None,  # Would need to visit the detail page to get this
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "registration_link": registration_link,
                    "source": "Devpost",
                    "image_url": image_url
                }
                
                # Save to database
                db_hackathon = HackathonModel(
                    name=hackathon["name"],
                    description=hackathon["description"],
                    start_date=hackathon["start_date"],
                    end_date=hackathon["end_date"],
                    location=hackathon["location"],
                    registration_link=hackathon["registration_link"],
                    source=hackathon["source"],
                    image_url=hackathon["image_url"]
                )
                
                # Check if hackathon already exists
                existing = db.query(HackathonModel).filter(
                    HackathonModel.name == hackathon["name"],
                    HackathonModel.source == "Devpost"
                ).first()
                
                if not existing:
                    db.add(db_hackathon)
                    db.commit()
                    hackathons.append(hackathon)
                
            except Exception as e:
                logger.error(f"Error processing hackathon card: {str(e)}")
                continue
        
        return hackathons
        
    except Exception as e:
        logger.error(f"Error scraping Devpost: {str(e)}")
        return []
    
    finally:
        db.close() 
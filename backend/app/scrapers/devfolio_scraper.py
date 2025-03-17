import requests
from datetime import datetime
import logging
from typing import List, Dict, Any
import json
from bs4 import BeautifulSoup
import time

from app.db.database import SessionLocal
from app.models.hackathon import HackathonModel

logger = logging.getLogger(__name__)

def get_location_from_hackathon_page(url: str) -> str:
    """
    Scrape the hackathon's page to get the exact location (city).
    
    Args:
        url: The URL of the hackathon page
        
    Returns:
        The location string (city name) or "In-person" if not found
    """
    try:
        # Add a small delay to avoid being rate-limited
        time.sleep(0.5)
        
        # Make request to the hackathon page
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the "HAPPENING" section which is followed by the location
        happening_elements = soup.find_all(string=lambda text: text and "HAPPENING" == text.strip().upper())
        
        # If we found HAPPENING elements
        for element in happening_elements:
            parent_div = element.parent
            if parent_div:
                # Get the next sibling which should contain the location
                next_element = parent_div.find_next_sibling()
                if next_element:
                    location_text = next_element.get_text().strip()
                    # Make sure it looks like a location
                    if location_text and len(location_text) < 100 and "," in location_text:
                        return location_text
        
        # Alternative approach - look for structure where HAPPENING is followed by location in the same container
        containers = soup.find_all(['div', 'section'])
        for container in containers:
            texts = container.find_all(text=True)
            for i, text in enumerate(texts):
                if text and "HAPPENING" == text.strip().upper() and i + 1 < len(texts):
                    location_text = texts[i + 1].strip()
                    if location_text and len(location_text) < 100 and "," in location_text:
                        return location_text
        
        # Last resort - try to find any element that might have a city, India format
        city_elements = soup.find_all(text=lambda text: text and 
                                      isinstance(text, str) and 
                                      "India" in text and 
                                      "," in text and 
                                      len(text.strip()) < 50)
        
        if city_elements:
            return city_elements[0].strip()
            
        return "In-person"  # Default if not found
        
    except Exception as e:
        logger.error(f"Error fetching location from {url}: {str(e)}")
        return "In-person"  # Default in case of errors

def scrape_devfolio() -> List[Dict[str, Any]]:
    """
    Fetch hackathon data from Devfolio's JSON API endpoint.
    
    Returns:
        List of hackathon dictionaries with scraped data.
    """
    try:
        # Create a database session
        db = SessionLocal()
        
        # URL for Devfolio hackathons JSON data
        url = "https://devfolio.co/_next/data/uw5JQ6xpZ9nB5NukThGXa/hackathons.json"
        
        # Make request to the API endpoint
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response
        data = response.json()
        
        # Extract hackathon data from the response
        open_hackathons = data.get("pageProps", {}).get("dehydratedState", {}).get("queries", [])[0].get("state", {}).get("data", {}).get("open_hackathons", [])
        featured_hackathons = data.get("pageProps", {}).get("dehydratedState", {}).get("queries", [])[0].get("state", {}).get("data", {}).get("featured_hackathons", [])
        
        # Combine both lists
        all_hackathons = open_hackathons + featured_hackathons
        
        hackathons = []
        
        for hackathon_data in all_hackathons:
            try:
                # Extract data from each hackathon
                name = hackathon_data.get("name", "Unknown Hackathon")
                slug = hackathon_data.get("slug", "")
                registration_link = f"https://{slug}.devfolio.co/" if slug else ""
                
                # Parse dates
                start_date = None
                end_date = None
                starts_at = hackathon_data.get("starts_at")
                ends_at = hackathon_data.get("ends_at")
                
                if starts_at:
                    start_date = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
                if ends_at:
                    end_date = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
                
                # Get location info
                is_online = hackathon_data.get("is_online", False)
                location = "Online"
                
                # For in-person hackathons, get the specific location
                if not is_online and registration_link:
                    location = get_location_from_hackathon_page(registration_link)
                    
                # Validate location to ensure it's not too long for database
                if isinstance(location, str):
                    # If location is suspiciously long, it might be HTML/JSON content
                    if len(location) > 200:
                        logger.warning(f"Location for {name} is too long ({len(location)} chars), truncating")
                        location = "In-person"
                    # Ensure location won't exceed database limit (typically 255 chars)
                    location = location[:250] if len(location) > 250 else location
                else:
                    location = "In-person"
                
                # Get settings for additional information
                settings = hackathon_data.get("settings", {})
                site_url = settings.get("site", "")
                
                # Get theme info
                themes = hackathon_data.get("themes", [])
                theme_names = [theme.get("theme", {}).get("name") for theme in themes if theme.get("theme", {}).get("name")]
                description = f"Themes: {', '.join(theme_names)}" if theme_names else None
                
                # Create hackathon dictionary
                hackathon = {
                    "name": name,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "registration_link": registration_link,
                    "source": "Devfolio",
                    "image_url": None  # No direct image URL in the JSON, would need additional logic to fetch
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
                    HackathonModel.source == "Devfolio"
                ).first()
                
                if not existing:
                    db.add(db_hackathon)
                    db.commit()
                    hackathons.append(hackathon)
                
            except Exception as e:
                logger.error(f"Error processing hackathon data: {str(e)}")
                continue
        
        return hackathons
        
    except Exception as e:
        logger.error(f"Error fetching Devfolio data: {str(e)}")
        return []
    
    finally:
        db.close() 
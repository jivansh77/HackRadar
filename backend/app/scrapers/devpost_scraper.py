import requests
from datetime import datetime
import logging
from typing import List, Dict, Any
import json
import re
import math

from app.db.database import SessionLocal
from app.models.hackathon import HackathonModel

logger = logging.getLogger(__name__)

# Set the logger to only show INFO and higher for this module
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def scrape_devpost() -> List[Dict[str, Any]]:
    """
    Fetch hackathon data from Devpost's JSON API endpoint with pagination.
    
    Returns:
        List of hackathon dictionaries with scraped data.
    """
    try:
        # Create a database session
        db = SessionLocal()
        
        # Headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        all_hackathons_data = []
        page = 1
        total_pages = None
        
        while total_pages is None or page <= total_pages:
            # Construct URL for the current page
            if page == 1:
                # Use the API endpoint for the first page
                url = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"
            else:
                # Use the paginated API endpoint for subsequent pages
                url = f"https://devpost.com/api/hackathons?page={page}&status[]=upcoming&status[]=open"
            
            logger.info(f"Fetching Devpost page {page}...")
            
            # Make the request
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse JSON data
            data = response.json()
            
            # Extract hackathons from the current page
            page_hackathons = data.get("hackathons", [])
            
            if not page_hackathons:
                # No more hackathons, exit the loop
                logger.info(f"No more hackathons found on page {page}")
                break
                
            # Add this page's hackathons to our collection
            all_hackathons_data.extend(page_hackathons)
            
            # Calculate total pages on first response if not already set
            if total_pages is None:
                meta = data.get("meta", {})
                total_count = meta.get("total_count", 0)
                per_page = meta.get("per_page", 9)  # Default to 9 if not specified
                
                if total_count > 0 and per_page > 0:
                    total_pages = math.ceil(total_count / per_page)
                    logger.info(f"Found {total_count} total hackathons across {total_pages} pages")
                else:
                    # If we can't determine total pages, just fetch one page
                    logger.warning("Could not determine total pages, will only fetch current page")
                    break
            
            page += 1
        
        logger.info(f"Successfully fetched data for {len(all_hackathons_data)} hackathons from Devpost")
        
        # Process all hackathons
        hackathons = []
        new_count = 0
        
        for hackathon_data in all_hackathons_data:
            try:
                # Extract basic information
                name = hackathon_data.get("title", "Unknown Hackathon")
                tagline = hackathon_data.get("tagline", "")
                registration_link = hackathon_data.get("url", "")
                
                # Extract location
                displayed_location = hackathon_data.get("displayed_location", {})
                location_str = displayed_location.get("location", "Unknown Location")
                
                # Define common cities to check for in title/organization name
                common_cities = [
                    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
                    "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Kanpur",
                    "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna",
                    "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Ranchi",
                    "Faridabad", "Coimbatore", "Gurgaon", "Noida", "Kochi", "Chandigarh",
                    "New York", "San Francisco", "London", "Berlin", "Toronto", "Singapore",
                    "Sydney", "Tokyo", "Paris", "Amsterdam", "Chicago", "Seattle"
                ]
                
                # Check if the event is online
                is_online = "online" in location_str.lower() or "virtual" in location_str.lower() or "remote" in location_str.lower()
                
                # Try to find city in the title
                city_match = None
                title_for_match = name.lower()
                
                # Try to find city in title
                for city in common_cities:
                    city_lower = city.lower()
                    if city_lower in title_for_match:
                        city_match = city
                        break
                
                # Set the final location string
                if is_online:
                    if city_match:
                        location = f"Online | {city_match}"
                    else:
                        location = "Online"
                else:
                    if city_match and "unknown" in location_str.lower():
                        location = city_match
                    else:
                        location = location_str
                
                # Process themes
                themes = hackathon_data.get("themes", [])
                theme_names = [theme.get("name") for theme in themes if theme.get("name")]
                themes_str = f"Themes: {', '.join(theme_names)}" if theme_names else ""
                
                # Extract prize amount if available
                prize_amount = hackathon_data.get("prize_amount", "")
                if prize_amount:
                    # Remove HTML tags from prize amount
                    prize_amount = re.sub(r'<.*?>', '', prize_amount)
                
                # Combine description elements
                description_parts = []
                if tagline:
                    description_parts.append(tagline)
                if themes_str:
                    description_parts.append(themes_str)
                if prize_amount:
                    description_parts.append(f"Prize: {prize_amount}")
                
                description = " | ".join(description_parts) if description_parts else None
                
                # Extract dates from submission_period_dates
                start_date = None
                end_date = None
                submission_dates = hackathon_data.get("submission_period_dates", "")
                
                if submission_dates:
                    try:
                        # Handle different date formats
                        if " - " in submission_dates:
                            date_parts = submission_dates.split(" - ")
                            
                            # Case: "Mar 15 - 16, 2025" (same month)
                            if len(date_parts) == 2 and not any(month in date_parts[1] for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                                # Extract components from the dates
                                start_part = date_parts[0].strip()  # e.g., "Mar 15"
                                end_part = date_parts[1].strip()    # e.g., "16, 2025"
                                
                                # If there's a comma in the end date, it has the year
                                if "," in end_part:
                                    end_day, year = end_part.split(", ")
                                    # Extract month from start date
                                    if " " in start_part:
                                        month = start_part.split(" ")[0]
                                        # Format complete dates
                                        start_date_str = f"{start_part}, {year}"
                                        end_date_str = f"{month} {end_day}, {year}"
                                        
                                        # Parse dates
                                        start_date = datetime.strptime(start_date_str, "%b %d, %Y")
                                        end_date = datetime.strptime(end_date_str, "%b %d, %Y")
                                    else:
                                        logger.debug(f"Unexpected start date format: {start_part}")
                                else:
                                    logger.debug(f"End date missing year: {end_part}")
                            
                            # Case: "Mar 15 - Apr 16, 2025" (different months)
                            else:
                                # If the year is only in the second part, add it to the first part
                                if "," in date_parts[1] and "," not in date_parts[0]:
                                    year = date_parts[1].split(", ")[1]
                                    date_parts[0] = f"{date_parts[0]}, {year}"
                                
                                # Parse start date
                                start_date = datetime.strptime(date_parts[0], "%b %d, %Y")
                                # Parse end date
                                end_date = datetime.strptime(date_parts[1], "%b %d, %Y")
                        
                        # Case: Single date format like "Mar 23, 2025"
                        elif "," in submission_dates and any(month in submission_dates for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                            # This is a single date - use it as both start and end date
                            date_str = submission_dates.strip()
                            parsed_date = datetime.strptime(date_str, "%b %d, %Y")
                            start_date = parsed_date
                            end_date = parsed_date  # Same day event
                        
                        else:
                            logger.debug(f"Unexpected date format: {submission_dates}")
                            
                    except Exception as e:
                        logger.debug(f"Failed to parse submission dates: {submission_dates}")
                
                # Extract image URL and convert to absolute URL if needed
                image_url = hackathon_data.get("thumbnail_url")
                if image_url and image_url.startswith("//"):
                    image_url = f"https:{image_url}"
                
                # Create hackathon dictionary
                hackathon = {
                    "name": name,
                    "description": description,
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
                    new_count += 1
                
            except Exception as e:
                logger.error(f"Error processing hackathon data: {str(e)}")
                continue
        
        if new_count > 0:
            logger.info(f"Added {new_count} new hackathons from Devpost to the database")
        else:
            logger.info("No new hackathons from Devpost to add")
            
        return hackathons
        
    except Exception as e:
        logger.error(f"Error fetching Devpost data: {str(e)}")
        return []
    
    finally:
        db.close() 
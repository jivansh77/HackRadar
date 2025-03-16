import requests
from datetime import datetime
import logging
from typing import List, Dict, Any
import json
import re

from app.db.database import SessionLocal
from app.models.hackathon import HackathonModel

logger = logging.getLogger(__name__)

def scrape_unstop() -> List[Dict[str, Any]]:
    """
    Fetch hackathon data from Unstop's JSON API endpoint.
    Extract location information from hackathon names by matching with city list.
    
    Returns:
        List of hackathon dictionaries with scraped data.
    """
    # Initialize empty list to store hackathons
    hackathons = []
    
    try:
        # Create a database session
        db = SessionLocal()
        
        # Headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        # Define fallback common cities in India
        common_cities = [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
            "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Kanpur",
            "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna",
            "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Ranchi",
            "Faridabad", "Coimbatore", "Gurgaon", "Noida", "Kochi", "Chandigarh"
        ]
        
        # First, fetch the list of cities from Unstop API
        cities = []
        try:
            city_url = "https://unstop.com/api/public/city-name"
            city_response = requests.get(city_url, headers=headers)
            city_response.raise_for_status()
            
            # Parse city data
            city_data = city_response.json()
            
            # Correct structure: the cities are under "data.cities_name"
            if isinstance(city_data, dict) and "data" in city_data:
                data_obj = city_data["data"]
                if isinstance(data_obj, dict) and "cities_name" in data_obj:
                    cities = data_obj["cities_name"]
                    if not isinstance(cities, list):
                        logger.warning("Cities data is not a list, using fallback")
                        cities = common_cities
            
            logger.info(f"Fetched {len(cities)} cities from Unstop API")
            
            # If we didn't get any cities from the API, use the fallback list
            if not cities:
                logger.warning("No cities fetched from API, using fallback city list")
                cities = common_cities
        except Exception as e:
            logger.error(f"Error fetching cities from API: {str(e)}, using fallback list")
            cities = common_cities
        
        # Sort cities by length (descending) to match longer city names first
        cities.sort(key=len, reverse=True)
        
        # Now fetch hackathon data
        all_hackathons_data = []
        page = 1
        last_page = None
        
        while last_page is None or page <= last_page:
            # Construct URL for the current page
            url = f"https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&page={page}&per_page=15&oppstatus=open"
            
            logger.info(f"Fetching page {page} from Unstop API")
            
            try:
                # Make the request
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                # Parse JSON data with error handling
                response_data = response.json()
                
                # Ensure response_data is a dictionary
                if not isinstance(response_data, dict):
                    logger.error(f"Hackathon API returned unexpected format (not a dict): {type(response_data)}")
                    break
                
                # Check for data key
                if "data" not in response_data:
                    logger.error(f"Hackathon API response missing 'data' key")
                    break
                
                data_obj = response_data.get("data", {})
                if not isinstance(data_obj, dict):
                    logger.error(f"Hackathon API 'data' is not a dict")
                    break
                
                # Extract hackathons from the current page - exact structure from the API
                page_hackathons = data_obj.get("data", [])
                
                if not isinstance(page_hackathons, list):
                    logger.error(f"Hackathon API 'data.data' is not a list")
                    break
                
                if not page_hackathons:
                    # No more hackathons, exit the loop
                    logger.info(f"No hackathons found on page {page}, stopping pagination")
                    break
                    
                # Get pagination info from the response
                if last_page is None:
                    last_page = data_obj.get("last_page")
                    logger.info(f"Total pages: {last_page}")
                    
                # Add this page's hackathons to our collection
                all_hackathons_data.extend(page_hackathons)
                
                page += 1
            except Exception as e:
                logger.error(f"Error processing page {page}: {str(e)}")
                break
        
        logger.info(f"Fetched {len(all_hackathons_data)} hackathons from Unstop")
        
        # Process all hackathons
        for index, hackathon_data in enumerate(all_hackathons_data):
            try:
                # Verify hackathon_data is a dictionary
                if not isinstance(hackathon_data, dict):
                    logger.error(f"Hackathon data at index {index} is not a dictionary")
                    continue
                
                # Extract basic information
                name = hackathon_data.get("title", "Unknown Hackathon")
                registration_link = hackathon_data.get("seo_url", "")
                if not registration_link:
                    # Fallback to constructing URL from public_url
                    public_url = hackathon_data.get("public_url", "")
                    registration_link = f"https://unstop.com/{public_url}" if public_url else ""
                
                # Extract region information
                region = hackathon_data.get("region", "").lower()
                
                # Extract dates - these are already in ISO format
                start_date = None
                end_date = None
                
                start_date_str = hackathon_data.get("start_date")
                end_date_str = hackathon_data.get("end_date")
                
                if start_date_str and isinstance(start_date_str, str):
                    try:
                        # The date format is ISO: "2025-03-15T00:00:00+05:30"
                        start_date = datetime.fromisoformat(start_date_str)
                    except Exception as e:
                        logger.warning(f"Failed to parse start date: {start_date_str}. Error: {str(e)}")
                
                if end_date_str and isinstance(end_date_str, str):
                    try:
                        end_date = datetime.fromisoformat(end_date_str)
                    except Exception as e:
                        logger.warning(f"Failed to parse end date: {end_date_str}. Error: {str(e)}")
                
                # Determine location
                location = None
                
                # Get organization name for later use
                org_data = hackathon_data.get("organisation", {})
                org_name = ""
                if isinstance(org_data, dict):
                    org_name = org_data.get("name", "").lower()
                
                # Extract potential city from title and organization name
                city_match = None
                title_for_match = name.lower()
                
                # Try to find city in the title or organization name
                for city in cities:
                    city_lower = city.lower()
                    if city_lower in title_for_match:
                        city_match = city
                        break
                    elif org_name and city_lower in org_name:
                        city_match = city
                        break
                
                # 1. If region is "online", set location to "Online" or "Online | City" if city found
                if region == "online":
                    if city_match:
                        location = f"Online | {city_match}"
                    else:
                        location = "Online"
                # 2. Check if it's marked offline
                elif region in ["offline", "in-person"]:
                    # For offline events, use the city match if found
                    if city_match:
                        location = city_match
                    else:
                        location = "Offline"
                # 3. Otherwise, use city match if found
                else:
                    if city_match:
                        location = city_match
                
                # If no location found and there's a region, use that as location
                if not location and hackathon_data.get("region"):
                    location = hackathon_data.get("region").title()
                
                # If still no location, set to "Unknown Location"
                if not location:
                    location = "Unknown Location"
                
                # Get description
                description_parts = []
                
                # Add organization name - with safe access
                org_data = hackathon_data.get("organisation", {})
                if isinstance(org_data, dict):
                    org_name = org_data.get("name")
                    if org_name:
                        description_parts.append(f"Organized by: {org_name}")
                
                # Add prize information - with safe access
                prizes = hackathon_data.get("prizes", [])
                prize_texts = []
                
                if isinstance(prizes, list):
                    for prize in prizes:
                        if not isinstance(prize, dict):
                            continue
                            
                        prize_text = ""
                        rank = prize.get("rank")
                        cash = prize.get("cash")
                        currency = prize.get("currency", "").replace("fa-", "") if prize.get("currency") else ""
                        others = prize.get("others")
                        
                        if rank:
                            prize_text += f"{rank}: "
                        
                        if cash:
                            if currency == "rupee":
                                prize_text += f"₹{cash} "
                            elif currency == "dollar":
                                prize_text += f"${cash} "
                            else:
                                prize_text += f"{cash} {currency} "
                        
                        if others:
                            prize_text += others
                            
                        if prize_text:
                            prize_texts.append(prize_text.strip())
                
                if prize_texts:
                    description_parts.append("Prizes: " + ", ".join(prize_texts))
                
                # Get filters for additional information - with safe access
                categories = []
                filters_data = hackathon_data.get("filters", [])
                
                if isinstance(filters_data, list):
                    for filter_data in filters_data:
                        if isinstance(filter_data, dict) and filter_data.get("type") == "category":
                            category_name = filter_data.get("name")
                            if category_name:
                                categories.append(category_name)
                
                if categories:
                    description_parts.append("Categories: " + ", ".join(categories))
                
                # Build final description
                description = " | ".join(description_parts) if description_parts else None
                
                # Create hackathon dictionary
                hackathon = {
                    "name": name,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "registration_link": registration_link,
                    "source": "Unstop",
                    "image_url": None  # Not including images as requested
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
                    HackathonModel.source == "Unstop"
                ).first()
                
                if not existing:
                    db.add(db_hackathon)
                    db.commit()
                    hackathons.append(hackathon)
                
            except Exception as e:
                logger.error(f"Error processing hackathon data at index {index}: {str(e)}")
                continue
        
        logger.info(f"Fetched {len(all_hackathons_data)} hackathons total, saved {len(hackathons)} new hackathons")
        return hackathons
        
    except Exception as e:
        logger.error(f"Error fetching Unstop data: {str(e)}")
        return []
    
    finally:
        db.close() 
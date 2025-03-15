import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from app.db.database import SessionLocal
from app.models.hackathon import HackathonModel

logger = logging.getLogger(__name__)

def scrape_devfolio() -> List[Dict[str, Any]]:
    """
    Scrape hackathon data from Devfolio.
    Since Devfolio uses JavaScript to render content, we need to use Selenium.
    
    Returns:
        List of hackathon dictionaries with scraped data.
    """
    driver = None
    try:
        # Create a database session
        db = SessionLocal()
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Set up Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # URL for Devfolio hackathons
        url = "https://devfolio.co/hackathons"
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".hackathon-card"))
        )
        
        # Scroll down to load more hackathons (if needed)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for page to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Find hackathon listings
        hackathon_cards = soup.select(".hackathon-card")
        
        hackathons = []
        
        for card in hackathon_cards:
            try:
                # Extract data from each card
                name_elem = card.select_one(".hackathon-name")
                name = name_elem.text.strip() if name_elem else "Unknown Hackathon"
                
                link_elem = card.select_one("a.hackathon-link")
                registration_link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                location_elem = card.select_one(".hackathon-location")
                location = location_elem.text.strip() if location_elem else None
                
                date_elem = card.select_one(".hackathon-date")
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
                
                image_elem = card.select_one("img.hackathon-image")
                image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
                
                # Create hackathon dictionary
                hackathon = {
                    "name": name,
                    "description": None,  # Would need to visit the detail page to get this
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "registration_link": registration_link,
                    "source": "Devfolio",
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
                    HackathonModel.source == "Devfolio"
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
        logger.error(f"Error scraping Devfolio: {str(e)}")
        return []
    
    finally:
        if driver:
            driver.quit()
        db.close() 
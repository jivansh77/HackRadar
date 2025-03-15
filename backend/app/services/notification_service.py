import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Path to Firebase service account key file
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")

# Initialize Firebase Admin SDK
try:
    if os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    else:
        logger.warning(f"Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}. Notifications will not work.")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin SDK: {str(e)}")

def send_notification(title: str, body: str, topic: str = "new_hackathons"):
    """
    Send a notification to all users subscribed to a topic.
    
    Args:
        title: Notification title
        body: Notification body
        topic: Topic to send notification to (default: "new_hackathons")
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not firebase_admin._apps:
            logger.warning("Firebase Admin SDK not initialized. Cannot send notification.")
            return False
        
        # Create message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )
        
        # Send message
        response = messaging.send(message)
        logger.info(f"Notification sent successfully: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

def notify_new_hackathons(hackathons: List[Dict[str, Any]]):
    """
    Send notifications for new hackathons.
    
    Args:
        hackathons: List of new hackathon dictionaries
    """
    if not hackathons:
        return
    
    # Send a notification for each new hackathon
    for hackathon in hackathons:
        title = f"New Hackathon: {hackathon['name']}"
        body = f"A new hackathon has been added from {hackathon['source']}."
        if hackathon.get('location'):
            body += f" Location: {hackathon['location']}."
        
        send_notification(title, body)
    
    # Send a summary notification if there are multiple hackathons
    if len(hackathons) > 1:
        title = f"{len(hackathons)} New Hackathons Added"
        body = f"Check out {len(hackathons)} new hackathons that were just added!"
        send_notification(title, body) 
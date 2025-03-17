import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
import base64
import json
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Initialize Firebase with credentials from environment variables
def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials from environment variables."""
    try:
        # First, check for base64 encoded credentials
        firebase_credentials_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
        if firebase_credentials_base64:
            logger.info("Found base64 encoded Firebase credentials in environment variables")
            try:
                # Decode base64 string to bytes
                firebase_credentials_json = base64.b64decode(firebase_credentials_base64)
                
                # Create credentials directory if it doesn't exist
                credentials_dir = Path("./credentials")
                credentials_dir.mkdir(exist_ok=True)
                
                # Write credentials to file
                credentials_path = credentials_dir / "firebase-credentials.json"
                with open(credentials_path, "wb") as f:
                    f.write(firebase_credentials_json)
                
                # Initialize Firebase with the created file
                cred = credentials.Certificate(str(credentials_path))
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully with base64 credentials")
                return True
            except Exception as e:
                logger.error(f"Error initializing Firebase with base64 credentials: {str(e)}")
        
        # Fall back to direct file path method
        firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
        if os.path.exists(firebase_credentials_path):
            cred = credentials.Certificate(firebase_credentials_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully with credentials file")
            return True
        else:
            logger.warning(f"Firebase credentials file not found at {firebase_credentials_path}. Notifications will not work.")
            return False
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {str(e)}")
        return False

# Initialize Firebase on module import
try:
    initialize_firebase()
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")

def send_notification(title: str, body: str, topic: str = "new_hackathons", data: Dict[str, str] = None):
    """
    Send a notification to all users subscribed to a topic.
    
    Args:
        title: Notification title
        body: Notification body
        topic: Topic to send notification to (default: "new_hackathons")
        data: Additional data to send with the notification
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not firebase_admin._apps:
            logger.warning("Firebase Admin SDK not initialized. Cannot send notification.")
            return False
        
        # Create notification
        notification = messaging.Notification(
            title=title,
            body=body,
        )
        
        # Create Android specific notification config
        android_config = messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                icon='notification_icon',
                color='#4CAF50',
                sound='default'
            ),
        )
        
        # Create APNS (Apple) specific config
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=title,
                        body=body,
                    ),
                    sound='default',
                    badge=1,
                ),
            ),
        )
        
        # Create web specific config - without the problematic link option
        webpush_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                icon='/logo2.png',
            ),
            # Removed the fcm_options with link that required HTTPS
        )
        
        # Create message with all configs
        message = messaging.Message(
            notification=notification,
            android=android_config,
            apns=apns_config,
            webpush=webpush_config,
            data=data or {},
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
    Send notifications for new hackathons in Mumbai.
    
    Args:
        hackathons: List of new hackathon dictionaries
    """
    if not hackathons:
        return
    
    # Filter hackathons to only include those in Mumbai
    mumbai_hackathons = [h for h in hackathons if h.get('location') and 'Mumbai' in h.get('location')]
    
    if not mumbai_hackathons:
        logger.info("No Mumbai hackathons to send notifications for.")
        return
    
    # Send a notification for each new Mumbai hackathon
    for hackathon in mumbai_hackathons:
        title = f"New Mumbai Hackathon: {hackathon['name']}"
        body = f"A new hackathon in Mumbai has been added from {hackathon['source']}."
        data = {
            "hackathon_id": str(hackathon.get('id', '')),
            "source": hackathon.get('source', ''),
            "url": hackathon.get('url', ''),
        }
        
        send_notification(title, body, "mumbai_hackathons", data)
    
    # Send a summary notification if there are multiple Mumbai hackathons
    if len(mumbai_hackathons) > 1:
        title = f"{len(mumbai_hackathons)} New Mumbai Hackathons Added"
        body = f"Check out {len(mumbai_hackathons)} new hackathons in Mumbai that were just added!"
        data = {
            "count": str(len(mumbai_hackathons)),
            "type": "summary"
        }
        send_notification(title, body, "mumbai_hackathons", data) 
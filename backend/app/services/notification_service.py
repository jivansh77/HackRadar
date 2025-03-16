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
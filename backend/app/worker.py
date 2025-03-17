from celery import Celery
import os
import logging
from ssl import CERT_NONE, CERT_REQUIRED
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - set to INFO level to reduce verbosity
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduce other loggers' verbosity
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)

# Redis URL from environment variable or default
REDIS_URL = os.getenv("REDIS_URL")

# Log the Redis URL being used (hide password) - only when starting up
if os.environ.get("SHOW_STARTUP_LOGS", "true").lower() == "true":
    logger.info(f"Initializing Celery with Redis: {REDIS_URL.replace(':', ':**', 1) if REDIS_URL else 'None'}")

# For Upstash Redis with TLS
broker_ssl_options = None
if REDIS_URL and 'upstash.io' in REDIS_URL:
    if os.environ.get("SHOW_STARTUP_LOGS", "true").lower() == "true":
        logger.info("Setting up Upstash Redis SSL configuration")
    # For Upstash, use proper certificate validation
    broker_ssl_options = {
        'ssl_cert_reqs': CERT_REQUIRED,
        'ssl_ca_certs': None,  # Let the system use the default CA certificates
    }
    
    # Try to use system CA certificates if available
    system_ca_paths = [
        '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
        '/etc/pki/tls/certs/ca-bundle.crt',    # RHEL/CentOS
        '/etc/ssl/ca-bundle.pem',              # OpenSUSE
        '/usr/local/etc/openssl/cert.pem',     # macOS Homebrew
        '/etc/ssl/cert.pem',                   # macOS/Alpine
    ]
    
    for path in system_ca_paths:
        if os.path.exists(path):
            broker_ssl_options['ssl_ca_certs'] = path
            if os.environ.get("SHOW_STARTUP_LOGS", "true").lower() == "true":
                logger.info(f"Using CA certificates from: {path}")
            break
    
    if broker_ssl_options['ssl_ca_certs'] is None:
        logger.warning("Could not find system CA certificates. Will rely on default behavior.")

# Create Celery app - explicitly set broker and specify backend as Redis
celery_app = Celery(
    "hackathon_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure Celery
celery_config = {
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'worker_hijack_root_logger': False,  # Don't hijack the root logger
    'worker_redirect_stdouts': False,    # Don't redirect stdout/stderr
    # Prevent beat from restarting processes
    'beat_max_loop_interval': 3600,      # 1 hour max interval instead of 5 minutes
    'beat_scheduler': 'celery.beat.PersistentScheduler',
    # Schedule periodic tasks
    'beat_schedule': {
        'scrape-hackathons-every-24-hours': {
            'task': 'app.services.hackathon_service.scrape_all_sources',
            'schedule': 86400.0,  # Every 24 hours
        },
    },
    # Important: include modules with tasks to ensure they're found
    'imports': [
        'app.services.hackathon_service',
    ],
}

# Add SSL options if using Upstash Redis
if broker_ssl_options:
    celery_config['broker_use_ssl'] = broker_ssl_options
    celery_config['redis_backend_use_ssl'] = broker_ssl_options

celery_app.conf.update(**celery_config)

# Only log configuration during startup if requested
if os.environ.get("SHOW_STARTUP_LOGS", "true").lower() == "true":
    logger.info(f"Celery broker configured")
    logger.info(f"Celery beat schedule configured for scraping every 24 hours")

# Import tasks AFTER creating Celery app to avoid circular imports
# Force import the tasks to ensure they're registered
import app.services.hackathon_service

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.start() 
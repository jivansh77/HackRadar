from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
import os
import logging
from app.services.hackathon_service import check_and_run_scraping_if_needed

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HackRadar API",
    description="API for aggregating hackathon data from multiple platforms",
    version="0.1.0",
)

# Get the environment
ENV = os.getenv("ENV", "dev")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Define allowed origins based on environment
allowed_origins = [
    "http://localhost:3000",                   # Local development
    "https://hack-radar.vercel.app",            # Production Vercel deployment
    "https://hack-radar-git-main-jivansh77s-projects.vercel.app",    # Alternative URL
    "https://www.hackradar.app",               # Custom domain if used
]

# Configure CORS with improved settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the HackRadar API",
        "docs": "/docs",
        "environment": ENV,
        "allowed_origins": allowed_origins,
    }

# Add startup event to check for scraping tasks
@app.on_event("startup")
async def startup_event():
    """
    Runs when the FastAPI app starts up.
    Check if we need to run the scraping task and run it if needed.
    """
    logger.info("Checking if hackathon scraping is needed on startup...")
    task_id = check_and_run_scraping_if_needed()
    if task_id:
        logger.info(f"Scraping task started with ID: {task_id}")
    else:
        logger.info("No scraping needed at startup")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
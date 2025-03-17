from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
import os

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
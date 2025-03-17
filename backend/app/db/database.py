from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable or default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine with SSL parameters for cloud databases like Neon
if 'neon.tech' in DATABASE_URL:
    # Strip the ?sslmode=require parameter if present
    if '?sslmode=require' in DATABASE_URL:
        base_url = DATABASE_URL.replace('?sslmode=require', '')
    else:
        base_url = DATABASE_URL
        
    # Create engine with SSL parameters - Neon doesn't support search_path in connect_args
    engine = create_engine(
        base_url,
        connect_args={"sslmode": "require"},
        echo=True  # Enable SQL query logging for debugging
    )
else:
    # Local database connection
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
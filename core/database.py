from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Validate DATABASE_URL at startup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Check if we're in development mode
    is_dev = os.environ.get("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]
    if is_dev:
        print("⚠️  WARNING: Using default SQLite database for development")
        DATABASE_URL = "sqlite:///./voice_coach.db"
    else:
        raise RuntimeError(
            "DATABASE_URL environment variable is required for production. "
            "Example: postgresql://user:password@localhost/dbname"
        )

# Fix for Render PostgreSQL URLs (they use postgres:// but SQLAlchemy needs postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with production-ready settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    # PostgreSQL/MySQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Max overflow connections
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False  # Set to True for SQL debugging
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
Centralized configuration management
"""
import os
import secrets
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
    IS_DEVELOPMENT = ENVIRONMENT in ["development", "dev", "local"]
    IS_PRODUCTION = ENVIRONMENT == "production"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if IS_DEVELOPMENT:
            print("⚠️  WARNING: Using generated SECRET_KEY for development")
            SECRET_KEY = "dev-" + secrets.token_urlsafe(32)
        else:
            raise RuntimeError(
                "SECRET_KEY is required in production. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        if IS_DEVELOPMENT:
            print("⚠️  WARNING: Using SQLite for development")
            DATABASE_URL = "sqlite:///./voice_coach.db"
        else:
            raise RuntimeError("DATABASE_URL is required in production")
    
    # CORS
    ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "")
    if IS_DEVELOPMENT:
        ALLOWED_ORIGINS = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
    elif not ALLOWED_ORIGINS_STR:
        raise RuntimeError("ALLOWED_ORIGINS is required in production")
    else:
        ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",")]
    
    # JWT
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL")  # For production rate limiting
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY and not IS_DEVELOPMENT:
        print("⚠️  WARNING: OPENAI_API_KEY not set")
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY and not IS_DEVELOPMENT:
        print("⚠️  WARNING: ELEVENLABS_API_KEY not set")
    
    # RabbitMQ
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    
    # Feature Flags
    ENABLE_SERVER_TTS = os.getenv("ENABLE_SERVER_TTS", "true").lower() == "true"
    ENABLE_VAD = os.getenv("ENABLE_VAD", "true").lower() == "true"
    ENABLE_AUGMENTATION = os.getenv("ENABLE_AUGMENTATION", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        if cls.IS_PRODUCTION:
            if not cls.SECRET_KEY or cls.SECRET_KEY.startswith("dev-"):
                errors.append("SECRET_KEY must be set for production")
            
            if not cls.DATABASE_URL or cls.DATABASE_URL.startswith("sqlite"):
                errors.append("Production database (PostgreSQL/MySQL) required")
            
            if not cls.ALLOWED_ORIGINS or cls.ALLOWED_ORIGINS == [""]:
                errors.append("ALLOWED_ORIGINS must be set for production")
        
        if errors:
            raise RuntimeError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print configuration (safe for logging)"""
        print("\n" + "="*60)
        print("Configuration")
        print("="*60)
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Database: {cls.DATABASE_URL.split('@')[-1] if '@' in cls.DATABASE_URL else 'SQLite'}")
        print(f"CORS Origins: {len(cls.ALLOWED_ORIGINS)} configured")
        print(f"Rate Limiting: {'Enabled' if cls.RATE_LIMIT_ENABLED else 'Disabled'}")
        print(f"Redis: {'Configured' if cls.REDIS_URL else 'Not configured'}")
        print(f"OpenAI: {'Configured' if cls.OPENAI_API_KEY else 'Not configured'}")
        print(f"ElevenLabs: {'Configured' if cls.ELEVENLABS_API_KEY else 'Not configured'}")
        print("="*60 + "\n")


# Validate configuration on import
try:
    Config.validate()
    if Config.IS_DEVELOPMENT:
        Config.print_config()
except RuntimeError as e:
    print(f"\n❌ Configuration Error:\n{e}\n")
    raise

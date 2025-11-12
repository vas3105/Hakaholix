"""
Configuration manager for Kerala Travel Assistant
Handles all environment variables and API keys
"""

import os
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(_name_)

# Load environment variables from .env file
load_dotenv()

class Config:
    """Central configuration class for all settings"""
    
    # ============================================
    # LLM Configuration
    # ============================================
    LLM_MODEL_NAME: str = os.getenv(
        "LLM_MODEL_NAME",
        "meta-llama/Llama-3.2-1B"
    )
    
    # ============================================
    # API Keys
    # ============================================

    # ============================================
    # Hugging Face / LLM API Access
    # ============================================
    HF_TOKEN: str = os.getenv(
        "HF_TOKEN",
        "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"  # optional default (empty if using local Granite)
    )


    WEATHER_API_KEY: str = os.getenv(
        "WEATHER_API_KEY",
        "c540902e3fac5160482f15da30f46ea3"
    )
    
    SKYSCANNER_API_KEY: str = os.getenv(
        "SKYSCANNER_API_KEY",
        "afe62c8c024412fab44fd7dd57cab65c"
    )
    
    # ============================================
    # API Endpoints
    # ============================================
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    WEATHER_FORECAST_URL: str = "https://api.openweathermap.org/data/2.5/forecast"
    SKYSCANNER_API_URL: str = "https://partners.api.skyscanner.net/apiservices"
    
    # ============================================
    # Database Configuration
    # ============================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./kerala_travel.db"
    )
    
    # ============================================
    # RAG Configuration
    # ============================================
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        "./data/chroma_db"
    )
    
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )
    
    # ============================================
    # Application Settings
    # ============================================
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))
    
    # ============================================
    # Rate Limiting
    # ============================================
    WEATHER_API_RATE_LIMIT: int = int(os.getenv("WEATHER_API_RATE_LIMIT", "60"))
    SKYSCANNER_API_RATE_LIMIT: int = int(os.getenv("SKYSCANNER_API_RATE_LIMIT", "10"))
    
    # ============================================
    # Request Timeouts (seconds)
    # ============================================
    API_REQUEST_TIMEOUT: int = 5
    LLM_GENERATION_TIMEOUT: int = 30
    
    # ============================================
    # Default Values
    # ============================================
    DEFAULT_LOCATION: str = "Kerala"
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_COUNTRY_CODE: str = "IN"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        errors = []
        
        # Check critical API keys
        if not cls.WEATHER_API_KEY or cls.WEATHER_API_KEY == "your_weather_api_key_here":
            logger.warning("⚠ WEATHER_API_KEY not set. Weather features will be limited.")
        
        if not cls.SKYSCANNER_API_KEY or cls.SKYSCANNER_API_KEY == "your_skyscanner_api_key_here":
            logger.warning("⚠ SKYSCANNER_API_KEY not set. Flight search will be disabled.")
        
        # Check model name
        if not cls.LLM_MODEL_NAME:
            errors.append("LLM_MODEL_NAME is required")
        
        if errors:
            for error in errors:
                logger.error(f"❌ Configuration error: {error}")
            return False
        
        logger.info("✅ Configuration validated successfully")
        return True
    
    @classmethod
    def get_info(cls) -> dict:
        """Get configuration info (safe for logging)"""
        return {
            "llm_model": cls.LLM_MODEL_NAME,
            "weather_api_configured": bool(cls.WEATHER_API_KEY),
            "skyscanner_api_configured": bool(cls.SKYSCANNER_API_KEY),
            "database_url": cls.DATABASE_URL.split("://")[0] + "://*",
            "debug_mode": cls.DEBUG,
            "log_level": cls.LOG_LEVEL,
            "embedding_model": cls.EMBEDDING_MODEL
        }


# ============================================
# Helper Functions
# ============================================

def get_weather_api_key() -> Optional[str]:
    """Get Weather API key"""
    return Config.WEATHER_API_KEY if Config.WEATHER_API_KEY else None

def get_skyscanner_api_key() -> Optional[str]:
    """Get Skyscanner API key"""
    return Config.SKYSCANNER_API_KEY if Config.SKYSCANNER_API_KEY else None

def is_weather_api_available() -> bool:
    """Check if Weather API is available"""
    key = get_weather_api_key()
    return key is not None and key != "your_weather_api_key_here"

def is_skyscanner_api_available() -> bool:
    """Check if Skyscanner API is available"""
    key = get_skyscanner_api_key()
    return key is not None and key != "your_skyscanner_api_key_here"


# Validate configuration on import
if _name_ != "_main_":
    Config.validate()

# ✅ Create global settings instance for easy access
settings = Config()

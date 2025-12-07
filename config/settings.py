"""
Configuration Settings
Application configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Agent Configuration
    AGENT_TIMEOUT: int = 300  # seconds
    MAX_CONCURRENT_TASKS: int = 10
    
    # Security
    API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


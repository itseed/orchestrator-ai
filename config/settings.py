"""
Configuration Settings
Application configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Orchestrator AI Agent"
    API_VERSION: str = "1.0.0"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None  # Override with full URL if provided
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Agent Configuration
    AGENT_TIMEOUT: int = 300  # seconds
    MAX_CONCURRENT_TASKS: int = 10
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    # Security
    API_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # LLM Configuration (for agents)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL"""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create singleton instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Default export
settings = get_settings()


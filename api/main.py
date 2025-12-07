"""
FastAPI Application
REST API for orchestrator
"""

from fastapi import FastAPI

from config import settings
from monitoring import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Orchestrator AI Agent API - Multi-agent coordination system",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Initialize logging
logger.info("Starting Orchestrator AI Agent API", version=settings.API_VERSION)

# TODO: Implement API routes
# See DEVELOPMENT_PLAN.md for implementation details

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


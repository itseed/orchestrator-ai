"""
FastAPI Application
REST API for orchestrator
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import settings
from monitoring import get_logger
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from state.store import StateStore
from api import routes

logger = get_logger(__name__)

# Global orchestrator instance
_orchestrator: OrchestratorEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global _orchestrator
    
    # Startup
    logger.info("Starting Orchestrator AI Agent API", version=settings.API_VERSION)
    
    # Initialize orchestrator
    registry = AgentRegistry()
    state_store = StateStore()
    _orchestrator = OrchestratorEngine(registry=registry, state_store=state_store)
    
    # Set orchestrator in routes
    routes.set_orchestrator(_orchestrator)
    
    logger.info("Orchestrator engine initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestrator AI Agent API")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Orchestrator AI Agent API - Multi-agent coordination system",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan
)

# Include routers
app.include_router(routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


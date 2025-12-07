"""
FastAPI Application
REST API for orchestrator
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import settings
from monitoring import get_logger, start_metrics_server
from monitoring.health import SystemHealthChecker, HealthStatus
from monitoring.dashboard import MonitoringDashboard, create_dashboard_routes
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from state.store import StateStore
from database.base import init_database, create_tables
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
    
    # Initialize database
    try:
        init_database()
        if settings.DATABASE_URL:  # Only create tables if database is configured
            create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database initialization failed, continuing without persistence", error=str(e))
    
    # Initialize orchestrator
    registry = AgentRegistry()
    state_store = StateStore()
    _orchestrator = OrchestratorEngine(registry=registry, state_store=state_store)
    
    # Set orchestrator in routes
    routes.set_orchestrator(_orchestrator)
    
    # Initialize health checker
    health_checker = SystemHealthChecker(
        registry=registry,
        state_store=state_store,
        message_broker=None  # Could add message broker later
    )
    routes.set_health_checker(health_checker)
    
    # Start metrics server if enabled
    if settings.ENABLE_METRICS:
        try:
            start_metrics_server(settings.METRICS_PORT)
            logger.info("Metrics server started", port=settings.METRICS_PORT)
        except Exception as e:
            logger.warning("Failed to start metrics server", error=str(e))
    
    # Initialize dashboard
    dashboard = MonitoringDashboard(health_checker=health_checker)
    create_dashboard_routes(app, dashboard)
    
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


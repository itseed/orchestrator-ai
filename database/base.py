"""
Database Base Configuration
SQLAlchemy setup and database connection
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
from monitoring import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Base class for models
Base = declarative_base()

# Database URL
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./orchestrator.db"
ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://").replace("postgresql://", "postgresql+asyncpg://")

# Sync engine and session
engine = None
SessionLocal = None

# Async engine and session
async_engine = None
AsyncSessionLocal = None


def init_database():
    """Initialize database connection"""
    global engine, SessionLocal, async_engine, AsyncSessionLocal
    
    if DATABASE_URL.startswith("sqlite"):
        # SQLite configuration
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.is_development
        )
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=settings.is_development
        )
    else:
        # PostgreSQL configuration with connection pooling
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=settings.is_development
        )
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.is_development
        )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    logger.info("Database initialized", database_url=DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session (sync)
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    
    Yields:
        Async database session
    """
    if AsyncSessionLocal is None:
        init_database()
    
    async with AsyncSessionLocal() as session:
        yield session


def create_tables():
    """Create all database tables"""
    if engine is None:
        init_database()
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


# Initialize on module import
init_database()


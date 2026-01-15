"""
Database Connection Module
PostgreSQL connection using Cloud SQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create base class for models
Base = declarative_base()

# Engine and session factory
engine = None
async_session_factory = None


async def init_db():
    """Initialize database connection"""
    global engine, async_session_factory
    
    try:
        # Create async engine
        engine = create_async_engine(
            settings.database_url,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        
        # Create session factory
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database connection established")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        # Don't raise - allow app to run in degraded mode without DB
        logger.warning("Running without database - some features may be unavailable")


async def close_db():
    """Close database connection"""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


async def get_session() -> AsyncSession:
    """Get database session"""
    if async_session_factory is None:
        raise Exception("Database not initialized")
    
    async with async_session_factory() as session:
        yield session


class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def health_check() -> bool:
        """Check database health"""
        if engine is None:
            return False
        
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except:
            return False
    
    @staticmethod
    async def get_table_stats():
        """Get basic table statistics"""
        if async_session_factory is None:
            return {}
        
        async with async_session_factory() as session:
            try:
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_live_tup as row_count
                    FROM pg_stat_user_tables
                """))
                
                stats = {}
                for row in result:
                    stats[row.tablename] = row.row_count
                
                return stats
            except:
                return {}

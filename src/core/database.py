"""
Database connection management for ManipulatorAI.

This module handles the setup, connection, and session management for
both PostgreSQL (via SQLAlchemy/SQLModel) and MongoDB (via Motor).
It provides dependency-injectable session getters for use in API endpoints.
"""

import logging
from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.database import Database as MongoDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# PostgreSQL / SQLModel Configuration
# =============================================================================

# Create an async engine instance. This is the core interface to the database.
# The engine is configured with the database URL from our settings.
# `echo=True` is useful for development to see the generated SQL statements.
# `pool_pre_ping=True` checks connection validity before use.
async_engine = create_async_engine(
    settings.postgres_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
)

# Create a sessionmaker factory. This factory will create new AsyncSession
# objects when called. We bind it to our engine.
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# MongoDB Configuration
# =============================================================================


class MongoDatabaseManager:
    """A manager class for the MongoDB client and database instances."""

    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None


mongo_manager = MongoDatabaseManager()


async def connect_to_mongo() -> None:
    """
    Connect to MongoDB, create a client, and get the database.
    This should be called during application startup.
    """
    logger.info("Connecting to MongoDB...")
    try:
        mongo_manager.client = AsyncIOMotorClient(
            settings.mongo_url,
            maxPoolSize=settings.mongo_max_pool_size,
            minPoolSize=settings.mongo_min_pool_size,
            uuidRepresentation="standard",  # Recommended for modern applications
        )
        mongo_manager.database = mongo_manager.client[settings.mongo_db_name]
        # The ismaster command is cheap and does not require auth.
        await mongo_manager.client.admin.command("ismaster")
        logger.info("MongoDB connection successful.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close the MongoDB connection.
    This should be called during application shutdown.
    """
    if mongo_manager.client:
        logger.info("Closing MongoDB connection...")
        mongo_manager.client.close()
        logger.info("MongoDB connection closed.")


def get_mongo_db() -> MongoDatabase:
    """
    FastAPI dependency to get a MongoDB database instance.

    Raises:
        RuntimeError: If the database connection has not been established.

    Returns:
        The application's `AsyncIOMotorDatabase` instance.
    """
    if mongo_manager.database is None:
        # This state should not be reachable if `connect_to_mongo` is
        # called successfully on startup.
        raise RuntimeError("MongoDB connection has not been established.")
    return mongo_manager.database


# =============================================================================
# Database Initialization
# =============================================================================
async def init_db() -> None:
    """
    Initialize the PostgreSQL database.

    This function creates all tables defined by SQLModel metadata.
    It should be called during application startup.
    """
    async with async_engine.begin() as conn:
        logger.info("Initializing PostgreSQL database...")
        # The following line will create tables based on SQLModel metadata.
        # In a production environment with Alembic, you might comment this out
        # and rely solely on migrations.
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("PostgreSQL database initialized successfully.")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.

    This is a generator that yields a single SQLAlchemy `AsyncSession`
    and ensures it's closed correctly after the request is handled.

    Yields:
        An `AsyncSession` object for database operations.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

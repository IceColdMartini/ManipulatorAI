import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from sqlmodel import SQLModel

# Add your model's MetaData object here
# for 'autogenerate' support.
# Alembic needs to know about the models to generate migrations.
from src.core.config import get_settings
from src.models.product import Product  # Import your models here

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Get application settings
settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    if not settings.postgres_url:
        raise ValueError("POSTGRES_URL must be set for migrations.")
    context.configure(
        url=settings.postgres_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper function to run migrations."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    This is adapted for an asyncio-compatible engine.
    """
    if not settings.postgres_url:
        raise ValueError("POSTGRES_URL must be set for migrations.")

    # Ensure the URL uses the asyncpg driver
    db_url = settings.postgres_url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Create a new section in the config for the async engine
    # and set the URL from our settings.
    alembic_config = config.get_section(config.config_ini_section)
    if alembic_config is None:
        alembic_config = {}
    alembic_config["sqlalchemy.url"] = db_url

    connectable = async_engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

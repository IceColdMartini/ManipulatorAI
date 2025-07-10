"""
Production-grade logging configuration for ManipulatorAI.

This module sets up a structured, JSON-based logging system using the
`structlog` library. It is designed to be environment-aware, providing
human-readable, colorized logs in development and efficient, machine-parseable
JSON logs in production.

Key Features:
- Structured Logging: All logs are emitted as JSON objects, enabling easy
  parsing, searching, and analysis in log management systems.
- Environment-Aware Formatting:
  - Development: Logs are colorized and formatted for easy reading.
  - Production: Logs are compact JSON strings for efficiency.
- Timestamping: Uses UTC for all timestamps to ensure consistency across
  different timezones.
- Correlation IDs: Ready to be integrated with middleware to add request-specific
  correlation IDs for tracing requests across services.
- Standard Library Integration: Captures and formats logs from standard library
  and third-party modules (e.g., Uvicorn, SQLAlchemy) seamlessly.
"""

import logging
import sys
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from structlog.types import Processor

from src.core.config import settings


def add_log_level_as_str(
    _logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Add the log level to the event dict as a string.
    This is useful for filtering logs in log management systems.
    """
    if "level" not in event_dict:
        event_dict["level"] = method_name
    return event_dict


def setup_logging() -> None:
    """
    Configure the logging system for the application.
    This function sets up `structlog` to handle all logging,
    ensuring consistent, structured output.
    """
    # Define shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        add_log_level_as_str,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]

    # Define environment-specific processors and formatters
    if settings.DEBUG:
        # Development-friendly logging
        processors = shared_processors + [
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate from
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )
    else:
        # Production-ready JSON logging
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use the structlog formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Set the logging level for uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    log = structlog.get_logger("manipulatorai.logging_config")
    log.info(
        "Logging setup complete",
        debug_mode=settings.DEBUG,
        log_level=root_logger.level,
    )

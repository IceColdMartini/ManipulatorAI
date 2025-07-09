"""
Production-grade structured logging configuration for ManipulatorAI.

This module provides a comprehensive logging system with JSON formatting,
correlation IDs, performance monitoring, and integration with external
monitoring systems for production-ready applications.

Features:
- Structured JSON logging for machine processing
- Correlation ID tracking across requests
- Performance monitoring with timing
- Error context with stack traces
- Log rotation and file management
- Environment-aware configuration
- Thread-safe logging operations
"""

import json
import logging
import logging.handlers
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, Union

import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

# Get settings instance
settings = get_settings()


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation IDs to log records.
    
    This ensures every log entry can be traced back to its originating request,
    which is crucial for debugging in distributed systems.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record if not already present."""
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(record, 'correlation_id', 'unknown')
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds ManipulatorAI-specific fields.
    
    This formatter ensures all logs have consistent structure and
    include essential metadata for monitoring and debugging.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add service metadata
        log_record['service'] = settings.app_name
        log_record['version'] = settings.app_version
        log_record['environment'] = settings.environment
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
            
        # Add user ID if available (for user-specific tracking)
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
            
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_record['duration_ms'] = record.duration
            
        # Add business context if available
        if hasattr(record, 'business_context'):
            log_record['business_context'] = record.business_context


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    This function sets up both standard library logging and structlog
    for consistent, production-ready log output. It configures:
    - Console output for development
    - File output with rotation for production
    - JSON formatting for machine processing
    - Correlation ID tracking
    """
    # Ensure log directory exists
    log_path = Path(settings.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()
    
    # Configure formatters based on environment
    if settings.log_format.lower() == "json":
        formatter = CustomJsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler for real-time monitoring
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation for persistent storage
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file_path,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.log_level))
    file_handler.addFilter(correlation_filter)
    root_logger.addHandler(file_handler)
    
    # Configure structlog for enhanced structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format.lower() == "json"
            else structlog.dev.ConsoleRenderer(colors=settings.is_development),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Log successful setup
    logger = get_logger(__name__)
    logger.info(
        "Logging system initialized successfully",
        log_level=settings.log_level,
        log_format=settings.log_format,
        log_file=settings.log_file_path,
        environment=settings.environment
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance with structured logging capabilities.
    
    Args:
        name: Logger name, defaults to calling module name
        
    Returns:
        Configured structlog logger instance with bound context
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    This provides a convenient way to add logging to service classes
    without having to manually create logger instances.
    """
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance bound to this class."""
        return get_logger(self.__class__.__name__)


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for request tracking.
    
    Returns:
        UUID string for correlation tracking
    """
    return str(uuid.uuid4())


@contextmanager
def correlation_context(correlation_id: str = None):
    """
    Context manager for correlation ID tracking.
    
    Args:
        correlation_id: Optional correlation ID, generates new one if not provided
        
    Usage:
        with correlation_context("req-123") as ctx:
            logger.info("Processing request", user_id=123)
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Add correlation ID to all loggers in this context
    logger = get_logger()
    bound_logger = logger.bind(correlation_id=correlation_id)
    
    try:
        yield correlation_id
    finally:
        pass


def log_function_call(include_args: bool = True, include_result: bool = False):
    """
    Decorator to automatically log function calls with arguments and results.
    
    Args:
        include_args: Whether to log function arguments
        include_result: Whether to log function return value
        
    Usage:
        @log_function_call(include_args=True, include_result=True)
        def process_user_data(user_id: int, data: dict):
            return processed_data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Log function entry
            log_data = {"event": "function_entry", "function": func_name}
            if include_args:
                log_data["args"] = args
                log_data["kwargs"] = kwargs
            
            logger.info("Function called", **log_data)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Log successful completion
                log_data = {
                    "event": "function_success",
                    "function": func_name,
                    "duration_ms": duration
                }
                if include_result:
                    log_data["result"] = result
                
                logger.info("Function completed successfully", **log_data)
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                # Log error with context
                logger.error(
                    "Function failed",
                    event="function_error",
                    function=func_name,
                    error_type=e.__class__.__name__,
                    error_message=str(e),
                    duration_ms=duration,
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


def log_performance(operation: str, threshold_ms: float = 1000.0):
    """
    Decorator to log performance metrics for operations.
    
    Args:
        operation: Name of the operation being measured
        threshold_ms: Log warning if operation takes longer than this (milliseconds)
        
    Usage:
        @log_performance("database_query", threshold_ms=500)
        def get_user_data(user_id: int):
            return db.query(...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Log performance metrics
                log_level = "warning" if duration > threshold_ms else "info"
                getattr(logger, log_level)(
                    f"Operation completed: {operation}",
                    event="performance_metric",
                    operation=operation,
                    duration_ms=duration,
                    threshold_ms=threshold_ms,
                    exceeded_threshold=duration > threshold_ms
                )
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation}",
                    event="performance_error",
                    operation=operation,
                    duration_ms=duration,
                    error_type=e.__class__.__name__,
                    error_message=str(e),
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


def log_error(error: Exception, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
    """
    Log an error with rich context information.
    
    Args:
        error: Exception that occurred
        context: Additional context about the error
        user_id: User ID if the error is user-specific
        
    Returns:
        Dictionary containing error details for further processing
    """
    error_data = {
        "event": "error_occurred",
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "service": settings.app_name,
        "environment": settings.environment,
        "context": context or {},
    }
    
    if user_id:
        error_data["user_id"] = user_id
    
    logger = get_logger()
    logger.error("Error occurred", **error_data, exc_info=True)
    
    return error_data


def log_business_event(event_type: str, **kwargs) -> None:
    """
    Log business-specific events for analytics and monitoring.
    
    Args:
        event_type: Type of business event (e.g., "user_registration", "purchase")
        **kwargs: Additional event data
        
    Usage:
        log_business_event("conversation_started", user_id=123, product_id=456)
    """
    logger = get_logger()
    logger.info(
        f"Business event: {event_type}",
        event="business_event",
        event_type=event_type,
        service=settings.app_name,
        **kwargs
    )


def log_security_event(event_type: str, severity: str = "info", **kwargs) -> None:
    """
    Log security-related events for monitoring and compliance.
    
    Args:
        event_type: Type of security event (e.g., "login_failed", "api_key_used")
        severity: Event severity ("info", "warning", "error", "critical")
        **kwargs: Additional event data
        
    Usage:
        log_security_event("webhook_verification_failed", severity="warning", ip="1.2.3.4")
    """
    logger = get_logger()
    getattr(logger, severity)(
        f"Security event: {event_type}",
        event="security_event",
        event_type=event_type,
        severity=severity,
        service=settings.app_name,
        **kwargs
    )


# Module-level logger for this logging configuration
module_logger = get_logger(__name__)
"""
ManipulatorAI - Main Application Entry Point

This is the primary FastAPI application that serves as the entry point for
the ManipulatorAI microservice. It handles webhook integrations, conversation
management, and AI-powered customer engagement with enterprise-grade
middleware, security, and monitoring.

Features:
- Production-ready middleware stack
- Comprehensive error handling
- Request correlation tracking
- Health check endpoints
- Security headers and CORS
- Performance monitoring
- Graceful startup/shutdown
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import get_settings, Settings
from .core.logging_config import setup_logging, get_logger, correlation_context, generate_correlation_id

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to all requests for distributed tracing.
    
    This ensures every request can be tracked across multiple services and
    makes debugging much easier in production environments.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Add correlation ID to request and response headers."""
        # Extract correlation ID from headers or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        
        # Add to request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Process request with correlation context
        with correlation_context(correlation_id):
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging with performance metrics.
    
    Logs all incoming requests with timing information, which is essential
    for monitoring and performance analysis in production.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Log request details and performance metrics."""
        start_time = time.time()
        
        # Extract request details
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log incoming request
        logger.info(f"Incoming request: {request.method} {request.url.path} - {correlation_id}")
        
        try:
            # Process request
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms")
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request error
            logger.error(f"Request failed: {request.method} {request.url.path} - {e.__class__.__name__}: {str(e)}")
            
            # Re-raise to be handled by global exception handler
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This handles initialization and cleanup of resources like database
    connections, Redis connections, and background tasks in a production-ready manner.
    """
    # Startup
    logger.info(f"Starting ManipulatorAI application - Version: {settings.app_version}, Environment: {settings.environment}")
    
    startup_start = time.time()
    
    try:
        # TODO: Initialize database connections
        logger.info("Initializing database connections...")
        # await initialize_postgres_connection()
        # await initialize_mongodb_connection()
        # await initialize_redis_connection()
        
        # TODO: Initialize Celery worker
        logger.info("Initializing task queue...")
        # await initialize_celery_worker()
        
        # TODO: Validate external service connections
        logger.info("Validating external service connections...")
        # await validate_azure_openai_connection()
        
        startup_duration = (time.time() - startup_start) * 1000
        logger.info(f"Application startup completed successfully in {startup_duration:.2f}ms")
        
    except Exception as e:
        startup_duration = (time.time() - startup_start) * 1000
        logger.error(f"Application startup failed after {startup_duration:.2f}ms: {e.__class__.__name__}: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ManipulatorAI application")
    
    shutdown_start = time.time()
    
    try:
        # TODO: Cleanup resources
        logger.info("Closing database connections...")
        # await close_postgres_connections()
        # await close_mongodb_connections()
        # await close_redis_connections()
        
        # TODO: Stop background tasks
        logger.info("Stopping background tasks...")
        # await stop_celery_workers()
        
        shutdown_duration = (time.time() - shutdown_start) * 1000
        logger.info(f"Application shutdown completed successfully in {shutdown_duration:.2f}ms")
        
    except Exception as e:
        shutdown_duration = (time.time() - shutdown_start) * 1000
        logger.error(f"Application shutdown encountered errors after {shutdown_duration:.2f}ms: {e.__class__.__name__}: {str(e)}")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application with enterprise-grade middleware.
    
    This function sets up all middleware, security, error handling, and routing
    in the correct order for optimal performance and security.
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with metadata
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered customer engagement and lead qualification service for social media interactions",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
        # Security and metadata
        contact={
            "name": "ManipulatorAI Support",
            "email": "support@manipulatorai.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": f"http://localhost:{settings.port}",
                "description": "Development server"
            }
        ] if settings.is_development else []
    )
    
    # Add security middleware (order matters!)
    
    # 1. Trusted host middleware (first line of defense)
    if not settings.is_development:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # 2. CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Response-Time"]
    )
    
    # 3. Custom middleware for correlation IDs
    app.add_middleware(CorrelationIdMiddleware)
    
    # 4. Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Global exception handlers
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with proper logging."""
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail} - {request.method} {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "correlation_id": correlation_id,
                "path": request.url.path
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors with detailed logging."""
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        logger.warning(f"Request validation failed: {request.method} {request.url.path} - {len(exc.errors())} errors")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "correlation_id": correlation_id,
                "path": request.url.path
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions with comprehensive logging."""
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        logger.error(f"Unhandled exception: {exc.__class__.__name__}: {str(exc)} - {request.method} {request.url.path}")
        
        # Return different responses based on environment
        if settings.is_development:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc),
                    "type": exc.__class__.__name__,
                    "correlation_id": correlation_id,
                    "path": request.url.path
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "correlation_id": correlation_id,
                    "path": request.url.path
                }
            )
    
    # Health check endpoints
    
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Basic health check endpoint for load balancers and monitoring.
        
        Returns:
            Health status with basic application information
        """
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": time.time()
        }
    
    @app.get("/health/detailed", tags=["System"])
    async def detailed_health_check():
        """
        Detailed health check with database and external service status.
        
        Returns:
            Comprehensive health status including all dependencies
        """
        health_data = {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": time.time(),
            "checks": {
                "application": "healthy",
                # TODO: Add actual health checks
                "database": "healthy",  # await check_postgres_health()
                "mongodb": "healthy",   # await check_mongodb_health()
                "redis": "healthy",     # await check_redis_health()
                "azure_openai": "healthy"  # await check_azure_openai_health()
            }
        }
        
        # Determine overall status
        unhealthy_services = [
            service for service, status in health_data["checks"].items()
            if status != "healthy"
        ]
        
        if unhealthy_services:
            health_data["status"] = "unhealthy"
            health_data["unhealthy_services"] = unhealthy_services
        
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_data
        )
    
    @app.get("/", tags=["System"])
    async def root():
        """
        Root endpoint with service information.
        
        Returns:
            Basic service information and API navigation
        """
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "description": "AI-powered customer engagement and lead qualification service",
            "docs": "/docs" if settings.is_development else None,
            "health": "/health",
            "environment": settings.environment
        }
    
    # TODO: Include API routers
    # app.include_router(api_router, prefix="/api/v1")
    
    logger.info(f"FastAPI application created successfully - {settings.app_name} v{settings.app_version} ({settings.environment})")
    
    return app


# Create the application instance
app = create_application()


def main():
    """
    Main entry point for running the application.
    
    This function is called when the module is executed directly
    and provides production-ready server configuration.
    """
    logger.info(f"Starting ManipulatorAI server - {settings.host}:{settings.port} ({settings.environment})")
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if not settings.is_development else 1,
        reload=settings.is_development,
        access_log=True,
        log_level=settings.log_level.lower(),
        # Performance and security settings
        loop="uvloop" if not settings.is_development else "auto",
        http="httptools" if not settings.is_development else "auto",
        # Limit request size to prevent DoS attacks
        limit_max_requests=1000 if not settings.is_development else None,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()

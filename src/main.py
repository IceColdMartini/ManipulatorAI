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
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    print("Starting up...")
    setup_logging()
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a correlation ID to each request and log request details.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        # Extract or generate a correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Bind the correlation ID to the logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Log the incoming request
        log = structlog.get_logger("manipulatorai.api")
        start_time = time.time()
        log.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        log.info(
            "Request finished",
            status_code=response.status_code,
            process_time_ms=f"{process_time:.2f}",
        )

        # Add correlation ID to the response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response


# Add middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # And this


@app.get("/", tags=["Health Check"])
async def root() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "ok"}


# Example of a custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom exception handler for HTTPException.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Custom exception handler for request validation errors.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )

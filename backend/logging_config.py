"""
ClipGenius - Structured Logging Configuration
Configures structlog for JSON (production) or colored console (development) output
"""
import os
import sys
import logging
import structlog
from typing import Any


def get_environment() -> str:
    """Determine current environment from ENV variable"""
    return os.getenv("ENV", "development").lower()


def is_production() -> bool:
    """Check if running in production mode"""
    return get_environment() in ("production", "prod")


def configure_logging(json_logs: bool = None, log_level: str = None) -> None:
    """
    Configure structlog for the application.

    Args:
        json_logs: Force JSON output (True) or colored console (False).
                   If None, auto-detect based on ENV variable.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to DEBUG in development, INFO in production.
    """
    # Auto-detect settings if not provided
    if json_logs is None:
        json_logs = is_production()

    if log_level is None:
        log_level = "INFO" if is_production() else "DEBUG"

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Shared processors for all environments
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON output for log aggregation tools
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored, human-readable console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None, **initial_context: Any) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)
        **initial_context: Initial context variables to bind to the logger

    Returns:
        A structlog BoundLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing video", video_id="abc123", duration=120)

        # With initial context
        logger = get_logger(__name__, service="analyzer")
        logger.info("Starting analysis")  # Will include service="analyzer"
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


# Pre-configured loggers for common modules
def get_api_logger() -> structlog.BoundLogger:
    """Get logger for API routes"""
    return get_logger("clipgenius.api", component="api")


def get_service_logger(service_name: str) -> structlog.BoundLogger:
    """Get logger for a service module"""
    return get_logger(f"clipgenius.services.{service_name}", component="service", service=service_name)


def get_background_logger() -> structlog.BoundLogger:
    """Get logger for background tasks"""
    return get_logger("clipgenius.background", component="background")

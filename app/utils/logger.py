"""
Structured logging configuration for the CodeChef MCP Server.

IMPORTANT: For STDIO-based MCP servers, NEVER write to stdout.
All logging MUST go to stderr to avoid corrupting JSON-RPC messages.

Uses Python's built-in logging. The structlog dependency in requirements.txt
is available for users who want richer structured output, but the default
here is stdlib logging to avoid duplicate-line issues with uvicorn's
internal logging.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging that writes to stderr.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    _logger = logging.getLogger("codechef-mcp")
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers on reimport (uvicorn reload)
    if _logger.handlers:
        return _logger

    # Create stderr handler (NEVER use stdout for MCP servers)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Structured format with timestamps
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    # Prevent log propagation to root logger (avoids duplicate lines
    # when structlog or uvicorn also configures the root logger)
    _logger.propagate = False

    return _logger


# Global logger instance
logger = setup_logging()

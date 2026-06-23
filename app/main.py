"""
CodeChef MCP Server — HTTP Entrypoint (Streamable HTTP Transport)

This is the main entrypoint for running the server as an HTTP service.
Used for browser-based AI clients (Cursor, Claude Browser, ChatGPT, Gemini).

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

The MCP endpoint will be available at:
    http://localhost:8000/mcp
"""

from app.mcp_server import mcp

# Import all tool modules to trigger @mcp.tool() registration
# These imports are required even though they appear unused —
# the decorators register tools with the mcp instance on import
import app.tools.contest       # noqa: F401 — registers: open_contest, list_problems, get_problem, get_contest_progress
import app.tools.execution     # noqa: F401 — registers: run_code
import app.tools.solving       # noqa: F401 — registers: generate_tests, validate_complexity, evaluate_confidence
import app.tools.submission    # noqa: F401 — registers: submit_solution, get_submission_status, retry_solution, get_submission_history

from app.utils.logger import logger

# Create the Streamable HTTP ASGI app
# This exposes the MCP server over HTTP for browser-based clients
app = mcp.streamable_http_app()

# NOTE: Database initialization is handled by run_server.py BEFORE
# uvicorn imports this module. Do NOT call init_db() here — it causes
# RuntimeWarning when uvicorn's reload process re-imports the module
# inside an already-running event loop.

logger.info("CodeChef MCP Server initialized (HTTP transport)")
logger.info(
    "Tools registered: open_contest, list_problems, get_problem, "
    "get_contest_progress, run_code, generate_tests, validate_complexity, "
    "evaluate_confidence, submit_solution, get_submission_status, "
    "retry_solution, get_submission_history"
)

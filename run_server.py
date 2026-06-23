"""
CodeChef MCP Server — Unified Entrypoint

Supports both STDIO (for Claude Desktop / LLM agents) and
HTTP / Streamable HTTP (for Cursor, web clients, programmatic access).

Usage:
    # STDIO mode (default — for Claude Desktop / MCP clients):
    python run_server.py

    # HTTP mode (for Cursor / browser clients):
    python run_server.py --http
    python run_server.py --http --host 0.0.0.0 --port 8000

Configure in Claude Desktop:
    {
        "mcpServers": {
            "codechef": {
                "command": "python",
                "args": ["/path/to/MCP_Chef/run_server.py"]
            }
        }
    }

Configure in Cursor:
    {
        "mcpServers": {
            "codechef-mcp": {
                "url": "http://localhost:8000/mcp"
            }
        }
    }
"""

import argparse
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.mcp_server import mcp  # noqa: E402

# Import all tool modules to trigger @mcp.tool() registration
import app.tools.contest       # noqa: F401, E402
import app.tools.execution     # noqa: F401, E402
import app.tools.solving       # noqa: F401, E402
import app.tools.submission    # noqa: F401, E402


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CodeChef Contest MCP Server — AI-powered competitive programming assistant"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP/SSE mode via Uvicorn (default: STDIO)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Bind address for HTTP mode (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Listen port for HTTP mode (default: 8000)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload in HTTP mode (use for production)",
    )
    return parser.parse_args()


def _init_database():
    """Initialize the SQLite database (sync wrapper for async init_db)."""
    from app.models.database import init_db
    print("[codechef-mcp] Initializing database...", file=sys.stderr)
    asyncio.run(init_db())
    print("[codechef-mcp] Database ready.", file=sys.stderr)


def main():
    """Run the MCP server entrypoint."""
    args = parse_args()

    # Initialize SQLite database BEFORE the server starts.
    # This ensures tables exist whether running STDIO or HTTP.
    try:
        _init_database()
    except Exception as e:
        print(f"[codechef-mcp] FATAL — database init failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.http:
        # ── HTTP / Streamable HTTP Transport ──────────────────────────
        print(
            f"[codechef-mcp] Starting HTTP transport on {args.host}:{args.port}...",
            file=sys.stderr,
        )
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=not args.no_reload,
        )
    else:
        # ── STDIO Transport ───────────────────────────────────────────
        # IMPORTANT: NEVER print to stdout — it corrupts JSON-RPC framing
        print("[codechef-mcp] Starting STDIO transport...", file=sys.stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

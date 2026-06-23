"""
FastMCP server instance for the CodeChef Contest MCP Server.

This module creates the central MCP server that all tools register against.
The FastMCP class uses Python type hints and docstrings to automatically
generate tool definitions.
"""

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server instance
# All tools across the project register against this single instance
mcp = FastMCP(
    "codechef-mcp",
    host="0.0.0.0",
    instructions="""
    CodeChef Contest MCP Server — AI-powered competitive programming assistant.

    Available capabilities:
    - Open a CodeChef contest and list all problems
    - Fetch complete problem details (statement, constraints, examples)
    - Run code in a secure Docker sandbox (C++, Python) with no network access
    - Generate adversarial edge-case tests for problems
    - Validate solution complexity and estimate runtime
    - Evaluate submission confidence before submitting
    - Submit solutions to CodeChef and poll for verdicts (AC/WA/TLE/RE)
    - Retry and self-repair failed solutions
    - Solve contests sequentially (Q1→Q5) with smart prioritization
    - Track contest progress and submission history

    Security: All code execution happens inside isolated Docker containers.
    The LLM NEVER gets raw shell access. Only constrained MCP tools are exposed.

    Authentication: Requires CodeChef credentials configured in .env file.
    """,
)

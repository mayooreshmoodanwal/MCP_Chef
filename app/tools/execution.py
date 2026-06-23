"""
MCP tools for running code securely in a Docker sandbox.
"""

from typing import Any
from app.mcp_server import mcp
from app.sandbox.runner import run_code_in_sandbox
from app.models.database import save_execution_log
from app.utils.logger import logger


@mcp.tool()
async def run_code(language: str, code: str, stdin: str = "") -> dict[str, Any]:
    """Execute code in a secure sandbox environment with no network access.

    Args:
        language: Programming language to run (e.g. "cpp", "python", "java", "go", "rust").
        code: Complete source code to compile and run.
        stdin: Input data to feed to standard input of the program.
    """
    logger.info(f"MCP Tool 'run_code' called for language={language}")

    # Run in secure Docker sandbox
    result = run_code_in_sandbox(language, code, stdin)

    # Save to execution logs in database asynchronously
    await save_execution_log(
        language=language,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        execution_time=result.execution_time,
        compile_error=result.compile_error,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    return result.to_dict()

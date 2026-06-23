"""
MCP tools for CodeChef contest management and problem fetching.
"""

from typing import Any
from app.mcp_server import mcp
from app.browser.contest import fetch_contest_details, fetch_problem_list
from app.browser.problem import fetch_problem as browser_fetch_problem
from app.solver.contest_solver import create_contest_state, get_contest_state
from app.utils.cache import get_cache, set_cache
from app.models.database import save_contest, save_problem, get_problem as db_get_problem
from app.utils.logger import logger


@mcp.tool()
async def open_contest(contest_code: str) -> dict[str, Any]:
    """Open a CodeChef contest, fetch its problems, and initialize progress tracking.

    Args:
        contest_code: The code of the contest (e.g., "START123").
    """
    contest_code = contest_code.upper()
    logger.info(f"MCP Tool 'open_contest' called for {contest_code}")

    # Check cache first
    cache_key = f"contest:{contest_code}"
    details = get_cache(cache_key)

    if not details:
        details = await fetch_contest_details(contest_code)
        if "error" in details:
            return {"status": "error", "message": details["error"]}
        set_cache(cache_key, details, expire_seconds=1800)

    # Save to database
    await save_contest(
        contest_code=contest_code,
        name=details["contest_name"],
        start_date=details["start_date"],
        end_date=details["end_date"],
        problem_count=details["problem_count"],
    )

    # Initialize contest solving state
    problems = details.get("problems", [])
    create_contest_state(contest_code, problems)

    return {
        "status": "success",
        "contest_code": contest_code,
        "contest_name": details["contest_name"],
        "problems": [
            {
                "code": p["code"],
                "name": p["name"],
                "category": p["category_name"],
                "successful_submissions": p["successful_submissions"],
            }
            for p in problems
        ],
        "problem_count": details["problem_count"],
    }


@mcp.tool()
async def list_problems(contest_code: str) -> list[dict[str, Any]]:
    """List all problems available in a contest.

    Args:
        contest_code: The code of the contest (e.g., "START123").
    """
    contest_code = contest_code.upper()
    logger.info(f"MCP Tool 'list_problems' called for {contest_code}")

    cache_key = f"contest_problems:{contest_code}"
    problems = get_cache(cache_key)

    if not problems:
        problems = await fetch_problem_list(contest_code)
        if problems:
            set_cache(cache_key, problems, expire_seconds=1800)

    return problems


@mcp.tool()
async def get_problem(contest_code: str, problem_code: str) -> dict[str, Any]:
    """Fetch complete problem details including description, constraints, and sample tests.

    Args:
        contest_code: The code of the contest (e.g., "START123").
        problem_code: The code of the problem (e.g., "PROB1").
    """
    contest_code = contest_code.upper()
    problem_code = problem_code.upper()
    logger.info(f"MCP Tool 'get_problem' called for {contest_code}/{problem_code}")

    # Check cache
    cache_key = f"problem:{contest_code}:{problem_code}"
    problem_details = get_cache(cache_key)

    if not problem_details:
        # Check DB if not in cache (to reduce API hits)
        db_problem = await db_get_problem(problem_code)
        if db_problem:
            # Reconstruct dict from DB model
            problem_details = {
                "problem_code": db_problem.problem_code,
                "contest_code": db_problem.contest_code,
                "name": db_problem.name,
                "statement": db_problem.statement,
                "time_limit": db_problem.time_limit,
                "memory_limit": db_problem.memory_limit,
                "difficulty": db_problem.difficulty,
                "constraints": db_problem.constraints,
                "input_format": db_problem.input_format,
                "output_format": db_problem.output_format,
                "url": db_problem.url,
                "sample_inputs": [],  # Samples can be fetched from browser/playwright if needed, or left empty if not cached
                "sample_outputs": [],
            }
        else:
            problem_details = await browser_fetch_problem(contest_code, problem_code)
            if "error" in problem_details:
                return {"status": "error", "message": problem_details["error"]}
            
            # Save to cache & DB
            set_cache(cache_key, problem_details, expire_seconds=3600)
            await save_problem(problem_details)

    return problem_details


@mcp.tool()
async def get_contest_progress(contest_code: str) -> dict[str, Any]:
    """Get the current progress tracker status (solved, skipped, remaining problems).

    Args:
        contest_code: The code of the contest (e.g., "START123").
    """
    contest_code = contest_code.upper()
    logger.info(f"MCP Tool 'get_contest_progress' called for {contest_code}")

    state = get_contest_state(contest_code)
    if not state:
        return {
            "status": "error",
            "message": f"Contest {contest_code} is not active. Call 'open_contest' first.",
        }

    return state.progress

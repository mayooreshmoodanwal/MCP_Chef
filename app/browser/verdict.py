"""
Verdict polling for CodeChef submissions.

Handles:
- Checking submission status
- Parsing verdict codes (AC, WA, TLE, MLE, RE, CE)
- Extracting error details
- Polling with backoff
"""

import asyncio

import httpx

from app.config import config
from app.utils.logger import logger


# Verdict code mapping
VERDICT_MAP = {
    "AC": "Accepted",
    "WA": "Wrong Answer",
    "TLE": "Time Limit Exceeded",
    "MLE": "Memory Limit Exceeded",
    "RE": "Runtime Error",
    "CE": "Compilation Error",
    "CTE": "Compile Time Error",
    "NZEC": "Non-Zero Exit Code",
}


async def poll_submission_verdict(
    submission_id: str,
    max_polls: int = 20,
    interval: float = 2.0,
) -> dict:
    """Poll CodeChef for the verdict of a submission.

    Args:
        submission_id: The submission ID to check
        max_polls: Maximum number of polling attempts
        interval: Seconds between polls

    Returns:
        Dict with verdict, execution time, memory usage, etc.
    """
    logger.info(f"Polling verdict for submission {submission_id}")

    url = f"{config.CODECHEF_API_URL}/ide/submit?solution_id={submission_id}"

    async with httpx.AsyncClient() as client:
        for attempt in range(max_polls):
            try:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "CodeChef-MCP/1.0",
                        "Accept": "application/json",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()

                    # Check if judging is complete
                    status = data.get("result_code", "")
                    if status and status != "wait":
                        verdict = VERDICT_MAP.get(status, status)
                        result = {
                            "submission_id": submission_id,
                            "verdict": verdict,
                            "verdict_code": status,
                            "execution_time": data.get("time", "N/A"),
                            "memory": data.get("memory", "N/A"),
                            "signal": data.get("signal", ""),
                        }

                        if status == "CE" or status == "CTE":
                            result["compile_error"] = data.get("cmpinfo", "")

                        logger.info(
                            f"Verdict for {submission_id}: {verdict} "
                            f"(time={result['execution_time']})"
                        )
                        return result

                logger.info(
                    f"Polling attempt {attempt + 1}/{max_polls} — still judging..."
                )
                await asyncio.sleep(interval)

            except Exception as e:
                logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(interval)

    return {
        "submission_id": submission_id,
        "verdict": "Unknown",
        "verdict_code": "TIMEOUT",
        "error": f"Verdict not available after {max_polls} polling attempts",
    }


async def get_submission_details(submission_id: str) -> dict:
    """Get detailed information about a specific submission.

    Args:
        submission_id: The submission ID

    Returns:
        Dict with full submission details
    """
    url = f"{config.CODECHEF_API_URL}/ide/submit?solution_id={submission_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "CodeChef-MCP/1.0",
                    "Accept": "application/json",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get submission details: {e}")
            return {"error": str(e)}

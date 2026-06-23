"""
Problem fetching and parsing from CodeChef.

Handles:
- Fetching full problem statement
- Parsing constraints, input/output format
- Extracting sample test cases
- Parsing time and memory limits
"""

import re

import httpx
from bs4 import BeautifulSoup

from app.config import config
from app.utils.logger import logger


async def fetch_problem(contest_code: str, problem_code: str) -> dict:
    """Fetch complete problem details from CodeChef.

    Args:
        contest_code: The contest code (e.g., "START123")
        problem_code: The problem code (e.g., "PROB1")

    Returns:
        Dict with problem statement, constraints, examples, limits
    """
    url = f"{config.CODECHEF_API_URL}/contests/{contest_code}/problems/{problem_code}"

    # Get cookies from authenticated browser session
    from app.browser.login import get_browser_context
    try:
        context = await get_browser_context()
        playwright_cookies = await context.cookies()
        cookies = {c["name"]: c["value"] for c in playwright_cookies}
    except Exception as e:
        logger.error(f"Failed to get authenticated browser context for cookies: {e}")
        cookies = {}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "CodeChef-MCP/1.0",
                    "Accept": "application/json",
                },
                cookies=cookies,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Parse HTML problem body
            problem_html = data.get("body", "")
            problem_text = _html_to_text(problem_html)

            # Check if it returned a placeholder/unauthorized statement
            if (
                "example problem statement in markdown" in problem_text.lower()
                or data.get("submit_error") == "You need to login to submit."
            ):
                logger.warning(
                    f"Detected placeholder or unauthorized statement for {problem_code}. "
                    "Retrying after forcing a fresh login..."
                )
                from app.browser import login
                login._browser_context = None  # Force re-login

                context = await get_browser_context()
                playwright_cookies = await context.cookies()
                cookies = {c["name"]: c["value"] for c in playwright_cookies}

                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "CodeChef-MCP/1.0",
                        "Accept": "application/json",
                    },
                    cookies=cookies,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                problem_html = data.get("body", "")
                problem_text = _html_to_text(problem_html)

            # Extract sample test cases
            sample_inputs, sample_outputs = _extract_samples(problem_html)

            return {
                "problem_code": problem_code,
                "contest_code": contest_code,
                "name": data.get("problem_name", problem_code),
                "statement": problem_text,
                "time_limit": data.get("max_timelimit", "1"),
                "memory_limit": data.get("source_sizelimit", "50000"),
                "difficulty": data.get("difficulty_rating", "unknown"),
                "tags": data.get("tags", []),
                "sample_inputs": sample_inputs,
                "sample_outputs": sample_outputs,
                "constraints": _extract_constraints(problem_text),
                "input_format": _extract_section(problem_text, "Input"),
                "output_format": _extract_section(problem_text, "Output"),
                "url": f"{config.CODECHEF_BASE_URL}/{contest_code}/problems/{problem_code}",
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Problem API error: {e.response.status_code}")
            return {
                "error": f"Problem '{problem_code}' not found in '{contest_code}': {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Failed to fetch problem: {e}")
            return {"error": str(e)}


def _html_to_text(html: str) -> str:
    """Convert HTML problem body to clean text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    # Replace <pre> blocks with code markers
    for pre in soup.find_all("pre"):
        pre.replace_with(f"\n```\n{pre.get_text()}\n```\n")

    # Replace <code> with backticks
    for code in soup.find_all("code"):
        code.replace_with(f"`{code.get_text()}`")

    text = soup.get_text(separator="\n")
    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_samples(html: str) -> tuple[list[str], list[str]]:
    """Extract sample input/output pairs from problem HTML.

    Returns:
        Tuple of (sample_inputs, sample_outputs)
    """
    inputs = []
    outputs = []

    if not html:
        return inputs, outputs

    soup = BeautifulSoup(html, "html.parser")

    # Try to find sample sections by common CodeChef patterns
    pre_tags = soup.find_all("pre")
    for i, pre in enumerate(pre_tags):
        text = pre.get_text().strip()
        # Heuristic: alternate pre tags are usually input/output
        if i % 2 == 0:
            inputs.append(text)
        else:
            outputs.append(text)

    return inputs, outputs


def _extract_constraints(text: str) -> str:
    """Extract the constraints section from problem text."""
    return _extract_section(text, "Constraints")


def _extract_section(text: str, section_name: str) -> str:
    """Extract a named section from problem text.

    Looks for common section headers like 'Input:', 'Output:', 'Constraints:'
    """
    patterns = [
        rf"(?:^|\n)\s*\*?\*?{section_name}\s*:?\*?\*?\s*\n(.*?)(?=\n\s*\*?\*?\w+\s*:|\Z)",
        rf"(?:^|\n)#{1,3}\s*{section_name}\s*\n(.*?)(?=\n#{1,3}\s|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""

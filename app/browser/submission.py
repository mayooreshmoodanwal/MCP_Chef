"""
Code submission to CodeChef via browser automation.

Handles:
- Navigating to the submit page
- Selecting language
- Pasting code
- Submitting and capturing submission ID
"""

from app.browser.login import get_browser_context
from app.config import config
from app.utils.logger import logger


# Language mapping for CodeChef's submit form
LANGUAGE_MAP = {
    "cpp": "C++17",
    "c++": "C++17",
    "cpp17": "C++17",
    "cpp14": "C++14",
    "python": "Python 3",
    "python3": "Python 3",
    "java": "Java",
    "go": "Go",
    "rust": "Rust",
}


async def submit_code(
    contest_code: str,
    problem_code: str,
    language: str,
    code: str,
) -> dict:
    """Submit code to CodeChef for a specific problem.

    Args:
        contest_code: Contest code (e.g., "START123")
        problem_code: Problem code (e.g., "PROB1")
        language: Programming language
        code: Source code to submit

    Returns:
        Dict with submission_id or error
    """
    lang_display = LANGUAGE_MAP.get(language.lower())
    if not lang_display:
        return {
            "error": f"Unsupported language: {language}. "
            f"Supported: {', '.join(LANGUAGE_MAP.keys())}"
        }

    logger.info(f"Submitting {language} code for {contest_code}/{problem_code}")

    try:
        context = await get_browser_context()
        page = await context.new_page()

        # Navigate to the problem submit page
        submit_url = (
            f"{config.CODECHEF_BASE_URL}/submit/{problem_code}"
            f"?contest={contest_code}"
        )
        await page.goto(submit_url, wait_until="networkidle")

        # Select language
        language_selector = page.locator('select[name="language"], #language')
        if await language_selector.count() > 0:
            await language_selector.select_option(label=lang_display)
        else:
            # Try clicking language dropdown in newer UI
            lang_btn = page.locator(f'text="{lang_display}"').first
            if await lang_btn.count() > 0:
                await lang_btn.click()

        # Enter code — try CodeMirror editor first, then textarea
        editor = page.locator(".CodeMirror")
        if await editor.count() > 0:
            # CodeMirror editor
            await editor.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Meta+A")
            await page.keyboard.type(code, delay=0)
        else:
            # Fallback to textarea
            textarea = page.locator('textarea[name="program"]')
            await textarea.fill(code)

        # Submit
        submit_btn = page.locator(
            'input[type="submit"][value*="Submit"], '
            'button[type="submit"], '
            '#submit_btn'
        )
        await submit_btn.click()

        # Wait for submission result page
        await page.wait_for_load_state("networkidle")

        # Extract submission ID from URL or page content
        current_url = page.url
        submission_id = _extract_submission_id(current_url)

        if submission_id:
            logger.info(f"Submission successful: ID={submission_id}")
            return {
                "submission_id": submission_id,
                "status": "submitted",
                "url": current_url,
            }
        else:
            # Try to get submission ID from the page
            content = await page.content()
            return {
                "status": "submitted",
                "url": current_url,
                "note": "Submission sent but could not extract submission ID",
            }

    except Exception as e:
        logger.error(f"Submission failed: {e}")
        return {"error": f"Submission failed: {str(e)}"}
    finally:
        await page.close()


def _extract_submission_id(url: str) -> str | None:
    """Extract submission ID from the post-submit URL."""
    import re

    # CodeChef URLs like /submit/complete/12345678
    match = re.search(r"/(\d{6,})", url)
    return match.group(1) if match else None

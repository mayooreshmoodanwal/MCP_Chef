"""
CodeChef login automation using Playwright.

Handles:
- Credential-based login
- Cookie persistence (save/load sessions)
- Session validation and re-authentication
- Secure cookie storage (never hardcoded)
"""

import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext

from app.config import config
from app.utils.logger import logger


# Cookie storage path
COOKIES_PATH = os.path.join(config.COOKIES_DIR, "codechef_cookies.json")


async def _ensure_cookies_dir():
    """Create the cookies directory if it doesn't exist."""
    Path(config.COOKIES_DIR).mkdir(parents=True, exist_ok=True)


async def save_cookies(context: BrowserContext) -> None:
    """Save browser cookies to disk for session persistence."""
    await _ensure_cookies_dir()
    cookies = await context.cookies()
    with open(COOKIES_PATH, "w") as f:
        json.dump(cookies, f, indent=2)
    logger.info(f"Saved {len(cookies)} cookies to disk")


async def load_cookies(context: BrowserContext) -> bool:
    """Load saved cookies into browser context.

    Returns:
        True if cookies were loaded, False if no saved cookies exist
    """
    if not os.path.exists(COOKIES_PATH):
        return False

    try:
        with open(COOKIES_PATH, "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        logger.info(f"Loaded {len(cookies)} cookies from disk")
        return True
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cookies: {e}")
        return False


async def is_logged_in(context: BrowserContext) -> bool:
    """Check if the current session is authenticated.

    Navigates to CodeChef and checks if the user is logged in
    by looking for the user profile element.
    """
    page = await context.new_page()
    try:
        await page.goto(f"{config.CODECHEF_BASE_URL}", wait_until="networkidle")
        # Check for logged-in indicators
        user_menu = await page.query_selector(
            'a[href*="/users/"], .user-name, nav .username'
        )
        return user_menu is not None
    except Exception as e:
        logger.error(f"Session check failed: {e}")
        return False
    finally:
        await page.close()


async def login_to_codechef() -> BrowserContext:
    """Login to CodeChef and return an authenticated browser context.

    Flow:
    1. Try to restore a saved session from cookies
    2. If no session or session expired, perform fresh login
    3. Save cookies for future use

    Returns:
        Authenticated BrowserContext

    Raises:
        RuntimeError: If login fails
    """
    if not config.CODECHEF_USERNAME or not config.CODECHEF_PASSWORD:
        raise RuntimeError(
            "CODECHEF_USERNAME and CODECHEF_PASSWORD must be set in .env file"
        )

    pw = await async_playwright().start()
    browser: Browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )

    # Try restoring saved session
    cookies_loaded = await load_cookies(context)
    if cookies_loaded and await is_logged_in(context):
        logger.info("Restored existing CodeChef session from cookies")
        return context

    # Perform fresh login
    logger.info("Performing fresh CodeChef login...")
    page = await context.new_page()

    try:
        await page.goto(
            f"{config.CODECHEF_BASE_URL}/login",
            wait_until="networkidle",
        )

        # Fill login form
        await page.fill('input[name="name"], #edit-name', config.CODECHEF_USERNAME)
        await page.fill(
            'input[name="pass"], #edit-pass', config.CODECHEF_PASSWORD
        )

        # Submit login
        await page.click('input[type="submit"], #edit-submit, button[type="submit"]')

        # Wait for navigation after login
        await page.wait_for_load_state("networkidle")

        # Verify login succeeded
        if "/login" in page.url:
            raise RuntimeError(
                "Login failed — check your CODECHEF_USERNAME and CODECHEF_PASSWORD"
            )

        logger.info(f"Successfully logged in as {config.CODECHEF_USERNAME}")
        await save_cookies(context)
        return context

    except Exception as e:
        logger.error(f"Login failed: {e}")
        await browser.close()
        await pw.stop()
        raise
    finally:
        await page.close()


# Global browser context (reused across tool calls)
_browser_context: BrowserContext | None = None


async def get_browser_context() -> BrowserContext:
    """Get or create an authenticated browser context.

    Maintains a singleton context for the lifetime of the server.
    Automatically re-authenticates if the session expires.
    """
    global _browser_context

    if _browser_context is None:
        _browser_context = await login_to_codechef()
    elif not await is_logged_in(_browser_context):
        logger.info("Session expired, re-authenticating...")
        _browser_context = await login_to_codechef()

    return _browser_context

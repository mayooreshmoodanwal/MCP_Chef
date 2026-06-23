"""
Centralized configuration for the CodeChef MCP Server.

All settings are loaded from environment variables (.env file).
Provides typed defaults and validation for all configurable parameters.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # ── CodeChef Auth ──────────────────────────────────────────────
    CODECHEF_USERNAME: str = os.getenv("CODECHEF_USERNAME", "")
    CODECHEF_PASSWORD: str = os.getenv("CODECHEF_PASSWORD", "")

    # ── Server ─────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── Sandbox Limits ─────────────────────────────────────────────
    SANDBOX_MEMORY_LIMIT: str = os.getenv("SANDBOX_MEMORY_LIMIT", "256m")
    SANDBOX_CPU_LIMIT: int = int(os.getenv("SANDBOX_CPU_LIMIT", "1"))
    SANDBOX_PID_LIMIT: int = int(os.getenv("SANDBOX_PID_LIMIT", "64"))
    COMPILE_TIMEOUT: int = int(os.getenv("COMPILE_TIMEOUT", "10"))
    EXECUTION_TIMEOUT: int = int(os.getenv("EXECUTION_TIMEOUT", "5"))
    STRESS_TEST_TIMEOUT: int = int(os.getenv("STRESS_TEST_TIMEOUT", "15"))

    # ── Solver ─────────────────────────────────────────────────────
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    CONFIDENCE_THRESHOLD: int = int(os.getenv("CONFIDENCE_THRESHOLD", "75"))

    # ── Redis ──────────────────────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ── Database ───────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./codechef_mcp.db",
    )

    # ── Paths ──────────────────────────────────────────────────────
    COOKIES_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "cookies",
    )

    # ── CodeChef URLs ──────────────────────────────────────────────
    CODECHEF_BASE_URL: str = "https://www.codechef.com"
    CODECHEF_API_URL: str = "https://www.codechef.com/api"

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return a list of warnings."""
        warnings = []
        if not cls.CODECHEF_USERNAME or not cls.CODECHEF_PASSWORD:
            warnings.append(
                "CODECHEF_USERNAME/CODECHEF_PASSWORD not set. "
                "Browser automation tools will fail."
            )
        return warnings


config = Config()

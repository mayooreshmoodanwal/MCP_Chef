"""
Sequential contest solver with smart strategy.

Solves contest problems Q1 → Q5 with:
- Priority ordering (easy first)
- Skip temporarily if stuck
- Revisit later
- Maximize accepted count
"""

from app.utils.logger import logger


class ContestState:
    """Tracks the state of a contest solving session."""

    def __init__(self, contest_code: str, problems: list[dict]):
        self.contest_code = contest_code
        self.problems = {p["code"]: p for p in problems}
        self.solved: set[str] = set()
        self.skipped: set[str] = set()
        self.attempted: set[str] = set()
        self.submission_history: dict[str, list[dict]] = {}

    @property
    def unsolved(self) -> list[str]:
        """Get unsolved problem codes in recommended order."""
        return [
            code for code in self.problems
            if code not in self.solved
        ]

    @property
    def progress(self) -> dict:
        return {
            "contest_code": self.contest_code,
            "total_problems": len(self.problems),
            "solved": len(self.solved),
            "solved_codes": sorted(self.solved),
            "attempted": len(self.attempted),
            "skipped": sorted(self.skipped),
            "remaining": sorted(self.unsolved),
            "completion_rate": f"{len(self.solved)/len(self.problems):.0%}" if self.problems else "0%",
        }

    def mark_solved(self, problem_code: str):
        """Mark a problem as successfully solved."""
        self.solved.add(problem_code)
        self.skipped.discard(problem_code)
        logger.info(f"✅ {problem_code} solved ({len(self.solved)}/{len(self.problems)})")

    def mark_attempted(self, problem_code: str):
        """Mark a problem as attempted."""
        self.attempted.add(problem_code)

    def mark_skipped(self, problem_code: str, reason: str = ""):
        """Temporarily skip a problem."""
        self.skipped.add(problem_code)
        logger.info(f"⏭️ Skipping {problem_code}: {reason}")

    def record_submission(self, problem_code: str, submission: dict):
        """Record a submission for a problem."""
        if problem_code not in self.submission_history:
            self.submission_history[problem_code] = []
        self.submission_history[problem_code].append(submission)

    def get_next_problem(self) -> str | None:
        """Get the next problem to solve using smart strategy.

        Strategy:
        1. Try unsolved, unskipped problems first (in order)
        2. Then revisit skipped problems
        3. Return None if all solved
        """
        # First pass: unattempted problems
        for code in self.problems:
            if code not in self.solved and code not in self.skipped:
                return code

        # Second pass: revisit skipped problems
        for code in sorted(self.skipped):
            if code not in self.solved:
                return code

        return None


# Global contest state tracker
_active_contests: dict[str, ContestState] = {}


def get_contest_state(contest_code: str) -> ContestState | None:
    """Get the active contest state."""
    return _active_contests.get(contest_code)


def create_contest_state(contest_code: str, problems: list[dict]) -> ContestState:
    """Create a new contest solving session."""
    state = ContestState(contest_code, problems)
    _active_contests[contest_code] = state
    logger.info(f"Contest session created: {contest_code} ({len(problems)} problems)")
    return state

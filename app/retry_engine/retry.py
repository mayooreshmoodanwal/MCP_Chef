"""
Retry engine for iterative solution repair.

When a solution fails (WA, TLE, RE), the retry engine:
1. Analyzes the verdict
2. Inspects failed test cases
3. Suggests a fix approach
4. Tracks retry count (configurable maximum)
"""

from app.config import config
from app.utils.logger import logger


class RetryState:
    """Tracks the retry state for a problem."""

    def __init__(self, problem_code: str):
        self.problem_code = problem_code
        self.attempts: list[dict] = []
        self.max_retries = config.MAX_RETRIES

    @property
    def retry_count(self) -> int:
        return len(self.attempts)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def record_attempt(self, verdict: str, code: str, analysis: str = ""):
        """Record a submission attempt."""
        self.attempts.append({
            "attempt": self.retry_count + 1,
            "verdict": verdict,
            "code_snippet": code[:200] + "..." if len(code) > 200 else code,
            "analysis": analysis,
        })

    def to_dict(self) -> dict:
        return {
            "problem_code": self.problem_code,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
            "attempts": self.attempts,
        }


def analyze_failure(verdict: str, stderr: str = "", failed_input: str = "") -> dict:
    """Analyze why a solution failed and suggest a fix approach.

    Args:
        verdict: The verdict code (WA, TLE, RE, MLE, CE)
        stderr: Standard error output
        failed_input: The test input that caused failure

    Returns:
        Dict with analysis and suggested fix approach
    """
    analysis = {
        "verdict": verdict,
        "diagnosis": "",
        "suggested_approach": "",
        "priority": "high",
    }

    if verdict in ("WA", "Wrong Answer"):
        analysis["diagnosis"] = (
            "Solution produces incorrect output. Possible causes: "
            "edge case not handled, off-by-one error, integer overflow, "
            "incorrect algorithm logic."
        )
        analysis["suggested_approach"] = (
            "1. Re-check algorithm correctness\n"
            "2. Test with boundary values (N=0, N=1, max N)\n"
            "3. Check for integer overflow (use long long for C++)\n"
            "4. Compare with brute-force on small inputs\n"
            "5. Review edge cases in problem statement"
        )

    elif verdict in ("TLE", "Time Limit Exceeded"):
        analysis["diagnosis"] = (
            "Solution is too slow. The time complexity is likely too high "
            "for the given constraints."
        )
        analysis["suggested_approach"] = (
            "1. Analyze current complexity — aim for O(n log n) or better\n"
            "2. Eliminate nested loops where possible\n"
            "3. Use efficient data structures (sets, maps, priority queues)\n"
            "4. Consider binary search, two pointers, or divide and conquer\n"
            "5. Pre-compute values to avoid redundant calculations"
        )
        analysis["priority"] = "critical"

    elif verdict in ("RE", "Runtime Error", "NZEC"):
        analysis["diagnosis"] = (
            "Solution crashed during execution. Possible causes: "
            "array index out of bounds, null pointer, division by zero, "
            "stack overflow (deep recursion)."
        )
        analysis["suggested_approach"] = (
            "1. Check array bounds and validate indices\n"
            "2. Handle empty input / edge cases\n"
            "3. Check for division by zero\n"
            "4. Increase recursion limit or convert to iterative\n"
            "5. Validate all input assumptions"
        )
        if stderr:
            analysis["stderr_clue"] = stderr[:500]

    elif verdict in ("MLE", "Memory Limit Exceeded"):
        analysis["diagnosis"] = (
            "Solution uses too much memory. Possible causes: "
            "large arrays, excessive recursion, unnecessary data storage."
        )
        analysis["suggested_approach"] = (
            "1. Reduce space complexity\n"
            "2. Use in-place algorithms\n"
            "3. Process input in chunks/streaming\n"
            "4. Avoid storing all intermediate results"
        )

    elif verdict in ("CE", "CTE", "Compilation Error"):
        analysis["diagnosis"] = "Code failed to compile."
        analysis["suggested_approach"] = (
            "1. Fix syntax errors\n"
            "2. Check language version compatibility\n"
            "3. Verify all imports/includes"
        )
        if stderr:
            analysis["compile_error"] = stderr[:500]

    else:
        analysis["diagnosis"] = f"Unknown verdict: {verdict}"
        analysis["suggested_approach"] = "Review the submission details and try again."

    if failed_input:
        analysis["failed_input_preview"] = (
            failed_input[:200] + "..." if len(failed_input) > 200 else failed_input
        )

    logger.info(f"Failure analysis: {verdict} → {analysis['diagnosis'][:80]}")
    return analysis


# Global retry state tracker (per problem)
_retry_states: dict[str, RetryState] = {}


def get_retry_state(problem_code: str) -> RetryState:
    """Get or create a retry state for a problem."""
    if problem_code not in _retry_states:
        _retry_states[problem_code] = RetryState(problem_code)
    return _retry_states[problem_code]


def reset_retry_state(problem_code: str):
    """Reset retry state for a problem (e.g., after AC)."""
    _retry_states.pop(problem_code, None)

"""
Confidence evaluation system for solution submissions.

Before submitting, the system evaluates:
- Sample test pass rate
- Generated test pass rate
- Complexity validation
- Runtime estimation

Submission occurs ONLY if confidence exceeds the configured threshold.
"""

from app.config import config
from app.utils.logger import logger


class ConfidenceReport:
    """Detailed confidence evaluation report."""

    def __init__(self):
        self.sample_pass: bool = False
        self.sample_details: str = ""
        self.generated_pass: bool = False
        self.generated_pass_rate: float = 0.0
        self.generated_details: str = ""
        self.complexity_valid: bool = False
        self.complexity_estimate: str = ""
        self.runtime_acceptable: bool = False
        self.runtime_estimate: str = ""
        self.score: int = 0

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "threshold": config.CONFIDENCE_THRESHOLD,
            "should_submit": self.score >= config.CONFIDENCE_THRESHOLD,
            "breakdown": {
                "sample_tests": {
                    "passed": self.sample_pass,
                    "details": self.sample_details,
                    "points": 30 if self.sample_pass else 0,
                },
                "generated_tests": {
                    "passed": self.generated_pass,
                    "pass_rate": f"{self.generated_pass_rate:.0%}",
                    "details": self.generated_details,
                    "points": int(40 * self.generated_pass_rate),
                },
                "complexity": {
                    "valid": self.complexity_valid,
                    "estimate": self.complexity_estimate,
                    "points": 15 if self.complexity_valid else 0,
                },
                "runtime": {
                    "acceptable": self.runtime_acceptable,
                    "estimate": self.runtime_estimate,
                    "points": 15 if self.runtime_acceptable else 0,
                },
            },
        }


def evaluate_confidence(
    sample_results: list[dict],
    generated_results: list[dict],
    complexity_estimate: str = "",
    time_limit: float = 1.0,
    avg_execution_time: float = 0.0,
) -> ConfidenceReport:
    """Evaluate confidence in a solution before submission.

    Scoring breakdown (out of 100):
    - Sample tests pass: 30 points
    - Generated tests pass rate: up to 40 points
    - Complexity validation: 15 points
    - Runtime estimation: 15 points

    Args:
        sample_results: Results of running sample test cases
        generated_results: Results of running generated edge-case tests
        complexity_estimate: Estimated time complexity (e.g., "O(n log n)")
        time_limit: Problem time limit in seconds
        avg_execution_time: Average execution time across tests

    Returns:
        ConfidenceReport with detailed breakdown
    """
    report = ConfidenceReport()

    # ── Sample Tests (30 points) ───────────────────────────────────
    if sample_results:
        passed = sum(1 for r in sample_results if r.get("success", False))
        total = len(sample_results)
        report.sample_pass = passed == total
        report.sample_details = f"{passed}/{total} sample tests passed"
    else:
        report.sample_details = "No sample tests available"

    # ── Generated Tests (40 points) ────────────────────────────────
    if generated_results:
        passed = sum(1 for r in generated_results if r.get("success", False))
        total = len(generated_results)
        report.generated_pass_rate = passed / total if total > 0 else 0
        report.generated_pass = report.generated_pass_rate >= 0.9
        report.generated_details = f"{passed}/{total} generated tests passed"
    else:
        report.generated_pass_rate = 0
        report.generated_details = "No generated tests run"

    # ── Complexity (15 points) ─────────────────────────────────────
    if complexity_estimate:
        report.complexity_estimate = complexity_estimate
        # Consider polynomial and better complexities as valid
        valid_complexities = [
            "O(1)", "O(log n)", "O(sqrt(n))", "O(n)",
            "O(n log n)", "O(n^2)", "O(n^2 log n)",
        ]
        report.complexity_valid = any(
            c.lower() in complexity_estimate.lower()
            for c in valid_complexities
        )
    else:
        report.complexity_estimate = "Not estimated"

    # ── Runtime (15 points) ────────────────────────────────────────
    if avg_execution_time > 0:
        report.runtime_estimate = f"{avg_execution_time:.3f}s (limit: {time_limit}s)"
        # Accept if execution time is within 80% of the time limit
        report.runtime_acceptable = avg_execution_time < (time_limit * 0.8)
    else:
        report.runtime_estimate = "Not measured"

    # ── Calculate Total Score ──────────────────────────────────────
    report.score = (
        (30 if report.sample_pass else 0)
        + int(40 * report.generated_pass_rate)
        + (15 if report.complexity_valid else 0)
        + (15 if report.runtime_acceptable else 0)
    )

    logger.info(
        f"Confidence score: {report.score}/100 "
        f"(threshold: {config.CONFIDENCE_THRESHOLD})"
    )

    return report

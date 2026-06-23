"""
MCP tools for solution solving, test generation, and confidence evaluation.
"""

import re
from typing import Any
from app.mcp_server import mcp
from app.validator.test_generator import generate_edge_cases
from app.validator.confidence import evaluate_confidence as run_confidence_eval
from app.utils.logger import logger


@mcp.tool()
async def generate_tests(problem_code: str, constraints: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate adversarial and edge-case test inputs for a problem.

    Args:
        problem_code: The code of the problem (e.g. "PROB1").
        constraints: Dictionary specifying input constraints. Supported keys:
            - n_min: minimum size of N (default 1)
            - n_max: maximum size of N (default 100000)
            - val_min: minimum value of array/string elements (default -1e9)
            - val_max: maximum value of array/string elements (default 1e9)
            - problem_type: "array", "string", "graph", "math" (default "array")
    """
    logger.info(f"MCP Tool 'generate_tests' called for {problem_code}")
    # Convert numerical keys to ints
    parsed_constraints = {}
    for k, v in constraints.items():
        if k in ("n_min", "n_max", "val_min", "val_max"):
            try:
                parsed_constraints[k] = int(float(v))
            except (ValueError, TypeError):
                parsed_constraints[k] = v
        else:
            parsed_constraints[k] = v

    test_cases = generate_edge_cases(parsed_constraints)
    return test_cases


@mcp.tool()
async def validate_complexity(code: str, language: str) -> dict[str, Any]:
    """Estimate time and space complexity of the code using static heuristic analysis.

    Looks for loop nesting depth and explicit comments like '// Complexity: O(...)'.

    Args:
        code: The source code to analyze.
        language: The programming language of the code (e.g., "cpp", "python").
    """
    logger.info(f"MCP Tool 'validate_complexity' called for language={language}")

    # 1. Look for explicit complexity comment
    comment_pattern = re.compile(
        r"(?:complexity|time\s+complexity)\s*[:=-]?\s*([oO]\s*\([^)]+\))",
        re.IGNORECASE,
    )
    match = comment_pattern.search(code)
    if match:
        estimate = match.group(1).strip()
        return {
            "complexity": estimate,
            "source": "code_comment",
            "explanation": "Found explicit complexity annotation in comments.",
        }

    # 2. Heuristic check of loops
    # Look for loop patterns
    loops = 0
    max_depth = 0
    current_depth = 0

    lines = code.split("\n")
    for line in lines:
        stripped = line.strip()
        # Simple indentation/braces depth estimator or syntax patterns
        # For C++/Java/Go/Rust, look for `{` and `}` or `for`/`while`
        # For Python, indentation is key but we can also just scan for nested loop keywords
        if any(keyword in stripped for keyword in ("for ", "while ", "for(", "while(")) and not stripped.startswith(("//", "#", "*")):
            loops += 1
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif "}" in stripped or (language.lower() == "python" and stripped == ""):
            # decrement depth but keep it >= 0
            current_depth = max(0, current_depth - 1)

    # Map depth to big-O
    if max_depth == 0:
        complexity = "O(1)"
        explanation = "No loops or recursion detected in code."
    elif max_depth == 1:
        complexity = "O(n)"
        explanation = "Single level loop detected. Linear time complexity assumed."
    elif max_depth == 2:
        complexity = "O(n^2)"
        explanation = "Double-nested loop structure detected. Quadratic time complexity assumed."
    else:
        complexity = f"O(n^{max_depth})"
        explanation = f"Deeply nested loop structure ({max_depth} levels) detected."

    # Look for binary search indicators to suggest O(log n)
    if any(term in code.lower() for term in ("binarysearch", "lower_bound", "upper_bound", "mid = ", ">> 1", "/ 2")):
        if complexity == "O(n)":
            complexity = "O(log n)"
            explanation += " Binary search pattern detected, refining estimate to logarithmic."
        elif complexity == "O(n^2)":
            complexity = "O(n log n)"
            explanation += " Contains nested loops with binary search characteristics. Refined to O(n log n)."

    return {
        "complexity": complexity,
        "source": "heuristic_analysis",
        "loops_found": loops,
        "max_nested_depth": max_depth,
        "explanation": explanation,
    }


@mcp.tool()
async def evaluate_confidence(
    problem_code: str,
    sample_results: list[dict[str, Any]],
    generated_results: list[dict[str, Any]],
    complexity_estimate: str,
    time_limit: float = 1.0,
    avg_execution_time: float = 0.0,
) -> dict[str, Any]:
    """Calculate the submission confidence score based on test results and complexity.

    Args:
        problem_code: The code of the problem (e.g. "PROB1").
        sample_results: List of execution results for sample tests. Must contain 'success' (bool).
        generated_results: List of execution results for generated edge-case tests. Must contain 'success' (bool).
        complexity_estimate: The estimated time complexity string (e.g., "O(n log n)").
        time_limit: Time limit of the problem in seconds.
        avg_execution_time: Average execution time of the code in seconds.
    """
    logger.info(f"MCP Tool 'evaluate_confidence' called for {problem_code}")

    report = run_confidence_eval(
        sample_results=sample_results,
        generated_results=generated_results,
        complexity_estimate=complexity_estimate,
        time_limit=time_limit,
        avg_execution_time=avg_execution_time,
    )

    return report.to_dict()

"""
Test case generation for competitive programming problems.

Generates:
- Small random tests
- Edge cases (empty/minimum input)
- Boundary cases (maximum constraints)
- Duplicate-heavy inputs
- Sorted/reverse sorted inputs
- Overflow scenarios
- Adversarial worst-case inputs
"""

import random
import string

from app.utils.logger import logger


def generate_edge_cases(constraints: dict) -> list[dict]:
    """Generate edge-case test inputs based on problem constraints.

    Args:
        constraints: Dict with constraint info. Expected keys:
            - n_min: minimum value of N (default 1)
            - n_max: maximum value of N (default 100000)
            - val_min: minimum element value (default -1000000000)
            - val_max: maximum element value (default 1000000000)
            - problem_type: "array", "string", "graph", "math" (default "array")

    Returns:
        List of test case dicts with 'name', 'input', and 'description'
    """
    n_min = constraints.get("n_min", 1)
    n_max = constraints.get("n_max", 100000)
    val_min = constraints.get("val_min", -1000000000)
    val_max = constraints.get("val_max", 1000000000)
    problem_type = constraints.get("problem_type", "array")

    test_cases = []

    # ── Minimum input ──────────────────────────────────────────────
    test_cases.append({
        "name": "minimum_input",
        "description": "Smallest valid input",
        "input": _generate_minimum(n_min, val_min, val_max, problem_type),
    })

    # ── Maximum input ──────────────────────────────────────────────
    # Capped to prevent sandbox OOM
    safe_n_max = min(n_max, 100000)
    test_cases.append({
        "name": "maximum_input",
        "description": f"Large input (N={safe_n_max})",
        "input": _generate_array(safe_n_max, val_min, val_max, problem_type),
    })

    # ── All same values ────────────────────────────────────────────
    test_cases.append({
        "name": "duplicate_values",
        "description": "All elements are identical",
        "input": _generate_duplicates(min(1000, n_max), val_min, val_max, problem_type),
    })

    # ── Sorted input ───────────────────────────────────────────────
    test_cases.append({
        "name": "sorted_ascending",
        "description": "Already sorted in ascending order",
        "input": _generate_sorted(min(1000, n_max), val_min, val_max, ascending=True),
    })

    # ── Reverse sorted ─────────────────────────────────────────────
    test_cases.append({
        "name": "sorted_descending",
        "description": "Sorted in descending order",
        "input": _generate_sorted(min(1000, n_max), val_min, val_max, ascending=False),
    })

    # ── Boundary values ────────────────────────────────────────────
    test_cases.append({
        "name": "boundary_values",
        "description": "Input with min/max boundary values",
        "input": _generate_boundary(min(100, n_max), val_min, val_max),
    })

    # ── Random small test ──────────────────────────────────────────
    for i in range(3):
        small_n = random.randint(n_min, min(20, n_max))
        test_cases.append({
            "name": f"random_small_{i+1}",
            "description": f"Random test with N={small_n}",
            "input": _generate_array(small_n, val_min, val_max, problem_type),
        })

    logger.info(f"Generated {len(test_cases)} test cases")
    return test_cases


def _generate_minimum(n_min: int, val_min: int, val_max: int, problem_type: str) -> str:
    """Generate minimum-size input."""
    if problem_type == "string":
        return f"1\na"
    return f"1\n{random.randint(val_min, val_max)}"


def _generate_array(n: int, val_min: int, val_max: int, problem_type: str) -> str:
    """Generate an array-based test input."""
    if problem_type == "string":
        s = "".join(random.choices(string.ascii_lowercase, k=n))
        return f"{n}\n{s}"

    arr = [random.randint(val_min, val_max) for _ in range(n)]
    return f"{n}\n{' '.join(map(str, arr))}"


def _generate_duplicates(n: int, val_min: int, val_max: int, problem_type: str) -> str:
    """Generate input where all values are the same."""
    if problem_type == "string":
        return f"{n}\n{'a' * n}"
    val = random.randint(val_min, val_max)
    arr = [val] * n
    return f"{n}\n{' '.join(map(str, arr))}"


def _generate_sorted(n: int, val_min: int, val_max: int, ascending: bool = True) -> str:
    """Generate a sorted array test input."""
    arr = sorted(
        [random.randint(val_min, val_max) for _ in range(n)],
        reverse=not ascending,
    )
    return f"{n}\n{' '.join(map(str, arr))}"


def _generate_boundary(n: int, val_min: int, val_max: int) -> str:
    """Generate input using boundary values."""
    arr = []
    for _ in range(n):
        choice = random.choice(["min", "max", "zero", "random"])
        if choice == "min":
            arr.append(val_min)
        elif choice == "max":
            arr.append(val_max)
        elif choice == "zero":
            arr.append(0)
        else:
            arr.append(random.randint(val_min, val_max))
    return f"{n}\n{' '.join(map(str, arr))}"

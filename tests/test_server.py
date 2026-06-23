"""
Test suite for the CodeChef MCP Server.

Tests verify:
- MCP server instantiation and tool registration
- Configuration loading
- Sandbox language config
- Test case generation
- Confidence evaluation
- Retry engine analysis
- Contest solver state management
- Cache layer operations
- Database model creation
"""

import asyncio
import pytest

# ── Phase 1: Core Server ──────────────────────────────────────────


def test_mcp_server_instance():
    """Verify the FastMCP server is properly instantiated."""
    from app.mcp_server import mcp
    assert mcp is not None
    assert mcp.name == "codechef-mcp"


def test_config_loads():
    """Verify configuration class loads with defaults."""
    from app.config import config
    assert config.HOST == "0.0.0.0"
    assert config.PORT == 8000
    assert config.SANDBOX_MEMORY_LIMIT == "256m"
    assert config.SANDBOX_CPU_LIMIT == 1
    assert config.SANDBOX_PID_LIMIT == 64
    assert config.COMPILE_TIMEOUT == 10
    assert config.EXECUTION_TIMEOUT == 5
    assert config.STRESS_TEST_TIMEOUT == 15
    assert config.MAX_RETRIES == 3
    assert config.CONFIDENCE_THRESHOLD == 75
    assert "codechef.com" in config.CODECHEF_BASE_URL


def test_config_validate():
    """Verify config.validate() reports warnings for missing credentials."""
    from app.config import config
    warnings = config.validate()
    # Unless .env is configured, credentials should trigger a warning
    if not config.CODECHEF_USERNAME or not config.CODECHEF_PASSWORD:
        assert len(warnings) > 0
        assert "CODECHEF_USERNAME" in warnings[0]


# ── Phase 2: Tool Registration ────────────────────────────────────


@pytest.mark.asyncio
async def test_tools_registered():
    """Verify all 12 MCP tools are registered after importing tool modules."""
    from app.mcp_server import mcp

    # Import tool modules to trigger registration
    import app.tools.contest       # noqa: F401
    import app.tools.execution     # noqa: F401
    import app.tools.solving       # noqa: F401
    import app.tools.submission    # noqa: F401

    # FastMCP stores tools internally; list them
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "open_contest",
        "list_problems",
        "get_problem",
        "get_contest_progress",
        "run_code",
        "generate_tests",
        "validate_complexity",
        "evaluate_confidence",
        "submit_solution",
        "get_submission_status",
        "retry_solution",
        "get_submission_history",
    ]

    for name in expected_tools:
        assert name in tool_names, f"Tool '{name}' not registered"

    assert len(tool_names) >= 12, f"Expected ≥12 tools, got {len(tool_names)}"


# ── Phase 3: Sandbox Language Config ──────────────────────────────


def test_supported_languages():
    """Verify all 5 PRD languages are configured."""
    from app.sandbox.languages import get_language_config, supported_languages

    langs = supported_languages()
    assert "cpp" in langs
    assert "python" in langs
    assert "java" in langs
    assert "go" in langs
    assert "rust" in langs


def test_language_config_cpp():
    """Verify C++ language config has correct Docker image and flags."""
    from app.sandbox.languages import get_language_config

    cfg = get_language_config("cpp")
    assert cfg is not None
    assert cfg.docker_image == "gcc:13"
    assert "-std=c++17" in cfg.compile_command
    assert cfg.file_extension == ".cpp"


def test_language_config_python():
    """Verify Python language config is interpreted (no compile)."""
    from app.sandbox.languages import get_language_config

    cfg = get_language_config("python")
    assert cfg is not None
    assert cfg.compile_command is None
    assert "python3" in cfg.run_command


def test_language_aliases():
    """Verify language aliases resolve correctly."""
    from app.sandbox.languages import get_language_config

    assert get_language_config("c++") is not None
    assert get_language_config("python3") is not None
    assert get_language_config("cpp17") is not None
    assert get_language_config("c++").name == get_language_config("cpp").name


def test_unsupported_language():
    """Verify unsupported language returns None."""
    from app.sandbox.languages import get_language_config
    assert get_language_config("cobol") is None


# ── Phase 4: Test Generator ──────────────────────────────────────


def test_edge_case_generation_default():
    """Verify edge case generator produces expected test categories."""
    from app.validator.test_generator import generate_edge_cases

    cases = generate_edge_cases({})
    names = [c["name"] for c in cases]

    assert "minimum_input" in names
    assert "maximum_input" in names
    assert "duplicate_values" in names
    assert "sorted_ascending" in names
    assert "sorted_descending" in names
    assert "boundary_values" in names
    assert any(n.startswith("random_small_") for n in names)
    assert len(cases) >= 9  # 6 fixed + 3 random


def test_edge_case_generation_string():
    """Verify string problem type generates string-based inputs."""
    from app.validator.test_generator import generate_edge_cases

    cases = generate_edge_cases({"problem_type": "string", "n_max": 100})
    min_case = next(c for c in cases if c["name"] == "minimum_input")
    assert "a" in min_case["input"]  # string-type minimum


def test_edge_case_input_format():
    """Verify each test case has the required keys."""
    from app.validator.test_generator import generate_edge_cases

    for case in generate_edge_cases({"n_max": 50}):
        assert "name" in case
        assert "description" in case
        assert "input" in case
        assert isinstance(case["input"], str)
        assert len(case["input"]) > 0


# ── Phase 5: Confidence Evaluator ────────────────────────────────


def test_confidence_perfect_score():
    """Verify a perfect scenario yields score ~100."""
    from app.validator.confidence import evaluate_confidence

    report = evaluate_confidence(
        sample_results=[{"success": True}, {"success": True}],
        generated_results=[{"success": True}] * 10,
        complexity_estimate="O(n log n)",
        time_limit=2.0,
        avg_execution_time=0.1,
    )

    assert report.score >= 95
    assert report.sample_pass is True
    assert report.generated_pass is True
    assert report.complexity_valid is True
    assert report.runtime_acceptable is True


def test_confidence_zero_score():
    """Verify all-failing scenario yields score 0."""
    from app.validator.confidence import evaluate_confidence

    report = evaluate_confidence(
        sample_results=[{"success": False}],
        generated_results=[{"success": False}] * 5,
        complexity_estimate="O(2^n)",
        time_limit=1.0,
        avg_execution_time=5.0,
    )

    assert report.score == 0
    assert report.sample_pass is False


def test_confidence_report_dict():
    """Verify confidence report serializes to dict with required keys."""
    from app.validator.confidence import evaluate_confidence

    report = evaluate_confidence(
        sample_results=[{"success": True}],
        generated_results=[],
        complexity_estimate="O(n)",
        time_limit=1.0,
        avg_execution_time=0.5,
    )
    d = report.to_dict()

    assert "score" in d
    assert "threshold" in d
    assert "should_submit" in d
    assert "breakdown" in d
    assert "sample_tests" in d["breakdown"]
    assert "generated_tests" in d["breakdown"]
    assert "complexity" in d["breakdown"]
    assert "runtime" in d["breakdown"]


# ── Phase 6: Retry Engine ────────────────────────────────────────


def test_retry_state_tracking():
    """Verify retry state tracks attempts and enforces max retries."""
    from app.retry_engine.retry import RetryState

    state = RetryState("PROB1")
    assert state.can_retry is True
    assert state.retry_count == 0

    state.record_attempt("WA", "int main() { return 0; }")
    assert state.retry_count == 1
    assert state.can_retry is True

    # Exhaust all retries (default max = 3)
    state.record_attempt("WA", "code v2")
    state.record_attempt("TLE", "code v3")
    assert state.retry_count == 3
    assert state.can_retry is False


def test_failure_analysis_wa():
    """Verify WA diagnosis mentions edge cases and off-by-one."""
    from app.retry_engine.retry import analyze_failure

    analysis = analyze_failure("WA")
    assert "Wrong Answer" not in analysis["verdict"] or analysis["verdict"] == "WA"
    assert "edge case" in analysis["suggested_approach"].lower() or \
           "off-by-one" in analysis["suggested_approach"].lower()


def test_failure_analysis_tle():
    """Verify TLE diagnosis focuses on complexity."""
    from app.retry_engine.retry import analyze_failure

    analysis = analyze_failure("TLE")
    assert "complexity" in analysis["diagnosis"].lower()
    assert analysis["priority"] == "critical"


def test_failure_analysis_re():
    """Verify RE diagnosis mentions array bounds."""
    from app.retry_engine.retry import analyze_failure

    analysis = analyze_failure("RE", stderr="Segmentation fault")
    assert "stderr_clue" in analysis
    assert "bounds" in analysis["suggested_approach"].lower() or \
           "index" in analysis["suggested_approach"].lower()


def test_global_retry_state():
    """Verify global retry state manager creates and retrieves per-problem state."""
    from app.retry_engine.retry import get_retry_state, reset_retry_state

    state = get_retry_state("TESTPROB")
    assert state.problem_code == "TESTPROB"
    assert state.retry_count == 0

    state.record_attempt("WA", "code")
    state2 = get_retry_state("TESTPROB")
    assert state2.retry_count == 1  # Same object

    reset_retry_state("TESTPROB")
    state3 = get_retry_state("TESTPROB")
    assert state3.retry_count == 0  # Fresh object


# ── Phase 7: Contest Solver ──────────────────────────────────────


def test_contest_state_lifecycle():
    """Verify contest state tracks solving progress correctly."""
    from app.solver.contest_solver import ContestState

    problems = [
        {"code": "A", "name": "Easy"},
        {"code": "B", "name": "Medium"},
        {"code": "C", "name": "Hard"},
    ]
    state = ContestState("TEST100", problems)

    assert len(state.unsolved) == 3
    assert state.progress["solved"] == 0

    state.mark_attempted("A")
    state.mark_solved("A")

    assert state.progress["solved"] == 1
    assert "A" in state.progress["solved_codes"]
    assert len(state.unsolved) == 2


def test_contest_skip_and_revisit():
    """Verify skip → revisit logic in get_next_problem."""
    from app.solver.contest_solver import ContestState

    problems = [
        {"code": "A", "name": "Easy"},
        {"code": "B", "name": "Hard"},
    ]
    state = ContestState("TEST101", problems)

    # First call returns A
    assert state.get_next_problem() == "A"

    # Skip A → next returns B
    state.mark_skipped("A", "too hard right now")
    assert state.get_next_problem() == "B"

    # Skip B too → revisit returns A (skipped set, alphabetically first)
    state.mark_skipped("B")
    next_prob = state.get_next_problem()
    assert next_prob in ("A", "B")

    # Solve everything
    state.mark_solved("A")
    state.mark_solved("B")
    assert state.get_next_problem() is None


# ── Phase 8: Cache Layer ─────────────────────────────────────────


def test_memory_cache_fallback():
    """Verify in-memory cache works when Redis is unavailable."""
    from app.utils.cache import get_cache, set_cache, delete_cache, clear_cache

    clear_cache()

    # Set and get
    set_cache("test_key", {"value": 42})
    result = get_cache("test_key")
    assert result == {"value": 42}

    # Delete
    delete_cache("test_key")
    assert get_cache("test_key") is None

    # Clear
    set_cache("key1", "v1")
    set_cache("key2", "v2")
    clear_cache()
    assert get_cache("key1") is None
    assert get_cache("key2") is None


# ── Phase 9: Database Models ─────────────────────────────────────


@pytest.mark.asyncio
async def test_database_init():
    """Verify database tables can be created without error."""
    from app.models.database import init_db
    # Should not raise
    await init_db()


@pytest.mark.asyncio
async def test_save_and_retrieve_contest():
    """Verify contest can be saved and retrieved."""
    from app.models.database import init_db, save_contest, get_contest

    await init_db()
    await save_contest(
        contest_code="TESTCONTEST",
        name="Test Contest",
        start_date="2026-01-01",
        end_date="2026-01-02",
        problem_count=5,
    )
    contest = await get_contest("TESTCONTEST")
    assert contest is not None
    assert contest.contest_name == "Test Contest"
    assert contest.problem_count == 5


# ── Phase 10: Sandbox Runner (unit-level, no Docker) ─────────────


def test_sandbox_result_success():
    """Verify SandboxResult.success property logic."""
    from app.sandbox.runner import SandboxResult

    ok = SandboxResult(stdout="42\n", exit_code=0)
    assert ok.success is True

    timeout = SandboxResult(exit_code=-1, timed_out=True)
    assert timeout.success is False

    compile_fail = SandboxResult(compile_error="error: expected ';'", exit_code=1)
    assert compile_fail.success is False


def test_sandbox_result_serialization():
    """Verify SandboxResult.to_dict() contains all required keys."""
    from app.sandbox.runner import SandboxResult

    r = SandboxResult(stdout="hello", stderr="", exit_code=0, execution_time=0.123)
    d = r.to_dict()

    assert "stdout" in d
    assert "stderr" in d
    assert "exit_code" in d
    assert "timed_out" in d
    assert "execution_time" in d
    assert "compile_error" in d
    assert "success" in d
    assert d["success"] is True


def test_unsupported_language_returns_error():
    """Verify run_code_in_sandbox returns error for unsupported lang."""
    from app.sandbox.runner import run_code_in_sandbox

    result = run_code_in_sandbox("brainfuck", "+++.")
    assert result.success is False
    assert "Unsupported" in result.stderr

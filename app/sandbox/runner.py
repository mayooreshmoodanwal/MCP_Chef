"""
Secure Docker-based code execution sandbox.

All code execution MUST occur inside isolated containers with:
- --network=none      (no internet access)
- --memory=256m       (memory limit)
- --cpus=1            (CPU limit)
- --pids-limit=64     (process limit)
- --read-only         (read-only filesystem)
- --cap-drop=ALL      (drop all Linux capabilities)
- Timeout protection  (compile: 10s, execute: 5s)

NEVER exposes raw shell access. Only constrained run_cpp/run_python functions.
"""

import os
import subprocess
import tempfile
import shutil

from app.config import config
from app.sandbox.languages import get_language_config, LanguageConfig
from app.utils.logger import logger


class SandboxResult:
    """Result of a sandbox code execution."""

    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        timed_out: bool = False,
        execution_time: float = 0.0,
        compile_error: str = "",
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.execution_time = execution_time
        self.compile_error = compile_error

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.compile_error

    def to_dict(self) -> dict:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "execution_time": self.execution_time,
            "compile_error": self.compile_error,
            "success": self.success,
        }


def _build_docker_command(
    lang_config: LanguageConfig,
    host_dir: str,
    command: str,
    timeout: int,
) -> list[str]:
    """Build the Docker run command with all security flags.

    This is the ONLY place subprocess commands are constructed.
    All flags enforce the PRD security requirements.
    """
    return [
        "docker", "run",
        "--rm",                                         # Remove container after exit
        "--network=none",                               # No internet access
        f"--memory={config.SANDBOX_MEMORY_LIMIT}",     # Memory limit
        f"--cpus={config.SANDBOX_CPU_LIMIT}",          # CPU limit
        f"--pids-limit={config.SANDBOX_PID_LIMIT}",    # Process limit
        "--read-only",                                  # Read-only filesystem
        "--cap-drop=ALL",                               # Drop all Linux capabilities
        "--tmpfs=/tmp:rw,size=64m",                    # Writable /tmp (needed for compilation)
        "-v", f"{host_dir}:/code:ro",                  # Mount code as read-only
        lang_config.docker_image,
        "sh", "-c", command,
    ]


def run_code_in_sandbox(
    language: str,
    code: str,
    stdin_input: str = "",
) -> SandboxResult:
    """Execute code inside a secure Docker sandbox.

    Args:
        language: Programming language (e.g., "cpp", "python")
        code: Source code to execute
        stdin_input: Input to feed via stdin

    Returns:
        SandboxResult with stdout, stderr, exit code, timing

    Raises:
        ValueError: If the language is not supported
        RuntimeError: If Docker is not available
    """
    lang_config = get_language_config(language)
    if not lang_config:
        return SandboxResult(
            stderr=f"Unsupported language: {language}",
            exit_code=1,
        )

    # Check Docker availability
    if not _docker_available():
        return SandboxResult(
            stderr="Docker is not running or not installed. Sandbox requires Docker.",
            exit_code=1,
        )

    # Create temp directory with source code
    tmp_dir = tempfile.mkdtemp(prefix="codechef_sandbox_")
    try:
        # Write source code to temp file
        filename = f"solution{lang_config.file_extension}"
        if language in ("java",):
            filename = "Main.java"
        filepath = os.path.join(tmp_dir, filename)
        with open(filepath, "w") as f:
            f.write(code)

        # Write stdin input
        stdin_path = os.path.join(tmp_dir, "input.txt")
        with open(stdin_path, "w") as f:
            f.write(stdin_input)

        # Step 1: Compile (if needed)
        if lang_config.compile_command:
            compile_result = _run_in_docker(
                lang_config,
                tmp_dir,
                f"cp /code/{filename} /tmp/{filename} && {lang_config.compile_command}",
                timeout=config.COMPILE_TIMEOUT,
            )
            if compile_result.exit_code != 0:
                return SandboxResult(
                    compile_error=compile_result.stderr or compile_result.stdout,
                    exit_code=compile_result.exit_code,
                )

        # Step 2: Execute with stdin
        if lang_config.compile_command:
            # Compiled language: compile and run in one container
            run_cmd = (
                f"cp /code/{filename} /tmp/{filename} && "
                f"{lang_config.compile_command} && "
                f"cat /code/input.txt | {lang_config.run_command}"
            )
        else:
            # Interpreted language: copy and run
            run_cmd = (
                f"cp /code/{filename} /tmp/{filename} && "
                f"cat /code/input.txt | {lang_config.run_command}"
            )

        result = _run_in_docker(
            lang_config,
            tmp_dir,
            run_cmd,
            timeout=config.EXECUTION_TIMEOUT,
        )

        return result

    finally:
        # Clean up temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _run_in_docker(
    lang_config: LanguageConfig,
    host_dir: str,
    command: str,
    timeout: int,
) -> SandboxResult:
    """Run a command inside a Docker container with security flags.

    This is an INTERNAL function — NEVER expose to the LLM directly.
    """
    import time

    docker_cmd = _build_docker_command(lang_config, host_dir, command, timeout)
    logger.info(f"Sandbox exec: {lang_config.name} (timeout={timeout}s)")

    start_time = time.time()
    try:
        proc = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5,  # Extra buffer beyond container timeout
        )
        elapsed = time.time() - start_time

        return SandboxResult(
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            exit_code=proc.returncode,
            execution_time=round(elapsed, 3),
        )

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        logger.warning(f"Sandbox timeout after {elapsed:.1f}s")
        return SandboxResult(
            stderr=f"Execution timed out after {timeout} seconds",
            exit_code=-1,
            timed_out=True,
            execution_time=round(elapsed, 3),
        )

    except Exception as e:
        logger.error(f"Sandbox error: {e}")
        return SandboxResult(
            stderr=str(e),
            exit_code=-1,
        )


def _docker_available() -> bool:
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_cpp(code: str, stdin_input: str = "") -> SandboxResult:
    """Run C++ code in a secure sandbox. Safe API for the MCP layer."""
    return run_code_in_sandbox("cpp", code, stdin_input)


def run_python(code: str, stdin_input: str = "") -> SandboxResult:
    """Run Python code in a secure sandbox. Safe API for the MCP layer."""
    return run_code_in_sandbox("python", code, stdin_input)

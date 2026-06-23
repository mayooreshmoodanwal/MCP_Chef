"""
Language-specific configurations for the sandbox runner.

Defines Docker images, compile commands, and run commands for each
supported programming language.
"""

from dataclasses import dataclass


@dataclass
class LanguageConfig:
    """Configuration for a supported programming language."""

    name: str
    docker_image: str
    file_extension: str
    compile_command: str | None  # None for interpreted languages
    run_command: str
    codechef_id: str  # CodeChef language identifier


# Supported language configurations
LANGUAGES: dict[str, LanguageConfig] = {
    "cpp": LanguageConfig(
        name="C++17",
        docker_image="gcc:13",
        file_extension=".cpp",
        compile_command="g++ -std=c++17 -O2 -o /tmp/solution /tmp/solution.cpp",
        run_command="/tmp/solution",
        codechef_id="cpp17",
    ),
    "cpp14": LanguageConfig(
        name="C++14",
        docker_image="gcc:13",
        file_extension=".cpp",
        compile_command="g++ -std=c++14 -O2 -o /tmp/solution /tmp/solution.cpp",
        run_command="/tmp/solution",
        codechef_id="cpp14",
    ),
    "python": LanguageConfig(
        name="Python 3",
        docker_image="python:3.12-slim",
        file_extension=".py",
        compile_command=None,
        run_command="python3 /tmp/solution.py",
        codechef_id="python3",
    ),
    "java": LanguageConfig(
        name="Java",
        docker_image="eclipse-temurin:21-jdk",
        file_extension=".java",
        compile_command="javac -d /tmp /tmp/Main.java",
        run_command="java -cp /tmp Main",
        codechef_id="java",
    ),
    "go": LanguageConfig(
        name="Go",
        docker_image="golang:1.22-alpine",
        file_extension=".go",
        compile_command="go build -o /tmp/solution /tmp/solution.go",
        run_command="/tmp/solution",
        codechef_id="go",
    ),
    "rust": LanguageConfig(
        name="Rust",
        docker_image="rust:1.75-slim",
        file_extension=".rs",
        compile_command="rustc -O -o /tmp/solution /tmp/solution.rs",
        run_command="/tmp/solution",
        codechef_id="rust",
    ),
}


# Aliases
LANGUAGES["c++"] = LANGUAGES["cpp"]
LANGUAGES["python3"] = LANGUAGES["python"]
LANGUAGES["cpp17"] = LANGUAGES["cpp"]


def get_language_config(language: str) -> LanguageConfig | None:
    """Get the configuration for a language.

    Args:
        language: Language name or alias (e.g., "cpp", "python", "c++")

    Returns:
        LanguageConfig or None if unsupported
    """
    return LANGUAGES.get(language.lower())


def supported_languages() -> list[str]:
    """Return list of supported language names (no aliases)."""
    seen = set()
    result = []
    for key, lang in LANGUAGES.items():
        if lang.name not in seen:
            seen.add(lang.name)
            result.append(key)
    return result

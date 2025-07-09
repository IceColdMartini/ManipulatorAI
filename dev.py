#!/usr/bin/env python3
"""
Development management script for ManipulatorAI

This script provides common development tasks like running tests,
formatting code, starting the development server, etc.

Usage:
    python dev.py <command>

Commands:
    test        - Run the test suite
    format      - Format code with black and isort
    lint        - Run linting with ruff and mypy
    serve       - Start the development server
    install     - Install all dependencies
    clean       - Clean up generated files
    check       - Run all quality checks (format, lint, test)
"""

import os
import shlex
import subprocess  # nosec B404 - subprocess is safe when used properly
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"📍 {description}")
    # Parse the command safely using shlex to avoid shell injection
    args = shlex.split(cmd)
    result = subprocess.run(args, capture_output=False)  # nosec B603 - Not using shell=True
    success = result.returncode == 0
    print(f"{'✅' if success else '❌'} {description} {'completed' if success else 'failed'}")
    return success


def main() -> None:
    """Main entry point for the development script."""
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Activate virtual environment command prefix
    venv_prefix = "source venv/bin/activate &&" if os.path.exists("venv/bin/activate") else ""

    if command == "test":
        print("🧪 Running test suite...")
        success = run_command(
            f"{venv_prefix} python -m pytest tests/ -v --cov-report=term-missing",
            "Running tests with coverage",
        )

    elif command == "format":
        print("🎨 Formatting code...")
        success = True
        success &= run_command(f"{venv_prefix} black src/ tests/", "Formatting with Black")
        success &= run_command(f"{venv_prefix} isort src/ tests/", "Sorting imports with isort")

    elif command == "lint":
        print("🔍 Running linting...")
        success = True
        success &= run_command(f"{venv_prefix} ruff check src/ tests/", "Linting with Ruff")
        success &= run_command(f"{venv_prefix} mypy src/", "Type checking with mypy")

    elif command == "serve":
        print("🚀 Starting development server...")
        success = run_command(
            f"{venv_prefix} python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000",
            "Starting development server",
        )

    elif command == "install":
        print("📦 Installing dependencies...")
        success = True
        success &= run_command("python -m venv venv", "Creating virtual environment")
        success &= run_command(f"{venv_prefix} pip install --upgrade pip", "Upgrading pip")
        success &= run_command(
            f"{venv_prefix} pip install -r requirements.txt", "Installing main dependencies"
        )
        success &= run_command(
            f"{venv_prefix} pip install -r requirements-dev.txt", "Installing dev dependencies"
        )
        success &= run_command(f"{venv_prefix} pre-commit install", "Installing pre-commit hooks")

    elif command == "clean":
        print("🧹 Cleaning up...")
        success = True
        success &= run_command(
            "rm -rf __pycache__ src/__pycache__ tests/__pycache__", "Removing __pycache__"
        )
        success &= run_command(
            "rm -rf .pytest_cache htmlcov .coverage coverage.xml", "Removing test artifacts"
        )
        success &= run_command("rm -rf .mypy_cache .ruff_cache", "Removing linter caches")

    elif command == "check":
        print("🔎 Running all quality checks...")
        success = True
        success &= run_command(f"{venv_prefix} black --check src/ tests/", "Checking code format")
        success &= run_command(
            f"{venv_prefix} isort --check-only src/ tests/", "Checking import order"
        )
        success &= run_command(f"{venv_prefix} ruff check src/ tests/", "Linting with Ruff")
        success &= run_command(f"{venv_prefix} mypy src/", "Type checking with mypy")
        success &= run_command(f"{venv_prefix} python -m pytest tests/ -v", "Running tests")

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    if success:
        print(f"🎉 {command.capitalize()} completed successfully!")
        sys.exit(0)
    else:
        print(f"💥 {command.capitalize()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Linting and formatting scripts."""

import subprocess
import sys


def lint():
    """Run ruff check."""
    result = subprocess.run(
        ["ruff", "check", "src"],
        check=False,
    )
    sys.exit(result.returncode)


def format_code():
    """Format code with ruff."""
    subprocess.run(["ruff", "format", "src"], check=True)
    subprocess.run(["ruff", "check", "--fix", "src"], check=True)
    print("✓ Code formatted")


def lint_fix():
    """Auto-fix linting issues."""
    subprocess.run(["ruff", "check", "--fix", "src"], check=True)
    print("✓ Linting issues fixed")


if __name__ == "__main__":
    lint()

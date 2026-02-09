#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run code validation checks for the project.

Runs one or more validation checks: linting (ruff check), formatting
(ruff format --check), type checking (ty check), docstring validation
(pydoclint), and tests (pytest --cov). All selected checks run independently
— a failure in one does not prevent others from running.

Usage:
    uv run python .claude/scripts/validate_code.py              # all checks
    uv run python .claude/scripts/validate_code.py --lint       # lint only
    uv run python .claude/scripts/validate_code.py --lint --type src/  # lint + type on src/
    uv run python .claude/scripts/validate_code.py --test tests/unit/  # tests on specific dir

Exit codes:
    0 - All selected checks passed
    1 - One or more checks failed
"""

# ruff: noqa: S105, S404, S603, S607

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from typing import Final

EXIT_SUCCESS: Final[int] = 0
EXIT_FAILURE: Final[int] = 1

_PASS: Final[str] = "PASS"
_FAIL: Final[str] = "FAIL"


def run_lint(paths: list[str]) -> bool:
    """Run ruff linting checks.

    Args:
        paths (list[str]): Files or directories to check.

    Returns:
        bool: True if linting passed, False otherwise.
    """
    print("\n--- Lint (ruff check) ---")
    result = subprocess.run(["uv", "run", "ruff", "check", *paths], check=False)
    passed = result.returncode == 0
    print(f"--- Lint: {_PASS if passed else _FAIL} ---\n")
    return passed


def run_format_check(paths: list[str]) -> bool:
    """Run ruff formatting checks (read-only).

    Args:
        paths (list[str]): Files or directories to check.

    Returns:
        bool: True if formatting passed, False otherwise.
    """
    print("\n--- Format (ruff format --check) ---")
    result = subprocess.run(["uv", "run", "ruff", "format", "--check", *paths], check=False)
    passed = result.returncode == 0
    print(f"--- Format: {_PASS if passed else _FAIL} ---\n")
    return passed


def run_type_check(paths: list[str]) -> bool:
    """Run type checking with ty.

    Args:
        paths (list[str]): Files or directories to check.

    Returns:
        bool: True if type checking passed, False otherwise.
    """
    print("\n--- Type Check (ty check) ---")
    result = subprocess.run(["uv", "run", "ty", "check", *paths], check=False)
    passed = result.returncode == 0
    print(f"--- Type Check: {_PASS if passed else _FAIL} ---\n")
    return passed


def run_doctest(paths: list[str]) -> bool:
    """Run doctest validation with pytest.

    Args:
        paths (list[str]): Files or directories to check.

    Returns:
        bool: True if all doctests passed, False otherwise.
    """
    print("\n--- Doctest (pytest --doctest-modules) ---")
    result = subprocess.run(["uv", "run", "pytest", "--doctest-modules", *paths], check=False)
    passed = result.returncode == 0
    print(f"--- Doctest: {_PASS if passed else _FAIL} ---\n")
    return passed


def run_docstring_check(paths: list[str]) -> bool:
    """Run docstring validation with pydoclint.

    Args:
        paths (list[str]): Files or directories to check.

    Returns:
        bool: True if docstring validation passed, False otherwise.
    """
    print("\n--- Docstring (pydoclint) ---")
    result = subprocess.run(
        ["uv", "tool", "run", "pydoclint", "--style=google", "--allow-init-docstring=True", *paths],
        check=False,
    )
    passed = result.returncode == 0
    print(f"--- Docstring: {_PASS if passed else _FAIL} ---\n")
    return passed


def run_tests(paths: list[str]) -> bool:
    """Run tests with pytest and coverage.

    Args:
        paths (list[str]): Files or directories to test.

    Returns:
        bool: True if all tests passed, False otherwise.
    """
    print("\n--- Tests (pytest --cov) ---")
    result = subprocess.run(["uv", "run", "pytest", "--cov", *paths], check=False)
    passed = result.returncode == 0
    print(f"--- Tests: {_PASS if passed else _FAIL} ---\n")
    return passed


CHECK_REGISTRY: Final[dict[str, tuple[str, Callable[[list[str]], bool]]]] = {
    "lint": ("Lint", run_lint),
    "format": ("Format", run_format_check),
    "type": ("Type Check", run_type_check),
    "docstring": ("Docstring", run_docstring_check),
    "doctest": ("Doctest", run_doctest),
    "test": ("Tests", run_tests),
}


def run_checks(selected: list[str], paths: list[str]) -> bool:
    """Run selected validation checks.

    Args:
        selected (list[str]): List of check keys to run (from CHECK_REGISTRY).
        paths (list[str]): Files or directories to validate.

    Returns:
        bool: True if all selected checks passed, False otherwise.
    """
    results: dict[str, bool] = {}

    for key in selected:
        label, check_fn = CHECK_REGISTRY[key]
        results[label] = check_fn(paths)

    # Summary
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print("=" * 40)
    print(f"  {passed}/{total} checks passed", end="")
    if failed:
        failed_names = [name for name, ok in results.items() if not ok]
        print(f"  (failed: {', '.join(failed_names)})")
    else:
        print()
    print(f"  Overall: {_PASS if failed == 0 else _FAIL}")
    print("=" * 40)

    return failed == 0


def main() -> None:
    """Entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Run code validation checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s                      # all checks on project root\n"
            "  %(prog)s --lint --type        # lint + type check only\n"
            "  %(prog)s --test tests/unit/   # tests on specific directory\n"
            "  %(prog)s --lint src/          # lint on src/ only\n"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="files or directories to validate (default: current directory)",
    )
    parser.add_argument("--lint", action="store_true", help="run ruff check")
    parser.add_argument("--format", action="store_true", help="run ruff format --check")
    parser.add_argument("--type", action="store_true", help="run ty check")
    parser.add_argument("--docstring", action="store_true", help="run pydoclint")
    parser.add_argument("--doctest", action="store_true", help="run pytest --doctest-modules")
    parser.add_argument("--test", action="store_true", help="run pytest --cov")
    parser.add_argument("--all", action="store_true", dest="run_all", help="run all checks (same as no flags)")

    args = parser.parse_args()

    # Determine which checks to run
    flags = {
        "lint": args.lint,
        "format": args.format,
        "type": args.type,
        "docstring": args.docstring,
        "doctest": args.doctest,
        "test": args.test,
    }

    any_flag_set = any(flags.values())

    if args.run_all or not any_flag_set:
        selected = list(CHECK_REGISTRY.keys())
    else:
        selected = [key for key, enabled in flags.items() if enabled]

    all_passed = run_checks(selected, args.paths)
    sys.exit(EXIT_SUCCESS if all_passed else EXIT_FAILURE)


if __name__ == "__main__":
    main()

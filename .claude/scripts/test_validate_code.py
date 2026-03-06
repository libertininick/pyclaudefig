"""Tests for the code validation script.

This module tests validate_code.py using real subprocess invocations wherever
possible. Only one test uses mocking: exception propagation from subprocess.run,
which cannot be triggered with real tools.
"""

# ruff: noqa: FBT001, PLR6301, S101, S404, S603, S607 # this is a test module

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import validate_code
from pytest_check import check

_SCRIPT_PATH = str(Path(__file__).resolve().parent / "validate_code.py")


# region Fixtures


@pytest.fixture
def clean_python_file(tmp_path: Path) -> str:
    """Create a Python file that passes lint and format checks.

    Args:
        tmp_path (Path): Pytest temporary directory.

    Returns:
        str: Path to the clean file.
    """
    f = tmp_path / "clean.py"
    f.write_text('"""A clean module."""\n\nx = 1\n')
    return str(f)


@pytest.fixture
def lint_failing_file(tmp_path: Path) -> str:
    """Create a Python file with unused imports (fails lint, passes format).

    Args:
        tmp_path (Path): Pytest temporary directory.

    Returns:
        str: Path to the file with lint errors.
    """
    f = tmp_path / "bad_lint.py"
    f.write_text("import os\nimport sys\n\nprint('unused imports')\n")
    return str(f)


@pytest.fixture
def multi_failing_file(tmp_path: Path) -> str:
    """Create a Python file that fails both lint and format checks.

    Args:
        tmp_path (Path): Pytest temporary directory.

    Returns:
        str: Path to the file with lint and format errors.
    """
    f = tmp_path / "bad_multi.py"
    f.write_text("import os\nx=1\n")
    return str(f)


# endregion

# region Check Functions — real subprocess, no mocking


class TestCheckFunctions:
    """Smoke tests for individual check functions with real subprocess."""

    def test_run_lint_clean_returns_true(self, clean_python_file: str) -> None:
        """run_lint on a clean file should return True."""
        assert validate_code.run_lint([clean_python_file]) is True

    def test_run_lint_bad_returns_false(self, lint_failing_file: str) -> None:
        """run_lint on a file with unused imports should return False."""
        assert validate_code.run_lint([lint_failing_file]) is False

    def test_run_format_check_clean_returns_true(self, clean_python_file: str) -> None:
        """run_format_check on a well-formatted file should return True."""
        assert validate_code.run_format_check([clean_python_file]) is True

    def test_run_type_check_clean_returns_true(self, clean_python_file: str) -> None:
        """run_type_check on a type-correct file should return True."""
        assert validate_code.run_type_check([clean_python_file]) is True

    def test_run_doctest_clean_returns_true(self, tmp_path: Path) -> None:
        """run_doctest on a file with a passing doctest should return True."""
        f = tmp_path / "with_doctest.py"
        f.write_text(
            '"""Module with doctest."""\n\n\n'
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers.\n\n'
            "    >>> add(1, 2)\n"
            "    3\n"
            '    """\n'
            "    return a + b\n"
        )
        assert validate_code.run_doctest([str(f)]) is True

    def test_run_docstring_check_clean_returns_true(self, tmp_path: Path) -> None:
        """run_docstring_check on a properly documented file should return True."""
        f = tmp_path / "documented.py"
        f.write_text(
            '"""Documented module."""\n\n\n'
            "def greet(name: str) -> str:\n"
            '    """Greet someone.\n\n'
            "    Args:\n"
            "        name (str): The name.\n\n"
            "    Returns:\n"
            "        str: The greeting.\n"
            '    """\n'
            '    return f"Hello, {name}"\n'
        )
        assert validate_code.run_docstring_check([str(f)]) is True


# endregion

# region CHECK_REGISTRY — structural validation, no subprocess


class TestCheckRegistry:
    """Tests for CHECK_REGISTRY structure and contents."""

    def test_contains_all_checks(self) -> None:
        """CHECK_REGISTRY should contain all expected check types."""
        expected_keys = {"lint", "format", "type", "docstring", "doctest", "test"}
        assert set(validate_code.CHECK_REGISTRY.keys()) == expected_keys

    def test_entries_have_label_and_function(self) -> None:
        """Each CHECK_REGISTRY entry should have a label string and callable function."""
        for key, (label, func) in validate_code.CHECK_REGISTRY.items():
            with check:
                assert isinstance(label, str), (
                    f"Check '{key}' should have a string label"
                )
            with check:
                assert callable(func), f"Check '{key}' should have a callable function"


# endregion

# region run_checks — orchestration logic, real subprocess (1 mock for exception)


class TestRunChecks:
    """Tests for run_checks orchestration function.

    All tests use real subprocess invocations except
    test_subprocess_exception_propagates, which requires simulating
    a FileNotFoundError that cannot occur when tools are installed.
    """

    def test_all_selected_pass_returns_true(self, clean_python_file: str) -> None:
        """run_checks should return True when all selected checks pass."""
        result = validate_code.run_checks(["lint", "format"], [clean_python_file])
        assert result is True

    def test_any_fail_returns_false(self, lint_failing_file: str) -> None:
        """run_checks should return False when any check fails.

        lint_failing_file fails lint but passes format, so the combined
        result should be False.
        """
        result = validate_code.run_checks(["lint", "format"], [lint_failing_file])
        assert result is False

    def test_all_selected_fail_returns_false(self, multi_failing_file: str) -> None:
        """run_checks should return False when all selected checks fail."""
        result = validate_code.run_checks(["lint", "format"], [multi_failing_file])
        assert result is False

    def test_single_pass_returns_true(self, clean_python_file: str) -> None:
        """run_checks with a single passing check should return True."""
        result = validate_code.run_checks(["lint"], [clean_python_file])
        assert result is True

    def test_single_fail_returns_false(self, lint_failing_file: str) -> None:
        """run_checks with a single failing check should return False."""
        result = validate_code.run_checks(["lint"], [lint_failing_file])
        assert result is False

    def test_empty_selected_returns_true(self) -> None:
        """run_checks with no selected checks should return True."""
        result = validate_code.run_checks([], ["."])
        assert result is True

    def test_invalid_check_key_raises_key_error(self) -> None:
        """run_checks with an unrecognized check key should raise KeyError."""
        with pytest.raises(KeyError):
            validate_code.run_checks(["invalid_key"], ["."])

    def test_subprocess_exception_propagates(self) -> None:
        """Exceptions from subprocess.run should propagate to the caller.

        This is the only mocked test: a FileNotFoundError cannot be triggered
        when uv is installed, but the propagation behavior should be documented.
        """
        with (
            patch.object(
                subprocess, "run", side_effect=FileNotFoundError("uv not found")
            ),
            pytest.raises(FileNotFoundError, match="uv not found"),
        ):
            validate_code.run_checks(["lint"], ["."])


# endregion

# region CLI — real subprocess invocations, no mocking


class TestCli:
    """Integration tests for CLI argument parsing and execution.

    All tests run the actual script via subprocess.run and assert on
    exit codes and stdout content. Temporary files ensure predictable results.
    """

    def test_help_flag_exits_zero(self) -> None:
        """CLI with --help should exit with code 0 and print usage."""
        result = subprocess.run(
            ["uv", "run", "python", _SCRIPT_PATH, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        with check:
            assert result.returncode == 0
        with check:
            assert "usage:" in result.stdout.lower()
        with check:
            assert "--lint" in result.stdout

    def test_lint_clean_file_exits_zero(self, tmp_path: Path) -> None:
        """CLI with --lint on a clean file should exit with code 0."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('"""A clean module."""\n\nx = 1\n')

        result = subprocess.run(
            ["uv", "run", "python", _SCRIPT_PATH, "--lint", str(clean_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == validate_code.EXIT_SUCCESS

    def test_lint_bad_file_exits_one(self, tmp_path: Path) -> None:
        """CLI with --lint on a file with lint errors should exit with code 1."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("import os\nimport sys\n\nprint('unused imports')\n")

        result = subprocess.run(
            ["uv", "run", "python", _SCRIPT_PATH, "--lint", str(bad_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == validate_code.EXIT_FAILURE

    def test_multiple_flags_runs_multiple_checks(self, tmp_path: Path) -> None:
        """CLI with multiple flags should run all selected checks."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('"""A clean module."""\n\nx = 1\n')

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                _SCRIPT_PATH,
                "--lint",
                "--format",
                str(clean_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        with check:
            assert "Lint" in result.stdout
        with check:
            assert "Format" in result.stdout
        with check:
            assert result.returncode == validate_code.EXIT_SUCCESS

    def test_all_flag_runs_all_checks(self, tmp_path: Path) -> None:
        """CLI with --all flag should run all checks."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('"""A clean module."""\n\nx = 1\n')

        result = subprocess.run(
            ["uv", "run", "python", _SCRIPT_PATH, "--all", str(clean_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        with check:
            assert "Lint" in result.stdout
        with check:
            assert "Format" in result.stdout
        with check:
            assert "Type Check" in result.stdout
        with check:
            assert "Docstring" in result.stdout

    def test_custom_path_argument(self, tmp_path: Path) -> None:
        """CLI should accept and use a custom path argument."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        clean_file = subdir / "module.py"
        clean_file.write_text('"""A clean module."""\n\nx = 1\n')

        result = subprocess.run(
            ["uv", "run", "python", _SCRIPT_PATH, "--lint", str(clean_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == validate_code.EXIT_SUCCESS

    def test_multiple_path_arguments(self, tmp_path: Path) -> None:
        """CLI should accept and use multiple path arguments."""
        file1 = tmp_path / "module1.py"
        file1.write_text('"""Module 1."""\n\nx = 1\n')
        file2 = tmp_path / "module2.py"
        file2.write_text('"""Module 2."""\n\ny = 2\n')

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                _SCRIPT_PATH,
                "--lint",
                str(file1),
                str(file2),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == validate_code.EXIT_SUCCESS


# endregion

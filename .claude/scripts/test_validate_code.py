"""Tests for the code validation script.

This module provides comprehensive tests for validate_code.py, covering
individual check functions, check orchestration, CLI argument parsing,
and exit codes.
"""

# ruff: noqa: FBT001, PLR6301, S101, S404 # this is a test module

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest
import validate_code
from pytest_check import check

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

# Maps each check key -> (function, expected subprocess command prefix)
_CHECK_COMMANDS: dict[str, tuple[str, list[str]]] = {
    "lint": ("run_lint", ["uv", "run", "ruff", "check"]),
    "format": ("run_format_check", ["uv", "run", "ruff", "format", "--check"]),
    "type": ("run_type_check", ["uv", "run", "ty", "check"]),
    "doctest": ("run_doctest", ["uv", "run", "pytest", "--doctest-modules"]),
    "docstring": (
        "run_docstring_check",
        [
            "uv",
            "tool",
            "run",
            "pydoclint",
            "--style=google",
            "--allow-init-docstring=True",
        ],
    ),
    "test": ("run_tests", ["uv", "run", "pytest", "--cov"]),
}

_CHECK_KEYS = sorted(_CHECK_COMMANDS)


class TestIndividualCheckFunctions:
    """Tests for individual check functions (run_lint, run_format_check, etc.)."""

    @pytest.mark.parametrize("key", _CHECK_KEYS)
    def test_check_success_returns_true(self, key: str) -> None:
        """Each check function should return True when subprocess returns code 0.

        Args:
            key (str): Check key from _CHECK_COMMANDS.
        """
        func_name, _ = _CHECK_COMMANDS[key]
        func = getattr(validate_code, func_name)
        mock_result = MagicMock(returncode=0)

        with patch.object(subprocess, "run", return_value=mock_result):
            result = func(["."])

        assert result is True

    @pytest.mark.parametrize("key", _CHECK_KEYS)
    def test_check_failure_returns_false(self, key: str) -> None:
        """Each check function should return False when subprocess returns non-zero code.

        Args:
            key (str): Check key from _CHECK_COMMANDS.
        """
        func_name, _ = _CHECK_COMMANDS[key]
        func = getattr(validate_code, func_name)
        mock_result = MagicMock(returncode=1)

        with patch.object(subprocess, "run", return_value=mock_result):
            result = func(["."])

        assert result is False

    @pytest.mark.parametrize("key", _CHECK_KEYS)
    def test_check_calls_correct_command(self, key: str) -> None:
        """Each check function should invoke its expected subprocess command.

        Args:
            key (str): Check key from _CHECK_COMMANDS.
        """
        func_name, expected_prefix = _CHECK_COMMANDS[key]
        func = getattr(validate_code, func_name)
        mock_result = MagicMock(returncode=0)
        paths = ["src/", "tests/"]

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            func(paths)

        mock_run.assert_called_once_with([*expected_prefix, *paths], check=False)


class TestCheckRegistry:
    """Tests for CHECK_REGISTRY structure and contents."""

    def test_check_registry_contains_all_checks(self) -> None:
        """CHECK_REGISTRY should contain all expected check types."""
        expected_keys = {"lint", "format", "type", "docstring", "doctest", "test"}
        with check:
            assert set(validate_code.CHECK_REGISTRY.keys()) == expected_keys

    def test_check_registry_entries_have_label_and_function(self) -> None:
        """Each CHECK_REGISTRY entry should have a label string and callable function."""
        for key, (label, func) in validate_code.CHECK_REGISTRY.items():
            with check:
                assert isinstance(label, str), (
                    f"Check '{key}' should have a string label"
                )
            with check:
                assert callable(func), f"Check '{key}' should have a callable function"

    @pytest.mark.parametrize(
        ("key", "expected_func_name"),
        [
            ("lint", "run_lint"),
            ("format", "run_format_check"),
            ("type", "run_type_check"),
            ("docstring", "run_docstring_check"),
            ("doctest", "run_doctest"),
            ("test", "run_tests"),
        ],
    )
    def test_check_registry_maps_to_correct_function(
        self, key: str, expected_func_name: str
    ) -> None:
        """Each CHECK_REGISTRY entry should map to the correct check function.

        Args:
            key (str): Registry key to look up.
            expected_func_name (str): Name of the expected function on validate_code.
        """
        _, func = validate_code.CHECK_REGISTRY[key]
        assert func is getattr(validate_code, expected_func_name)


class TestRunChecks:
    """Tests for run_checks orchestration function."""

    def test_all_pass_returns_true(self) -> None:
        """run_checks should return True when all selected checks pass."""
        mock_result = MagicMock(returncode=0)

        with patch.object(subprocess, "run", return_value=mock_result):
            result = validate_code.run_checks(["lint", "format"], ["."])

        assert result is True

    def test_some_fail_returns_false(self) -> None:
        """run_checks should return False when some checks fail."""
        mock_results = [MagicMock(returncode=0), MagicMock(returncode=1)]

        with patch.object(subprocess, "run", side_effect=mock_results):
            result = validate_code.run_checks(["lint", "format"], ["."])

        assert result is False

    def test_all_fail_returns_false(self) -> None:
        """run_checks should return False when all checks fail."""
        mock_result = MagicMock(returncode=1)

        with patch.object(subprocess, "run", return_value=mock_result):
            result = validate_code.run_checks(["lint", "format", "type"], ["."])

        assert result is False

    def test_runs_all_selected_checks(self) -> None:
        """run_checks should run all selected checks even if some fail."""
        mock_results = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
            MagicMock(returncode=0),
        ]

        with patch.object(subprocess, "run", side_effect=mock_results) as mock_run:
            validate_code.run_checks(["lint", "format", "type"], ["."])

        assert mock_run.call_count == 3

    def test_passes_paths_to_each_check(self) -> None:
        """run_checks should pass provided paths to each check function."""
        mock_result = MagicMock(returncode=0)
        paths = ["src/", "tests/"]

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            validate_code.run_checks(["lint"], paths)

        mock_run.assert_called_once_with(
            ["uv", "run", "ruff", "check", *paths], check=False
        )

    def test_empty_selected_returns_true(self) -> None:
        """run_checks with no selected checks should return True."""
        result = validate_code.run_checks([], ["."])
        assert result is True

    @pytest.mark.parametrize("returncode,expected", [(0, True), (1, False)])
    def test_single_check_returns_expected(
        self, returncode: int, expected: bool
    ) -> None:
        """run_checks with single check should reflect that check's result.

        Args:
            returncode (int): Simulated subprocess return code.
            expected (bool): Expected boolean result from run_checks.
        """
        mock_result = MagicMock(returncode=returncode)

        with patch.object(subprocess, "run", return_value=mock_result):
            result = validate_code.run_checks(["type"], ["."])

        assert result is expected


class TestCliArgumentParsing:
    """Tests for CLI argument parsing and check selection logic."""

    def test_no_flags_runs_all_checks(self) -> None:
        """main() with no flags should run all checks."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_SUCCESS

    def test_all_flag_runs_all_checks(self) -> None:
        """main() with --all flag should run all checks."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py", "--all"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_SUCCESS

    @pytest.mark.parametrize(
        ("flag", "expected_tokens"),
        [
            ("--lint", ["ruff", "check"]),
            ("--format", ["ruff", "format"]),
            ("--type", ["ty", "check"]),
            ("--docstring", ["pydoclint"]),
            ("--doctest", ["pytest", "--doctest-modules"]),
            ("--test", ["pytest", "--cov"]),
        ],
    )
    def test_single_flag_runs_only_that_check(
        self, flag: str, expected_tokens: list[str]
    ) -> None:
        """main() with a single flag should run only the corresponding check.

        Args:
            flag (str): CLI flag to pass to main().
            expected_tokens (list[str]): Tokens expected in the subprocess command.
        """
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            patch("sys.argv", ["validate_code.py", flag]),
            pytest.raises(SystemExit),
        ):
            validate_code.main()

        assert mock_run.call_count == 1
        call_args = mock_run.call_args[0][0]
        for token in expected_tokens:
            with check:
                assert token in call_args

    def test_multiple_flags_runs_selected_checks(self) -> None:
        """main() with multiple flags should run only those checks."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            patch("sys.argv", ["validate_code.py", "--lint", "--type"]),
            pytest.raises(SystemExit),
        ):
            validate_code.main()

        assert mock_run.call_count == 2

    def test_default_path_is_current_directory(self) -> None:
        """main() without path argument should use current directory."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            patch("sys.argv", ["validate_code.py", "--lint"]),
            pytest.raises(SystemExit),
        ):
            validate_code.main()

        call_args = mock_run.call_args[0][0]
        assert "." in call_args

    def test_single_path_argument(self) -> None:
        """main() should accept and use single path argument."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            patch("sys.argv", ["validate_code.py", "--lint", "src/"]),
            pytest.raises(SystemExit),
        ):
            validate_code.main()

        call_args = mock_run.call_args[0][0]
        assert "src/" in call_args

    def test_multiple_path_arguments(self) -> None:
        """main() should accept and use multiple path arguments."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            patch("sys.argv", ["validate_code.py", "--type", "src/", "tests/"]),
            pytest.raises(SystemExit),
        ):
            validate_code.main()

        call_args = mock_run.call_args[0][0]
        with check:
            assert "src/" in call_args
        with check:
            assert "tests/" in call_args


class TestExitCodes:
    """Tests for main() function exit codes."""

    def test_all_checks_pass_exits_zero(self) -> None:
        """main() should exit with code 0 when all checks pass."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_SUCCESS

    def test_single_check_fails_exits_one(self) -> None:
        """main() should exit with code 1 when a check fails."""
        mock_result = MagicMock(returncode=1)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py", "--lint"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_FAILURE

    def test_some_checks_fail_exits_one(self) -> None:
        """main() should exit with code 1 when some checks fail."""
        mock_results = [MagicMock(returncode=0), MagicMock(returncode=1)]

        with (
            patch.object(subprocess, "run", side_effect=mock_results),
            patch("sys.argv", ["validate_code.py", "--lint", "--format"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_FAILURE

    def test_all_checks_fail_exits_one(self) -> None:
        """main() should exit with code 1 when all checks fail."""
        mock_result = MagicMock(returncode=1)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py", "--lint", "--format", "--type"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_FAILURE

    def test_selected_checks_all_pass_exits_zero(self) -> None:
        """main() should exit with code 0 when all selected checks pass."""
        mock_result = MagicMock(returncode=0)

        with (
            patch.object(subprocess, "run", return_value=mock_result),
            patch("sys.argv", ["validate_code.py", "--docstring", "--test"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_code.main()

        assert exc_info.value.code == validate_code.EXIT_SUCCESS


class TestConstants:
    """Tests for module-level constants."""

    def test_exit_success_constant_is_zero(self) -> None:
        """EXIT_SUCCESS constant should be 0."""
        assert validate_code.EXIT_SUCCESS == 0

    def test_exit_failure_constant_is_one(self) -> None:
        """EXIT_FAILURE constant should be 1."""
        assert validate_code.EXIT_FAILURE == 1

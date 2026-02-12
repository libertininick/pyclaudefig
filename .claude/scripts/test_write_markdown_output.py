"""Tests for the write_markdown_output module.

This module provides comprehensive tests for write_markdown_output.py, covering
timestamp generation, file writing, CLI argument parsing, and error handling.
"""

# ruff: noqa: S101

from __future__ import annotations

import argparse
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pytest_check import check
from write_markdown_output import (
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    EXIT_WRITE_ERROR,
    WriteError,
    _build_argument_parser,
    generate_timestamp,
    main,
    write_markdown_output,
)


def test_generate_timestamp_format() -> None:
    """Timestamp should match format YYYY-MM-DDTHHmmssZ."""
    # Arrange
    fixed_datetime = datetime(2026, 2, 10, 14, 30, 45, tzinfo=UTC)

    # Act
    timestamp = generate_timestamp(now=fixed_datetime)

    # Assert
    assert timestamp == "2026-02-10T143045Z"


class TestWriteMarkdownOutput:
    """Tests for write_markdown_output function."""

    def test_write_markdown_output_creates_file(self, tmp_path: Path) -> None:
        """File should be created in the output directory with correct content."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert result_path.is_file()
        with check:
            assert result_path.read_text(encoding="utf-8") == content

    def test_write_markdown_output_filename_format(self, tmp_path: Path) -> None:
        """Filename should follow format {timestamp}-{scope}.md."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"
        fixed_datetime = datetime(2026, 2, 10, 14, 30, 45, tzinfo=UTC)

        # Act
        result_path = write_markdown_output(
            scope, content, output_dir, now=fixed_datetime
        )

        # Assert
        assert result_path.name == "2026-02-10T143045Z-test-plan.md"

    def test_write_markdown_output_creates_directory(self, tmp_path: Path) -> None:
        """Output directory should be created if it doesn't exist."""
        # Arrange
        output_dir = tmp_path / "nested" / "outputs"
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"
        assert not output_dir.exists()

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        with check:
            assert output_dir.exists()
        with check:
            assert output_dir.is_dir()
        with check:
            assert result_path.exists()

    def test_write_markdown_output_with_existing_directory(
        self, tmp_path: Path
    ) -> None:
        """Should work correctly when output directory already exists."""
        # Arrange
        output_dir = tmp_path / "outputs"
        output_dir.mkdir(parents=True)
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        with check:
            assert output_dir.exists()
        with check:
            assert result_path.exists()

    def test_write_markdown_output_accepts_string_path(self, tmp_path: Path) -> None:
        """Should accept output_dir as string path."""
        # Arrange
        output_dir = str(tmp_path / "outputs")
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert isinstance(result_path, Path)

    def test_write_markdown_output_raises_on_directory_creation_failure(
        self, tmp_path: Path
    ) -> None:
        """Should raise WriteError if directory creation fails."""
        # Arrange - create a file, then try to mkdir under it (always fails)
        blocker = tmp_path / "blocker"
        blocker.write_text("file")
        output_dir = blocker / "subdir"
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act / Assert
        with pytest.raises(WriteError, match="Cannot create output directory"):
            write_markdown_output(scope, content, output_dir)

    def test_write_markdown_output_raises_on_file_write_failure(
        self, tmp_path: Path
    ) -> None:
        """Should raise WriteError if file writing fails."""
        # Arrange - make directory read-only to trigger write failure
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()
        output_dir.chmod(0o555)
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        try:
            # Act / Assert
            with pytest.raises(WriteError, match="Cannot write file"):
                write_markdown_output(scope, content, output_dir)
        finally:
            # Restore permissions so tmp_path cleanup works
            output_dir.chmod(0o755)

    def test_write_markdown_output_directory_error_preserves_cause(
        self, tmp_path: Path
    ) -> None:
        """Should preserve the original OSError when directory creation fails."""
        # Arrange - create a file, then try to mkdir under it
        blocker = tmp_path / "blocker"
        blocker.write_text("file")
        output_dir = blocker / "subdir"
        scope = "test"
        content = "# Test"

        # Act / Assert
        with pytest.raises(WriteError) as exc_info:
            write_markdown_output(scope, content, output_dir)

        with check:
            assert exc_info.value.__cause__ is not None
        with check:
            assert isinstance(exc_info.value.__cause__, OSError)

    def test_write_markdown_output_with_empty_content(self, tmp_path: Path) -> None:
        """Should handle empty content correctly."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "test-plan"
        empty_content = ""

        # Act
        result_path = write_markdown_output(scope, empty_content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert result_path.read_text(encoding="utf-8") == ""

    def test_write_markdown_output_with_hyphenated_scope(self, tmp_path: Path) -> None:
        """Should handle scope with hyphens."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "my-complex-test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        assert "my-complex-test-plan" in result_path.name

    def test_write_markdown_output_with_utf8_content(self, tmp_path: Path) -> None:
        """Should handle UTF-8 non-ASCII content."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "utf8-test"
        content = "# Test\n\nAccented: café\nCJK: 你好世界\nEmoji: 🚀🎉\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert result_path.read_text(encoding="utf-8") == content

    def test_write_markdown_output_returns_absolute_path(self, tmp_path: Path) -> None:
        """Returned path should be absolute."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope = "test-plan"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        result_path = write_markdown_output(scope, content, output_dir)

        # Assert
        assert result_path.is_absolute()


class TestBuildArgumentParser:
    """Tests for _build_argument_parser function."""

    def test_build_argument_parser_creates_parser(self) -> None:
        """Should create an ArgumentParser instance."""
        # Act
        parser = _build_argument_parser()

        # Assert
        assert isinstance(parser, argparse.ArgumentParser)

    @pytest.mark.parametrize(
        ("args", "expected_scope", "expected_output_dir"),
        [
            # Short form
            (
                ["-s", "test-scope", "-o", "/fake/outputs"],
                "test-scope",
                "/fake/outputs",
            ),
            # Long form
            (
                ["--scope", "test-scope", "--output-dir", "/fake/outputs"],
                "test-scope",
                "/fake/outputs",
            ),
        ],
    )
    def test_build_argument_parser_accepts_valid_args(
        self, args: list[str], expected_scope: str, expected_output_dir: str
    ) -> None:
        """Parser should accept both short and long form arguments."""
        # Arrange
        parser = _build_argument_parser()

        # Act
        parsed_args = parser.parse_args(args)

        # Assert
        with check:
            assert parsed_args.scope == expected_scope
        with check:
            assert parsed_args.output_dir == expected_output_dir

    def test_build_argument_parser_requires_scope(self) -> None:
        """Parser should require --scope argument."""
        # Arrange
        parser = _build_argument_parser()
        args_without_scope = ["-o", "/fake/outputs"]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_without_scope)

    def test_build_argument_parser_requires_output_dir(self) -> None:
        """Parser should require --output-dir argument."""
        # Arrange
        parser = _build_argument_parser()
        args_without_output = ["-s", "scope"]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_without_output)


class TestMain:
    """Tests for main CLI entry point."""

    def test_main_success_returns_exit_success(self, tmp_path: Path) -> None:
        """Main should return EXIT_SUCCESS when file is written successfully."""
        # Arrange
        output_dir = tmp_path / "outputs"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        exit_code = main(
            argv=["-s", "test-scope", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        assert exit_code == EXIT_SUCCESS

    def test_main_write_error_returns_exit_write_error(self, tmp_path: Path) -> None:
        """Main should return EXIT_WRITE_ERROR when write_markdown_output raises."""
        # Arrange - create a file blocker to trigger directory creation failure
        blocker = tmp_path / "blocker"
        blocker.write_text("file")
        output_dir = blocker / "subdir"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        exit_code = main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        assert exit_code == EXIT_WRITE_ERROR

    def test_main_file_write_failure_returns_exit_write_error(
        self, tmp_path: Path
    ) -> None:
        """Main should return EXIT_WRITE_ERROR when file writing fails."""
        # Arrange - make directory read-only to trigger write failure
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()
        output_dir.chmod(0o555)
        content = "# Test Plan\n\nThis is a test plan.\n"

        try:
            # Act
            exit_code = main(
                argv=["-s", "test", "-o", str(output_dir)],
                stdin=io.StringIO(content),
            )

            # Assert
            assert exit_code == EXIT_WRITE_ERROR
        finally:
            # Restore permissions so tmp_path cleanup works
            output_dir.chmod(0o755)

    def test_main_usage_error_returns_exit_usage_error(self) -> None:
        """Main should return EXIT_USAGE_ERROR for invalid arguments."""
        # Arrange - empty argv means no required arguments provided

        # Act / Assert
        # argparse calls sys.exit() directly, so we catch SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main(argv=[])

        assert exc_info.value.code == EXIT_USAGE_ERROR

    def test_main_prints_success_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main should print success message with file path."""
        # Arrange
        output_dir = tmp_path / "outputs"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        captured = capsys.readouterr()
        with check:
            assert "[WRITTEN]" in captured.out
        with check:
            assert str(output_dir) in captured.out

    def test_main_prints_error_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main should print error message to stderr on failure."""
        # Arrange - create a file blocker to trigger directory creation failure
        blocker = tmp_path / "blocker"
        blocker.write_text("file")
        output_dir = blocker / "subdir"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        captured = capsys.readouterr()
        with check:
            assert "[ERROR]" in captured.err
        with check:
            assert "Cannot create output directory" in captured.err

    def test_main_writes_correct_content(self, tmp_path: Path) -> None:
        """Main should write the piped stdin content to the output file."""
        # Arrange
        output_dir = tmp_path / "outputs"
        content = "# Test Plan\n\nThis is a test plan.\n"

        # Act
        main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        written_files = list(output_dir.glob("*.md"))
        with check:
            assert len(written_files) == 1
        with check:
            assert written_files[0].read_text(encoding="utf-8") == content

    def test_main_special_characters_writes_correct_content(
        self, tmp_path: Path
    ) -> None:
        """Main should preserve special characters from stdin end-to-end."""
        # Arrange
        content = (
            "# Review with `backticks`\n"
            "\n"
            "Here's a $variable and ${another_var}.\n"
            "She said \"hello\" and 'goodbye'.\n"
            "Backslash: \\ pipe: | ampersand: & semicolon: ;\n"
            "Parens: () brackets: [] braces: {}\n"
            "```python\n"
            "x = f'{value}'\n"
            "```\n"
        )
        output_dir = tmp_path / "outputs"

        # Act
        exit_code = main(
            argv=["-s", "special-chars-review", "-o", str(output_dir)],
            stdin=io.StringIO(content),
        )

        # Assert
        written_files = list(output_dir.glob("*.md"))
        with check:
            assert exit_code == EXIT_SUCCESS
        with check:
            assert len(written_files) == 1
        with check:
            assert written_files[0].read_text(encoding="utf-8") == content

    def test_main_empty_stdin_returns_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main should return EXIT_WRITE_ERROR when stdin is empty."""
        # Arrange
        output_dir = tmp_path / "outputs"

        # Act
        exit_code = main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO(""),
        )

        # Assert
        captured = capsys.readouterr()
        with check:
            assert exit_code == EXIT_WRITE_ERROR
        with check:
            assert "No content received from stdin" in captured.err

    def test_main_whitespace_only_stdin_returns_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main should return EXIT_WRITE_ERROR when stdin is only whitespace."""
        # Arrange
        output_dir = tmp_path / "outputs"

        # Act
        exit_code = main(
            argv=["-s", "scope", "-o", str(output_dir)],
            stdin=io.StringIO("   \n\n  "),
        )

        # Assert
        captured = capsys.readouterr()
        with check:
            assert exit_code == EXIT_WRITE_ERROR
        with check:
            assert "No content received from stdin" in captured.err


@pytest.mark.parametrize(
    ("exit_code", "expected_value"),
    [
        (EXIT_SUCCESS, 0),
        (EXIT_WRITE_ERROR, 1),
        (EXIT_USAGE_ERROR, 2),
    ],
)
def test_exit_codes(exit_code: int, expected_value: int) -> None:
    """Exit codes should have correct values and be distinct."""
    # Act / Assert
    assert exit_code == expected_value

"""Tests for the write_markdown_output module.

This module provides comprehensive tests for write_markdown_output.py, covering
timestamp generation, file writing, CLI argument parsing, and error handling.
"""

# ruff: noqa: S101 # this is a test module

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest_check import check
from write_markdown_output import (
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    EXIT_WRITE_ERROR,
    WriteError,
    _build_argument_parser,
    _resolve_content,
    generate_timestamp,
    main,
    write_markdown_output,
)


@pytest.fixture
def sample_content() -> str:
    """Sample markdown content for testing."""
    return "# Test Plan\n\nThis is a test plan.\n"


@pytest.fixture
def sample_scope() -> str:
    """Sample scope string for filename."""
    return "test-plan"


@pytest.fixture
def content_file(tmp_path: Path, sample_content: str) -> Path:
    """Create a temporary content file for testing."""
    filepath = tmp_path / "content.md"
    filepath.write_text(sample_content, encoding="utf-8")
    return filepath


class TestGenerateTimestamp:
    """Tests for generate_timestamp function."""

    def test_generate_timestamp_format(self) -> None:
        """Timestamp should match format YYYY-MM-DDTHHmmssZ."""
        # Arrange
        fixed_datetime = datetime(2026, 2, 10, 14, 30, 45, tzinfo=UTC)

        # Act
        with patch("write_markdown_output.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_datetime
            timestamp = generate_timestamp()

        # Assert
        assert timestamp == "2026-02-10T143045Z"

class TestWriteMarkdownOutput:
    """Tests for write_markdown_output function."""

    def test_write_markdown_output_creates_file(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """File should be created in the output directory with correct content."""
        # Arrange
        output_dir = tmp_path / "outputs"

        # Act
        result_path = write_markdown_output(sample_scope, sample_content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert result_path.is_file()
        with check:
            assert result_path.read_text(encoding="utf-8") == sample_content

    def test_write_markdown_output_filename_format(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Filename should follow format {timestamp}-{scope}.md."""
        # Arrange
        output_dir = tmp_path / "outputs"
        fixed_datetime = datetime(2026, 2, 10, 14, 30, 45, tzinfo=UTC)

        # Act
        with patch("write_markdown_output.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_datetime
            result_path = write_markdown_output(
                sample_scope, sample_content, output_dir
            )

        # Assert
        assert result_path.name == "2026-02-10T143045Z-test-plan.md"

    def test_write_markdown_output_creates_directory(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Output directory should be created if it doesn't exist."""
        # Arrange
        output_dir = tmp_path / "nested" / "outputs"
        assert not output_dir.exists()

        # Act
        result_path = write_markdown_output(sample_scope, sample_content, output_dir)

        # Assert
        with check:
            assert output_dir.exists()
        with check:
            assert output_dir.is_dir()
        with check:
            assert result_path.exists()

    def test_write_markdown_output_with_existing_directory(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Should work correctly when output directory already exists."""
        # Arrange
        output_dir = tmp_path / "outputs"
        output_dir.mkdir(parents=True)

        # Act
        result_path = write_markdown_output(sample_scope, sample_content, output_dir)

        # Assert
        with check:
            assert output_dir.exists()
        with check:
            assert result_path.exists()

    def test_write_markdown_output_accepts_string_path(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Should accept output_dir as string path."""
        # Arrange
        output_dir = str(tmp_path / "outputs")

        # Act
        result_path = write_markdown_output(sample_scope, sample_content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert isinstance(result_path, Path)

    def test_write_markdown_output_raises_on_directory_creation_failure(
        self,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Should raise WriteError if directory creation fails."""
        # Arrange
        output_dir = Path("/invalid_root/directory")

        # Act / Assert
        with pytest.raises(WriteError, match="Cannot create output directory"):
            write_markdown_output(sample_scope, sample_content, output_dir)

    def test_write_markdown_output_raises_on_file_write_failure(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Should raise WriteError if file writing fails."""
        # Arrange
        output_dir = tmp_path / "outputs"
        output_dir.mkdir(parents=True)

        # Act / Assert
        with (
            patch("pathlib.Path.write_text", side_effect=OSError("Disk full")),
            pytest.raises(WriteError, match="Cannot write file"),
        ):
            write_markdown_output(sample_scope, sample_content, output_dir)

    def test_write_markdown_output_with_empty_content(
        self,
        tmp_path: Path,
        sample_scope: str,
    ) -> None:
        """Should handle empty content correctly."""
        # Arrange
        output_dir = tmp_path / "outputs"
        empty_content = ""

        # Act
        result_path = write_markdown_output(sample_scope, empty_content, output_dir)

        # Assert
        with check:
            assert result_path.exists()
        with check:
            assert result_path.read_text(encoding="utf-8") == ""

    def test_write_markdown_output_with_special_characters_in_scope(
        self,
        tmp_path: Path,
        sample_content: str,
    ) -> None:
        """Should handle scope with various characters."""
        # Arrange
        output_dir = tmp_path / "outputs"
        scope_with_dashes = "my-complex-test-plan"

        # Act
        result_path = write_markdown_output(
            scope_with_dashes,
            sample_content,
            output_dir,
        )

        # Assert
        assert "my-complex-test-plan" in result_path.name

    def test_write_markdown_output_returns_absolute_path(
        self,
        tmp_path: Path,
        sample_scope: str,
        sample_content: str,
    ) -> None:
        """Returned path should be absolute."""
        # Arrange
        output_dir = tmp_path / "outputs"

        # Act
        result_path = write_markdown_output(sample_scope, sample_content, output_dir)

        # Assert
        assert result_path.is_absolute()


class TestResolveContent:
    """Tests for _resolve_content function."""

    def test_resolve_content_from_content_arg(self, sample_content: str) -> None:
        """Should return content from --content argument when provided."""
        # Arrange
        args = argparse.Namespace(content=sample_content, file=None)

        # Act
        result = _resolve_content(args)

        # Assert
        assert result == sample_content

    def test_resolve_content_from_file_arg(
        self,
        content_file: Path,
        sample_content: str,
    ) -> None:
        """Should read content from --file argument when provided."""
        # Arrange
        args = argparse.Namespace(content=None, file=str(content_file))

        # Act
        result = _resolve_content(args)

        # Assert
        assert result == sample_content

    def test_resolve_content_prefers_content_over_file(
        self,
        content_file: Path,
    ) -> None:
        """Should prefer --content over --file when content is not None."""
        # Arrange
        content_arg = "# Direct content"
        args = argparse.Namespace(content=content_arg, file=str(content_file))

        # Act
        result = _resolve_content(args)

        # Assert
        assert result == content_arg

    def test_resolve_content_raises_when_file_not_found(self) -> None:
        """Should raise WriteError when file doesn't exist."""
        # Arrange
        args = argparse.Namespace(content=None, file="/nonexistent/file.md")

        # Act / Assert
        with pytest.raises(WriteError, match="Content file not found"):
            _resolve_content(args)

    def test_resolve_content_raises_when_file_not_readable(
        self,
        tmp_path: Path,
    ) -> None:
        """Should raise WriteError when file can't be read."""
        # Arrange
        filepath = tmp_path / "unreadable.md"
        filepath.write_text("content", encoding="utf-8")
        args = argparse.Namespace(content=None, file=str(filepath))

        # Act / Assert
        with (
            patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")),
            pytest.raises(WriteError, match="Cannot read content file"),
        ):
            _resolve_content(args)

    def test_resolve_content_raises_when_path_is_directory(
        self,
        tmp_path: Path,
    ) -> None:
        """Should raise WriteError when file path is actually a directory."""
        # Arrange
        directory = tmp_path / "subdir"
        directory.mkdir()
        args = argparse.Namespace(content=None, file=str(directory))

        # Act / Assert
        with pytest.raises(WriteError, match="Content file not found"):
            _resolve_content(args)


class TestBuildArgumentParser:
    """Tests for _build_argument_parser function."""

    def test_build_argument_parser_creates_parser(self) -> None:
        """Should create an ArgumentParser instance."""
        # Act
        parser = _build_argument_parser()

        # Assert
        assert isinstance(parser, argparse.ArgumentParser)

    def test_build_argument_parser_accepts_valid_args(self) -> None:
        """Parser should accept valid argument combinations."""
        # Arrange
        parser = _build_argument_parser()
        valid_args = [
            "-s",
            "test-scope",
            "-c",
            "# Content",
            "-o",
            "/tmp/outputs",
        ]

        # Act
        args = parser.parse_args(valid_args)

        # Assert
        with check:
            assert args.scope == "test-scope"
        with check:
            assert args.content == "# Content"
        with check:
            assert args.output_dir == "/tmp/outputs"

    def test_build_argument_parser_requires_scope(self) -> None:
        """Parser should require --scope argument."""
        # Arrange
        parser = _build_argument_parser()
        args_without_scope = ["-c", "# Content", "-o", "/tmp/outputs"]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_without_scope)

    def test_build_argument_parser_requires_content_or_file(self) -> None:
        """Parser should require either --content or --file."""
        # Arrange
        parser = _build_argument_parser()
        args_without_content = ["-s", "scope", "-o", "/tmp/outputs"]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_without_content)

    def test_build_argument_parser_rejects_both_content_and_file(self) -> None:
        """Parser should reject both --content and --file together."""
        # Arrange
        parser = _build_argument_parser()
        args_with_both = [
            "-s",
            "scope",
            "-c",
            "Content",
            "-f",
            "/tmp/file.md",
            "-o",
            "/tmp/outputs",
        ]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_with_both)

    def test_build_argument_parser_requires_output_dir(self) -> None:
        """Parser should require --output-dir argument."""
        # Arrange
        parser = _build_argument_parser()
        args_without_output = ["-s", "scope", "-c", "Content"]

        # Act / Assert
        with pytest.raises(SystemExit):
            parser.parse_args(args_without_output)

    def test_build_argument_parser_accepts_file_argument(self) -> None:
        """Parser should accept --file argument."""
        # Arrange
        parser = _build_argument_parser()
        valid_args = [
            "-s",
            "test-scope",
            "-f",
            "/tmp/content.md",
            "-o",
            "/tmp/outputs",
        ]

        # Act
        args = parser.parse_args(valid_args)

        # Assert
        with check:
            assert args.file == "/tmp/content.md"
        with check:
            assert args.content is None

    def test_build_argument_parser_accepts_short_flags(self) -> None:
        """Parser should accept short flags (-s, -c, -o)."""
        # Arrange
        parser = _build_argument_parser()
        args_with_short_flags = ["-s", "scope", "-c", "Content", "-o", "/tmp/out"]

        # Act
        args = parser.parse_args(args_with_short_flags)

        # Assert
        with check:
            assert args.scope == "scope"
        with check:
            assert args.content == "Content"
        with check:
            assert args.output_dir == "/tmp/out"

    def test_build_argument_parser_accepts_long_flags(self) -> None:
        """Parser should accept long flags (--scope, --content, --output-dir)."""
        # Arrange
        parser = _build_argument_parser()
        args_with_long_flags = [
            "--scope",
            "scope",
            "--content",
            "Content",
            "--output-dir",
            "/tmp/out",
        ]

        # Act
        args = parser.parse_args(args_with_long_flags)

        # Assert
        with check:
            assert args.scope == "scope"
        with check:
            assert args.content == "Content"
        with check:
            assert args.output_dir == "/tmp/out"


class TestMain:
    """Tests for main CLI entry point."""

    def test_main_success_returns_exit_success(
        self,
        tmp_path: Path,
    ) -> None:
        """Main should return EXIT_SUCCESS when file is written successfully."""
        # Arrange
        output_dir = tmp_path / "outputs"
        test_args = [
            "script.py",
            "-s",
            "test-scope",
            "-c",
            "# Content",
            "-o",
            str(output_dir),
        ]

        # Act
        with patch("sys.argv", test_args):
            exit_code = main()

        # Assert
        assert exit_code == EXIT_SUCCESS

    def test_main_write_error_returns_exit_write_error(
        self,
    ) -> None:
        """Main should return EXIT_WRITE_ERROR when write_markdown_output raises."""
        # Arrange
        test_args = [
            "script.py",
            "-s",
            "scope",
            "-c",
            "Content",
            "-o",
            "/invalid_root/dir",
        ]

        # Act
        with patch("sys.argv", test_args):
            exit_code = main()

        # Assert
        assert exit_code == EXIT_WRITE_ERROR

    def test_main_usage_error_returns_exit_usage_error(
        self,
    ) -> None:
        """Main should return EXIT_USAGE_ERROR for invalid arguments."""
        # Arrange
        test_args = ["script.py"]  # Missing required arguments

        # Act / Assert
        # argparse calls sys.exit() directly, so we catch SystemExit
        with (
            patch("sys.argv", test_args),
            patch("sys.stderr"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == EXIT_USAGE_ERROR

    def test_main_prints_success_message(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Main should print success message with file path."""
        # Arrange
        output_dir = tmp_path / "outputs"
        test_args = [
            "script.py",
            "-s",
            "scope",
            "-c",
            "Content",
            "-o",
            str(output_dir),
        ]

        # Act
        with patch("sys.argv", test_args):
            main()

        # Assert
        captured = capsys.readouterr()
        with check:
            assert "[WRITTEN]" in captured.out
        with check:
            assert str(output_dir) in captured.out

    def test_main_prints_error_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Main should print error message to stderr on failure."""
        # Arrange
        test_args = [
            "script.py",
            "-s",
            "scope",
            "-c",
            "Content",
            "-o",
            "/invalid_root/dir",
        ]

        # Act
        with patch("sys.argv", test_args):
            main()

        # Assert
        captured = capsys.readouterr()
        with check:
            assert "[ERROR]" in captured.err
        with check:
            assert "Cannot create output directory" in captured.err

    def test_main_with_file_argument(
        self,
        tmp_path: Path,
        content_file: Path,
    ) -> None:
        """Main should work correctly with --file argument."""
        # Arrange
        output_dir = tmp_path / "outputs"
        test_args = [
            "script.py",
            "-s",
            "scope",
            "-f",
            str(content_file),
            "-o",
            str(output_dir),
        ]

        # Act
        with patch("sys.argv", test_args):
            exit_code = main()

        # Assert
        assert exit_code == EXIT_SUCCESS

    def test_main_with_nonexistent_file(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Main should handle nonexistent file with error."""
        # Arrange
        output_dir = tmp_path / "outputs"
        test_args = [
            "script.py",
            "-s",
            "scope",
            "-f",
            "/nonexistent/file.md",
            "-o",
            str(output_dir),
        ]

        # Act
        with patch("sys.argv", test_args):
            exit_code = main()

        # Assert
        captured = capsys.readouterr()
        with check:
            assert exit_code == EXIT_WRITE_ERROR
        with check:
            assert "Content file not found" in captured.err


class TestExitCodes:
    """Tests for exit code constants."""

    def test_exit_codes_are_distinct(self) -> None:
        """All exit codes should have distinct values."""
        exit_codes = {EXIT_SUCCESS, EXIT_WRITE_ERROR, EXIT_USAGE_ERROR}
        assert len(exit_codes) == 3

    def test_exit_success_is_zero(self) -> None:
        """EXIT_SUCCESS should be 0."""
        assert EXIT_SUCCESS == 0

    def test_exit_write_error_is_one(self) -> None:
        """EXIT_WRITE_ERROR should be 1."""
        assert EXIT_WRITE_ERROR == 1

    def test_exit_usage_error_is_two(self) -> None:
        """EXIT_USAGE_ERROR should be 2."""
        assert EXIT_USAGE_ERROR == 2

#!/usr/bin/env -S uv run --script
"""Write content to a timestamped markdown file.

This module provides a simple utility for agents to write markdown output
files with UTC timestamps in the filename, following the repository's
naming conventions.

Example usage:
    Write content from a file (recommended)

    ```sh
    python write_markdown_output.py -s "sql-validation-plan" -f /tmp/output-content.md -o ".claude/agent-outputs/plans"
    ```

    Write content from a CLI argument (simple content only)

    ```sh
    python write_markdown_output.py -s "parser-review" -c "# Review" -o ".claude/agent-outputs/reviews"
    ```

Exit codes:
    0: File written successfully
    1: Error writing file
    2: Usage error (missing arguments)
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

# =============================================================================
# Exit Codes
# =============================================================================

EXIT_SUCCESS: Final[int] = 0
EXIT_WRITE_ERROR: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2


# =============================================================================
# Exceptions
# =============================================================================


class WriteError(Exception):
    """Raised when file cannot be written."""


# =============================================================================
# Public API
# =============================================================================


def generate_timestamp() -> str:
    """Generate UTC timestamp in ISO format for output filenames.

    Returns:
        str: Timestamp in format YYYY-MM-DDTHHmmssZ (e.g., '2026-02-02T025204Z')
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")


def write_markdown_output(scope: str, content: str, output_dir: Path | str) -> Path:
    """Write content to a timestamped markdown file.

    Creates the output directory if it doesn't exist, generates a UTC timestamp,
    and writes the content to a file named `<timestamp>-<scope>.md`.

    Args:
        scope (str): Scope/title for the filename (e.g., "sql-validation-plan").
            Should be lowercase with hyphens, no spaces.
        content (str): Markdown content to write.
        output_dir (Path | str): Output directory path. Will be created if it doesn't exist.

    Returns:
        Path: Full path to the created file.

    Raises:
        WriteError: If the file cannot be written.

    Example:
        >>> path = write_markdown_output(
        ...     scope="test-plan",
        ...     content="# Test Plan",
        ...     output_dir="/tmp/test-outputs"
        ... )
        >>> path.name  # doctest: +SKIP
        '2026-02-02T025204Z-test-plan.md'
    """
    timestamp = generate_timestamp()
    output_path = Path(output_dir)

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise WriteError(f"Cannot create output directory: {e}") from e

    filename = f"{timestamp}-{scope}.md"
    file_path = output_path / filename

    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise WriteError(f"Cannot write file: {e}") from e

    return file_path


# =============================================================================
# CLI
# =============================================================================


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        int: Exit code (see module constants for values).
    """
    parser = _build_argument_parser()
    args = parser.parse_args()

    try:
        content = _resolve_content(args)
        file_path = write_markdown_output(
            scope=args.scope,
            content=content,
            output_dir=args.output_dir,
        )
    except WriteError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return EXIT_WRITE_ERROR

    print(f"[WRITTEN] {file_path}")
    return EXIT_SUCCESS


def _resolve_content(args: argparse.Namespace) -> str:
    """Resolve content from either --content or --file argument.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        str: The resolved content string.

    Raises:
        WriteError: If the content file cannot be read.
    """
    if args.content is not None:
        return args.content
    file_path = Path(args.file)
    if not file_path.is_file():
        raise WriteError(f"Content file not found: {args.file}")
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise WriteError(f"Cannot read content file: {e}") from e


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser with usage and help text.
    """
    parser = argparse.ArgumentParser(
        prog="write_markdown_output",
        description="Write content to a timestamped markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -s "sql-plan" -f /tmp/output-content.md -o ".claude/agent-outputs/plans"
  %(prog)s -s "review" -c "# Simple review" -o ".claude/agent-outputs/reviews"

Exit codes:
  0  File written successfully
  1  Error writing file
  2  Usage error (missing arguments)
""",
    )

    parser.add_argument(
        "-s",
        "--scope",
        required=True,
        metavar="SCOPE",
        help="Scope/title for the filename (e.g., 'sql-validation-plan')",
    )

    content_group = parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help="Path to a file containing the markdown content (recommended)",
    )
    content_group.add_argument(
        "-c",
        "--content",
        metavar="CONTENT",
        help="Markdown content string (for simple content without shell-special characters)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        metavar="DIR",
        help="Output directory path",
    )

    return parser


if __name__ == "__main__":
    sys.exit(main())

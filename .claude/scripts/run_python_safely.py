"""Safety guardrail for agent-executed Python code.

This module provides static AST analysis to detect potentially dangerous
operations in Python code before execution. It is designed to prevent
destructive mistakes by AI agents, not to guard against malicious actors
deliberately trying to bypass security.

Philosophy:
    - Block anything that could be destructive
    - Be conservative—false positives are acceptable
    - Agent can always ask the user for permission to run blocked code directly

What This Tool Catches Well (Agent Mistakes):
    - File destruction: os, shutil, open(), unlink(), rmdir(), rmtree(), etc.
    - Shell execution: subprocess, os.system (os is blocked)
    - Network access: socket, requests, httpx, urllib
    - Code injection: eval(), exec(), compile(), __import__()
    - Runaway execution: 5-minute timeout prevents infinite loops

What This Tool Allows:
    - Pure computation (math, string manipulation, data structures)
    - File reading via pathlib (read_text, read_bytes)
    - Standard library modules not in the blocklist (json, re, itertools, etc.)

Intentionally Allowed Modules:
    - tempfile: Allows agents to create temporary working files for intermediate
      results. Files are confined to system temp directories and auto-cleaned.
    - asyncio: Allows async/await patterns. Doesn't directly enable filesystem
      or network access (those are blocked by their respective module checks).

Known Limitations (Deliberate Bypass Attempts):
    This tool uses static analysis and cannot detect:
    - String obfuscation: getattr(__builtins__, "op"+"en")
    - Encoded payloads: base64-encoded imports executed via exec
    - Runtime code generation

    However, the layered approach means most bypass attempts hit at least one
    blocked item (e.g., getattr and exec are both blocked).

Example usage:
    Execute inline code::

        python run_python_safely.py -c "print(2 + 2)"

    Execute code from file::

        python run_python_safely.py -f script.py

Exit codes:
    0: Code executed successfully
    1: Code blocked due to safety concerns
    2: Usage error or file not found
    3: Execution timed out (5 minute limit)
"""

from __future__ import annotations

import argparse
import ast
import subprocess  # noqa: S404 - required for code execution with timeout
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterator

# =============================================================================
# Exit Codes
# =============================================================================

EXIT_SUCCESS: Final[int] = 0
EXIT_BLOCKED: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_TIMEOUT: Final[int] = 3

EXECUTION_TIMEOUT_SECONDS: Final[int] = 300

# =============================================================================
# Exceptions
# =============================================================================


class FileReadError(Exception):
    """Raised when a source file cannot be read."""


# =============================================================================
# Types
# =============================================================================


class IssueCategory(Enum):
    """Categories of safety issues."""

    IMPORT = "import"
    BUILTIN = "builtin"
    METHOD = "method"
    SYNTAX = "syntax"


@dataclass(frozen=True)
class SafetyIssue:
    """A detected safety issue in Python code.

    Attributes:
        category (IssueCategory): The type of issue (import, builtin, method, syntax).
        name (str): The specific item that was blocked (e.g., "os", "eval").
        detail (str): Human-readable explanation for the agent.
    """

    category: IssueCategory
    name: str
    detail: str


@dataclass(frozen=True)
class CodeSource:
    """Source code and execution arguments."""

    code: str
    exec_args: list[str]


# =============================================================================
# Constants: Blocked Imports
# =============================================================================
# Modules that provide access to destructive capabilities, organized by threat:
#
# File/Process Operations: os, sys, subprocess, shutil
#   - Can delete files, execute commands, modify environment
#
# Network Operations: socket, requests, httpx, urllib, ftplib
#   - Can exfiltrate data or download malicious payloads
#
# Dangerous Serialization: pickle, shelve, marshal
#   - Deserializing untrusted data can execute arbitrary code
#
# Low-Level Access: ctypes
#   - Direct memory manipulation and C library calls
#
# Concurrency: multiprocessing, threading
#   - Can spawn processes/threads that bypass this check
#
# Dynamic Import System: importlib, builtins
#   - Can dynamically import blocked modules or access blocked builtins

BLOCKED_IMPORTS: Final[frozenset[str]] = frozenset({
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "requests",
    "httpx",
    "urllib",
    "ftplib",
    "pickle",
    "shelve",
    "marshal",
    "ctypes",
    "multiprocessing",
    "threading",
    "importlib",
    "builtins",
})

_IMPORT_DETAILS: Final[dict[str, str]] = {
    "os": "file system and process operations",
    "sys": "system-level access and modification",
    "subprocess": "shell command execution",
    "shutil": "high-level file operations",
    "socket": "network socket operations",
    "requests": "HTTP requests",
    "httpx": "HTTP requests",
    "urllib": "URL handling and requests",
    "ftplib": "FTP operations",
    "pickle": "arbitrary code execution via deserialization",
    "shelve": "file-based persistence with pickle",
    "marshal": "low-level serialization",
    "ctypes": "C library access and memory manipulation",
    "multiprocessing": "process spawning",
    "threading": "thread spawning",
    "importlib": "dynamic import system",
    "builtins": "access to built-in functions",
}

# =============================================================================
# Constants: Blocked Builtins
# =============================================================================
# Built-in functions that enable dangerous operations:
#
# Code Execution: eval, exec, compile
#   - Can execute arbitrary Python code, bypassing all static checks
#
# File Access: open
#   - Direct file read/write access (use pathlib.read_text for safe reads)
#
# Dynamic Import: __import__
#   - Can import any module at runtime, bypassing import checks
#
# Reflection/Introspection: getattr, setattr, delattr, globals, locals, vars
#   - Can access/modify any attribute or namespace dynamically
#   - Example bypass: getattr(__builtins__, "open")("file.txt")
#
# Other: breakpoint, input
#   - breakpoint: Drops into debugger (blocks execution)
#   - input: Blocks waiting for user input (hangs agent execution)

BLOCKED_BUILTINS: Final[frozenset[str]] = frozenset({
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "breakpoint",
    "input",
})

_BUILTIN_DETAILS: Final[dict[str, str]] = {
    "eval": "arbitrary code execution",
    "exec": "arbitrary code execution",
    "compile": "code compilation for execution",
    "open": "file system access",
    "__import__": "dynamic module import",
    "getattr": "dynamic attribute access",
    "setattr": "dynamic attribute modification",
    "delattr": "dynamic attribute deletion",
    "globals": "global namespace access",
    "locals": "local namespace access",
    "vars": "namespace access",
    "breakpoint": "debugger invocation",
    "input": "user input during execution",
}

# =============================================================================
# Constants: Blocked Methods
# =============================================================================
# Method names that modify the filesystem. These are blocked on ANY object,
# not just pathlib.Path. This means `my_custom_object.unlink()` will be blocked
# even if unrelated to files. This is intentional—false positives are acceptable.
#
# IMPORTANT: Read operations (read_text, read_bytes) are ALLOWED.
# This lets agents inspect file contents while preventing destructive changes.
#
# Write Operations: write_text, write_bytes
# Creation: touch, mkdir
# Deletion: rmdir, unlink, rmtree (rmtree is recursive!)
# Rename/Move: rename, replace
# Links: symlink_to, hardlink_to, link_to
# Permissions: chmod, lchmod

BLOCKED_METHODS: Final[frozenset[str]] = frozenset({
    "write_text",
    "write_bytes",
    "touch",
    "mkdir",
    "rmdir",
    "unlink",
    "rename",
    "replace",
    "symlink_to",
    "hardlink_to",
    "link_to",
    "chmod",
    "lchmod",
    "rmtree",
})

_METHOD_DETAILS: Final[dict[str, str]] = {
    "write_text": "file write operation",
    "write_bytes": "file write operation",
    "touch": "file creation",
    "mkdir": "directory creation",
    "rmdir": "directory deletion",
    "unlink": "file deletion",
    "rename": "file/directory rename",
    "replace": "file/directory replacement",
    "symlink_to": "symbolic link creation",
    "hardlink_to": "hard link creation",
    "link_to": "link creation",
    "chmod": "permission modification",
    "lchmod": "permission modification",
    "rmtree": "recursive directory deletion",
}


# =============================================================================
# Public API
# =============================================================================


def check_code(code: str) -> list[SafetyIssue]:
    """Analyze Python code for potentially dangerous operations.

    Performs AST-based static analysis with four sequential checks:

    1. **Import Check**: Blocks modules that could cause damage.
       - File/process: os, sys, subprocess, shutil
       - Network: socket, requests, httpx, urllib, ftplib
       - Dangerous serialization: pickle, shelve, marshal
       - Low-level access: ctypes, multiprocessing, threading
       - Dynamic imports: importlib, builtins

    2. **Builtin Check**: Blocks dangerous built-in function calls.
       - Code execution: eval(), exec(), compile()
       - File access: open()
       - Dynamic import: __import__()
       - Reflection: getattr(), setattr(), delattr()
       - Namespace access: globals(), locals(), vars()
       - Other: breakpoint(), input()

    3. **Builtin Alias Check**: Blocks assigning builtins to variables.
       - Catches: ``evil = eval`` or ``evil := eval``
       - Catches tuple unpacking: ``e, x = eval, exec``
       - Prevents bypass via aliasing (e.g., ``my_func = eval; my_func(code)``)

    4. **Method Check**: Blocks filesystem-modifying method calls AND references.
       - Write operations: write_text(), write_bytes()
       - Creation: touch(), mkdir()
       - Deletion: rmdir(), unlink(), rmtree()
       - Rename/move: rename(), replace()
       - Links: symlink_to(), hardlink_to(), link_to()
       - Permissions: chmod(), lchmod()
       - Note: Read operations (read_text, read_bytes) are ALLOWED.
       - Note: Method references like ``delete_func = path.unlink`` are blocked
         because they could be called later to bypass detection.

    False Positives:
        The method check blocks ANY object's method with a blocked name, so
        ``my_custom_object.unlink()`` would be blocked even if unrelated to files.
        This is intentional—the agent can ask for permission to run directly.

    Args:
        code (str): Python source code to analyze.

    Returns:
        list[SafetyIssue]: Detected issues. Empty list means the code is safe to execute.

    Examples:
        >>> issues = check_code("import os")
        >>> len(issues)
        1
        >>> issues[0].category
        <IssueCategory.IMPORT: 'import'>
        >>> issues[0].name
        'os'

        >>> issues = check_code("x = 1 + 2")
        >>> len(issues)
        0

        >>> issues = check_code("Path('x').read_text()")  # Reads are allowed
        >>> len(issues)
        0

        >>> issues = check_code("evil = eval")  # Alias detection
        >>> len(issues)
        1
        >>> issues[0].category
        <IssueCategory.BUILTIN: 'builtin'>

        >>> issues = check_code("e, x = eval, exec")  # Tuple unpacking
        >>> len(issues)
        2
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [
            SafetyIssue(
                category=IssueCategory.SYNTAX,
                name="SyntaxError",
                detail=str(e),
            )
        ]

    return [
        *_collect_import_issues(tree),
        *_collect_builtin_issues(tree),
        *_collect_builtin_alias_issues(tree),
        *_collect_method_issues(tree),
    ]


def format_issues(issues: list[SafetyIssue]) -> str:
    """Format safety issues into agent-readable output.

    Args:
        issues (list[SafetyIssue]): List of detected safety issues.

    Returns:
        str: Formatted string with one issue per line.

    Example:
        >>> issues = [
        ...     SafetyIssue(IssueCategory.IMPORT, "os", "file system operations"),
        ...     SafetyIssue(IssueCategory.BUILTIN, "eval", "arbitrary code execution"),
        ... ]
        >>> print(format_issues(issues))
          - Import: os (file system operations)
          - Builtin: eval (arbitrary code execution)
    """
    return "\n".join(f"  - {issue.category.value.capitalize()}: {issue.name} ({issue.detail})" for issue in issues)


# =============================================================================
# Private Helpers: Import Checking
# =============================================================================


def _collect_import_issues(tree: ast.AST) -> Iterator[SafetyIssue]:
    """Yield unique safety issues for blocked imports in the AST."""
    seen: set[str] = set()

    for node in ast.walk(tree):
        for issue in _get_import_issues_from_node(node):
            if issue.name not in seen:
                seen.add(issue.name)
                yield issue


def _get_import_issues_from_node(node: ast.AST) -> Iterator[SafetyIssue]:
    """Yield import issues from a single AST node (may include duplicates)."""
    if isinstance(node, ast.Import):
        yield from _get_issues_from_import(node)
    elif isinstance(node, ast.ImportFrom):
        yield from _get_issues_from_import_from(node)


def _get_issues_from_import(node: ast.Import) -> Iterator[SafetyIssue]:
    """Yield issues for an Import node (e.g., ``import os``)."""
    for alias in node.names:
        module = alias.name.split(".")[0]
        if issue := _create_import_issue(module):
            yield issue


def _get_issues_from_import_from(node: ast.ImportFrom) -> Iterator[SafetyIssue]:
    """Yield issues for an ImportFrom node (e.g., ``from os import path``)."""
    if node.module:
        module = node.module.split(".")[0]
        if issue := _create_import_issue(module):
            yield issue
    else:
        # Relative import: from . import os
        for alias in node.names:
            name = alias.name.split(".")[0]
            if issue := _create_import_issue(name):
                yield issue


def _create_import_issue(module: str) -> SafetyIssue | None:
    """Create an import issue if the module is blocked."""
    if module not in BLOCKED_IMPORTS:
        return None

    return SafetyIssue(
        category=IssueCategory.IMPORT,
        name=module,
        detail=_IMPORT_DETAILS.get(module, "blocked import"),
    )


# =============================================================================
# Private Helpers: Builtin Checking
# =============================================================================


def _collect_builtin_issues(tree: ast.AST) -> Iterator[SafetyIssue]:
    """Yield safety issues for blocked builtin function calls."""
    seen: set[str] = set()

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue

        name = node.func.id
        if name in BLOCKED_BUILTINS and name not in seen:
            seen.add(name)
            yield SafetyIssue(
                category=IssueCategory.BUILTIN,
                name=name,
                detail=_BUILTIN_DETAILS.get(name, "blocked builtin"),
            )


def _collect_builtin_alias_issues(tree: ast.AST) -> Iterator[SafetyIssue]:
    """Yield unique safety issues for assignments that alias blocked builtins.

    Detects patterns like ``evil = eval`` where a blocked builtin is assigned
    to a variable, which could then be called to bypass direct call detection.
    Also detects tuple unpacking patterns like ``e, x = eval, exec``.
    """
    seen: set[str] = set()

    for node in ast.walk(tree):
        for issue in _get_alias_issues_from_node(node):
            if issue.name not in seen:
                seen.add(issue.name)
                yield issue


def _get_alias_issues_from_node(node: ast.AST) -> Iterator[SafetyIssue]:
    """Yield builtin alias issues from a single AST node (may include duplicates)."""
    if isinstance(node, ast.Assign):
        yield from _get_alias_issues_from_assign(node)
    elif (
        isinstance(node, ast.NamedExpr)
        and isinstance(node.value, ast.Name)
        and (issue := _create_builtin_alias_issue(node.value.id))
    ):
        yield issue


def _get_alias_issues_from_assign(node: ast.Assign) -> Iterator[SafetyIssue]:
    """Yield alias issues from an Assign node."""
    if isinstance(node.value, ast.Name) and (issue := _create_builtin_alias_issue(node.value.id)):
        # Simple assignment: evil = eval
        yield issue
    elif isinstance(node.value, ast.Tuple):
        # Tuple unpacking: e, x = eval, exec
        yield from _get_alias_issues_from_tuple(node.value)


def _get_alias_issues_from_tuple(node: ast.Tuple) -> Iterator[SafetyIssue]:
    """Yield alias issues from a Tuple node."""
    for elt in node.elts:
        if isinstance(elt, ast.Name) and (issue := _create_builtin_alias_issue(elt.id)):
            yield issue


def _create_builtin_alias_issue(name: str) -> SafetyIssue | None:
    """Create a builtin alias issue if the name is a blocked builtin."""
    if name not in BLOCKED_BUILTINS:
        return None

    return SafetyIssue(
        category=IssueCategory.BUILTIN,
        name=name,
        detail=_BUILTIN_DETAILS.get(name, "blocked builtin") + " (aliased)",
    )


# =============================================================================
# Private Helpers: Method Checking
# =============================================================================


def _collect_method_issues(tree: ast.AST) -> Iterator[SafetyIssue]:
    """Yield unique safety issues for blocked method calls and references.

    Detects both direct calls (``path.unlink()``) and method references
    (``delete_func = path.unlink``) which could be called later to bypass detection.
    """
    seen: set[str] = set()

    for node in ast.walk(tree):
        for issue in _get_method_issues_from_node(node):
            if issue.name not in seen:
                seen.add(issue.name)
                yield issue


def _get_method_issues_from_node(node: ast.AST) -> Iterator[SafetyIssue]:
    """Yield method issues from a single AST node (may include duplicates)."""
    # Method calls: path.unlink()
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if issue := _create_method_issue(node.func.attr):
            yield issue
    # Method references: delete_func = path.unlink
    elif isinstance(node, ast.Attribute) and (issue := _create_method_issue(node.attr, is_reference=True)):
        yield issue


def _create_method_issue(method: str, *, is_reference: bool = False) -> SafetyIssue | None:
    """Create a method issue if blocked."""
    if method not in BLOCKED_METHODS:
        return None

    detail = _METHOD_DETAILS.get(method, "blocked method")
    if is_reference:
        detail += " (reference)"
    return SafetyIssue(category=IssueCategory.METHOD, name=method, detail=detail)


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
        source = _get_code_source(args)
    except FileReadError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if issues := check_code(source.code):
        print("[BLOCKED] Code execution blocked due to safety concerns:")
        print(format_issues(issues))
        print("\nIf this code is safe, ask the user for permission to run directly.")
        return EXIT_BLOCKED

    print("[EXECUTED]", flush=True)
    return _execute_code(source.exec_args)


# =============================================================================
# CLI: Private Helpers
# =============================================================================


def _build_argument_parser() -> argparse.ArgumentParser:  # pragma: no cover
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_python_safely",
        description="Execute Python code safely by checking for dangerous operations first.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c "print(2 + 2)"          Execute inline code
  %(prog)s -f script.py               Execute code from file

Exit codes:
  0  Code executed successfully
  1  Code blocked due to safety concerns
  2  Usage error or file not found
  3  Execution timed out (5 minute limit)
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c",
        "--code",
        metavar="CODE",
        help="Python code to execute as a string",
    )
    group.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help="Path to Python file to execute",
    )

    return parser


def _read_code_from_file(filepath: Path) -> CodeSource:
    """Read Python code from a file.

    Args:
        filepath (Path): Path to the Python file.

    Returns:
        CodeSource: The code and execution arguments.

    Raises:
        FileReadError: If the file doesn't exist or can't be read.
    """
    if not filepath.exists():
        raise FileReadError(f"File not found: {filepath}")
    try:
        code = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileReadError(f"Cannot read file: {e}") from e

    return CodeSource(code=code, exec_args=[sys.executable, str(filepath)])


def _get_code_source(args: argparse.Namespace) -> CodeSource:  # pragma: no cover
    """Extract code source from parsed CLI arguments."""
    if args.code is not None:
        return CodeSource(
            code=args.code,
            exec_args=[sys.executable, "-c", args.code],
        )
    return _read_code_from_file(Path(args.file))


def _execute_code(exec_args: list[str]) -> int:  # pragma: no cover
    """Execute code with timeout protection.

    Args:
        exec_args (list[str]): Arguments for subprocess.run.

    Returns:
        int: Exit code from the subprocess, or EXIT_TIMEOUT if timed out.
    """
    try:
        result = subprocess.run(  # noqa: S603
            exec_args, check=False, timeout=EXECUTION_TIMEOUT_SECONDS
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print(
            f"\n[TIMEOUT] Code execution timed out after {EXECUTION_TIMEOUT_SECONDS // 60} minutes.",
            file=sys.stderr,
        )
        return EXIT_TIMEOUT


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

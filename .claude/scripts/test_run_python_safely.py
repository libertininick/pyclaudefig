"""Comprehensive tests for run_python_safely module."""
# ruff: noqa: S101, S404, S603, S607, PLR6301, PLC1901, PLC2701, PLW1510, PLW1514

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from run_python_safely import (
    BLOCKED_BUILTINS,
    BLOCKED_IMPORTS,
    BLOCKED_METHODS,
    CodeSource,
    FileReadError,
    IssueCategory,
    SafetyIssue,
    _read_code_from_file,
    check_code,
    format_issues,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_python_file(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary Python file for testing."""
    filepath = tmp_path / "test_script.py"
    yield filepath
    filepath.unlink(missing_ok=True)


@pytest.fixture
def script_path() -> Path:
    """Path to the run_python_safely.py script."""
    return Path(__file__).parent / "run_python_safely.py"


# ============================================================================
# TestCheckCodeImports
# ============================================================================


class TestCheckCodeImports:
    """Tests for import detection in check_code."""

    def test_blocked_import_os(self) -> None:
        """Given 'import os', check_code returns issue for os."""
        issues = check_code("import os")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"

    def test_blocked_import_subprocess(self) -> None:
        """Given 'import subprocess', check_code returns issue."""
        issues = check_code("import subprocess")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "subprocess"

    def test_blocked_import_from(self) -> None:
        """Given 'from os import path', check_code returns issue for os."""
        issues = check_code("from os import path")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"

    def test_blocked_import_nested(self) -> None:
        """Given 'import os.path', check_code returns issue for os."""
        issues = check_code("import os.path")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"

    def test_safe_import_math(self) -> None:
        """Given 'import math', check_code returns empty list."""
        issues = check_code("import math")
        assert len(issues) == 0

    def test_safe_import_json(self) -> None:
        """Given 'import json', check_code returns empty list."""
        issues = check_code("import json")
        assert len(issues) == 0

    def test_safe_import_pathlib(self) -> None:
        """Given 'import pathlib', check_code returns empty list."""
        issues = check_code("import pathlib")
        assert len(issues) == 0

    @pytest.mark.parametrize("blocked_import", list(BLOCKED_IMPORTS))
    def test_all_blocked_imports_detected(self, blocked_import: str) -> None:
        """Parametrized test for all items in BLOCKED_IMPORTS."""
        code = f"import {blocked_import}"
        issues = check_code(code)
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == blocked_import

    def test_duplicate_imports_deduplicated(self) -> None:
        """Given 'import os; import os', check_code returns single issue."""
        issues = check_code("import os\nimport os")
        assert len(issues) == 1
        assert issues[0].name == "os"

    def test_import_from_star_returns_issue(self) -> None:
        """Given 'from os import *', check_code returns issue for os."""
        issues = check_code("from os import *")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"


# ============================================================================
# TestCheckCodeBuiltins
# ============================================================================


class TestCheckCodeBuiltins:
    """Tests for builtin detection in check_code."""

    def test_blocked_builtin_eval(self) -> None:
        """Given 'eval(x)', check_code returns issue for eval."""
        issues = check_code("eval(x)")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "eval"

    def test_blocked_builtin_exec(self) -> None:
        """Given 'exec(x)', check_code returns issue for exec."""
        issues = check_code("exec(x)")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "exec"

    def test_blocked_builtin_open(self) -> None:
        """Given 'open(x)', check_code returns issue for open."""
        issues = check_code("open('file.txt')")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "open"

    def test_blocked_builtin_compile(self) -> None:
        """Given 'compile(x, y, z)', check_code returns issue for compile."""
        issues = check_code("compile('x', 'f', 'exec')")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "compile"

    def test_safe_builtin_len(self) -> None:
        """Given 'len([1,2,3])', check_code returns empty list."""
        issues = check_code("len([1, 2, 3])")
        assert len(issues) == 0

    def test_safe_builtin_str(self) -> None:
        """Given 'str(42)', check_code returns empty list."""
        issues = check_code("str(42)")
        assert len(issues) == 0

    def test_safe_builtin_print(self) -> None:
        """Given 'print(x)', check_code returns empty list."""
        issues = check_code("print('hello')")
        assert len(issues) == 0

    def test_safe_builtin_range(self) -> None:
        """Given 'range(10)', check_code returns empty list."""
        issues = check_code("range(10)")
        assert len(issues) == 0

    @pytest.mark.parametrize("blocked_builtin", list(BLOCKED_BUILTINS))
    def test_all_blocked_builtins_detected(self, blocked_builtin: str) -> None:
        """Parametrized test for all items in BLOCKED_BUILTINS."""
        code = f"{blocked_builtin}(x)"
        issues = check_code(code)
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == blocked_builtin

    def test_duplicate_builtins_deduplicated(self) -> None:
        """Given 'eval(x); eval(y)', check_code returns single issue."""
        issues = check_code("eval(x)\neval(y)")
        assert len(issues) == 1
        assert issues[0].name == "eval"

    def test_blocked_builtin_as_argument(self) -> None:
        """Given 'print(eval(x))', check_code returns issue for eval."""
        issues = check_code("print(eval(x))")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "eval"

    def test_blocked_builtin_nested_in_expression(self) -> None:
        """Given 'result = 1 + eval(x)', check_code returns issue for eval."""
        issues = check_code("result = 1 + eval(x)")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "eval"

    def test_multiple_blocked_builtins_in_expression(self) -> None:
        """Given 'exec(eval(x))', check_code returns issues for both."""
        issues = check_code("exec(eval(x))")
        assert len(issues) == 2
        names = {issue.name for issue in issues}
        assert names == {"eval", "exec"}


# ============================================================================
# TestCheckCodeBuiltinAliases
# ============================================================================


class TestCheckCodeBuiltinAliases:
    """Tests for builtin alias detection in check_code."""

    def test_blocked_builtin_alias_eval(self) -> None:
        """Given 'evil = eval', check_code returns issue for eval."""
        issues = check_code("evil = eval")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "eval"
        assert "aliased" in issues[0].detail

    def test_blocked_builtin_alias_exec(self) -> None:
        """Given 'run = exec', check_code returns issue for exec."""
        issues = check_code("run = exec")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "exec"
        assert "aliased" in issues[0].detail

    def test_blocked_builtin_alias_open(self) -> None:
        """Given 'file_open = open', check_code returns issue for open."""
        issues = check_code("file_open = open")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "open"
        assert "aliased" in issues[0].detail

    def test_blocked_builtin_walrus_operator(self) -> None:
        """Given '(evil := eval)', check_code returns issue for eval."""
        issues = check_code("x = (evil := eval)")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == "eval"
        assert "aliased" in issues[0].detail

    def test_safe_assignment_not_builtin(self) -> None:
        """Given 'x = y', check_code returns empty list."""
        issues = check_code("x = y")
        assert len(issues) == 0

    def test_safe_assignment_to_literal(self) -> None:
        """Given 'x = 42', check_code returns empty list."""
        issues = check_code("x = 42")
        assert len(issues) == 0

    def test_duplicate_aliases_deduplicated(self) -> None:
        """Given 'a = eval; b = eval', check_code returns single issue."""
        issues = check_code("a = eval\nb = eval")
        assert len(issues) == 1
        assert issues[0].name == "eval"

    @pytest.mark.parametrize("blocked_builtin", list(BLOCKED_BUILTINS))
    def test_all_blocked_builtins_aliases_detected(self, blocked_builtin: str) -> None:
        """Parametrized test for aliasing all items in BLOCKED_BUILTINS."""
        code = f"alias = {blocked_builtin}"
        issues = check_code(code)
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.BUILTIN
        assert issues[0].name == blocked_builtin

    def test_blocked_builtin_tuple_unpacking(self) -> None:
        """Given 'e, x = eval, exec', check_code returns issues for both."""
        issues = check_code("e, x = eval, exec")
        assert len(issues) == 2
        names = {issue.name for issue in issues}
        assert names == {"eval", "exec"}
        # Both should be marked as aliased
        for issue in issues:
            assert "aliased" in issue.detail

    def test_blocked_builtin_tuple_unpacking_single(self) -> None:
        """Given 'e, y = eval, my_func', check_code returns issue for eval."""
        issues = check_code("e, y = eval, my_func")
        assert len(issues) == 1
        assert issues[0].name == "eval"
        assert "aliased" in issues[0].detail

    def test_blocked_builtin_tuple_unpacking_mixed_safe(self) -> None:
        """Given 'a, b, c = len, str, int', check_code returns empty list."""
        issues = check_code("a, b, c = len, str, int")
        assert len(issues) == 0


# ============================================================================
# TestCheckCodeMethods
# ============================================================================


class TestCheckCodeMethods:
    """Tests for method detection in check_code."""

    def test_blocked_method_unlink(self) -> None:
        """Given 'path.unlink()', check_code returns issue."""
        issues = check_code("path.unlink()")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "unlink"

    def test_blocked_method_write_text(self) -> None:
        """Given 'path.write_text(x)', check_code returns issue."""
        issues = check_code("path.write_text('content')")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "write_text"

    def test_blocked_method_mkdir(self) -> None:
        """Given 'path.mkdir()', check_code returns issue."""
        issues = check_code("path.mkdir()")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "mkdir"

    def test_blocked_method_rmtree(self) -> None:
        """Given 'shutil.rmtree(x)', check_code returns issue."""
        issues = check_code("tree.rmtree()")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "rmtree"

    def test_safe_method_read(self) -> None:
        """Given 'file.read()', check_code returns empty list."""
        issues = check_code("file.read()")
        assert len(issues) == 0

    def test_safe_method_append(self) -> None:
        """Given 'list.append(x)', check_code returns empty list."""
        issues = check_code("items.append(1)")
        assert len(issues) == 0

    def test_safe_method_strip(self) -> None:
        """Given 's.strip()', check_code returns empty list."""
        issues = check_code("s.strip()")
        assert len(issues) == 0

    @pytest.mark.parametrize("blocked_method", list(BLOCKED_METHODS))
    def test_all_blocked_methods_detected(self, blocked_method: str) -> None:
        """Parametrized test for all items in BLOCKED_METHODS."""
        code = f"obj.{blocked_method}()"
        issues = check_code(code)
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == blocked_method

    def test_duplicate_methods_deduplicated(self) -> None:
        """Given 'a.unlink(); b.unlink()', check_code returns single issue."""
        issues = check_code("a.unlink()\nb.unlink()")
        assert len(issues) == 1
        assert issues[0].name == "unlink"

    def test_blocked_method_on_chained_call(self) -> None:
        """Given 'Path('x').parent.unlink()', check_code returns issue."""
        issues = check_code("Path('x').parent.unlink()")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "unlink"

    def test_blocked_method_on_deeply_chained_call(self) -> None:
        """Given 'obj.a.b.c.unlink()', check_code returns issue."""
        issues = check_code("obj.a.b.c.unlink()")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "unlink"

    def test_blocked_method_in_list_comprehension(self) -> None:
        """Given '[p.unlink() for p in paths]', check_code returns issue."""
        issues = check_code("[p.unlink() for p in paths]")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "unlink"


# ============================================================================
# TestCheckCodeMethodReferences
# ============================================================================


class TestCheckCodeMethodReferences:
    """Tests for method reference detection (without calls) in check_code."""

    def test_blocked_method_reference_unlink(self) -> None:
        """Given 'delete = path.unlink', check_code returns issue."""
        issues = check_code("delete = path.unlink")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "unlink"
        assert "reference" in issues[0].detail

    def test_blocked_method_reference_write_text(self) -> None:
        """Given 'writer = path.write_text', check_code returns issue."""
        issues = check_code("writer = path.write_text")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "write_text"
        assert "reference" in issues[0].detail

    def test_blocked_method_reference_mkdir(self) -> None:
        """Given 'create_dir = path.mkdir', check_code returns issue."""
        issues = check_code("create_dir = path.mkdir")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "mkdir"
        assert "reference" in issues[0].detail

    def test_blocked_method_reference_rmtree(self) -> None:
        """Given 'cleanup = shutil.rmtree', check_code returns issue."""
        issues = check_code("cleanup = shutil.rmtree")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == "rmtree"
        assert "reference" in issues[0].detail

    def test_safe_method_reference_read_text(self) -> None:
        """Given 'reader = path.read_text', check_code returns empty list."""
        issues = check_code("reader = path.read_text")
        assert len(issues) == 0

    def test_safe_method_reference_append(self) -> None:
        """Given 'adder = items.append', check_code returns empty list."""
        issues = check_code("adder = items.append")
        assert len(issues) == 0

    @pytest.mark.parametrize("blocked_method", list(BLOCKED_METHODS))
    def test_all_blocked_method_references_detected(self, blocked_method: str) -> None:
        """Parametrized test for referencing all items in BLOCKED_METHODS."""
        code = f"func = obj.{blocked_method}"
        issues = check_code(code)
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.METHOD
        assert issues[0].name == blocked_method


# ============================================================================
# TestCheckCodeRelativeImports
# ============================================================================


class TestCheckCodeRelativeImports:
    """Tests for relative import detection in check_code."""

    def test_relative_import_blocked_os(self) -> None:
        """Given 'from . import os', check_code returns issue for os."""
        issues = check_code("from . import os")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"

    def test_relative_import_blocked_subprocess(self) -> None:
        """Given 'from . import subprocess', check_code returns issue."""
        issues = check_code("from . import subprocess")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "subprocess"

    def test_relative_import_safe_module(self) -> None:
        """Given 'from . import mymodule', check_code returns empty list."""
        issues = check_code("from . import mymodule")
        assert len(issues) == 0

    def test_relative_import_multiple_blocked(self) -> None:
        """Given 'from . import os, sys', check_code returns issues for both."""
        issues = check_code("from . import os, sys")
        assert len(issues) == 2
        names = {issue.name for issue in issues}
        assert names == {"os", "sys"}

    def test_relative_import_parent_level(self) -> None:
        """Given 'from .. import os', check_code returns issue for os."""
        issues = check_code("from .. import os")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.IMPORT
        assert issues[0].name == "os"


# ============================================================================
# TestCheckCodeSyntax
# ============================================================================


class TestCheckCodeSyntax:
    """Tests for syntax error handling in check_code."""

    def test_syntax_error_returns_issue(self) -> None:
        """Given 'def f(', check_code returns syntax issue."""
        issues = check_code("def f(")
        assert len(issues) == 1
        assert issues[0].category == IssueCategory.SYNTAX
        assert issues[0].name == "SyntaxError"

    def test_valid_code_returns_empty(self) -> None:
        """Given 'x = 1 + 2', check_code returns empty list."""
        issues = check_code("x = 1 + 2")
        assert len(issues) == 0

    def test_empty_code_returns_empty(self) -> None:
        """Given empty string, check_code returns empty list."""
        issues = check_code("")
        assert len(issues) == 0

    def test_whitespace_only_returns_empty(self) -> None:
        """Given whitespace only, check_code returns empty list."""
        issues = check_code("   \n\t  ")
        assert len(issues) == 0

    def test_comment_only_returns_empty(self) -> None:
        """Given comment only, check_code returns empty list."""
        issues = check_code("# This is a comment")
        assert len(issues) == 0


# ============================================================================
# TestCheckCodeCombined
# ============================================================================


class TestCheckCodeCombined:
    """Tests for code with multiple types of issues."""

    def test_multiple_issues_all_returned(self) -> None:
        """Given code with import, builtin, and method issues, returns all."""
        code = "import os\neval(x)\npath.unlink()"
        issues = check_code(code)
        assert len(issues) == 3
        categories = {issue.category for issue in issues}
        assert categories == {
            IssueCategory.IMPORT,
            IssueCategory.BUILTIN,
            IssueCategory.METHOD,
        }

    def test_multiple_imports_returned(self) -> None:
        """Given code with multiple blocked imports, returns all."""
        code = "import os\nimport subprocess"
        issues = check_code(code)
        assert len(issues) == 2
        names = {issue.name for issue in issues}
        assert names == {"os", "subprocess"}

    def test_safe_code_with_complex_logic(self) -> None:
        """Given safe code with complex logic, returns empty list."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = [fibonacci(i) for i in range(10)]
print(result)
"""
        issues = check_code(code)
        assert len(issues) == 0


# ============================================================================
# TestFormatIssues
# ============================================================================


class TestFormatIssues:
    """Tests for format_issues function."""

    def test_format_single_import_issue(self) -> None:
        """Given single import issue, formats correctly."""
        issues = [SafetyIssue(IssueCategory.IMPORT, "os", "file system operations")]
        result = format_issues(issues)
        assert result == "  - Import: os (file system operations)"

    def test_format_single_builtin_issue(self) -> None:
        """Given single builtin issue, formats correctly."""
        issues = [SafetyIssue(IssueCategory.BUILTIN, "eval", "arbitrary code execution")]
        result = format_issues(issues)
        assert result == "  - Builtin: eval (arbitrary code execution)"

    def test_format_multiple_issues(self) -> None:
        """Given multiple issues, formats all on separate lines."""
        issues = [
            SafetyIssue(IssueCategory.IMPORT, "os", "file system operations"),
            SafetyIssue(IssueCategory.BUILTIN, "eval", "arbitrary code execution"),
            SafetyIssue(IssueCategory.METHOD, "unlink", "file deletion"),
        ]
        result = format_issues(issues)
        lines = result.split("\n")
        assert len(lines) == 3
        assert "Import: os" in lines[0]
        assert "Builtin: eval" in lines[1]
        assert "Method: unlink" in lines[2]

    def test_format_empty_list(self) -> None:
        """Given empty list, returns empty string."""
        result = format_issues([])
        assert result == ""

    def test_format_syntax_issue(self) -> None:
        """Given syntax issue, formats correctly."""
        issues = [SafetyIssue(IssueCategory.SYNTAX, "SyntaxError", "unexpected EOF")]
        result = format_issues(issues)
        assert result == "  - Syntax: SyntaxError (unexpected EOF)"


# ============================================================================
# TestCLICodeString
# ============================================================================


class TestCLICodeString:
    """Tests for CLI with -c flag (code string input)."""

    def test_cli_safe_code_executes(self, script_path: Path) -> None:
        """Test -c with safe code executes and returns 0."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "print(2 + 2)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[EXECUTED]" in result.stdout
        assert "4" in result.stdout

    def test_cli_unsafe_import_blocks(self, script_path: Path) -> None:
        """Test -c with unsafe import blocks and returns 1."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "import os"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Import: os" in result.stdout

    def test_cli_unsafe_builtin_blocks(self, script_path: Path) -> None:
        """Test -c with unsafe builtin blocks and returns 1."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "eval('1+1')"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Builtin: eval" in result.stdout

    def test_cli_unsafe_method_blocks(self, script_path: Path) -> None:
        """Test -c with unsafe method blocks and returns 1."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "path.unlink()"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Method: unlink" in result.stdout

    def test_cli_blocked_output_includes_permission_hint(self, script_path: Path) -> None:
        """Test blocked output includes hint about asking user permission."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "import os"],
            capture_output=True,
            text=True,
        )
        assert "ask the user for permission" in result.stdout

    def test_cli_syntax_error_blocks(self, script_path: Path) -> None:
        """Test -c with syntax error blocks and returns 1."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "def f("],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Syntax" in result.stdout


# ============================================================================
# TestCLIFileInput
# ============================================================================


class TestCLIFileInput:
    """Tests for CLI with -f flag (file input)."""

    def test_cli_file_safe_executes(self, script_path: Path, tmp_python_file: Path) -> None:
        """Test -f with safe file executes and returns 0."""
        tmp_python_file.write_text("print('hello from file')")
        result = subprocess.run(
            ["python", str(script_path), "-f", str(tmp_python_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[EXECUTED]" in result.stdout
        assert "hello from file" in result.stdout

    def test_cli_file_unsafe_blocks(self, script_path: Path, tmp_python_file: Path) -> None:
        """Test -f with unsafe file blocks and returns 1."""
        tmp_python_file.write_text("import subprocess")
        result = subprocess.run(
            ["python", str(script_path), "-f", str(tmp_python_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Import: subprocess" in result.stdout

    def test_cli_file_not_found(self, script_path: Path) -> None:
        """Test -f with non-existent file returns 2."""
        result = subprocess.run(
            ["python", str(script_path), "-f", "/nonexistent/file.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "[ERROR]" in result.stderr
        assert "not found" in result.stderr.lower()

    def test_cli_file_with_syntax_error(self, script_path: Path, tmp_python_file: Path) -> None:
        """Test -f with file containing syntax error blocks."""
        tmp_python_file.write_text("def broken(")
        result = subprocess.run(
            ["python", str(script_path), "-f", str(tmp_python_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[BLOCKED]" in result.stdout
        assert "Syntax" in result.stdout


# ============================================================================
# TestCLIEdgeCases
# ============================================================================


class TestCLIEdgeCases:
    """Tests for CLI edge cases."""

    def test_cli_no_args_shows_help(self, script_path: Path) -> None:
        """Test no arguments shows error and returns 2."""
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        # argparse prints error to stderr
        assert "required" in result.stderr.lower() or "usage" in result.stderr.lower()

    def test_cli_help_flag(self, script_path: Path) -> None:
        """Test --help shows usage information."""
        result = subprocess.run(
            ["python", str(script_path), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
        assert "-c" in result.stdout
        assert "-f" in result.stdout

    def test_cli_empty_code_string(self, script_path: Path) -> None:
        """Test -c with empty string executes (empty code is safe)."""
        result = subprocess.run(
            ["python", str(script_path), "-c", ""],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[EXECUTED]" in result.stdout

    def test_cli_code_returning_nonzero(self, script_path: Path) -> None:
        """Test -c with code that exits non-zero returns that code."""
        result = subprocess.run(
            ["python", str(script_path), "-c", "raise SystemExit(42)"],
            capture_output=True,
            text=True,
        )
        # Safe to execute, but the executed code exits with 42
        assert result.returncode == 42

    def test_cli_complex_safe_code(self, script_path: Path) -> None:
        """Test -c with complex but safe code executes."""
        code = """
import json
import math
data = {'pi': math.pi, 'e': math.e}
print(json.dumps(data))
"""
        result = subprocess.run(
            ["python", str(script_path), "-c", code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[EXECUTED]" in result.stdout
        assert "3.14" in result.stdout  # pi value


# ============================================================================
# TestReadCodeFromFile
# ============================================================================


class TestReadCodeFromFile:
    """Tests for _read_code_from_file function."""

    def test_read_valid_file(self, tmp_path: Path) -> None:
        """Given a valid Python file, returns CodeSource with correct content."""
        filepath = tmp_path / "test_script.py"
        filepath.write_text("print('hello')", encoding="utf-8")

        result = _read_code_from_file(filepath)

        assert isinstance(result, CodeSource)
        assert result.code == "print('hello')"
        assert str(filepath) in result.exec_args

    def test_read_file_preserves_encoding(self, tmp_path: Path) -> None:
        """Given a file with unicode content, returns correct content."""
        filepath = tmp_path / "unicode_script.py"
        content = "print('こんにちは')"
        filepath.write_text(content, encoding="utf-8")

        result = _read_code_from_file(filepath)

        assert result.code == content

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Given a non-existent file, raises FileReadError."""
        filepath = tmp_path / "nonexistent.py"

        with pytest.raises(FileReadError, match="File not found"):
            _read_code_from_file(filepath)

    def test_unreadable_file_raises_error(self, tmp_path: Path) -> None:
        """Given a file with invalid encoding, raises FileReadError."""
        filepath = tmp_path / "binary_file.py"
        # Write invalid UTF-8 bytes
        filepath.write_bytes(b"\x80\x81\x82")

        with pytest.raises(FileReadError, match="Cannot read file"):
            _read_code_from_file(filepath)

    def test_exec_args_contains_python_and_filepath(self, tmp_path: Path) -> None:
        """Returned exec_args should contain python executable and filepath."""
        filepath = tmp_path / "script.py"
        filepath.write_text("x = 1", encoding="utf-8")

        result = _read_code_from_file(filepath)

        assert result.exec_args[0] == sys.executable
        assert result.exec_args[1] == str(filepath)
        assert len(result.exec_args) == 2


# ============================================================================
# TestSafetyIssueDataclass
# ============================================================================


class TestSafetyIssueDataclass:
    """Tests for SafetyIssue dataclass."""

    def test_safety_issue_is_frozen(self) -> None:
        """SafetyIssue should be immutable (frozen)."""
        issue = SafetyIssue(IssueCategory.IMPORT, "os", "file ops")
        with pytest.raises(AttributeError):
            issue.name = "changed"  # type: ignore[misc]

    def test_safety_issue_equality(self) -> None:
        """SafetyIssue instances with same values should be equal."""
        issue1 = SafetyIssue(IssueCategory.IMPORT, "os", "file ops")
        issue2 = SafetyIssue(IssueCategory.IMPORT, "os", "file ops")
        assert issue1 == issue2

    def test_safety_issue_hashable(self) -> None:
        """SafetyIssue should be hashable (for use in sets)."""
        issue = SafetyIssue(IssueCategory.IMPORT, "os", "file ops")
        issue_set = {issue}
        assert issue in issue_set


# ============================================================================
# TestIssueCategoryEnum
# ============================================================================


class TestIssueCategoryEnum:
    """Tests for IssueCategory enum."""

    def test_category_values(self) -> None:
        """IssueCategory should have expected values."""
        assert IssueCategory.IMPORT.value == "import"
        assert IssueCategory.BUILTIN.value == "builtin"
        assert IssueCategory.METHOD.value == "method"
        assert IssueCategory.SYNTAX.value == "syntax"

    def test_category_count(self) -> None:
        """IssueCategory should have exactly 4 members."""
        assert len(IssueCategory) == 4

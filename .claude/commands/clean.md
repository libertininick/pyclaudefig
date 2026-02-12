---
name: clean
description: Clean Python code by organizing, simplifying, and removing bloat
depends_on_agents:
  - code-cleaner
---

# Clean Code

Clean Python code files: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command dispatches the `code-cleaner` agent to analyze and fix code quality issues including:
- Code organization (imports, module structure)
- Bloat removal (unused imports, variables, dead code)
- Pythonic idioms (comprehensions, built-ins, context managers)
- Complexity reduction (extract helpers, reduce nesting)
- Docstring quality (format and accuracy)
- Type hint completeness

## Usage

```
/clean <file>              # Single file
/clean <glob>              # Multiple files via glob pattern
/clean staged              # Git staged files
/clean unstaged            # Git unstaged modified files
/clean all                 # All Python files in project
```

### Flags

- `--dry-run`: Report findings without modifying files

## Examples

```bash
# Clean a single file
/clean src/my_library/utils/parser.py

# Clean all files in a directory
/clean src/my_library/**/*.py

# Clean only staged files before commit
/clean staged

# Preview what would be cleaned
/clean staged --dry-run

# Clean all modified files
/clean unstaged

# Clean entire codebase
/clean all
```

## Target Resolution

### `<file>` or `<glob>`
- Direct file path: `/clean path/to/file.py`
- Glob pattern: `/clean src/**/*.py`
- Multiple patterns supported: `/clean src/*.py tests/*.py`

### `staged`
Files staged for commit:
```bash
git diff --cached --name-only --diff-filter=d -- "*.py"
```

### `unstaged`
Modified but unstaged files:
```bash
git diff --name-only --diff-filter=d -- "*.py"
```

### `all`
All tracked Python files:
```bash
git ls-files "*.py"
```

## Execution Flow

1. **Resolve targets** - Convert command arguments to file list
2. **Dispatch to code-cleaner agent** - Agent loads its context bundle
3. **Process each file**:
   - Read and analyze
   - Apply fixes (unless --dry-run)
   - Validate with `validate-code` skill: `uv run python .claude/scripts/validate_code.py`
4. **Report results** - Summary of changes/findings

## After Cleaning

- Review changes with `git diff`
- Run full validation: `uv run python .claude/scripts/validate_code.py`
- Commit cleaned code

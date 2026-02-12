---
name: validate-code
description: Run code validation checks (lint, format, type, docstring, doctest, test). Use when validating code quality after writing or modifying Python code.
user-invocable: true
argument-hint: "[--lint] [--format] [--type] [--docstring] [--doctest] [--test] [paths...]"
---

# Validate

Run code validation checks via a single centralized script. All checks run independently — a failure in one does not prevent others from running.

## Quick Reference

| Flag | Check | Underlying Command |
|------|-------|--------------------|
| `--lint` | Linting | `uv run ruff check` |
| `--format` | Formatting | `uv run ruff format --check` |
| `--type` | Type checking | `uv run ty check` |
| `--docstring` | Docstrings | `uv tool run pydoclint --style=google --allow-init-docstring=True` |
| `--doctest` | Doctest examples | `uv run pytest --doctest-modules` |
| `--test` | Tests + coverage | `uv run pytest --cov` |

## Usage

```bash
# Run all checks on project root
uv run python .claude/scripts/validate_code.py

# Run specific checks
uv run python .claude/scripts/validate_code.py --lint --type

# Run on specific path
uv run python .claude/scripts/validate_code.py --lint src/chain_reaction/

# Run on specific file
uv run python .claude/scripts/validate_code.py --docstring src/chain_reaction/utils/parser.py

# Run tests on specific directory
uv run python .claude/scripts/validate_code.py --test tests/unit/
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All selected checks passed |
| 1 | One or more checks failed |

## When to Use

- **After writing code** — run all checks to verify quality
- **After modifying code** — run checks scoped to changed files
- **Before committing** — run full validation as a final gate
- **During review** — verify code meets quality standards

## Mutation Commands (Not Part of Validation)

The validate script is **read-only** — it checks but does not modify files. For auto-fixing, use these commands directly:

```bash
uv run ruff check --fix <paths>   # auto-fix lint issues
uv run ruff format <paths>        # auto-format code
```

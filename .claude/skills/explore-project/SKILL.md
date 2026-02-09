---
name: explore-project
version: 1.0.0
description: Explore project structure to understand layout, packages, and key files. Use when you need context about how the project is organized.
user-invocable: true
---

# Explore Project Structure

Discover and understand the layout of any Python project. Use this when you need context about how the project is organized before making changes.

## Quick Start

Run these commands to understand the project:

```bash
# 1. Top-level layout
ls -1 .

# 2. Project configuration
cat pyproject.toml   # or setup.py, setup.cfg

# 3. Directory tree (2 levels deep, ignore noise)
find . -maxdepth 2 -type d \
  -not -path './.git*' \
  -not -path './.venv*' \
  -not -path './venv*' \
  -not -path './.claude*' \
  -not -path './__pycache__*' \
  -not -path './.mypy_cache*' \
  -not -path './.pytest_cache*' \
  -not -path './.ruff_cache*' \
  -not -path './.tox*' \
  -not -path './.nox*' \
  -not -path './node_modules*' \
  -not -path './dist*' \
  -not -path './build*' \
  -not -path './*.egg-info*' \
  | sort
```

## What to Look For

### 1. Identify the Package Layout

| Layout | How to Recognize | Entry Point |
|--------|-----------------|-------------|
| **src layout** | `src/<package>/` with `__init__.py` | `src/<package>/` |
| **flat layout** | `<package>/` at root with `__init__.py` | `<package>/` |
| **single module** | Standalone `.py` files at root | Root `.py` files |

### 2. Identify Key Directories

Look for these common directories and understand their role:

| Directory | Typical Purpose |
|-----------|----------------|
| `tests/`, `test/` | Test suite |
| `docs/`, `doc/` | Documentation |
| `scripts/` | Utility/build scripts |
| `examples/` | Usage examples |
| `notebooks/` | Jupyter notebooks |
| `migrations/`, `alembic/` | Database migrations |
| `config/`, `conf/` | Configuration files |
| `data/` | Data files |
| `api/` | API definitions |
| `app/` | Application entry point |

### 3. Identify the Package Manager

| File | Manager |
|------|---------|
| `pyproject.toml` with `[tool.uv]` | uv |
| `pyproject.toml` with `[tool.poetry]` | Poetry |
| `requirements.txt` | pip |
| `Pipfile` | pipenv |
| `setup.py` / `setup.cfg` | setuptools |

### 4. Identify Entry Points

Check `pyproject.toml` for:
- `[project.scripts]` - CLI entry points
- `[project.gui-scripts]` - GUI entry points
- `[tool.setuptools.packages]` - Package discovery config

## When to Use

- Before implementing a feature that spans multiple modules
- When asked about project organization
- When you need to find where specific functionality lives
- When onboarding to an unfamiliar codebase

---
name: frameworks
version: 1.0.0
description: Approved frameworks and libraries for this codebase. Apply when selecting libraries, checking if a framework is approved, or fetching documentation for approved tools.
user-invocable: false
---

# Frameworks

Approved frameworks and libraries for this codebase.

## Critical Rules

1. **Use ONLY approved frameworks** - NEVER introduce alternatives or substitutes
2. **Fetch docs when uncertain** - Use the `fetch-docs` skill with the doc ID from the table below
3. **Use modern patterns** - Avoid deprecated methods; check latest docs if uncertain

## Quick Reference

| Framework | Purpose | Doc ID | Docs |
|-----------|---------|--------|------|
| pytest | Testing | `/pytest-dev/pytest` | [docs](https://docs.pytest.org/en/stable/) |
| pytest-check | Multiple failures per test | `/okken/pytest-check` | [docs](https://github.com/okken/pytest-check) |
| ruff | Linter and formatter | `/astral-sh/ruff` | [docs](https://docs.astral.sh/ruff/) |
| ty | Type checker | `/astral-sh/ty` | [docs](https://docs.astral.sh/ty/) |
| uv | Package manager | `/astral-sh/uv` | [docs](https://docs.astral.sh/uv/) |

## Fetching Documentation

When uncertain about API details, use the `fetch-docs` skill with the doc ID from the Quick Reference table above.

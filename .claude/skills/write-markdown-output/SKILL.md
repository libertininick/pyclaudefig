---
name: write-markdown-output
version: 1.2.0
description: Write content to a timestamped markdown file. Use when agents need to save plans, reviews, or other outputs.
user-invocable: true
argument-hint: <-s "scope" -o "output-dir">
---

# Write Markdown Output

Write content to a markdown file with a UTC timestamp in the filename.

## Quick Reference

| Input | Description |
|-------|-------------|
| `stdin` | Markdown content (always read from stdin; use a heredoc) |
| `-s`, `--scope` | Scope/title for the filename (e.g., "sql-validation-plan") |
| `-o`, `--output-dir` | Output directory path |

## Output Format

Files are written to: `<output-dir>/<timestamp>-<scope>.md`

| Format | Example |
|--------|---------|
| Timestamp | `2026-02-02T025204Z` |
| Full path | `.claude/agent-outputs/plans/2026-02-02T025204Z-sql-validation-plan.md` |

## Usage

Pass content via a bash heredoc. The single-quoted delimiter `<<'CONTENT_EOF'` prevents all shell interpolation, making backticks, dollar signs, quotes, and other special characters completely safe. Content is always read from stdin:

```bash
uv run python .claude/scripts/write_markdown_output.py -s "scope-name" -o ".claude/agent-outputs/plans" <<'CONTENT_EOF'
# Your Markdown Content

Code with `backticks`, $variables, "double quotes", and 'single quotes' are all safe.
CONTENT_EOF
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | File written successfully |
| 1 | Error writing file |
| 2 | Usage error (missing arguments) |

## Output

On success, prints the full path to the created file:

```
[WRITTEN] .claude/agent-outputs/plans/2026-02-02T025204Z-sql-validation-plan.md
```

## Agent Workflow

1. Generate content (plan, review, PR description, etc.)
2. Determine appropriate output directory
3. Use a single Bash call with a heredoc to pipe content via stdin
4. Report the file path to the user

## Output Directories

| Content Type | Directory |
|--------------|-----------|
| Plans | `.claude/agent-outputs/plans/` |
| Reviews | `.claude/agent-outputs/reviews/` |
| PR Descriptions | `.claude/agent-outputs/pr-descriptions/` |

---
name: write-markdown-output
version: 1.1.0
description: Write content to a timestamped markdown file. Use when agents need to save plans, reviews, or other outputs.
user-invocable: true
argument-hint: <-s "scope" -f "content-file" -o "output-dir">
---

# Write Markdown Output

Write content to a markdown file with a UTC timestamp in the filename.

## Quick Reference

| Input | Description |
|-------|-------------|
| `-s`, `--scope` | Scope/title for the filename (e.g., "sql-validation-plan") |
| `-f`, `--file` | Path to file containing markdown content **(recommended)** |
| `-c`, `--content` | Markdown content string (simple content only) |
| `-o`, `--output-dir` | Output directory path |

**Note**: `-f` and `-c` are mutually exclusive. Use `-f` for all real-world content to avoid shell quoting issues with single quotes, backticks, dollar signs, etc.

## Output Format

Files are written to: `<output-dir>/<timestamp>-<scope>.md`

| Format | Example |
|--------|---------|
| Timestamp | `2026-02-02T025204Z` |
| Full path | `.claude/agent-outputs/plans/2026-02-02T025204Z-sql-validation-plan.md` |

## Usage

### Recommended: Write content via file (-f)

Use the Write tool to save content to `/tmp/output-content.md`, then pass it with `-f`:

```bash
# Step 1: Use Write tool to create /tmp/output-content.md with the content
# Step 2: Invoke script with -f
uv run python .claude/scripts/write_markdown_output.py \
    -s "sql-validation-plan" \
    -f /tmp/output-content.md \
    -o ".claude/agent-outputs/plans"
```

### Alternative: Inline content (-c)

Only for simple content without shell-special characters:

```bash
uv run python .claude/scripts/write_markdown_output.py \
    -s "parser-review" \
    -c "# Simple content without quotes or backticks" \
    -o ".claude/agent-outputs/reviews"
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

## Python Function

```python
from datetime import datetime, timezone
from pathlib import Path

def write_markdown_output(scope: str, content: str, output_dir: Path | str) -> Path:
    """Write content to a timestamped markdown file.

    Args:
        scope: Scope/title for the filename (e.g., "sql-validation-plan").
        content: Markdown content to write.
        output_dir: Output directory path.

    Returns:
        Path: Full path to the created file.
    """
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}-{scope}.md"
    file_path = output_path / filename
    file_path.write_text(content, encoding="utf-8")

    return file_path
```

## Agent Workflow

1. Generate content (plan, review, PR description, etc.)
2. Determine appropriate output directory
3. Use the **Write tool** to save content to `/tmp/output-content.md`
4. Invoke script with `-f /tmp/output-content.md -s <scope> -o <dir>`
5. Report the file path to the user

## Output Directories

| Content Type | Directory |
|--------------|-----------|
| Plans | `.claude/agent-outputs/plans/` |
| Reviews | `.claude/agent-outputs/reviews/` |
| PR Descriptions | `.claude/agent-outputs/pr-descriptions/` |

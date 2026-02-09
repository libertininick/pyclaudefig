---
name: add-framework
version: 1.0.0
description: Add a new approved framework to the frameworks skill
depends_on_skills:
  - frameworks
  - validate-manifest
---

# Add Framework

Add a new approved framework: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## Usage

```
/add-framework <framework-name>
```

## Examples

```
/add-framework httpx
/add-framework pydantic
/add-framework sqlalchemy
```

## What This Does

This command adds a new approved framework to the codebase by:
1. Looking up the Context7 library ID
2. Finding official documentation links
3. Updating the frameworks skill with the new entry

## Workflow

### Step 1: Resolve Context7 Library ID

Use the Context7 MCP to find the library ID:

```
mcp__context7__resolve-library-id(libraryName="$ARGUMENTS", query="$ARGUMENTS documentation")
```

Present the results to the user and confirm the correct library ID.

### Step 2: Find Documentation URL

Search for the official documentation URL. Use web search if needed:
- Check the Context7 results for documentation links
- Look for official docs (not GitHub README)
- Prefer: `docs.<framework>.com`, `<framework>.readthedocs.io`, or official project docs

### Step 3: Confirm with User

Present the gathered information and ask the user to confirm:

| Field | Value |
|-------|-------|
| Framework name | `<name>` |
| Purpose | `<brief description>` |
| Context7 ID | `<id>` |
| Docs URL | `<url>` |

Ask: "Does this look correct? Should I add this framework?"

### Step 4: Update frameworks/SKILL.md

Add a new row to the Quick Reference table in `.claude/skills/frameworks/SKILL.md`:

```markdown
| <Framework> | <Purpose> | `<Context7 ID>` | [docs](<URL>) |
```

Keep the table sorted alphabetically by framework name.

### Step 5: Regenerate Bundles

Since the frameworks skill is included in agent bundles, regenerate them:

```bash
uv run python .claude/scripts/generate_bundles.py
```

### Step 6: Validate Manifest

Run the manifest validation script:

```bash
uv run python .claude/scripts/validate_manifest.py
```

Fix any errors before completing.

## Walkthrough

`/add-framework httpx` would:
1. Find Context7 ID: `/encode/httpx`
2. Find docs: `https://www.python-httpx.org/`
3. Add row: `| httpx | Async HTTP client | /encode/httpx | [docs](https://www.python-httpx.org/) |`

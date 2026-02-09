---
name: validate-manifest
version: 1.0.0
description: Validate .claude/manifest.json structure and references. Apply after modifying the manifest to ensure correctness.
user-invocable: false
---

# Validate Manifest

Validates the `.claude/manifest.json` file for structure, required fields, and dependency references.

## When to Apply

Use this skill after modifying the manifest:
- Adding a new skill, agent, or command
- Updating dependencies (`depends_on_skills`, `depends_on_agents`)
- Changing categories or versions

## Validation Script

Run the validation script:

```bash
uv run python .claude/scripts/validate_manifest.py
```

**Exit codes:**
- `0` - Manifest is valid
- `1` - Validation errors found (printed to stderr)

## What Gets Validated

| Check | Description |
|-------|-------------|
| JSON syntax | File must be valid JSON |
| Required fields | Each entry type has required fields (see below) |
| Categories | Skill categories must exist in `categories` object |
| Dependencies | All referenced skills/agents must exist |
| Uniqueness | Names must be unique within each type |
| Version format | Must be semver (e.g., "1.0.0") |

## Required Fields by Type

### Skills
```json
{
  "name": "skill-name",
  "category": "conventions|assessment|templates|utilities",
  "description": "Brief description",
  "user_invocable": true|false,
  "version": "1.0.0"
}
```

### Agents
```json
{
  "name": "agent-name",
  "description": "Brief description",
  "model": "opus|sonnet|haiku",
  "version": "1.0.0",
  "depends_on_skills": ["skill-name-1", "skill-name-2"]
}
```

### Commands
```json
{
  "name": "command-name",
  "description": "Brief description",
  "version": "1.0.0"
}
```

Optional command fields: `depends_on_skills`, `depends_on_agents`

## Workflow for Manifest Updates

1. **Make changes** to manifest.json
2. **Run validation**:
   ```bash
   uv run python .claude/scripts/validate_manifest.py
   ```
3. **Fix any errors** reported to stderr
4. **Repeat** until validation passes

## Example: Adding a New Skill

```json
{
  "name": "my-new-skill",
  "category": "conventions",
  "description": "What the skill does",
  "user_invocable": false,
  "version": "1.0.0"
}
```

Then validate:
```bash
uv run python .claude/scripts/validate_manifest.py
```

---
name: create-skill
version: 1.0.0
description: Create a new Claude Code skill
depends_on_skills:
  - skill-template
  - validate-manifest
---

# Create a New Skill

Create a new Claude Code skill: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command guides you through creating a new skill with proper structure and registration.

The workflow:
1. **Validate name** - Ensure skill name is lowercase with hyphens, max 64 chars
2. **Determine skill type** - Reference (auto-loaded), Task (manual only), or Hybrid
3. **Create directory** - Create `.claude/skills/<skill-name>/`
4. **Create SKILL.md** - Generate skill file with frontmatter and initial content
5. **Register in manifest** - Add entry to `.claude/manifest.json`
6. **Update CLAUDE.md** - Add to appropriate category in Skills section

## Usage

```
/create-skill <skill-name> + <description of skill>
```

## Examples

```
/create-skill naming-conventions to capture our specific naming convention patterns exemplified in <file>.py
/create-skill deployment-checklist for our 3 step checklist ...
/create-skill api-conventions ...
```

## When to Use This Command

Use `/create-skill` when:
- Converting conventions or patterns into reusable guidance
- Creating workflow automation that Claude should follow
- Documenting reference material for auto-loading
- Building task-specific skills with side effects

## Skill Types

| Type | `user-invocable` | `disable-model-invocation` | Use For |
|------|------------------|---------------------------|---------|
| **Reference** | `false` | (default) | Conventions, patterns, style guides. Claude loads automatically. |
| **Task** | (default) | `true` | Deployments, commits, side-effects. Manual trigger only. |
| **Hybrid** | (default) | (default) | Both auto-load and manual invocation work. |

## Workflow Steps

### Step 1: Validate Skill Name

Ensure the skill name:
- Is lowercase with hyphens (e.g., `my-new-skill`)
- Is max 64 characters
- Doesn't conflict with existing skills

Check existing skills:
```bash
ls -la .claude/skills/
```

### Step 2: Determine Skill Type and Category

Ask the user which type and category:

**Categories** (from manifest):
- `conventions` - Coding standards that define how code should be written
- `assessment` - Criteria used by reviewers to assess code quality
- `templates` - Format specifications for agent outputs
- `utilities` - Tools and scripts for common operations

### Step 3: Create Skill Directory and SKILL.md

```bash
mkdir -p .claude/skills/$ARGUMENTS
```

Create `SKILL.md` with this structure:

```yaml
---
name: <skill-name>
version: 1.0.0
description: <What this skill does. Claude uses this to decide when to load it.>
user-invocable: <true/false based on type>
disable-model-invocation: <true if task-only>
argument-hint: <optional hints for autocomplete>
---

# <Skill Title>

<Prescriptive, actionable instructions>
```

### Step 4: Register in manifest.json

Add entry to `.claude/manifest.json` in the `skills` array:

```json
{
  "name": "<skill-name>",
  "category": "<category>",
  "description": "<Brief description>",
  "user_invocable": <true/false>,
  "version": "1.0.0"
}
```

### Step 5: Update CLAUDE.md

Add the skill name to the appropriate category in `.claude/CLAUDE.md` Skills section:

```markdown
**Categories**:
- **Conventions**: ..., `<new-skill>`
```

### Step 6: Validate Manifest

Run the manifest validation script:

```bash
uv run python .claude/scripts/validate_manifest.py
```

Fix any errors before proceeding.

## Writing Effective Skills

For detailed guidance on writing prescriptive, actionable skills:
- Use `/skill-template` to see the full reference
- Include CORRECT/INCORRECT examples
- Use tables for quick reference
- Keep under 500 lines (use supporting files for details)

## After Creating

Test the skill:
1. If user-invocable: Try `/<skill-name>` to invoke it
2. If auto-loadable: Ask Claude something that should trigger it
3. Verify with: "What skills are available?"

If the skill is added to an agent's `depends_on_skills` list, regenerate bundles:
```bash
uv run python .claude/scripts/generate_bundles.py
```

---
name: skill-template
description: Skill structure, frontmatter options, and writing guidelines. Reference for creating Claude Code skills.
user-invocable: true
---

# Skill Template Reference

Reference documentation for creating [Claude Code skills](https://code.claude.com/docs/en/skills) with actionable, prescriptive instructions.

Use `/create-skill <name>` to create a new skill with guided workflow.

## Skill Location

```
.claude/skills/<skill-name>/SKILL.md
```

## SKILL.md Structure

```yaml
---
name: skill-name
description: What this skill does. Claude uses this to decide when to load it.
user-invocable: true          # Set false to hide from /menu (reference content)
disable-model-invocation: true # Set true to prevent auto-loading (manual only)
argument-hint: [arg1] [arg2]  # Shown during autocomplete
allowed-tools: Read, Grep     # Restrict tools when skill is active
context: fork                 # Run in isolated subagent
agent: Explore                # Subagent type when context: fork
---

# Skill Title

Your prescriptive, actionable instructions here.
```

## Frontmatter Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (defaults to directory name). Lowercase, hyphens, max 64 chars. |
| `description` | **Yes** | What it does and when to use it. Claude uses this for auto-loading. |
| `user-invocable` | No | `false` = hide from `/` menu. Use for background knowledge. Default: `true` |
| `disable-model-invocation` | No | `true` = only manual `/name` invocation. Use for side-effects. Default: `false` |
| `argument-hint` | No | Hint shown during autocomplete, e.g., `[filename] [format]` |
| `allowed-tools` | No | Comma-separated tools Claude can use without permission |
| `context` | No | `fork` = run in isolated subagent context |
| `agent` | No | Subagent type when `context: fork` (`Explore`, `Plan`, `general-purpose`) |

## Skill Types

| Type | `user-invocable` | `disable-model-invocation` | Use for |
|------|------------------|---------------------------|---------|
| Reference | `false` | (default) | Conventions, patterns, style guides. Claude loads automatically. |
| Task | (default) | `true` | Deployments, commits, side-effects. Manual trigger only. |
| Hybrid | (default) | (default) | Both auto-load and manual invocation work. |

## Writing Effective Skills

### Transform Principles into Patterns

Skills must be **prescriptive and actionable**. Vague principles don't change outputs.

```markdown
# INCORRECT - vague principle
Names should be descriptive and reveal intent.

# CORRECT - actionable pattern
## Function Names
**Pattern**: `<verb>_<noun>` in `snake_case`

| Verb | When to use | Example |
|------|-------------|---------|
| `get_` | Retrieve from memory/cache | `get_user_by_id` |
| `fetch_` | Retrieve from external source | `fetch_api_data` |
| `create_` | Instantiate new object | `create_session` |
```

### Use CORRECT/INCORRECT Examples

Show exactly what to do and what to avoid:

````markdown
```python
# CORRECT - descriptive name with verb_noun pattern
def fetch_user_by_email(email: str) -> User:
    """Fetch user from database by email address."""
    ...

# INCORRECT - generic name, no verb
def get_data(x):
    ...
```
````

### Use Tables for Quick Reference

Tables are scannable and enforceable:

```markdown
| Element | Convention | Example |
|---------|------------|---------|
| Functions | `verb_noun` | `fetch_user`, `validate_input` |
| Variables | `snake_case` | `user_count`, `is_valid` |
| Classes | `PascalCase` | `SearchIndex`, `UserSession` |
```

### Include Validation Commands

When applicable, show how to verify compliance using the `validate-code` skill:

```markdown
## Validation

Run checks via the `validate-code` skill:
```bash
uv run python .claude/scripts/validate_code.py                    # all checks
uv run python .claude/scripts/validate_code.py --lint --type      # specific checks
uv run python .claude/scripts/validate_code.py --docstring <path> # scoped to path
```
```

## Size Guidelines

- Keep `SKILL.md` under **500 lines**
- Move detailed reference material to separate files in the skill directory
- Reference supporting files from SKILL.md:

```markdown
## Additional Resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

## String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed to skill |
| `$ARGUMENTS[N]` or `$N` | Specific argument by index (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |

Example:

```yaml
---
name: fix-issue
description: Fix a GitHub issue
argument-hint: [issue-number]
---

Fix GitHub issue $ARGUMENTS following our coding standards.
```

## Skill Directory Structure

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output
└── scripts/
    └── validate.sh    # Script Claude can execute
```

## Registration Checklist

After creating the SKILL.md, register the skill in the system:

### 1. Add to manifest.json

Add an entry to `.claude/manifest.json` in the `skills` array:

```json
{
  "name": "my-skill",
  "category": "conventions",
  "description": "Short description for auto-loading decisions"
}
```

| Field | Description |
|-------|-------------|
| `name` | Must match directory name |
| `category` | One of: `conventions`, `assessment`, `templates`, `utilities` |
| `description` | Brief description (used by manifest consumers) |

### 2. Update CLAUDE.md Skills Section

Add the skill name to the appropriate category in `.claude/CLAUDE.md`:

```markdown
**Categories**:
- **Conventions**: `frameworks`, ..., `my-new-skill`
- **Assessment**: `maintainability`, `testability`
- **Templates**: `plan-template`, ...
- **Utilities**: `run-python-safely`, ...
```

### 3. Regenerate Bundles (if used by agents)

If the skill is added to any agent's `depends_on` list in manifest.json, regenerate bundles:

```bash
uv run python .claude/scripts/generate_bundles.py
```

**Note**: Only add skills to agent `depends_on` lists if the agent needs that skill's context. Most new skills won't need this step.

---

## Content Checklist

Before finalizing a skill, verify:

- [ ] Description clearly states **what** and **when**
- [ ] Instructions are **prescriptive** (patterns, not principles)
- [ ] Includes **CORRECT/INCORRECT** code examples
- [ ] Uses **tables** for quick reference where applicable
- [ ] Under **500 lines** (move details to supporting files)
- [ ] Correct `user-invocable` / `disable-model-invocation` settings
- [ ] Includes **validation commands** if applicable
- [ ] Includes Quick Reference / Quick Start at top if applicable

## Registration Checklist

- [ ] Added to `manifest.json` with correct category
- [ ] Added to CLAUDE.md Skills section
- [ ] Bundles regenerated (if skill added to agent `depends_on`)

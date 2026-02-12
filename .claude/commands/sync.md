---
name: sync
version: 1.0.0
description: Sync Claude context files with skills, agents, and commands on disk
---

# Sync Claude Context Files

Synchronize `.claude/` context files with the actual skills, agents, and commands on disk: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## Quick Reference

| Task | Command |
|------|---------|
| Full sync | `uv run python .claude/scripts/sync_context.py` |
| Preview changes | `uv run python .claude/scripts/sync_context.py --dry-run` |
| Check for drift | `uv run python .claude/scripts/sync_context.py --check` |
| Regenerate bundles | `uv run python .claude/scripts/generate_bundles.py` |

## Examples

```
/sync                # Full sync (scripts + bundles)
/sync --dry-run      # Preview changes without writing
/sync --check        # Check for drift
```

## What Gets Updated

| Section | Source of Truth | Updates |
|---------|-----------------|---------|
| CLAUDE.md Commands | `.claude/commands/*.md` | Command table |
| CLAUDE.md Agents | `.claude/agents/*.md` | Agent table |
| CLAUDE.md Context Bundles | Agent list | Bundle table |
| CLAUDE.md Skills | `manifest.json` | Category lists |
| manifest.json | Skill/agent/command frontmatter | Entries added/removed |
| Bundles | Skills + manifest | Regenerated |

## Usage

### 1. After Adding a New Skill

```bash
# Create skill directory and SKILL.md
mkdir -p .claude/skills/my-skill
# ... create SKILL.md with frontmatter ...

# Sync to update manifest.json and CLAUDE.md
uv run python .claude/scripts/sync_context.py

# If skill is used by an agent, add to depends_on_skills in manifest.json, then:
uv run python .claude/scripts/generate_bundles.py
```

### 2. After Adding a New Agent

```bash
# Create agent file with frontmatter
# ... create .claude/agents/my-agent.md ...

# Sync to update manifest.json, CLAUDE.md, and generate bundles
uv run python .claude/scripts/sync_context.py
```

### 3. After Adding a New Command

```bash
# Create command file with frontmatter
# ... create .claude/commands/my-command.md ...

# Sync to update manifest.json and CLAUDE.md
uv run python .claude/scripts/sync_context.py
```

### 4. After Removing Items

The sync script detects items that exist in manifest.json but not on disk, and removes them.

### 5. Check for Drift

To see what's out of sync without making changes:

```bash
uv run python .claude/scripts/sync_context.py --check
```

## Frontmatter Requirements

### Skills (.claude/skills/*/SKILL.md)

```yaml
---
name: skill-name
description: What the skill does
user-invocable: true|false
---
```

Synced to manifest: `description`, `category`
Not synced (used by Claude Code runtime): `user-invocable`, `name`

### Agents (.claude/agents/*.md)

```yaml
---
name: agent-name
description: What the agent does
model: opus|sonnet
---
```

Synced to manifest: `description`, `depends_on_skills`
Not synced (used by Claude Code runtime): `model`, `name`

### Commands (.claude/commands/*.md)

```yaml
---
name: command-name
description: What the command does
depends_on_agents: [agent1, agent2]
depends_on_skills: [skill1, skill2]
---
```

Synced to manifest: `description`, `depends_on_agents`, `depends_on_skills`
Not synced: `name` (defaults to filename)

## Script Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without writing files |
| `--check` | Exit with error code if files need updating |
| `--verbose` | Show detailed output |

## Manual Sync Steps

If you prefer to sync manually:

1. **Scan for new skills**: `ls .claude/skills/*/SKILL.md`
2. **Scan for new agents**: `ls .claude/agents/*.md`
3. **Scan for new commands**: `ls .claude/commands/*.md`
4. **Update manifest.json**: Add/remove entries
5. **Update CLAUDE.md sections**: Commands, Agents, Context Bundles, Skills
6. **Regenerate bundles**: `uv run python .claude/scripts/generate_bundles.py`

## Post-Sync Checklist

- [ ] manifest.json has all skills, agents, commands
- [ ] CLAUDE.md Commands table matches `.claude/commands/`
- [ ] CLAUDE.md Agents table matches `.claude/agents/`
- [ ] CLAUDE.md Context Bundles table lists all agents
- [ ] CLAUDE.md Skills categories list all skills
- [ ] Bundles regenerated if skill content changed

---

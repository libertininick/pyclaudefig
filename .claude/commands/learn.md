---
name: learn
version: 1.0.0
description: Learn from feedback and iteratively improve Claude Code configuration
depends_on_agents:
  - config-learner
depends_on_skills:
  - validate-manifest
---

# Learn from Feedback

Learn from feedback and improve configuration: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command invokes the **config-learner** agent to analyze your feedback about Claude's behavior and iteratively improve the `.claude/` configuration. Changes may include updating skills, modifying agent instructions, adjusting CLAUDE.md rules, or creating new skills/agents.

The workflow:
1. **Analyze feedback** -- Understand what went wrong or what needs improvement
2. **Inspect configuration** -- Read relevant skills, agents, commands, and CLAUDE.md
3. **Detect contradictions** -- Check for conflicts with existing rules
4. **Propose changes** -- Present a structured change proposal with rationale
5. **Get approval** -- Wait for your confirmation before applying
6. **Apply and sync** -- Make changes, sync manifest, regenerate bundles, validate

## Usage

```
/learn <feedback>
/learn <feedback> --no-session
```

## Flags

| Flag | Description |
|------|-------------|
| `--no-session` | Exclude current conversation context; work from feedback text alone |

## Examples

### Corrective Feedback
```
/learn You kept forgetting to use run-python-safely when executing generated Python. Update the config so this happens proactively.
/learn You used Optional[str] instead of str | None in several places. Make sure the modern union syntax is enforced.
```

### Pattern Feedback
```
/learn You over-engineered the parser feature. On first pass, produce focused minimal implementations.
/learn You created too many small files. Prefer fewer, cohesive modules unless there is a clear separation reason.
```

### Narrow Feedback (no session context)
```
/learn Always run tests before claiming a task is done. --no-session
/learn Use str | None instead of Optional[str] everywhere. --no-session
```

### New Capability
```
/learn I want you to learn how to write database migration scripts following our team's conventions.
/learn Learn how to generate API client code from OpenAPI specs.
```

## Important Notes

- All changes are proposed and require your approval before applying
- The agent will never delete configuration without explicit confirmation
- Changes are validated (manifest, sync, bundles) before the command completes
- By default, the current conversation is included as context; use `--no-session` for narrow, context-free learnings
- Run `/sync` after if you want to double-check everything is in sync

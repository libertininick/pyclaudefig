---
name: implement
description: Execute plan phases using specialized agents
depends_on_agents:
  - python-code-writer
  - python-test-writer
  - code-cleaner
---

# Implement Plan

Implement one or more phases of plan: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command orchestrates implementation of phases from an approved plan document by dispatching work to specialized agents.

## Usage

```
/implement Phase <N> from <plan-path>              # Single phase (includes cleaning)
/implement Phase <N> from <plan-path> --no-clean   # Skip code cleaning
/implement Phase <N1>, <N2>, and <N3> from <plan-path>  # Multiple phases
/implement <plan-path>                             # Entire plan
```

### Flags

- `--no-clean`: Skip the code cleaning step (cleaning runs by default)

## Examples:
```
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --no-clean
/implement Phase 3 and 4 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/implement .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
```

## Prerequisites

1. Create a plan first using `/plan <feature-description>`
2. Have the plan approved and saved to `.claude/agent-outputs/plans/<YYYY-MM-DDTHHmmssZ>-<scope>-plan.md`

## Execution Flow

For each specified phase:

1. **Parse the Plan**
   - Read the plan document
   - Extract requirements for the specified phase(s)
   - Identify files to create/modify

2. **Implement Source Code**
   - Dispatch to `python-code-writer` agent
   - Agent applies relevant development convention skills (`frameworks`, `class-design`, `function-design`, `naming-conventions`, etc.)
   - Agent checks that docstrings, type hints, and coding conventions are properly followed

3. **Implement Tests**
   - Dispatch to `python-test-writer` agent
   - Agent applies `testing` skill for test conventions
   - Agent checks that docstrings, type hints, and testing conventions are properly followed

4. **Validate**
   - Run the `validate-code` skill: `uv run python .claude/scripts/validate_code.py`
   - All checks must pass before proceeding

5. **Clean Code (default, skip with --no-clean)**
   - Dispatch to `code-cleaner` agent
   - Agent cleans all files created or modified across all implemented phases
   - Validates changes pass quality checks
   - Reports summary of cleaning operations
   - Skip this step if `--no-clean` flag is provided

## After Implementation

- **Code Review**: Run `/review --staged --plan <plan-path> --phase <N>`
- **Next Phase**: Run `/implement Phase <N+1> from <same-plan>`
- **Integration**: Verify the implementation integrates with existing code

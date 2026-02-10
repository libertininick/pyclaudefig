---
name: pr-description
version: 1.0.0
description: Generate PR description from branch changes
depends_on_skills:
  - pr-description-template
  - write-markdown-output
---

# Generate PR Description

Generate a pull request description from current branch changes: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## Template Reference

**IMPORTANT**: Before generating, load the PR description template skill for format and examples:
- Use `/pr-description-template format` to see the required format
- Use `/pr-description-template feature|bugfix|refactor` for examples based on change type

## Usage

```
/pr-description
/pr-description --plan <plan-path>
/pr-description --plan <plan-path> --phases <N1,N2,...>
```

## Examples:
```
/pr-description
/pr-description --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/pr-description --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --phases 1,2
```

## Execution Flow

### 1. Load Template

Read the PR description template skill to understand the required format:
- `.claude/skills/pr-description-template/SKILL.md` - Format specification and guidelines

### 2. Gather Branch Information

```bash
# Get current branch name
git branch --show-current

# Get all commits on this branch not in main
git log main..HEAD --oneline

# Get full diff against main
git diff main...HEAD

# Get list of changed files
git diff main...HEAD --name-status
```

### 3. Analyze Changes

For each changed file:
- Categorize by type (source code, tests, documentation, configuration)
- Identify semantic changes (new features, refactors, bug fixes)
- Note any files that touch critical areas
- Determine which template type best fits (feature, bugfix, or refactor)

### 4. Extract Plan Context (if provided)

If `--plan` is specified:
- Read the plan document
- Extract the Summary and goals
- Identify design decisions documented in the plan
- Determine which phases were implemented (from `--phases` or by analyzing completed work)
- Identify remaining phases for "Future Phases" section

### 5. Check Development Conventions

Apply relevant development convention skills to review changes:
- Note any intentional deviations that should be documented
- These MUST be called out in "Key Design Decisions"

### 6. Generate PR Description

Generate the PR description following the format from the template skill. Reference the appropriate example:
- `.claude/skills/pr-description-template/example-feature.md` - For new features
- `.claude/skills/pr-description-template/example-bugfix.md` - For bug fixes
- `.claude/skills/pr-description-template/example-refactor.md` - For refactoring

### 7. Write Output

Use the `write-markdown-output` skill to write the PR description:

```bash
# Step 1: Use Write tool to save PR description content to /tmp/output-content.md
# Step 2: Invoke script with -f
uv run python .claude/scripts/write_markdown_output.py \
    -s "<branch-name>-pr" \
    -f /tmp/output-content.md \
    -o ".claude/agent-outputs/pr-descriptions"
```

## Output

The PR description is written using the `write-markdown-output` skill to:
```
.claude/agent-outputs/pr-descriptions/<timestamp>-<branch-name>-pr.md
```

The description is also displayed in the terminal for easy copying.

## When to Use This Command

- **Before creating a PR** - Generate description after all changes are committed
- **After completing implementation** - Summarize what was built
- **For documentation** - Create a record of changes and decisions

## Tips

- Run `/review --staged` or `/review --commits main..HEAD` before this command to ensure code quality
- Provide the plan path for richer context in the description
- Review the generated description and adjust as needed before creating the PR

---

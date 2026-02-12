---
name: update-plan
description: Sync plan with main and update completed phases
depends_on_skills:
  - plan-template
---

# Update Plan

Update an existing implementation plan: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command updates an existing plan document after syncing with `main` to ensure the plan remains accurate and actionable.

The update process will:
1. **Sync with main** - Pull latest changes from main branch and merge into current branch
2. **Analyze changes** - Review the diff to understand what changed in main
3. **Review implemented phases** - Check which phases/steps have already been completed
4. **Update the plan** - Modify the plan document to reflect current state

## Usage

```
/update-plan <plan-path>
/update-plan <plan-path> --completed-phases <N1,N2,...>
```

## Examples:
```
/update-plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/update-plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --completed-phases 1,2
```

## Versioning Behavior

**The original plan file is NEVER modified.** Instead, a new versioned copy is created with all updates applied.

### Naming Convention

The new file is named by appending `-version-N` before the `.md` extension:

- **First update**: `original-plan.md` → `original-plan-version-2.md`
- **Subsequent updates**: If the input is already a versioned file (e.g., `original-plan-version-2.md`), increment the version: `original-plan-version-3.md`

### Detection Logic

1. Check if the filename matches the pattern `*-version-N.md` (where N is a number)
2. If yes: strip `-version-N.md`, increment N, and create `-version-(N+1).md`
3. If no: append `-version-2.md` (the original is implicitly version 1)

### Example:

| Input file | Output file |
|------------|-------------|
| `api-refactor-plan.md` | `api-refactor-plan-version-2.md` |
| `api-refactor-plan-version-2.md` | `api-refactor-plan-version-3.md` |
| `api-refactor-plan-version-5.md` | `api-refactor-plan-version-6.md` |

## Prerequisites

1. An existing plan document created via `/plan`
2. A feature branch with work in progress
3. Changes committed (no uncommitted changes that would conflict with merge)

## Execution Flow

### 1. Sync with Main Branch

```bash
git fetch origin main
git merge origin/main
```

If merge conflicts occur, stop and ask for guidance.

### 2. Analyze Main Branch Changes

- Get the diff between the plan's base point and current main
- Identify files mentioned in the plan that have changed
- Categorize changes by impact:
  - **Breaking changes** - APIs or interfaces that affect the plan
  - **Helpful additions** - New code that the plan can leverage
  - **Neutral changes** - No impact on the plan

### 3. Review Implemented Work

Check which phases are complete by:
- Reading the commit history on the feature branch
- Comparing implementation against plan requirements
- Verifying tests exist for implemented phases
- Checking validation criteria from the plan

### 4. Create Versioned Plan Copy

**Do NOT modify the original plan file.** Instead:

1. Determine the output filename using the versioning logic described above
2. Copy the original plan file contents into the new versioned file
3. Apply all updates to the **new file only**

Updates to apply in the new file:
- Mark completed phases as `[COMPLETED]`
- Update file paths if they've changed
- Adjust implementation steps based on main changes
- Add notes about what changed and why
- Remove or modify steps that are no longer needed
- Add new steps if main changes require additional work

## Plan Update Format

The updated plan will include:

```markdown
## Update History

### Update - YYYY-MM-DD
**Merged from main:** <commit-range>
**Completed phases:** 1, 2

#### Changes from Main
- [File/Feature]: Description of change and impact on plan

#### Plan Adjustments
- Phase 3: Updated step 2 to use new API from main
- Phase 4: Removed step 3 (already implemented in main)
```

## Output

- A **new versioned plan file** is created with all updates applied
- The **original plan file remains untouched**
- An "Update History" section is added/appended in the new file
- Completed phases are clearly marked in the new file
- The output message includes the path to the new versioned file

## When to Use This Command

- **After implementing a phase** - Sync with main before starting the next phase
- **Before starting new work** - Ensure plan reflects latest main
- **After extended breaks** - Catch up with changes made to main
- **Periodically during long implementations** - Keep plan current

## Important Notes

- **The original plan file is NEVER modified** - all updates go into a new versioned copy
- **Always commit your work** before running this command
- **Review the merge carefully** if conflicts occur
- The planner agent **does NOT write implementation code** during updates
- If main changes significantly affect the plan, consider creating a new plan

---

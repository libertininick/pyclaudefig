# Reviewer-Friendly PRs with Claude Code

This guide shows how to use this repository's Claude Code configuration to create PRs that are easy for human reviewers to evaluate. AI agents can generate substantial code quickly—your responsibility is to curate, validate, and present that work in a way that respects reviewers' time.

## The Core Problem

A coding agent can produce in minutes what takes a human reviewer hours to properly evaluate. Submitting agent output without curation transfers your time savings directly onto reviewers as a burden, degrading code quality when they inevitably start skimming.

## Principles

**You are the author, not the agent.** When you submit a PR, you own it. "The agent wrote it" is not a defense.

**Reviewers' time is more scarce than yours.** A 30-minute effort organizing your PR saves hours of reviewer confusion.

**Guide attention to what matters.** Help reviewers focus on decisions that need human judgment.

---

## The Recommended Workflow

This configuration provides a structured workflow that produces reviewer-friendly PRs by design:

```
/plan → /implement → /review → /pr-description → Human Review
```

### 1. Plan First (`/plan`)

Start every non-trivial change with a plan:

```
/plan Add batch processing for the data pipeline
```

The `planner` agent will:
- Clarify requirements and ask questions
- Explore existing patterns in the codebase
- Break work into phases with specific steps
- Write a plan document to `.claude/agent-outputs/plans/`

**Why this helps reviewers:** The plan becomes documentation of intent. Reviewers can compare implementation against the plan to understand design decisions.

### 2. Implement by Phase (`/implement`)

Execute the plan phase by phase:

```
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
```

The `python-code-writer` and `python-test-writer` agents implement each phase, followed by automatic code cleaning.

**Why this helps reviewers:** Phased implementation keeps PRs focused. Each phase is a logical unit reviewers can evaluate independently.

### 3. Review Before Submitting (`/review`)

Run the two-phase review before requesting human review:

```
/review --staged --plan <plan-path> --phase 2
```

This invokes:
- `code-style-reviewer` - Conventions, naming, type hints, organization
- `code-substance-reviewer` - Correctness, edge cases, design quality
- `test-reviewer` - Reviews test suites for quality, coverage completeness, organization

The review is written to `.claude/agent-outputs/reviews/`.

**Why this helps reviewers:** You catch issues before they do. Address Critical and Improvement findings; Nitpicks are optional.

### 4. Generate the PR Description (`/pr-description`)

Generate a structured PR description from your changes:

```
/pr-description --plan <plan-path> --phases 1,2
```

This creates a description following the repository's standard format, written to `.claude/agent-outputs/pr-descriptions/`.

**Why this helps reviewers:** Consistent structure, organized file lists, and explicitly flagged review areas.

---

## PR Description Format

The `/pr-description` command uses the `pr-description-template` skill to generate descriptions with this structure:

### Required Sections

| Section | Purpose |
|---------|---------|
| **Summary** | What changed and why (2-4 sentences) |
| **What's Included** | Files organized by category (Source, Tests, Docs, Config) |
| **Key Design Decisions** | Numbered decisions with rationale—easy to reference in comments |
| **Critical Areas for Review** | Prioritized areas with line numbers and reasoning |

### Optional Sections

| Section | When to Include |
|---------|-----------------|
| **Future Phases** | When PR is partial implementation of a larger plan |
| **Breaking Changes** | When there are breaking changes requiring migration |
| **Testing Notes** | When testing requires special setup |

### Template Examples

View examples for your change type:

```
/pr-description-template feature    # New functionality
/pr-description-template bugfix     # Bug fixes
/pr-description-template refactor   # Code restructuring
/pr-description-template format     # See the full format spec
```

---

## Before Requesting Human Review

### Validate Agent Output

Run all validation checks with a single command:

```bash
uv run .claude/scripts/validate_code.py
```

### Self-Review Checklist

```
[ ] I've reviewed every line of the diff myself
[ ] I can explain and defend each design decision
[ ] /review findings have been addressed (Critical + Improvements)
[ ] Tests pass locally
[ ] PR description follows the template (use /pr-description)
[ ] Critical areas for review are flagged with line numbers
[ ] If PR is large, I've split into phases or provided reading order
```

### Questions to Answer

Before requesting review, ensure you can answer:

- Do I understand every change and why it was made?
- Could I defend each design decision if questioned?
- Which areas am I uncertain about and need extra scrutiny?

---

## Structuring Large Changes

### One Logical Change Per PR

If the implementation plan has multiple phases, consider separate PRs:

```
PR 1: Phase 1 - Add BatchProcessor class
PR 2: Phase 2 - Integrate with existing pipeline
PR 3: Phase 3 - Add retry logic
```

### Use Plan References

When your PR implements part of a larger plan, include the plan path:

```
/pr-description --plan <plan-path> --phases 1,2
```

The generated description will include a "Future Phases" section documenting what's coming.

### Categorize by Review Priority

The `pr-description-template` structures this for you, but ensure you're specific:

**Critical Areas for Review** (need careful attention):
```markdown
1. **`src/pipeline/batch_processor.py:L45-L78`** - Core batch chunking logic. Verify boundary conditions for partial batches.
2. **`src/pipeline/retry.py:L20-L35`** - Exception classification. Wrong classification could cause infinite retries.
```

**What's Included** (provides context but may not need deep review):
```markdown
**Tests:**
- `tests/pipeline/test_batch_processor.py` - Unit tests for BatchProcessor
```

---

## What Not to Do

**Don't dump raw agent output.** Use `/pr-description` to structure your changes.

**Don't skip `/review`.** Catching issues before human review shows respect for reviewers' time.

**Don't submit changes you don't understand.** If the agent produced code you can't explain, either learn it or don't submit it.

**Don't use volume as a bludgeon.** If the PR is too big to review, split it into phases.

**Don't ignore plan phases.** If you deviate from the plan, document why in Key Design Decisions.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/plan <description>` | Create implementation plan |
| `/implement Phase N from <plan>` | Implement specific phase |
| `/review --staged` | Review staged changes before commit |
| `/review --commits main..HEAD` | Review all commits on branch |
| `/pr-description` | Generate PR description from changes |
| `/pr-description --plan <path>` | Include plan context in description |

| Skill | Purpose |
|-------|---------|
| `/pr-description-template feature` | Example for new features |
| `/pr-description-template bugfix` | Example for bug fixes |
| `/pr-description-template refactor` | Example for refactoring |
| `/pr-description-template format` | Full format specification |

---

## Remember

Your reviewers are your teammates, not your rubber stamps. The workflow in this configuration—plan, implement, review, describe—produces PRs that respect reviewers' time by default. Use it.

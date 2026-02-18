---
name: review
description: Unified code review for source and test files
depends_on_agents:
  - code-style-reviewer
  - code-substance-reviewer
  - test-reviewer
depends_on_skills:
  - review-template
  - write-markdown-output
---

# Code Review

Conduct a code review: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## Review Process

This command orchestrates a comprehensive review using specialized agents, then aggregates results into a unified report.

### Phase 1: Resolve and Classify Files

Determine which files to review based on arguments, then classify them:

**Test files** match any of:
- Filename starts with `test_` (e.g., `test_parser.py`)
- Filename ends with `_test.py` (e.g., `parser_test.py`)
- Located in `tests/` directory

**Source files** are all other `.py` files.

### Phase 2: Run Tests (if test files in scope)

If test files are being reviewed, execute `uv run pytest <test-files> -v` to verify tests pass before reviewing. For full validation, use `uv run .claude/scripts/validate_code.py`.

### Phase 3: Launch Reviews (parallel)

Launch the applicable review agents **in parallel** using multiple `Task` tool calls in a single message. The reviewers have strictly disjoint scopes and produce independent analysis, so parallel execution is safe and significantly faster.

**Always launch (on all files in scope):**
- `code-style-reviewer` — with all files + plan context (if `--plan` provided)
- `code-substance-reviewer` — with all files + plan context (if `--plan` provided)

**Conditionally launch (if test files in scope):**
- `test-reviewer` — with only the test files + test execution results from Phase 2

Wait for **all** launched agents to complete before proceeding to Phase 4.

### Phase 4: Aggregate and Write Report

After all reviews complete:

1. **Collect findings** from all reviewers that ran
2. **Identify overlapping concerns** - issues flagged by multiple reviewers indicate higher priority
3. **Determine verdict**:
   - APPROVE: No critical issues from any reviewer
   - NEEDS CHANGES: Critical issues found OR many significant improvements needed
   - REJECT: Fundamental design problems requiring rearchitecture
4. **Invoke `review-template` skill** for output format
5. **Use `write-markdown-output` skill** to write the unified report:

```bash
uv run .claude/scripts/write_markdown_output.py -s "<scope>-review" -o ".claude/agent-outputs/reviews" <<'CONTENT_EOF'
<aggregated review content here>
CONTENT_EOF
```

**IMPORTANT**: Launch all applicable reviewers in parallel (multiple Task calls in a single message). They have disjoint scopes.

## Filtering Flags

| Flag | Files Reviewed | Reviewers Used |
|------|----------------|----------------|
| *(default)* | All files (auto-classified) | Style + Substance on all; Test-reviewer on test files |
| `--src-only` | Source files only | Style + Substance |
| `--tests-only` | Test files only | Style + Substance + Test-reviewer |

When `--src-only` is specified, test files are excluded even if explicitly listed.
When `--tests-only` is specified, source files are excluded even if explicitly listed.

## Specialized Reviewers

| Reviewer | Model | Focus | Runs On |
|----------|-------|-------|---------|
| **code-style-reviewer** | Sonnet | Conventions, naming, docstrings, type hints, imports, organization, Pythonic patterns | All files |
| **code-substance-reviewer** | Opus | Correctness, edge cases, error handling, design quality, maintainability, testability | All files |
| **test-reviewer** | Sonnet | Substantive assertions, test organization, edge case coverage, fixture usage, mock discipline | Test files only |

## Usage

### Review Specific Files
```
/review <file1> [file2] [file3]...
```

**Examples:**
```
/review src/my_library/tools/parser.py
/review src/my_library/tools/parser.py tests/tools/test_parser.py
/review tests/tools/test_parser.py
```

### Review with Filtering
```
/review <target> --src-only
/review <target> --tests-only
```

**Examples:**
```
/review --staged --src-only         # Only source files from staged changes
/review --staged --tests-only       # Only test files from staged changes
/review src/ tests/ --src-only      # Only source files even though tests/ specified
```

### Review a Commit
```
/review --commit <hash>
```

Reviews all files changed in the specified commit.

**Examples:**
```
/review --commit abc123f
/review --commit HEAD
/review --commit HEAD --tests-only
```

### Review a Commit Range
```
/review --commits <base>..<head>
```

Reviews all files changed between two commits.

**Examples:**
```
/review --commits main..HEAD
/review --commits abc123f..def456a
/review --commits main..HEAD --src-only
```

### Review Staged Changes
```
/review --staged
```

Reviews all currently staged files (useful before committing).

### Review Unstaged Changes
```
/review --unstaged
```

Reviews all files with unstaged modifications.

## Adding Plan Context (Optional)

Add implementation context from a plan document:

```
/review <target> --plan <plan-path> [--phase <N>]
```

When provided, the reviewers will:
- Understand the **intended design** from the plan
- Verify the implementation **matches the plan's requirements**
- Check that **acceptance criteria** are addressed

**Examples:**
```
/review --staged --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --phase 2
/review src/foo.py --plan .claude/agent-outputs/plans/2024-01-22T143052Z-new-feature-plan.md
```

## What Gets Reviewed

### Style Review (code-style-reviewer) - All Files

Rule-based checks using convention skills:

| Skill | What's Checked |
|-------|----------------|
| `naming-conventions` | Variables, functions, classes, modules |
| `docstring-conventions` | Presence, format, completeness |
| `type-hints` | Coverage and correctness |
| `code-organization` | Imports, module structure, file layout |
| `pythonic-conventions` | Comprehensions, built-ins, context managers |
| `function-design` | Signatures, parameters, return types |
| `class-design` | Interfaces, attributes, method organization |

### Substance Review (code-substance-reviewer) - All Files

Design and correctness analysis using:

| Skill | What's Checked |
|-------|----------------|
| `class-design` | Coupling, cohesion, composition, inheritance |
| `function-design` | Responsibility, complexity, parameters |
| `maintainability` | Readability, change tolerance, hidden assumptions |
| `testability` | Dependency injection, global state, pure functions |

Plus correctness analysis: requirements match, logic correctness, edge cases, error handling

### Test Quality Review (test-reviewer) - Test Files Only

Test-specific analysis using:

| Category | What's Checked |
|----------|----------------|
| Substantive assertions | Tests prove something meaningful, not rubber stamps |
| True functionality | Tests verify behavior, not implementation details |
| Test organization | Tests mirror source structure, cohesive groupings |
| Edge case coverage | Error paths and boundary conditions tested |
| Test data variety | Realistic, varied data; parametrization used appropriately |
| Fixture usage | Fixtures reduce duplication without tight coupling |
| Mock discipline | Mocks used only when necessary |

## Output

Review documents are written using the `write-markdown-output` skill to:
```
.claude/agent-outputs/reviews/<timestamp>-<scope>-review.md
```

Where `<scope>` is derived from:
  - File name (single file): `2024-01-22T143052Z-parser-review.md`
  - Directory/module (multiple files): `2024-01-22T143052Z-tools-review.md`
  - Plan phase: `2024-01-22T143052Z-phase-2-api-refactor-review.md`
  - Commit: `2024-01-22T143052Z-commit-abc123f-review.md`
  - Staged changes: `2024-01-22T143052Z-staged-review.md`

### Report Structure

The merged report contains:

1. **Summary** - Scope, verdict, key finding, reviewers used
2. **Critical Issues** - Must fix before merge (from any reviewer)
3. **Improvements** - Should address, grouped by category
4. **Nitpicks** - Minor items, one line each
5. **Overlapping Concerns** - Issues flagged by multiple reviewers (elevated priority)

Empty sections are omitted. Use `review-template` skill for exact format.

## Scope Determination

Derive `<scope>` for output filename from:

| Review Target | Scope |
|---------------|-------|
| Single file `foo.py` | `foo` |
| Single test file `test_foo.py` | `test-foo` |
| Multiple files in `tools/` | `tools` |
| Commit `abc123f` | `commit-abc123f` |
| Staged changes | `staged` |
| Plan phase 2 | `phase-2-<plan-name>` |

## When to Use This Command

- **After implementing a feature** - Verify quality before committing
- **After refactoring** - Ensure changes maintain code quality
- **Before a PR** - Get comprehensive feedback on all changes
- **After `/implement`** - Review the implemented phase
- **After writing tests** - Verify tests are substantive

## Important Notes

- The reviewers **do NOT modify any code** - they only generate review documents
- Reviews run in parallel (style + substance + test quality) since scopes are disjoint
- Overlapping findings from multiple reviewers indicate higher priority issues
- Tests are automatically run before test quality review
- For test writing based on review findings, use `python-test-writer` agent
- For implementing review suggestions, use `python-code-writer` agent

---

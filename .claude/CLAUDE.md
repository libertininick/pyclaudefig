# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Quick Reference

| Task | Command |
|------|---------|
| Install/sync dependencies | `uv sync` |
| **Validate all** | **`uv run .claude/scripts/validate_code.py`** |
| Validate (selective) | `uv run .claude/scripts/validate_code.py --lint --type` |
| Format code | `uv run ruff format` |
| Lint code | `uv run ruff check` |
| Docstring check | `uv tool run pydoclint --style=google --allow-init-docstring=True` |
| Type check | `uv run ty check` |
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov` |

## Critical Rules

1. **Approved frameworks only** - Use `frameworks` skill; never substitute alternatives
2. **Load convention skills before editing code** - Before writing, moving, or restructuring Python code, read the relevant skill files from `.claude/skills/`:
   - Moving/reorganizing code → `code-organization/SKILL.md`
   - Writing/modifying functions → `function-design/SKILL.md`
   - Writing/modifying classes → `class-design/SKILL.md`, `class-design/rules.md`
   - Naming anything → `naming-conventions/SKILL.md`
   - Refactoring complex code → `complexity-refactoring/SKILL.md`
3. **Fetch docs when uncertain** - Use `fetch-docs` skill (see `frameworks` skill for doc IDs)
4. **Safe Python execution (MANDATORY -- NO EXCEPTIONS)** - When ANY agent generates Python code and wants to run it, it MUST use `run-python-safely` as the FIRST attempt. Do NOT ask the user for permission -- just run it through the skill automatically. Only if `run-python-safely` blocks or fails should the agent ask the user to run the code manually. Exceptions (standard CLI tools that skip this skill): `uv run pytest`, `ruff`, `ty check`, `uv run .claude/scripts/validate_code.py`, other repository scripts.
5. **Mandatory task delegation** - See Task Delegation section below; NEVER skip
6. **Never hallucinate** - Ask if uncertain about paths, modules, or APIs
7. **Never delete code** unless explicitly instructed
8. **Never commit** unless explicitly instructed
9. **Google-style docstrings only** - NEVER use RST or Sphinx-style docstrings (`:param:`, `:returns:`, `:rtype:`, etc.). Always follow `docstring-conventions` skill. Zero exceptions.

---

## Task Delegation (MANDATORY)

> **REQUIREMENT**: You MUST delegate tasks to specialized agents whenever a matching agent exists.
> If no agent matches, you MUST load the appropriate compact context bundles before proceeding.
> NEVER attempt a task directly without either delegating or loading bundles first.

### Delegation Routing Table

Evaluate every user request against this table. Use the **first matching row**.

| User Request | Delegate To | Notes |
|-------------|-------------|-------|
| Write, implement, or modify Python code | `python-code-writer` | Includes new functions, classes, modules, bug fixes, feature additions |
| Write or update tests | `python-test-writer` | Includes new test files, adding test cases, fixing failing tests |
| Review code (general) | `code-style-reviewer` + `code-substance-reviewer` | Launch both in parallel; use `/review` command when available |
| Review tests | `test-reviewer` | May combine with code reviewers if reviewing both source and tests |
| Clean, refactor, or organize code | `code-cleaner` | Includes import cleanup, complexity reduction, docstring fixes |
| Brainstorm or explore ideas before planning | `brainstormer` | Use as precursor to `/plan`; interviews user to discover true scope |
| Create an implementation plan | `planner` | For new features, refactors, or architectural changes |
| Improve Claude Code configuration | `config-learner` | For feedback, skill updates, CLAUDE.md changes |

### When No Agent Matches

If the request does not clearly map to an agent above, the main agent MUST:

1. **Identify relevant skills** from the Skills section below
2. **Load compact context bundles** for those skills by reading the corresponding files from `.claude/bundles/`:
   - Python coding tasks → `bundles/python-code-writer-compact.md`
   - Code quality/style questions → `bundles/code-style-reviewer-compact.md`
   - Design/architecture questions → `bundles/code-substance-reviewer-compact.md`
   - Test-related questions → `bundles/test-reviewer-compact.md` or `bundles/python-test-writer-compact.md`
   - Planning/scoping questions → `bundles/planner-compact.md`
   - Configuration/skills questions → `bundles/config-learner-compact.md`
3. **Then proceed** with the task using the loaded context

### Examples

```
# CORRECT - delegate to subagent
User: "Add a retry mechanism to the API client"
Action: Delegate to python-code-writer

# CORRECT - delegate to multiple subagents
User: "Review this PR"
Action: Delegate to code-style-reviewer + code-substance-reviewer + test-reviewer

# CORRECT - no agent match, load bundles first
User: "What naming convention should I use for async functions?"
Action: Load bundles/code-style-reviewer-compact.md, then answer

# INCORRECT - doing work directly without delegating or loading bundles
User: "Write a function to parse CSV files"
Action: Writing code directly without delegating to python-code-writer
```

---

## Commands

Reusable workflows in `.claude/commands/`. See each file for details.

| Command | Purpose |
|---------|---------|
| `/add-framework` | Add a new approved framework |
| `/brainstorm` | Multi-turn brainstorming session before planning |
| `/clean` | Clean Python code files |
| `/create-skill` | Create a new Claude Code skill |
| `/implement` | Execute plan phases |
| `/learn` | Learn from feedback and iteratively improve Claude Code configuration |
| `/plan` | Create implementation plan |
| `/pr-description` | Generate PR description |
| `/review` | Unified code review (source + tests) |
| `/sync` | Sync Claude context files with skills, agents, and commands on disk |
| `/update-plan` | Sync plan with main and create versioned update |


---

## Agents

Specialized sub-agents in `.claude/agents/`. See each file for details.

| Agent | Scope |
|-------|-------|
| `brainstormer` | Interviews user to discover scope and generate ideas before planning |
| `code-cleaner` | Cleans and organizes Python code |
| `code-style-reviewer` | Reviews style and conventions |
| `code-substance-reviewer` | Reviews design and correctness |
| `config-learner` | Analyzes user feedback and iteratively improves Claude Code configuration. Updates skills, agents, commands, and CLAUDE.md based on what went well or poorly. |
| `planner` | Creates implementation plans |
| `python-code-writer` | Writes production code |
| `python-test-writer` | Writes tests |
| `test-reviewer` | Reviews test quality and coverage |


---

## Context Bundles

Pre-composed skill content for agents. Bundles provide exactly the context each agent needs.

| Agent | Full Bundle | Compact Bundle |
|-------|-------------|----------------|
| `code-cleaner` | `bundles/code-cleaner.md` | `bundles/code-cleaner-compact.md` |
| `code-style-reviewer` | `bundles/code-style-reviewer.md` | `bundles/code-style-reviewer-compact.md` |
| `code-substance-reviewer` | `bundles/code-substance-reviewer.md` | `bundles/code-substance-reviewer-compact.md` |
| `config-learner` | `bundles/config-learner.md` | `bundles/config-learner-compact.md` |
| `planner` | `bundles/planner.md` | `bundles/planner-compact.md` |
| `python-code-writer` | `bundles/python-code-writer.md` | `bundles/python-code-writer-compact.md` |
| `python-test-writer` | `bundles/python-test-writer.md` | `bundles/python-test-writer-compact.md` |
| `test-reviewer` | `bundles/test-reviewer.md` | `bundles/test-reviewer-compact.md` |

**Regenerate bundles** after modifying skills:
```bash
uv run .claude/scripts/generate_bundles.py
```


---

## Skills

Skills provide coding standards and conventions. See `.claude/manifest.json` for the complete catalog.

**Categories**:
- **Conventions**: `class-design`, `code-organization`, `complexity-refactoring`, `data-structures`, `docstring-conventions`, `frameworks`, `function-design`, `naming-conventions`, `pythonic-conventions`, `test-writing`, `type-hints`
- **Assessment**: `maintainability`, `test-quality`, `testability`
- **Templates**: `plan-template`, `pr-description-template`, `review-template`, `skill-template`
- **Utilities**: `explore-project`, `fetch-docs`, `run-python-safely`, `validate-code`, `validate-manifest`, `write-markdown-output`

**Note**: Agents should load their context bundles (above) rather than invoking skills individually.


---

## Agent Outputs

Agents write outputs to `.claude/agent-outputs/` using `write-markdown-output` skill:

```
.claude/agent-outputs/
├── brainstorms/     # Brainstorming session takeaways
├── plans/           # Implementation plans
├── reviews/         # Code reviews
└── pr-descriptions/ # PR descriptions
```

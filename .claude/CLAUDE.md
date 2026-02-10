# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Quick Reference

| Task | Command |
|------|---------|
| Install/sync dependencies | `uv sync` |
| **Validate all** | **`uv run python .claude/scripts/validate_code.py`** |
| Validate (selective) | `uv run python .claude/scripts/validate_code.py --lint --type` |
| Format code | `uv run ruff format` |
| Lint code | `uv run ruff check` |
| Docstring check | `uv tool run pydoclint --style=google --allow-init-docstring=True` |
| Type check | `uv run ty check` |
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov` |

## Critical Rules

> **PYTHON EXECUTION**: When running generated Python via Bash, use `run-python-safely` skill first.
> Exceptions: `uv run pytest`, `ruff`, `ty check`, `uv run python .claude/scripts/validate_code.py`, other standard CLI tools.

1. **Approved frameworks only** - Use `frameworks` skill; never substitute alternatives
2. **Apply convention skills** - Skills provide coding standards
3. **Fetch docs when uncertain** - Use Context7 MCP (see `frameworks` skill for IDs)
4. **Use specialized agents** - See Agents section
5. **Never hallucinate** - Ask if uncertain about paths, modules, or APIs
6. **Never delete code** unless explicitly instructed
7. **Never commit** unless explicitly instructed

---

## Commands

Reusable workflows in `.claude/commands/`. See each file for details.

| Command | Purpose |
|---------|---------|
| `/add-framework` | Add a new approved framework |
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
uv run python .claude/scripts/generate_bundles.py
```


---

## Skills

Skills provide coding standards and conventions. See `.claude/manifest.json` for the complete catalog.

**Categories**:
- **Conventions**: `class-design`, `code-organization`, `complexity-refactoring`, `data-structures`, `docstring-conventions`, `frameworks`, `function-design`, `naming-conventions`, `pythonic-conventions`, `test-writing`, `type-hints`
- **Assessment**: `maintainability`, `test-quality`, `testability`
- **Templates**: `plan-template`, `pr-description-template`, `review-template`, `skill-template`
- **Utilities**: `explore-project`, `run-python-safely`, `validate-code`, `validate-manifest`, `write-markdown-output`

**Note**: Agents should load their context bundles (above) rather than invoking skills individually.


---

## Agent Outputs

Agents write outputs to `.claude/agent-outputs/` using `write-markdown-output` skill:

```
.claude/agent-outputs/
├── plans/           # Implementation plans
├── reviews/         # Code reviews
└── pr-descriptions/ # PR descriptions
```

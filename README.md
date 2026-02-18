# pyclaudefig
Stop configuring Claude Code from scratch for every Python project. `pyclaudefig` is a heavily opinionated, ready-to-go configuration designed for teams that have embraced the Astral ecosystem — ruff, uv, and ty — as their standard toolchain.

## Quick Start

### Prerequisites

This configuration assumes you already have:

1. **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** installed and working
2. **[uv](https://docs.astral.sh/uv/)** managing your project virtualenv
3. **Dev tools installed and configured** in your venv:
   - `ruff` (formatting + linting)
   - `ty` (type checking)
   - `pytest` + `pytest-check` + `pytest-cov` (testing + coverage)
   - `pydoclint` (docstring formatting)
   - All tools are runnable via `uv run .claude/scripts/validate_code.py`
4. **[Context7](https://context7.com/sign-up) free account** for fetching up-to-date framework documentation via MCP

### Initial setup

1. **Download [`.claude/`](.claude/)** into your project root

   ```sh
   cd /path/to/your/project

   # Download pyclaudefig
   curl -L https://api.github.com/repos/libertininick/pyclaudefig/tarball/HEAD | tar -xz

   # Move .claude directory to root of project and remove remaining items from download
   mv libertininick-pyclaudefig-*/.claude ./ && rm -rf libertininick-pyclaudefig-*
   ```

2. **Connect the Context7 MCP server** to Claude Code

   ```sh
   # Generate an API key at https://context7.com after signing up
   claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
   ```

   Verify it's connected by running `/mcp` inside a Claude session — you should see `context7 · ✔ connected`.

3. **Start a Claude Code session** in your project's root directory

    ```sh
    cd /path/to/your/project
    claude
    ```

4. **Add approved frameworks** i.e. the python libraries your project depends on (see [Adding a New Framework](#adding-a-new-framework)) 

    ```sh
    /add-framework <python library>
    ```

5. **Run `/sync`** inside your Claude session to generate context bundles for the subagents (they're gitignored):

   ```sh
   /sync
   ```

   Re-run `/sync` any time you make changes to `.claude/`, add a skill/command/agent, or update a setting.

### Sync local config

After initial setup, you may want to sync your local config with changed pushed to `pyclaudefig`. Here's an approach using `rsync`:

   ```sh
   cd /path/to/your/project

   # Download pyclaudefig
   curl -L https://api.github.com/repos/libertininick/pyclaudefig/tarball/HEAD | tar -xz

   # Sync changes
   # NOTE: use --dry-run to look before you leap ;)
   rsync -av \
   --delete \
   --exclude='agent-outputs' \
   --exclude='bundles' \
   --exclude='**/__pycache__' \
   libertininick-pyclaudefig-*/.claude/ \
   .claude/ \
   --dry-run

   # Remove remaining items from download
   rm -rf libertininick-pyclaudefig-*
   ```
### Core Workflow

The core loop is: **plan → implement → review → commit → update plan**, one phase at a time.

Here's what a typical session looks like:

```sh
# 1. Create a plan — the planner agent explores the codebase, asks
#    clarifying questions, and writes a phased implementation plan.
/plan Add retry logic to the API client

#    Output: .claude/agent-outputs/plans/<timestamp>-api-client-plan.md
#    Review the plan and iterate until you're happy with it.

# 2. Implement Phase 1 — code-writer and test-writer agents execute
#    the first phase, then validate with ruff, ty, and pytest.
/implement Phase 1 from .claude/agent-outputs/plans/<timestamp>-api-client-plan.md

# 3. Review Phase 1 — style, substance, and test-quality reviewers
#    run in parallel and produce a unified review report.
/review --staged --plan .claude/agent-outputs/plans/<timestamp>-api-client-plan.md --phase 1

#    Address any findings, then stage your changes.

# 4. Commit — once the review is clean, commit the phase.
git add -p && git commit

# 5. Update the plan — syncs with main, marks Phase 1 complete,
#    and creates a new versioned plan file with adjustments.
#    (The original plan is never modified.)
/update-plan .claude/agent-outputs/plans/<timestamp>-api-client-plan.md --completed-phases 1

# 6. Repeat from step 2 for Phase 2, 3, etc.
```

Every command supports `--help` for usage and examples (e.g., `/review --help`).

## Usage Guides

Deep dives into specific topics. Start here after you're comfortable with the Quick Start workflow.

| Guide | What You'll Learn |
|-------|-------------------|
| **[Understanding LLM Coding Agents](usage-guides/understanding-llm-coding-agents.md)** | Step-by-step guide to how AI coding agents actually work. Pattern matching, tool use, context windows, and agentic loops demystified. |
| **[Agentic Coding Workflow](usage-guides/agentic-coding-workflow.md)** | Complete walkthrough of the plan → implement → review cycle. Commands, agents, validation, troubleshooting. |
| **[Context Window Management](usage-guides/context-window-management.md)** | Why AI performance degrades as context fills up, and how this configuration uses agents and bundles to keep sessions efficient. |
| **[Reviewer-Friendly PRs](usage-guides/reviewer-friendly-prs.md)** | Creating PRs that respect reviewers' time. Validation checklists, description templates, structuring large changes. |
| **[Thinking Tokens & Model Selection](usage-guides/thinking-llms-guide.md)** | How thinking tokens actually work, when extended thinking helps (and when it doesn't), and practical model selection guidance for code generation. |

---

## Architecture Overview

### Design Philosophy

This configuration separates concerns into three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                        COMMANDS                             │
│           Orchestration: workflows that use agents          │
│       /plan  /implement  /review  /pr-description           │
└─────────────────────────┬───────────────────────────────────┘
                          │ invoke
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         AGENTS                              │
│            Execution: specialists that do work              │
│ planner  code-writer  test-writer  test-reviewer  reviewers │
└─────────────────────────┬───────────────────────────────────┘
                          │ load
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         SKILLS                              │
│          Knowledge: conventions, templates, criteria        │
│  class-design  test-writing  frameworks  plan-template  ... │
└─────────────────────────────────────────────────────────────┘
```

**Why this separation matters:**

- **Skills** = Knowledge that multiple agents share (conventions, templates)
- **Agents** = Focused specialists with specific responsibilities
- **Commands** = User-facing workflows that compose agents

### Single Source of Truth

`manifest.json` defines all relationships:

```json
{
  "skills": [{ "name": "class-design", "category": "conventions", ... }],
  "agents": [{ "name": "planner", "depends_on_skills": ["plan-template", ...] }],
  "commands": [{ "name": "plan", "depends_on_agents": ["planner"] }]
}
```

Changes to relationships happen in one place. The manifest drives:
- Bundle generation (what skills each agent receives)
- CLAUDE.md generation (via `/sync`)
- Documentation of dependencies

### Bundle Generation

Agents need skill knowledge, but loading skills individually at runtime is inefficient. Instead:

1. **manifest.json** declares which skills each agent depends on
2. **generate_bundles.py** pre-composes skills into bundles
3. **Agents** load a single bundle file with all their context

```bash
# Regenerate bundles after modifying skills
uv run .claude/scripts/generate_bundles.py
```

Two bundle variants are generated:
- **Full bundle** (`planner.md`): Complete skill content including examples
- **Compact bundle** (`planner-compact.md`): Quick Reference sections only

### Layered Skills

Complex skills split content across files:

```
skills/class-design/
├── SKILL.md      # Main content + Quick Reference table
├── rules.md      # Decision flow and rules
└── examples.md   # Code examples
```

The frontmatter in `SKILL.md` declares layers:

```yaml
---
name: class-design
layers:
  rules: rules.md
  examples: examples.md
---
```

Bundles include all layers. Compact bundles include only Quick Reference.

### Git-Ignored Outputs

Two directories regenerate as needed:

```
.claude/
├── bundles/         # Generated by generate_bundles.py
└── agent-outputs/   # Written by agents at runtime
    ├── plans/
    ├── reviews/
    └── pr-descriptions/
```

Both are `.gitignore`d. Regenerate bundles after skill changes. Agent outputs are timestamped for history.

---

## Directory Structure

```
.claude/
├── CLAUDE.md              # Root agent instructions (auto-generated by /sync)
├── settings.json          # Project specific Claude settings
│
├── commands/              # User-invocable workflows
│   ├── plan.md
│   ├── implement.md
│   ├── review.md
│   └── ...
│
├── agents/                # Execution specialists
│   ├── planner.md
│   ├── python-code-writer.md
│   └── ...
│
├── manifest.json          # Single source of truth
│
├── skills/                # Knowledge & conventions
│   ├── class-design/
│   │   ├── SKILL.md
│   │   ├── rules.md
│   │   └── examples.md
│   ├── test-writing/
│   │   └── SKILL.md
│   └── ...
│
├── bundles/               # Pre-composed context (generated, gitignored)
│   ├── planner.md
│   ├── planner-compact.md
│   └── ...
│
├── agent-outputs/         # Agent work products (generated, gitignored)
│   ├── plans/
│   ├── reviews/
│   └── pr-descriptions/
│
└── scripts/               # Automation
    ├── generate_bundles.py
    └── sync_context.py
```

---

## Customization Guide

### Adding a New Framework

Use the `/add-framework` command to register a new approved library:

```sh
/add-framework httpx
```

This will:
1. Resolve the doc ID (for documentation lookup)
2. Find the official documentation URL
3. Confirm the details with you
4. Update `skills/frameworks/SKILL.md` with the new entry
5. Regenerate bundles and validate the manifest

Run `/add-framework --help` for more examples.

### Adding a New Skill

1. **Create the skill directory and files:**
   ```bash
   /create-skill
   # Follow prompts for name, category, description
   ```

2. **Edit the generated SKILL.md** with your conventions

3. **Add to manifest.json** (if not auto-added):
   ```json
   {
     "name": "your-skill",
     "category": "conventions",
     "description": "What this skill provides"
   }
   ```

4. **Add to agent dependencies** in manifest.json:
   ```json
   {
     "name": "python-code-writer",
     "depends_on_skills": ["your-skill", ...]
   }
   ```

5. **Regenerate bundles:**
   ```bash
   uv run .claude/scripts/generate_bundles.py
   ```

6. **Update CLAUDE.md:**
   ```bash
   /sync
   ```

### Adding a New Agent

1. **Create agent file** in `agents/`:
   ```yaml
   ---
   name: your-agent
   description: What this agent does
   model: sonnet  # or opus
   bundle: bundles/your-agent.md
   tools:
     - Read
     - Write
     - Edit
   ---

   Instructions for the agent...
   ```

2. **Add to manifest.json:**
   ```json
   {
     "name": "your-agent",
     "description": "What this agent does",
     "depends_on_skills": ["skill1", "skill2"]
   }
   ```

3. **Generate bundles with sync:**
   ```bash
   /sync
   ```

### Adding a New Command

1. **Create command file** in `commands/`:
   ```yaml
   ---
   name: your-command
   description: What this command does
   depends_on_agents:
     - agent-it-uses
   ---

   # Command Title

   Instructions for what this command does...
   ```

2. **Add to manifest.json:**
   ```json
   {
     "name": "your-command",
     "description": "What this command does",
     "depends_on_agents": ["agent-it-uses"]
   }
   ```

3. **Sync context:**
   ```bash
   /sync
   ```

### Teaching Claude from Feedback

Use `/learn` to turn mistakes (or good patterns) into permanent configuration changes:

```sh
/learn You kept using Optional[str] instead of str | None. Enforce the modern union syntax.
/learn Always run tests before claiming a task is done. --no-session
```

The `config-learner` agent analyzes your feedback, proposes targeted changes to skills, CLAUDE.md, or agent instructions, and applies them after your approval. See [Learning from Mistakes](usage-guides/agentic-coding-workflow.md#learning-from-mistakes-with-learn) for the full guide.

### Modifying Conventions

1. **Edit the skill's SKILL.md** (and rules.md/examples.md if layered)
2. **Regenerate bundles** so agents get updated context
3. **Test** by running a command that uses the affected agents

---

## Skill Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **conventions** | How code should be written | `class-design`, `naming-conventions`, `test-writing` |
| **assessment** | Criteria for code review | `maintainability`, `testability`, `test-quality` |
| **templates** | Output format specifications | `plan-template`, `review-template` |
| **utilities** | Reusable operations | `run-python-safely`, `write-markdown-output` |

---

## Troubleshooting

### Agent doesn't know about a skill
- Check `manifest.json` that the agent's `depends_on_skills` includes the skill
- Regenerate bundles: `uv run .claude/scripts/generate_bundles.py`

### Command not appearing in /help
- Ensure the command file has correct frontmatter
- Run `/sync` to regenerate CLAUDE.md

### Changes to skills not reflected
- Regenerate bundles after any skill modification
- Bundles are gitignored, so they won't auto-update

### CLAUDE.md out of sync
- Run `/sync` to regenerate from current disk state


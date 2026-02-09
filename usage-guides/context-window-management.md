# Context Window Management

## Quick Take

**The core insight:** Your AI assistant's context window is a fixed-size knapsack. Everything it knows about your project must fit inside that knapsack, and the fuller it gets, the worse the AI performs. This isn't gradual degradation; it's a cliff.

**What the research shows:** The 2024 "Lost in the Middle" study found that LLM accuracy drops by 30%+ when relevant information is buried in the middle of long contexts. In some cases, adding more context made models perform *worse* than having no context at all.

**The practical threshold:** Treat 70% context utilization as your ceiling. Beyond 80%, expect forgotten instructions, shorter responses, and degraded reasoning.

**What this configuration provides:**
- **Specialized agents** that run in isolated context windows, keeping your main session clean
- **Context bundles** that give agents pre-composed conventions without per-skill overhead
- **Commands** that orchestrate multi-agent workflows, delegating context-heavy work
- **Skills** that provide conventions on-demand rather than bloating CLAUDE.md

**The bottom line:** Use agents for heavy lifting, commands for workflows, and reserve your main session for orchestration and decision-making.

---

## Why Context Management Matters

When you send a message to Claude Code, you're not sending just that prompt. You're sending the complete conversation: all previous exchanges, system instructions, CLAUDE.md, tool schemas, and your current input. Everything goes into the context window. If it's not there, the AI doesn't know about it.

### The Performance Cliff

AI performance doesn't degrade gradually as context fills up. It falls off a cliff.

| Threshold | What Happens |
|-----------|--------------|
| 0-50% | Full capacity—tackle complex, multi-file work |
| 50-70% | Still effective—good for focused tasks |
| **70%** | **Proactive compaction point**—compact before symptoms appear |
| 80%+ | Degraded mode—shorter responses, forgotten context |
| 90%+ | Critical—auto-compact imminent, start fresh if possible |

Symptoms of context exhaustion:
- Instructions being forgotten or ignored
- Earlier context "bleeding" into unrelated responses
- The AI re-suggesting approaches already tried
- Shorter, less detailed responses

---

## Context Management with Agents

The most powerful tool for context management in this configuration is **agent delegation**. Each agent runs in an isolated context window, performs its work, and returns only the results.

### How Agents Preserve Context

| Agent | What It Handles | Context Benefit |
|-------|-----------------|-----------------|
| `planner` | Deep codebase exploration, multi-file analysis | Keeps exploration out of your main session |
| `python-code-writer` | Implementation with full convention loading | Loads bundles in its own context |
| `python-test-writer` | Test creation with testing conventions | Isolates test-specific context |
| `code-style-reviewer` | Style checking against all conventions | Loads style bundle independently |
| `code-substance-reviewer` | Design and correctness analysis | Deep analysis in isolated context |

**The math:**  

- A complex task requires `X` tokens of input context 
- Accumulates `Y` tokens of working context
- Produces a `Z`-token answer
- Running `N` such tasks in your main window means `(X + Y + Z) × N` tokens consumed
- Agents farm out the `(X + Y) × N` work and return only the `Z`-token summaries

### When to Delegate to Agents

**Use agents for:**
- Research and exploration (`planner`)
- Implementation work (`python-code-writer`)
- Test writing (`python-test-writer`)
- Code review (`code-style-reviewer`, `code-substance-reviewer`)
- Any task that requires loading multiple skills/conventions

**Handle directly when:**
- Making quick edits you can verify immediately
- Asking simple questions about the codebase
- Running validation commands (`ruff`, `pytest`, etc.)
- Orchestrating multi-phase work

---

## Commands: Orchestrated Context Efficiency

Commands in this configuration orchestrate agents and workflows, letting you express intent while the system manages context distribution.

### `/plan <feature-description>`

Creates an implementation plan before writing code.

**Context benefit:** The `planner` agent loads its full bundle, explores the codebase extensively, and returns a focused plan document. Your main session receives only the plan summary.

**When to use:** New features, architectural changes, complex refactoring.

### `/implement <phase> from <plan-path>`

Executes plan phases using specialized agents.

**Context benefit:** Dispatches work to `python-code-writer`, `python-test-writer`, and `code-cleaner` in sequence. Each agent loads its own conventions in isolation.

**Workflow:**
```
/plan add user authentication
# Review and approve the plan
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-auth-plan.md
/implement Phase 2 from .claude/agent-outputs/plans/2024-01-22T143052Z-auth-plan.md
```

### `/review <target>`

Runs code review with two specialized agents.

**Context benefit:** Style and substance reviewers each load their bundles independently and return focused reports.

**Examples:**
```
/review --staged                    # Review staged changes
/review --commit HEAD               # Review last commit
/review src/my_library/tools/   # Review specific files
```

### `/update-plan <plan-path>`

Syncs a plan with changes from main branch, creating a new versioned copy with updates applied. The original plan file is never modified.

**Context benefit:** Keeps plans current without rebuilding context from scratch.

---

## Context Bundles: Pre-Composed Conventions

Agents in this configuration use **context bundles**—pre-composed skill content that provides exactly the context each agent needs.

### Why Bundles Matter

Without bundles, an agent loading 10 skills would:
1. Make 10 skill invocations
2. Accumulate all skill content sequentially
3. Push relevant conventions into the "lost in the middle" zone

With bundles, an agent:
1. Reads one file containing all relevant conventions
2. Has conventions at the end of context (highest attention)
3. Starts work immediately

### Available Bundles

| Agent | Bundle | Contents |
|-------|--------|----------|
| `code-cleaner` | `bundles/code-cleaner.md` | Cleans Python code |
| `code-style-reviewer` | `bundles/code-style-reviewer.md` | All style-focused conventions |
| `code-substance-reviewer` | `bundles/code-substance-reviewer.md` | Design, maintainability, testability conventions |
| `planner` | `bundles/planner.md` | plan-template, write-markdown-output, frameworks, code-organization, data-structures, function-design, class-design, testability, maintainability, naming-conventions, testing |
| `python-code-writer` | `bundles/python-code-writer.md` | frameworks, code-organization, naming-conventions, function-design, class-design, data-structures, type-hints, pythonic-conventions, docstring-conventions, testability, maintainability, complexity-refactoring, run-python-safely |
| `python-test-writer` | `bundles/python-test-writer.md` | testing, frameworks, naming-conventions, function-design, type-hints, pythonic-conventions, docstring-conventions |
| `test-reviewer` | `bundles/test-reviewer.md` | Test quality |


**Compact bundles** (`*-compact.md`) exist for when you need abbreviated conventions.

### Regenerating Bundles

After modifying skills:
```bash
uv run python .claude/scripts/generate_bundles.py
```

---

## Skills: On-Demand Conventions

Skills provide coding standards without permanently bloating context. They're loaded when needed, not at session start.

### How Skills Save Context

Instead of putting all coding conventions in CLAUDE.md (which loads every session), this configuration:
1. Keeps CLAUDE.md lean with pointers to skills
2. Lets agents load skill bundles in their isolated contexts
3. Allows direct skill invocation when needed

### Using Skills Directly

For quick convention lookups without spawning an agent:

```
# Check naming conventions
Use the naming-conventions skill

# Get framework guidance
Use the frameworks skill
```

### Key Skills for This Repository

| Category | Skills |
|----------|--------|
| **Conventions** | `naming-conventions`, `function-design`, `class-design`, `type-hints`, `docstring-conventions`, `code-organization`, `pythonic-conventions` |
| **Assessment** | `testability`, `maintainability` |
| **Safety** | `run-python-safely`, `frameworks` |
| **Templates** | `plan-template`, `review-template`, `pr-description-template` |

---

## Practical Context Management

### Start Sessions with Clear Intent

Bad:
> "Help me work on the codebase"

Good:
> "Implement the parser refactoring from Phase 2 of the plan"

Clear intent lets Claude focus on relevant context rather than loading everything.

### Use `/clear` Between Unrelated Tasks

After completing a feature, before starting something unrelated:
```
/clear
```

This resets context rather than dragging along stale history.

### Compact at Natural Breakpoints

Don't wait for auto-compaction. Compact proactively:
```
/compact preserve the API changes we made to src/my_library/tools/
```

Good compaction points:
- After completing a plan phase
- After a successful code review
- Before switching to a different area of the codebase

### Break Large Tasks into Phases

Instead of:
> "Refactor the entire authentication system"

Use:
```
/plan refactor authentication system
# Approve the plan
/implement Phase 1 from <plan-path>
# Verify, commit
/implement Phase 2 from <plan-path>
# Verify, commit
```

Each phase gets clean context. Work persists in commits, not context.

### Let Agents Explore, You Orchestrate

For investigation tasks, don't do this in your main session:
```
# Don't do this directly - uses your context
Read all the files in src/my_library/tools/
```

Instead:
```
# Delegate to an agent
Use the Explore agent to understand how the tools module is structured
```

The agent explores extensively in its own context and returns a focused summary.

---

## Anti-Patterns to Avoid

### The Correction Spiral

Claude does something wrong, you correct it, it's still wrong, you correct again. Context gets polluted with failed approaches.

**Solution:** After two failed corrections, use `/clear` and write a better initial prompt incorporating what you learned.

### The Infinite Exploration

Asking Claude to "investigate" without scoping it. Claude reads hundreds of files, filling context with potentially irrelevant information.

**Solution:** Scope investigations explicitly:
```
# Bad
Investigate the authentication system

# Good
Find where JWT tokens are validated
```

### Loading Skills Manually

Invoking skills one-by-one when an agent would load them all via bundle:

**Solution:** Use agents for tasks requiring multiple conventions. Let them load their bundles.

### Keeping Stale Plan Context

Continuing implementation discussions long after the plan is obsolete:

**Solution:** Use `/update-plan` to sync plans with main, or `/clear` and start fresh with updated requirements.

---

## Quick Reference

### Essential Commands

| Command | Purpose |
|---------|---------|
| `/clear` | Reset context entirely |
| `/compact [instructions]` | Compress conversation history |
| `/plan <description>` | Create implementation plan (isolated context) |
| `/implement <phase>` | Execute plan phase with agents |
| `/review <target>` | Code review with agents |

### Context-Efficient Workflow

```
# 1. Plan in isolated context
/plan add new feature

# 2. Implement phases (each in isolated context)
/implement Phase 1 from <plan-path>
/implement Phase 2 from <plan-path>

# 3. Review (isolated context)
/review --staged --plan <plan-path>

# 4. Clear before unrelated work
/clear
```

### Key Principles

1. **Delegate heavy work to agents** - They run in isolated contexts
2. **Use commands for workflows** - They orchestrate context-efficient patterns
3. **Compact proactively at 70%** - Don't wait for degradation
4. **Clear between unrelated tasks** - Fresh context beats stale history
5. **Scope explorations explicitly** - Unbounded investigation fills context fast
6. **Let bundles handle conventions** - Don't load skills manually when agents will

---

## Further Reading

**Research:**
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (TACL 2024): https://aclanthology.org/2024.tacl-1.9/

**Anthropic Documentation:**
- Context Windows: https://docs.claude.com/en/docs/build-with-claude/context-windows
- Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices

**This Configuration:**
- Agent definitions: `.claude/agents/`
- Command definitions: `.claude/commands/`
- Skill catalog: `.claude/manifest.json`
- Context bundles: `.claude/bundles/`

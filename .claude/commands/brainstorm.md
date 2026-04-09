---
name: brainstorm
description: Multi-turn brainstorming session to discover true scope and generate ideas before planning
depends_on_agents:
  - brainstormer
---

# Brainstorming Session

Start a brainstorming session about: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command invokes the **brainstormer agent** to run a multi-turn interview session that helps you discover what you actually want before jumping into planning.

The brainstormer will:
1. **Explore the codebase** - Build context about relevant code and patterns
2. **Interview you** - Ask probing questions to uncover the real problem, constraints, and goals
3. **Challenge assumptions** - Surface alternatives and simpler approaches you may not have considered
4. **Generate ideas** - Brainstorm approaches collaboratively during the conversation
5. **Synthesize takeaways** - Write a brainstorm summary to `.claude/agent-outputs/brainstorms/<YYYY-MM-DDTHHmmssZ>-<scope>-brainstorm.md`

## When to Use This Command

Use `/brainstorm` **before** `/plan` when:
- You have a vague idea but haven't nailed down the scope
- You want to explore alternatives before committing to an approach
- The problem space is complex and you need to think it through
- You want AI to interview you rather than you driving the conversation

**Skip brainstorming for**:
- Well-defined tasks with clear requirements (go straight to `/plan`)
- Simple one-line fixes
- Tasks where scope is already locked in

## Usage

```
/brainstorm <topic or rough idea>
```

## Examples

```
/brainstorm How should we handle authentication in this project?
/brainstorm I want to make the CLI faster but I'm not sure where to start
/brainstorm We need some kind of caching layer
/brainstorm Rethink how we structure the test suite
```

## What You Get

A brainstorm document containing:
- **Problem Statement**: The *real* problem, not just the surface request
- **Key Insights**: Non-obvious things that emerged from the discussion
- **Decided Scope**: Must-have / should-have / won't-do breakdown
- **Ideas Generated**: Selected approach and alternatives considered
- **Open Questions**: Unknowns for planning to resolve
- **Plan Prompt**: A ready-to-use prompt you can copy-paste directly into `/plan`

## After Brainstorming

Once the brainstorm is complete:
1. Copy the **Plan Prompt** from the brainstorm output
2. Run **`/plan <paste the plan prompt here>`**
3. The planner will reference the brainstorm document for full context

## The Interview Pattern

The brainstormer follows a structured interview approach:

1. **Surface understanding** - What are you literally asking for?
2. **Dig deeper** - What's the real problem? What does "done" look like?
3. **Challenge and expand** - What if we didn't do this? What's the simpler version? The 10x version?
4. **Converge** - Confirm priorities, identify key decisions

The agent asks 1-3 questions at a time, shares its thinking, and generates ideas throughout the conversation — not just at the end.

---

# Thinking Tokens, Extended Thinking, and Model Selection for Code Generation

A practical guide for developers using Claude and Claude Code.

---

## How Thinking Tokens Actually Work

### The Mechanism

All LLMs — "thinking" and "regular" — are autoregressive models. They generate one token at a time, where each new token is conditioned on the full sequence of tokens that came before it (input + everything generated so far).

Thinking tokens are not a separate system. There is no "reasoning engine" that runs first and passes results to a "writing engine." It's one continuous generation pass:

```
input → model → [think_1, think_2, ..., think_N, out_1, out_2, ..., out_M]
```

When the model generates `think_47`, it attends to the input plus `think_1` through `think_46`. When it later generates `out_3`, it attends to the input plus all thinking tokens plus `out_1` and `out_2`. There is exactly one forward pass per token and `N + M` forward passes total.

The only thing that makes thinking tokens "special" is a formatting convention — the model emits delimiters (like `<thinking>...</thinking>`), and the serving infrastructure partitions the output into hidden reasoning and visible response. From the model's perspective, it's all just tokens in one sequence.

### Why Not a Recursive Two-Pass System?

You *could* architect a system that runs the model once to produce a scratchpad, concatenates it to the input, and runs the model a second time. Some early chain-of-thought research did exactly this. But it's unnecessary — the autoregressive architecture already gives you this for free. Each generated token is already in the KV cache and available as context for all future tokens. There's nothing to "re-feed."

### What Makes "Thinking Models" Different from Regular LLMs

The core transformer architecture is the same. The differences are in training:

**Regular LLMs** are trained on next-token prediction, then fine-tuned (RLHF, etc.) for helpfulness and safety. They *can* do chain-of-thought if prompted ("think step by step"), but they weren't specifically optimized for productive internal reasoning.

**Thinking models** (Claude with extended thinking, OpenAI o-series, DeepSeek-R1) are trained with reinforcement learning that *rewards* useful internal deliberation. The model learns that spending tokens working through a problem before answering leads to better outcomes, so it develops effective reasoning strategies during training.

The key insight: LLMs have a fixed amount of computation per token. Without thinking tokens, the model gets one forward pass to go from question to answer. Thinking tokens give the model a scratchpad — more sequential compute steps to decompose problems, consider alternatives, check its work, and catch errors before committing. It's trading inference cost (more tokens) for quality.

---

## Extended Thinking in Claude

### How It Works in Claude Code

In Claude Code, you don't configure thinking budgets directly. Instead, you control thinking through **model selection** and **effort levels**:

- **Switch models** with the `/model` command during a session (e.g., `/model opus`, `/model sonnet`, `/model haiku`).
- **Set effort level** with `/model` or the `CLAUDE_CODE_EFFORT_LEVEL` environment variable (`low`, `medium`, `high`, `max`).

Claude Code handles thinking budgets behind the scenes — higher effort levels and more capable models get more thinking tokens. Claude returns a **summary** of its internal reasoning (called "summarized thinking"), though you're billed for the full thinking tokens generated.

---

## When to Use Thinking for Code Generation

### Thinking Helps Most When

**The problem requires multi-step reasoning.** Architectural decisions, debugging across multiple interacting systems, designing algorithms with complex edge cases. The scratchpad lets Claude decompose the problem, consider alternatives, and verify its approach before writing code.

**Correctness is critical and errors are expensive.** Security-sensitive code, financial calculations, data migration logic. Thinking lets Claude check invariants and reason about failure modes.

**The task is ambiguous or underspecified.** When Claude needs to infer requirements, weigh tradeoffs, or decide between multiple valid approaches. Thinking tokens let it explicitly reason about the decision rather than jumping to the first plausible answer.

**Complex refactoring spanning multiple files.** Understanding how changes propagate through a codebase requires holding multiple constraints in mind simultaneously.

### Thinking Adds Less Value When

**The task is well-defined and pattern-matching.** Writing a standard CRUD endpoint, adding a new field to a Pydantic model, writing a Dockerfile for a standard Python app. The model already knows the pattern — extra thinking just adds latency and cost.

**You're iterating quickly on small changes.** When you're in a tight edit-run-test loop, speed matters more than deliberation depth.

**The solution space is narrow.** Boilerplate, formatting, linting fixes, simple test cases. There's one obvious answer and thinking won't find a better one.

**High-volume automated tasks.** Batch processing, routine code reviews, simple file transformations — the throughput/cost tradeoff favors skipping extended thinking.

---

## Model Selection for Claude Code

### The Three-Tier Mental Model

| Model | Strengths | Best For |
|---|---|---|---|
| **Opus** | Deepest reasoning, 1M context window, agent teams, adaptive thinking | Architecture, complex debugging, multi-agent orchestration, large codebase analysis |
| **Sonnet** | Best coding model, excellent with extended thinking, fast | Daily development, most coding tasks, implementation, testing |
| **Haiku** | Fastest, cheapest, surprisingly capable | File reads, linting, formatting, simple scripts, sub-agent tasks |

### Decision Framework

**Spend more than 5 seconds deciding?** Use Sonnet for implementation, Opus for design/research. Don't overthink model selection.

**Use Opus when:**
- Designing system architecture or making decisions with non-obvious tradeoffs
- Debugging across multiple interacting systems with tangled dependencies
- Orchestrating multi-agent workflows (Opus is effective at managing subagent teams)
- Working with very large codebases that benefit from the 1M token context window
- Planning large refactors where missing an edge case costs hours

**Use Sonnet (with extended thinking) when:**
- Implementing features from a well-defined plan
- Writing and debugging most production code
- Code review requiring attention to logic and security
- Complex but scoped tasks: "add auth to this endpoint," "refactor this module"
- Writing comprehensive test suites

**Use Sonnet (without extended thinking) when:**
- Routine implementation you're iterating on quickly
- Simple bug fixes with obvious causes
- Documentation and comments
- Straightforward code generation from clear specs

**Use Haiku when:**
- Simple file reads and content extraction
- Routine formatting and style corrections
- Basic linting and syntax validation
- Worker agents in multi-agent systems
- Quick status checks and simple analysis

### Effort Levels (Opus 4.6)

Configure via `/model` in Claude Code or `CLAUDE_CODE_EFFORT_LEVEL`:

- **Low**: Fast responses for straightforward tasks. Good for routine work where you know what you want.
- **Medium**: Balanced reasoning. Matches Sonnet 4.5's best benchmark scores while using ~76% fewer output tokens.
- **High** (default): Deep reasoning for complex problems.
- **Max**: Maximum deliberation for the hardest problems.

---

## Practical Tips

**Read Claude's thinking output to debug your prompts.** The summarized thinking reveals how Claude interpreted your instructions — useful for iterating on prompts for your subagent pipeline.

**Don't prescribe thinking steps.** "Think step by step about X, then Y, then Z" often performs worse than "Think deeply about this problem." Claude's trained reasoning strategies may be better than what you'd prescribe.

**Use interleaved thinking for agentic workflows.** If Claude is calling tools (reading files, running tests), interleaved thinking lets it reason about intermediate results rather than planning everything upfront.

---

## Summary

Thinking tokens aren't magic — they're the same autoregressive generation, just giving the model more sequential compute before committing to an answer. Use them when the task benefits from deliberation (complex reasoning, high-stakes correctness, ambiguous requirements) and skip them when pattern-matching suffices (boilerplate, well-defined tasks, high-volume automation).

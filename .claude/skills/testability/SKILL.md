---
name: testability
description: Testability assessment criteria for code review. Apply when writing new code that will be tested or evaluating code for dependency injection, global state, pure functions, and test seams.
user-invocable: false
layers:
  rules: rules.md
  examples: examples.md
---

# Testability Assessment

Evaluate whether code can be effectively unit tested in isolation.

**Layers**:
- `rules.md` - Quick reference and severity guidance
- `examples.md` - Detailed code examples

## Quick Reference

| Factor | Question | Severity if problematic |
|--------|----------|------------------------|
| Dependency injection | Are deps passed in? | High |
| Global state | Is shared state avoided? | High |
| Pure functions | Is logic separated from I/O? | Medium |
| Time/randomness | Are these injectable? | Medium |
| File system | Can it be abstracted? | Medium |
| Seams | Can behavior be substituted? | Medium-High |
| Observability | Can you assert on outputs? | Medium |
| Mock avoidance | Does the design eliminate the need for mocking? | High |

## Quick Heuristic

If testing a function requires:
- **0 mocks**: Excellent testability (pure function)
- **1-2 mocks**: Acceptable (clear external boundaries only)
- **3-5 mocks**: Redesign required (too many responsibilities or mocking internal code)
- **6+ mocks**: Design failure (refactor before writing tests)

If any mock or `monkeypatch.setattr` targets internal functions, methods, or classes rather than external boundaries, the count is irrelevant -- redesign for testability instead.

For rules: see `rules.md`
For examples: see `examples.md`

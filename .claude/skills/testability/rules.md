# Testability: Rules

Evaluate whether code can be effectively unit tested in isolation.

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

## Quick Heuristic

If testing a function requires:
- **0 mocks**: Excellent testability (pure function)
- **1-2 mocks**: Good testability (clear dependencies)
- **3-5 mocks**: Concerning (might need refactoring)
- **6+ mocks**: Likely design problem (too many responsibilities)

---

## Dependency Injection

**Rule**: Dependencies should be passed in, not created internally.

| Flag as | Condition |
|---------|-----------|
| **High** | External services (DB, HTTP, files) created internally |
| **Medium** | Configuration created internally |
| **Low** | Only simple value objects created internally |

---

## Global State

**Rule**: Avoid reading from or writing to global/module state.

| Flag as | Condition |
|---------|-----------|
| **High** | Global state affects function behavior |
| **Medium** | Global state is read-only configuration |
| **Low** | Global state is truly constant (e.g., `PI = 3.14159`) |

---

## Pure Functions vs Side Effects

**Rule**: Separate side effects from logic. Extract pure functions.

| Flag as | Condition |
|---------|-----------|
| **Medium** | Business logic is tangled with I/O |
| **Low** | I/O is clearly separated but could be cleaner |

---

## Time and Randomness

**Rule**: Non-deterministic operations should be injectable.

| Flag as | Condition |
|---------|-----------|
| **Medium** | Time/random makes tests flaky or requires complex mocking |
| **Low** | Non-determinism is in test-unimportant code paths |

---

## File System Access

**Rule**: Abstract file operations behind protocols.

| Flag as | Condition |
|---------|-----------|
| **Medium** | File operations are core to functionality |
| **Low** | File access is peripheral (e.g., config loading at startup) |

---

## Test Seams

**Rule**: Provide clear points to substitute test doubles.

A **seam** is a place where you can alter behavior without editing the code.

| Flag as | Condition |
|---------|-----------|
| **High** | Critical code paths have no seams |
| **Medium** | Some seams exist but major ones are missing |

---

## Assertions and Observability

**Rule**: Functions should return values or update observable state.

| Flag as | Condition |
|---------|-----------|
| **Medium** | Testing requires verifying mock interactions instead of outputs |
| **Low** | Outputs exist but could be richer |

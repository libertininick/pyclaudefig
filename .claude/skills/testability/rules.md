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
| Mock avoidance | Does the design eliminate the need for mocking? | High |

## Quick Heuristic

If testing a function requires:
- **0 mocks**: Excellent testability (pure function)
- **1-2 mocks**: Acceptable (clear external boundaries only)
- **3-5 mocks**: Redesign required (too many responsibilities or mocking internal code)
- **6+ mocks**: Design failure (refactor before writing tests)

If any mock or `monkeypatch.setattr` targets internal functions, methods, or classes rather than external boundaries, the count is irrelevant -- redesign for testability instead.

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

---

## Mock & Monkeypatch Avoidance

**Rule**: Code should be designed so tests rarely need mocks or monkeypatching. If testing requires mocking internal code or using `monkeypatch.setattr` on internal functions, the design is the problem -- not the test.

| Flag as | Condition |
|---------|-----------|
| **High** | Testing requires mocking internal functions or methods |
| **High** | Testing requires `monkeypatch.setattr` on internal functions or methods |
| **High** | Testing requires more than 3 mocks or monkeypatches |
| **Medium** | Testing requires mocking/monkeypatching at code layer instead of transport boundary |
| **Low** | Testing uses `monkeypatch.setenv` for env vars (acceptable) |

**Ask**: "Can this code be tested without any mocks or `monkeypatch.setattr` calls? If not, what design change would make that possible?"

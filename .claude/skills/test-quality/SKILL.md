---
name: test-quality
version: 1.0.0
description: Test quality assessment criteria for reviewing tests. Apply when evaluating tests for substantive coverage, organization, maintainability, and realistic test data variety.
user-invocable: false
layers:
  rules: rules.md
  examples: examples.md
---

# Test Quality Assessment

Evaluate whether tests verify true functionality rather than rubber-stamping code with superficial assertions.

**Layers**:
- `rules.md` - Quick reference and severity guidance
- `examples.md` - Detailed code examples

## Quick Reference

| Factor | Question | Severity if problematic |
|--------|----------|------------------------|
| Substantive assertions | Does the test prove anything meaningful? | Critical |
| True functionality | Is observable behavior tested, not implementation? | Critical |
| Test organization | Are tests in the right module and cohesive? | Improvement |
| Edge case coverage | Are error paths and boundaries tested? | Critical/Improvement |
| Test data variety | Is data varied or repetitive? | Improvement |
| Fixture usage | Are fixtures reducing duplication without tight coupling? | Improvement |
| Mock discipline | Are mocks used only when necessary? | Improvement/Critical |
| Tests run | Do tests actually pass without errors? | Critical |

## Quick Heuristic

A test is valuable if:
- **Failure reveals bugs**: The test would fail if the implementation was wrong
- **Survives refactoring**: The test wouldn't break if implementation details changed
- **Documents intent**: Reading the test explains what the code should do
- **Runs independently**: The test passes regardless of execution order

For rules: see `rules.md`
For examples: see `examples.md`

# Test Quality: Rules

Evaluate whether tests verify true functionality and provide meaningful coverage.

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

---

## 1. Substantive Assertions (No Rubber Stamps)

**Rule**: Tests must prove something meaningful about the code under test.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Test has no assertions or only asserts `is not None` |
| **Critical** | Test only asserts on mock return values |
| **Critical** | Test asserts something that could never fail (`assert True`) |
| **Improvement** | Test only verifies data types, not values |
| **Improvement** | Test verifies structure but not content |

**Ask**: "If the implementation returned garbage, would this test catch it?"

---

## 2. True Functionality Testing

**Rule**: Test observable behavior, not implementation details.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Test calls private methods directly (`_method()`) |
| **Critical** | Test asserts on internal state not exposed in the API |
| **Critical** | Test would break from a pure refactoring (same behavior, different implementation) |
| **Improvement** | Test duplicates assertions from other tests without testing new behavior |
| **Nitpick** | Test name describes implementation rather than behavior |

**Ask**: "Would this test still pass if I refactored the implementation without changing behavior?"

---

## 3. Test Organization

**Rule**: Tests should mirror source structure and group related tests cohesively.

| Flag as | Condition |
|---------|-----------|
| **Improvement** | Test file doesn't mirror source module structure |
| **Improvement** | Unrelated tests in the same test class |
| **Improvement** | Related tests scattered across multiple files |
| **Nitpick** | Test class lacks docstring explaining what's being tested |
| **Nitpick** | Tests not in logical order (setup/basic/complex/edge cases) |

**Ask**: "Can I find the tests for a module easily? Are grouped tests actually related?"

---

## 4. Happy Path AND Edge Case Coverage

**Rule**: Test both expected paths and error conditions.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Function has error handling but no tests exercise it |
| **Critical** | Function validates input but no invalid input tests exist |
| **Improvement** | Missing boundary condition tests (empty, one, many) |
| **Improvement** | Missing null/empty/None input tests |
| **Improvement** | Missing tests for documented exceptions |
| **Nitpick** | Edge cases tested but could use more variety |

**Ask**: "What happens at the boundaries? What happens with invalid input?"

---

## 5. Test Data Variety

**Rule**: Use varied, realistic test data defined inline. Avoid repetition; use parametrization. Each test should define its own data so the reader sees inputs and outputs together.

| Flag as | Condition |
|---------|-----------|
| **Improvement** | Same hardcoded test data repeated across multiple tests |
| **Improvement** | Tests that should be parametrized are written as separate functions |
| **Improvement** | Test data is unrealistic (e.g., single-character names, `1` for all IDs) |
| **Improvement** | Test data lacks type/edge diversity (no nulls, dates, large numbers, empty strings, infinity) |
| **Improvement** | Test data hidden in fixtures instead of defined inline in the test |
| **Nitpick** | Magic numbers without comments explaining significance |
| **Nitpick** | Test data could be more descriptive (e.g., `"test"` vs `"alice@example.com"`) |

**Ask**: "Is this data realistic and diverse? Can I see inputs and outputs together without jumping to a fixture?"

---

## 6. Fixture Usage

**Rule**: Fixtures are for instantiating dependency instances (connections, services, toolkit objects), not for defining test data. Test data belongs inline in each test so the reader sees inputs and expected outputs together without jumping elsewhere.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Fixture modifies global state or module variables |
| **Critical** | Fixtures depend on execution order |
| **Improvement** | Fixture defines test data (dicts, DataFrames, simple values) that should be inline |
| **Improvement** | Tests tightly coupled to complex fixture chains |
| **Improvement** | Fixture does too much (setup + cleanup + assertions) |
| **Nitpick** | Fixture in conftest.py used by only one test file |

**Ask**: "Does this fixture create a reusable dependency instance, or is it just hiding test data?"

---

## 7. Mock Discipline

**Rule**: Mock only what you must. Prefer real objects and fakes over mocks.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Mocking the unit under test itself |
| **Critical** | Mock configured incorrectly (returns wrong type, missing methods) |
| **Improvement** | Mocking when a real object would work fine |
| **Improvement** | More than 3 mocks in a single test (indicates design smell) |
| **Improvement** | Mocking standard library functions unnecessarily |
| **Nitpick** | Mock assertions on call order when order doesn't matter |

**Ask**: "Do I really need to mock this, or could I use the real thing?"

---

## 8. Tests Run Successfully

**Rule**: Tests must actually run and pass.

| Flag as | Condition |
|---------|-----------|
| **Critical** | Syntax errors preventing test from running |
| **Critical** | Import errors (missing dependencies, wrong paths) |
| **Critical** | Tests that fail (assertion errors, unexpected exceptions) |
| **Critical** | Tests marked `skip` or `xfail` without explanation |
| **Improvement** | Tests emit warnings (deprecation, resource, etc.) |
| **Improvement** | Tests are slow without being marked as slow |

**Ask**: "Do these tests actually pass when I run `pytest`?"

---

## Review Checklist

When reviewing a test file, check each category:

1. **Substantive?** - Would garbage output fail these tests?
2. **Behavioral?** - Would refactoring break these tests inappropriately?
3. **Organized?** - Can I find and understand these tests?
4. **Complete?** - Are edge cases and error paths covered?
5. **Varied?** - Is test data realistic and not repetitive?
6. **Clean fixtures?** - Are fixtures helping or hurting?
7. **Minimal mocks?** - Are mocks truly necessary?
8. **Running?** - Do tests pass without errors or warnings?

# Example Plan: Fix DataFrame Column Type Validation Bug

## Bug Overview
The `validate_column_types()` function in `src/my_library/dataframe_toolkit/validation.py` incorrectly validates nullable integer columns. When a DataFrame has an integer column with null values (dtype `Int64`), the validation fails with a false negative, claiming the column is a float when it should pass as an integer type.

**Bug Report:**
- **Expected**: DataFrame with `Int64` column (nullable integer) should pass integer type validation
- **Actual**: Validation raises `TypeError: Expected integer type, got float64`
- **Impact**: Users cannot validate DataFrames with nullable integer columns, blocking data processing workflows

## Goals
- Fix the type validation logic to correctly handle nullable integer types
- Ensure the fix doesn't break existing validation for other numeric types
- Add comprehensive tests for edge cases involving nullable types
- Maintain backward compatibility with existing validation behavior

## Phases

- [ ] [Phase 1: Identify Impacted Code](#phase-1-identify-impacted-code)
- [ ] [Phase 2: Reproduce Bug with Test](#phase-2-reproduce-bug-with-test)
- [ ] [Phase 3: Fix the Bug](#phase-3-fix-the-bug)
- [ ] [Phase 4: Add Tests for Edge Cases](#phase-4-add-tests-for-edge-cases-optional-but-recommended)
- [ ] [Phase 5: Final Validation and Documentation](#phase-5-final-validation-and-documentation)

## Bug Fix Strategy

This bug fix follows **Test-Driven Development (TDD)** principles:
1. **Identify**: Locate and understand the buggy code
2. **Reproduce**: Write a failing test that reproduces the bug
3. **Fix**: Modify the code to make the test pass
4. **Validate**: Verify the fix and add tests for new edge cases

## Implementation Plan

### Phase 1: Identify Impacted Code
**Goal**: Locate the buggy code and understand the root cause

#### Step 1.1: Find the buggy function
- **Action**: Read `src/my_library/dataframe_toolkit/validation.py` to locate `validate_column_types()`
- **Details**:
  - Find the function definition and its type checking logic
  - Identify where integer type validation occurs
  - Look for how nullable types (Int64, Float64) are handled
  - Note any dependencies on other functions or libraries
- **Why**: Must understand the existing logic before writing a reproduction test
- **Validation**:
  - **Manual Check**: Identified the exact line(s) where type checking fails for nullable integers
  - **Manual Check**: Documented the current logic: likely using `df[col].dtype == np.int64` which doesn't match `Int64`

#### Step 1.2: Analyze the root cause
- **Action**: Determine why nullable integers fail validation
- **Details**:
  - Research Polars nullable integer types (Int64 vs int64)
  - Check if validation uses exact dtype matching (brittle) vs category checking (robust)
  - Identify if the issue is in dtype detection or in the validation logic
  - Document expected vs actual behavior
- **Why**: Understanding root cause ensures the fix is correct and complete
- **Validation**:
  - **Manual Check**: Root cause documented in comments or plan notes
  - **Manual Check**: Confirmed whether issue is dtype matching, casting, or logic error

---

### Phase 2: Reproduce Bug with Test
**Goal**: Write a failing test that demonstrates the bug

**Pattern**: Write test FIRST → verify it FAILS → then proceed to fix

#### Step 2.1: Write a test that reproduces the bug
- **File**: `tests/dataframe_toolkit/test_validation.py`
- **Action**: Create test that triggers the bug with nullable integer column
- **Details**:
  - Use `python-test-writer` agent to implement the test
  - Create DataFrame with `Int64` column (nullable integer) containing null values
  - Call `validate_column_types()` with integer type expectation
  - Test should FAIL with current code, reproducing the reported bug
  - Test name: `test_validate_column_types_nullable_integers`
- **Why**: Confirms we can reproduce the bug before attempting a fix
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py::test_validate_column_types_nullable_integers -v`
  - **Expected**: Test FAILS with the same error reported in the bug: `TypeError: Expected integer type, got float64`
  - **Manual Check**: Test accurately reproduces the user-reported bug scenario

#### Step 2.2: Verify existing tests still pass
- **Action**: Run existing validation tests to establish baseline
- **Details**:
  - Run all tests in `test_validation.py` except the new one
  - Verify that current code passes existing tests
  - Document which tests are currently passing
  - This confirms we're only fixing the specific bug, not breaking other functionality
- **Why**: Ensures we don't inadvertently break working functionality with our fix
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py -v --ignore=tests/dataframe_toolkit/test_validation.py::test_validate_column_types_nullable_integers`
  - **Expected**: All existing tests pass (baseline behavior is correct)
  - **Manual Check**: Documented which tests currently pass

---

### Phase 3: Fix the Bug
**Goal**: Modify code to make the reproduction test pass

**Pattern**: Minimal change to fix the bug → verify test passes → ensure no regressions

#### Step 3.1: Implement the fix
- **File**: `src/my_library/dataframe_toolkit/validation.py`
- **Action**: Modify `validate_column_types()` to correctly handle nullable integer types
- **Details**:
  - Change validation logic from exact dtype matching to category-based checking
  - Use `pl.datatypes.is_integer(df[col].dtype)` instead of `df[col].dtype == pl.Int64`
  - This handles both `Int64` (nullable) and `int64` (non-nullable) integer types
  - Alternatively, check for both: `df[col].dtype in [pl.Int64, pl.int64, pl.Int32, pl.int32, ...]`
  - Update the function docstring to mention nullable type support
  - Add inline comment explaining why category checking is used
- **Why**: Fixes the bug by correctly recognizing nullable integers as valid integer types
- **Dependencies**: Requires Phase 2 complete (test written)
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py::test_validate_column_types_nullable_integers -v`
  - **Expected**: Test NOW PASSES (was failing before fix)
  - **Manual Check**: Code change is minimal and focused on the specific bug

#### Step 3.2: Verify no regressions
- **Action**: Run all existing validation tests to ensure fix doesn't break anything
- **Details**:
  - Run complete test suite for validation module
  - All previously passing tests must still pass
  - New test (from Step 2.1) must now also pass
  - If any test fails, revise the fix to avoid breaking existing behavior
- **Why**: Confirms the fix is correct and maintains backward compatibility
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py -v`
  - **Expected**: All tests pass (existing + new test)
  - **Manual Check**: No tests that were passing before now fail

#### Step 3.3: Run type checking and linting
- **Action**: Ensure code quality standards are maintained
- **Validation**:
  - **Command**: `uv run ruff check --fix && uv run ruff format`
  - **Expected**: No linting errors, code properly formatted
  - **Command**: `uv run ty check src/my_library/dataframe_toolkit/validation.py`
  - **Expected**: No type errors
  - **Command**: `uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/validation.py`
  - **Expected**: Docstring format is valid
  - **Manual Check**: Updated docstring mentions nullable type support

---

### Phase 4: Add Tests for Edge Cases (Optional but Recommended)
**Goal**: Ensure comprehensive test coverage for related scenarios

#### Step 4.1: Identify additional edge cases
- **Action**: Brainstorm edge cases revealed by this bug
- **Details**:
  - Nullable floats (Float64) - should they pass float validation?
  - Mixed nullable and non-nullable columns in same DataFrame
  - Empty DataFrames with nullable types
  - All-null columns (Int64 with all null values)
  - Other nullable types: String vs string, Boolean vs boolean
- **Why**: Bug fixes often reveal gaps in test coverage
- **Validation**:
  - **Manual Check**: List of 3-5 edge cases identified and documented

#### Step 4.2: Write tests for edge cases
- **File**: `tests/dataframe_toolkit/test_validation.py`
- **Action**: Use `python-test-writer` agent to add tests for identified edge cases
- **Details**:
  - Add test for nullable float columns: `test_validate_column_types_nullable_floats`
  - Add test for mixed nullable/non-nullable: `test_validate_column_types_mixed_nullable`
  - Add test for all-null column: `test_validate_column_types_all_null_column`
  - Each test should verify expected behavior (pass or fail with clear error)
- **Why**: Prevents similar bugs in the future and improves robustness
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py -v -k "nullable or null"`
  - **Expected**: All new edge case tests pass
  - **Manual Check**: Tests cover meaningful scenarios related to the bug

#### Step 4.3: Verify complete test coverage
- **Action**: Check test coverage for the validation module
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/test_validation.py -v --cov=src/my_library/dataframe_toolkit/validation --cov-report=term-missing`
  - **Expected**: Coverage >= 95% for validation.py
  - **Manual Check**: All branches of type validation logic are covered

---

### Phase 5: Final Validation and Documentation
**Goal**: Ensure fix is complete and properly documented

#### Step 5.1: Run full test suite
- **Action**: Verify fix doesn't break anything in broader codebase
- **Validation**:
  - **Command**: `uv run pytest tests/dataframe_toolkit/ -v`
  - **Expected**: All tests pass (not just validation tests)
  - **Manual Check**: No unexpected test failures outside validation module

#### Step 5.2: Document the fix
- **Action**: Update relevant documentation
- **Details**:
  - Add comment in code explaining the fix (why category checking vs exact matching)
  - Update function docstring to mention nullable type support
  - Consider adding example in docstring showing nullable integer validation
  - If there's a CHANGELOG.md, add entry: "Fixed: validate_column_types now correctly handles nullable integer columns (Int64)"
- **Why**: Future developers need to understand why the fix was necessary
- **Validation**:
  - **Manual Check**: Code comment explains the nullable type issue
  - **Manual Check**: Docstring updated with nullable type information
  - **Manual Check**: CHANGELOG.md updated (if applicable)

#### Step 5.3: Final quality checks
- **Action**: Run all quality checks
- **Validation**:
  - **Command**: `uv run ruff check && uv run ty check . && uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/`
  - **Expected**: All quality checks pass
  - **Manual Check**: Code follows project conventions

---

## Files Modified

### Implementation File
- `src/my_library/dataframe_toolkit/validation.py` - Fixed type validation logic

### Test File
- `tests/dataframe_toolkit/test_validation.py` - Added reproduction test and edge case tests

### Documentation (Optional)
- `CHANGELOG.md` - Documented the bug fix (if file exists)

## Testing Requirements

### Bug Reproduction Test (Required)
**Test**: `test_validate_column_types_nullable_integers`
- **Given**: DataFrame with Int64 (nullable integer) column containing some null values
- **When**: `validate_column_types()` is called with integer type expectation
- **Then**: Validation passes without raising TypeError

### Edge Case Tests (Added in Phase 4)
**Test**: `test_validate_column_types_nullable_floats`
- **Given**: DataFrame with Float64 (nullable float) column
- **When**: `validate_column_types()` is called with float type expectation
- **Then**: Validation passes correctly

**Test**: `test_validate_column_types_mixed_nullable`
- **Given**: DataFrame with both nullable (Int64) and non-nullable (int64) integer columns
- **When**: `validate_column_types()` is called for all integer columns
- **Then**: Both column types pass validation

**Test**: `test_validate_column_types_all_null_column`
- **Given**: DataFrame with Int64 column containing only null values
- **When**: `validate_column_types()` is called with integer type expectation
- **Then**: Validation behavior is defined and consistent

### Regression Tests
- All existing tests in `test_validation.py` must continue to pass

## Acceptance Criteria

### Bug Fix Acceptance
- [x] Bug is reproduced with a failing test (Phase 2)
- [x] Fix makes the reproduction test pass (Phase 3)
- [x] All existing tests continue to pass (no regressions)
- [x] Root cause is identified and documented
- [x] Fix is minimal and targeted to the specific bug

### Quality Acceptance
- [x] New test(s) added to prevent regression
- [x] Code follows project conventions
- [x] Type checking passes (`uv run ty check .`)
- [x] Linting passes (`uv run ruff check`)
- [x] Docstring validation passes
- [x] Test coverage >= 95% for modified code

### Documentation Acceptance
- [x] Code comment explains the fix
- [x] Function docstring updated (if needed)
- [x] CHANGELOG.md updated (if applicable)

## Test-Driven Development Summary

This bug fix demonstrates the TDD cycle:

1. **RED**: Write a failing test that reproduces the bug (Phase 2)
   - Test fails with current code
   - Confirms bug exists

2. **GREEN**: Write minimal code to make the test pass (Phase 3)
   - Fix is targeted and minimal
   - Test now passes

3. **REFACTOR**: Add edge case tests and improve coverage (Phase 4)
   - Prevent similar bugs
   - Improve robustness

4. **VALIDATE**: Verify no regressions and document (Phase 5)
   - All tests pass
   - Fix is documented

This approach ensures the fix is correct, complete, and maintainable.

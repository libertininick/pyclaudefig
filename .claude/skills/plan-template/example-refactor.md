---
scope: sql-generation-refactor
created: 2026-01-26T143052Z
updated: 2026-01-26T143052Z
version: 2
---

# Implementation Plan: Refactor SQL Generation Module

## Overview
Refactor the existing SQL generation logic scattered across multiple files into a cohesive, maintainable module with clear abstractions. Current code has duplication, inconsistent error handling, and tight coupling between query building and execution.

## Requirements

### Functional Requirements
- FR1: Preserve all existing SQL generation functionality
- FR2: Consolidate duplicate query building logic into reusable components
- FR3: Separate query building from query execution concerns
- FR4: Maintain backward compatibility with existing API

### Non-Functional Requirements
- NFR1: Improve code maintainability by reducing duplication by 70%
- NFR2: Enhance testability through better separation of concerns
- NFR3: Maintain or improve performance (no regressions)
- NFR4: Complete refactor without breaking existing tests
- NFR5: Add comprehensive docstrings to all new/modified code

### Assumptions & Constraints
- Must maintain existing public API surface
- Cannot change database schema or query semantics
- Using SQLGlot for SQL parsing and generation (see frameworks.md)
- All existing tests must continue to pass

## Phases

- [ ] [Phase 1: ClauseBuilder Module](#phase-1-clausebuilder-module)
- [ ] [Phase 2: QueryBuilder Module](#phase-2-querybuilder-module)
- [ ] [Phase 3: QueryExecutor Module](#phase-3-queryexecutor-module)
- [ ] [Phase 4: Toolkit Refactoring](#phase-4-toolkit-refactoring)
- [ ] [Phase 5: Final Quality Assurance](#phase-5-final-quality-assurance)

## Architecture Analysis

### Current State
**Existing code structure:**
- `src/my_library/dataframe_toolkit/toolkit.py` - Main toolkit with mixed concerns
- `src/my_library/dataframe_toolkit/sql_utils.py` - Some SQL utilities (incomplete)
- Query building logic scattered across 5+ methods in toolkit.py
- Duplicate WHERE clause construction in 3 different places
- JOIN logic mixed with DataFrame operations

**Code smells identified:**
- God class: `DataFrameToolkit` has 850 lines with SQL generation, execution, and data processing
- Duplicated code: WHERE clause building repeated 3 times with slight variations
- Tight coupling: Query building directly calls database execution
- Missing abstractions: No clear model for query components (SELECT, WHERE, JOIN)
- Inconsistent error handling: Some methods raise exceptions, others return None

### Proposed Changes
**New structure:**
- `src/my_library/dataframe_toolkit/sql/query_builder.py` - Core query building abstractions
- `src/my_library/dataframe_toolkit/sql/clause_builder.py` - Clause construction utilities (WHERE, JOIN, etc.)
- `src/my_library/dataframe_toolkit/sql/query_executor.py` - Query execution (separated from building)
- `src/my_library/dataframe_toolkit/sql/__init__.py` - Public API exports
- `src/my_library/dataframe_toolkit/toolkit.py` - Refactored to use new SQL module

**Key changes:**
- Extract query building into `QueryBuilder` class
- Extract clause construction into standalone functions
- Separate query execution into `QueryExecutor` class
- Update `DataFrameToolkit` to delegate to new modules
- Maintain backward compatibility through adapter methods

### Design Decisions
1. **Use Builder Pattern**: QueryBuilder provides fluent interface for constructing queries incrementally
2. **Separate read/write concerns**: Read queries and write queries use different builder classes
3. **SQLGlot for SQL AST**: Leverage SQLGlot for parsing and generating SQL (already approved in frameworks.md)
4. **No breaking changes**: Existing toolkit methods delegate to new implementation, maintaining same signatures
5. **Incremental migration**: Refactor one method at a time, keeping tests green

## File Inventory

### Files to Create
- `src/my_library/dataframe_toolkit/sql/__init__.py` - Module exports
- `src/my_library/dataframe_toolkit/sql/query_builder.py` - QueryBuilder class
- `src/my_library/dataframe_toolkit/sql/clause_builder.py` - Clause construction utilities
- `src/my_library/dataframe_toolkit/sql/query_executor.py` - Query execution
- `tests/dataframe_toolkit/sql/test_query_builder.py` - QueryBuilder tests
- `tests/dataframe_toolkit/sql/test_clause_builder.py` - Clause builder tests
- `tests/dataframe_toolkit/sql/test_query_executor.py` - Query executor tests

### Files to Modify
- `src/my_library/dataframe_toolkit/toolkit.py` - Refactor to use new SQL module
- `src/my_library/dataframe_toolkit/__init__.py` - Update exports
- `tests/dataframe_toolkit/test_toolkit.py` - Update to test through new architecture

### Files to Delete (if any)
- `src/my_library/dataframe_toolkit/sql_utils.py` - Logic will be migrated to new sql/ module

## Implementation Steps

### Phase 1: ClauseBuilder Module
**Goal**: Create and validate clause building utilities
**Pattern**: Write → Test → Validate

#### Step 1.1: Write - Create sql submodule with ClauseBuilder
- **Files**:
  - `src/my_library/dataframe_toolkit/sql/__init__.py`
  - `src/my_library/dataframe_toolkit/sql/clause_builder.py`
- **Action**: Create sql submodule and implement clause building functions
- **Details**:
  - Create directory: `src/my_library/dataframe_toolkit/sql/`
  - Create `__init__.py` with module docstring describing purpose
  - Implement `clause_builder.py` with functions:
    - `build_where_clause(conditions: list[tuple[str, str, Any]]) -> str`
    - `build_join_clause(join_type: str, table: str, on_condition: str) -> str`
    - `build_select_clause(columns: list[str], distinct: bool = False) -> str`
  - Use SQLGlot for SQL generation to ensure valid syntax
  - Add comprehensive Google-style docstrings with examples
  - All functions pure (no side effects)
  - Export clause builder functions from `__init__.py`
- **Why**: Foundation for reusable SQL clause construction, consolidating duplicated logic
- **Dependencies**: None

#### Step 1.2: Test - Create ClauseBuilder test suite
- **File**: `tests/dataframe_toolkit/sql/test_clause_builder.py`
- **Action**: Use `python-test-writer` agent to create comprehensive tests
- **Details**:
  - Test each clause building function
  - Test with various SQL conditions and data types
  - Test edge cases: empty lists, None values, special characters
  - Test SQL injection prevention
  - Aim for ≥95% coverage
- **Why**: Ensure clause builders work correctly before integration
- **Dependencies**: Requires Step 1.1

#### Step 1.3: Validate - Verify ClauseBuilder implementation
- **Action**: Run tests and quality checks on clause_builder module
- **Validation Steps**:
  1. **Import check**: `uv run python .claude/scripts/run_python_safely.py -c "from my_library.dataframe_toolkit.sql.clause_builder import build_where_clause; clause = build_where_clause([('age', '>', 18)]); print('OK' if clause else 'FAIL')"`
     - Expected: Prints "OK"
  2. **Test execution**: `uv run pytest tests/dataframe_toolkit/sql/test_clause_builder.py -v --cov=src/my_library/dataframe_toolkit/sql/clause_builder --cov-report=term-missing`
     - Expected: All tests pass with ≥95% coverage
  3. **Code quality**: `uv run ruff check src/my_library/dataframe_toolkit/sql/clause_builder.py`
     - Expected: No errors
  4. **Type checking**: `uv run ty check src/my_library/dataframe_toolkit/sql/clause_builder.py`
     - Expected: No errors
  5. **Docstring validation**: `uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/sql/clause_builder.py`
     - Expected: No errors
- **Manual Checks**:
  - All functions have type hints and Google-style docstrings
  - Functions are pure with no side effects
  - SQL output is valid and secure
- **Dependencies**: Requires Step 1.2

### Phase 2: QueryBuilder Module
**Goal**: Create and validate query builder class
**Pattern**: Write → Test → Validate

#### Step 2.1: Write - Create QueryBuilder class
- **File**: `src/my_library/dataframe_toolkit/sql/query_builder.py`
- **Action**: Implement fluent QueryBuilder interface
- **Details**:
  - Create class `QueryBuilder` with methods:
    - `select(*columns: str) -> Self`
    - `from_table(table: str) -> Self`
    - `where(condition: str) -> Self`
    - `join(table: str, on: str, join_type: str = "INNER") -> Self`
    - `build() -> str` - Returns final SQL string
  - Use SQLGlot internally for AST manipulation
  - Use ClauseBuilder functions from Phase 1
  - Builder pattern: methods return self for chaining
  - Add validation: ensure from_table called before build()
  - Add comprehensive Google-style docstrings with examples
  - Update `__init__.py` to export QueryBuilder
- **Why**: Provide clean, type-safe interface for building queries
- **Dependencies**: Requires Phase 1 complete

#### Step 2.2: Test - Create QueryBuilder test suite
- **File**: `tests/dataframe_toolkit/sql/test_query_builder.py`
- **Action**: Use `python-test-writer` agent to create QueryBuilder tests
- **Details**:
  - Test query building with method chaining
  - Test various SQL clause combinations (SELECT, WHERE, JOIN)
  - Test validation (e.g., build() without from_table())
  - Test SQL output correctness using SQLGlot parser
  - Test integration with ClauseBuilder functions
  - Aim for ≥95% coverage
- **Why**: Ensure QueryBuilder produces valid SQL and handles edge cases
- **Dependencies**: Requires Step 2.1

#### Step 2.3: Validate - Verify QueryBuilder implementation
- **Action**: Run tests and quality checks on query_builder module
- **Validation Steps**:
  1. **Import check**: `uv run python .claude/scripts/run_python_safely.py -c "from my_library.dataframe_toolkit.sql.query_builder import QueryBuilder; sql = QueryBuilder().select('id', 'name').from_table('users').where('age > 18').build(); print('OK' if 'SELECT' in sql else 'FAIL')"`
     - Expected: Prints "OK"
  2. **Test execution**: `uv run pytest tests/dataframe_toolkit/sql/test_query_builder.py -v --cov=src/my_library/dataframe_toolkit/sql/query_builder --cov-report=term-missing`
     - Expected: All tests pass with ≥95% coverage
  3. **Code quality**: `uv run ruff check src/my_library/dataframe_toolkit/sql/query_builder.py`
     - Expected: No errors
  4. **Type checking**: `uv run ty check src/my_library/dataframe_toolkit/sql/query_builder.py`
     - Expected: No errors
  5. **Docstring validation**: `uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/sql/query_builder.py`
     - Expected: No errors
- **Manual Checks**:
  - Methods return Self for proper chaining
  - All type hints present
  - SQL output is syntactically correct
  - Validation logic works (e.g., prevents build() without from_table())
- **Dependencies**: Requires Step 2.2

### Phase 3: QueryExecutor Module
**Goal**: Create and validate query executor class
**Pattern**: Write → Test → Validate

#### Step 3.1: Write - Create QueryExecutor class
- **File**: `src/my_library/dataframe_toolkit/sql/query_executor.py`
- **Action**: Implement query execution with separation from building
- **Details**:
  - Create class `QueryExecutor` with constructor accepting connection
  - Method: `execute_query(sql: str, params: dict | None = None) -> pl.DataFrame`
  - Method: `execute_update(sql: str, params: dict | None = None) -> int` - Returns rows affected
  - Add error handling with clear exception messages
  - Add query logging at DEBUG level
  - Support parameterized queries to prevent SQL injection
  - Add comprehensive Google-style docstrings with examples
  - Update `__init__.py` to export QueryExecutor
- **Why**: Separate execution from building for better testability and single responsibility
- **Dependencies**: Requires Phase 1 complete (can develop in parallel with Phase 2)

#### Step 3.2: Test - Create QueryExecutor test suite
- **File**: `tests/dataframe_toolkit/sql/test_query_executor.py`
- **Action**: Use `python-test-writer` agent to create QueryExecutor tests
- **Details**:
  - Use mock database connection for testing
  - Test query execution returns DataFrame
  - Test parameterized queries prevent SQL injection
  - Test error handling (connection errors, invalid SQL)
  - Test update operations return row counts
  - Test query logging functionality
  - Aim for ≥90% coverage
- **Why**: Ensure QueryExecutor handles execution correctly and safely
- **Dependencies**: Requires Step 3.1

#### Step 3.3: Validate - Verify QueryExecutor implementation
- **Action**: Run tests and quality checks on query_executor module
- **Validation Steps**:
  1. **Import check**: `uv run python .claude/scripts/run_python_safely.py -c "from my_library.dataframe_toolkit.sql.query_executor import QueryExecutor; print('OK')"`
     - Expected: Prints "OK"
  2. **Test execution**: `uv run pytest tests/dataframe_toolkit/sql/test_query_executor.py -v --cov=src/my_library/dataframe_toolkit/sql/query_executor --cov-report=term-missing`
     - Expected: All tests pass with ≥90% coverage
  3. **Code quality**: `uv run ruff check src/my_library/dataframe_toolkit/sql/query_executor.py`
     - Expected: No errors
  4. **Type checking**: `uv run ty check src/my_library/dataframe_toolkit/sql/query_executor.py`
     - Expected: No errors
  5. **Docstring validation**: `uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/sql/query_executor.py`
     - Expected: No errors
  6. **Module exports**: `uv run python .claude/scripts/run_python_safely.py -c "from my_library.dataframe_toolkit.sql import QueryBuilder, QueryExecutor; print('OK')"`
     - Expected: Prints "OK"
- **Manual Checks**:
  - Error handling is comprehensive and clear
  - Connection handling is proper
  - Parameterized queries work correctly
  - Tests use mocking appropriately
- **Dependencies**: Requires Step 3.2

### Phase 4: Toolkit Refactoring
**Goal**: Migrate DataFrameToolkit to use new SQL module
**Pattern**: Write → Test → Validate

#### Step 4.1: Write - Refactor DataFrameToolkit methods
- **File**: `src/my_library/dataframe_toolkit/toolkit.py`
- **Action**: Refactor all SQL generation methods to use new sql module
- **Details**:
  - Import new SQL module: `from my_library.dataframe_toolkit.sql import QueryBuilder, QueryExecutor, build_where_clause, build_join_clause`
  - Start with `query_with_filters()` as proof of concept
  - Identify all methods that build SQL queries (approximately 6-8 methods)
  - Refactor each to use QueryBuilder and QueryExecutor
  - Remove duplicate WHERE clause construction
  - Remove inline SQL string concatenation
  - Keep all method signatures identical (backward compatibility)
  - Maintain identical external behavior
  - Add comments marking refactored sections
- **Why**: Complete migration to new architecture while maintaining backward compatibility
- **Dependencies**: Requires Phases 1, 2, and 3 complete

#### Step 4.2: Test - Verify toolkit backward compatibility
- **Action**: Run existing toolkit tests to ensure no breaking changes
- **Details**:
  - All existing tests in `test_toolkit.py` must pass without modification
  - If tests fail, investigate and fix refactored code (not tests)
  - Add integration test demonstrating QueryBuilder + QueryExecutor workflow
  - Test end-to-end query building and execution through toolkit
- **Why**: Ensure refactor maintains backward compatibility and existing functionality
- **Dependencies**: Requires Step 4.1

#### Step 4.3: Validate - Verify toolkit refactoring
- **Action**: Run tests and validation checks
- **Validation Steps**:
  1. **Proof of concept test**: `uv run pytest tests/dataframe_toolkit/test_toolkit.py::test_query_with_filters -v`
     - Expected: Test passes without modification
  2. **Full toolkit tests**: `uv run pytest tests/dataframe_toolkit/test_toolkit.py -v`
     - Expected: All existing tests pass
  3. **Integration verification**: `uv run pytest tests/dataframe_toolkit/ -v`
     - Expected: All tests pass
  4. **Code quality**: `uv run ruff check src/my_library/dataframe_toolkit/toolkit.py`
     - Expected: No errors
  5. **Type checking**: `uv run ty check src/my_library/dataframe_toolkit/toolkit.py`
     - Expected: No errors
- **Manual Checks**:
  - Method signatures unchanged
  - Behavior identical to pre-refactor
  - Code duplication significantly reduced
  - SQL generation uses new module throughout
- **Dependencies**: Requires Step 4.2

#### Step 4.4: Write - Clean up deprecated code and update exports
- **Files**:
  - `src/my_library/dataframe_toolkit/sql_utils.py` (delete)
  - `src/my_library/dataframe_toolkit/__init__.py` (update)
- **Action**: Remove old code and update module exports
- **Details**:
  - Verify all functions from sql_utils.py migrated to new sql/ module
  - Search for any remaining imports of sql_utils: `uv run python -m grep -r "from.*sql_utils" src/`
  - Delete sql_utils.py
  - Update toolkit `__init__.py`:
    - Add export: `from my_library.dataframe_toolkit.sql import QueryBuilder, QueryExecutor`
    - Update module docstring to mention new sql module
    - Update `__all__` if present
- **Why**: Clean up deprecated code and make new module accessible from toolkit namespace
- **Dependencies**: Requires Step 4.3

#### Step 4.5: Validate - Final cleanup verification
- **Action**: Verify cleanup and exports
- **Validation Steps**:
  1. **No sql_utils imports**: `uv run python -m grep -r "sql_utils" src/`
     - Expected: No matches found
  2. **Tests still pass**: `uv run pytest tests/dataframe_toolkit/ -v`
     - Expected: All tests pass
  3. **Exports work**: `uv run python .claude/scripts/run_python_safely.py -c "from my_library.dataframe_toolkit import QueryBuilder; print('OK')"`
     - Expected: Prints "OK"
- **Manual Checks**:
  - sql_utils.py deleted
  - No orphaned imports
  - New sql module accessible from toolkit namespace
- **Dependencies**: Requires Step 4.4

### Phase 5: Final Quality Assurance
**Goal**: Comprehensive validation of entire refactor
**Pattern**: Comprehensive testing and validation

#### Step 5.1: Run comprehensive test suite
- **Action**: Run all tests with coverage analysis
- **Validation Steps**:
  1. **Full test suite**: `uv run pytest tests/dataframe_toolkit/ -v --cov=src/my_library/dataframe_toolkit --cov-report=term-missing`
     - Expected: All tests pass, coverage ≥90%
  2. **SQL module coverage**: `uv run pytest tests/dataframe_toolkit/sql/ -v --cov=src/my_library/dataframe_toolkit/sql --cov-report=term-missing`
     - Expected: Coverage ≥95% for sql module
- **Manual Checks**:
  - No test failures
  - No flaky tests
  - Coverage meets requirements
- **Dependencies**: Requires Phase 4 complete

#### Step 5.2: Run all code quality checks
- **Action**: Validate code quality across all modified files
- **Validation Steps**:
  1. **Linting**: `uv run ruff check src/my_library/dataframe_toolkit/`
     - Expected: No errors
  2. **Formatting**: `uv run ruff format --check src/my_library/dataframe_toolkit/`
     - Expected: All files properly formatted
  3. **Type checking**: `uv run ty check src/my_library/dataframe_toolkit/`
     - Expected: No type errors
  4. **Docstrings**: `uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/dataframe_toolkit/sql/`
     - Expected: No docstring errors
- **Manual Checks**:
  - Code properly formatted
  - Type-safe throughout
  - Documentation complete
- **Dependencies**: Requires Step 5.1

#### Step 5.3: Performance regression testing
- **Action**: Verify no performance degradation
- **Details**:
  - Run representative query benchmarks
  - Compare execution times before/after refactor
  - Ensure new implementation is not >5% slower
  - Document any performance improvements
- **Validation**:
  - Manual timing comparison of representative queries
  - Expected: Comparable or better performance
- **Manual Checks**:
  - No obvious performance regressions
  - Query execution times within acceptable range
- **Dependencies**: Requires Step 5.2

#### Step 5.4: Measure code duplication reduction
- **Action**: Verify DRY principle improvements
- **Details**:
  - Count lines of duplicated SQL generation code before/after
  - Calculate reduction percentage
  - Verify ≥70% reduction in duplication
  - Document specific areas of improvement
- **Manual Checks**:
  - WHERE clause building consolidated (was duplicated 3 times)
  - SQL string concatenation eliminated
  - Query building centralized in QueryBuilder
  - Code is more maintainable and readable
- **Dependencies**: Requires Step 5.2

## Testing Requirements

### Unit Tests
**Agent Guidance**: Use `python-test-writer` agent for all test implementations

#### Test Files Required
- `tests/dataframe_toolkit/sql/test_clause_builder.py` - Clause building functions
- `tests/dataframe_toolkit/sql/test_query_builder.py` - QueryBuilder class
- `tests/dataframe_toolkit/sql/test_query_executor.py` - QueryExecutor class
- `tests/dataframe_toolkit/test_toolkit.py` - Integration tests (existing tests must pass)

### Integration Tests
- All existing `test_toolkit.py` tests must pass unchanged
- Add integration test demonstrating QueryBuilder + QueryExecutor workflow
- Test end-to-end query building and execution

### Performance Tests (if applicable)
- Benchmark representative queries before and after refactor
- Ensure no regressions (>5% slowdown)

## Code Quality Requirements

- [x] All functions have type hints
- [x] All public APIs have Google-style docstrings
- [x] Code follows project conventions (see development-conventions/)
- [x] No code duplication (DRY principle) - this is a primary goal
- [x] Error handling with clear messages
- [x] Passes `uv run ruff check`
- [x] Passes `uv run ty check .`
- [x] Passes docstring linting

## Dependencies

### External Dependencies
- SQLGlot (already in project dependencies per frameworks.md)

### Internal Dependencies
- Polars for DataFrame operations
- Existing database connection utilities

### Blocking Items
None

## Acceptance Criteria

### Functional Acceptance
- [x] All existing DataFrameToolkit functionality preserved
- [x] All existing tests pass without modification
- [x] No breaking changes to public API
- [x] SQL generation moved to dedicated module
- [x] Query building separated from query execution

### Quality Acceptance
- [x] All unit tests pass (`uv run pytest`)
- [x] Code coverage ≥90% for new sql module
- [x] Type checking passes (`uv run ty check .`)
- [x] Linting passes (`uv run ruff check`)
- [x] Docstring validation passes
- [x] No performance regressions
- [x] Code duplication reduced by ≥70%

### Refactoring Acceptance
- [x] QueryBuilder provides fluent interface for query construction
- [x] Clause building logic consolidated into reusable functions
- [x] QueryExecutor handles all database interactions
- [x] DataFrameToolkit delegates to new sql module
- [x] Old sql_utils.py removed
- [x] Clear separation between query building and execution

### Documentation Acceptance
- [x] All new classes/functions have Google-style docstrings
- [x] Module-level docstrings explain purpose and usage
- [x] Examples provided in docstrings
- [x] Architecture documented in docstrings

## Future Enhancements

- Add query optimization hints to QueryBuilder
- Support for CTEs (Common Table Expressions)
- Query result caching layer
- Query plan analysis and optimization suggestions
- Support for more complex join types and subqueries

---

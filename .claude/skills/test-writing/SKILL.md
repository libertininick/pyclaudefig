---
name: test-writing
version: 1.1.0
description: Pytest testing conventions for this codebase. Apply when writing or reviewing tests including test naming, structure, fixtures, and parametrization.
user-invocable: false
---

# Testing Conventions

Pytest conventions for writing maintainable, behavior-focused tests.

## Quick Reference

| Element | Convention |
|---------|------------|
| Test file naming | `test_<module>.py` |
| Test function naming | `test_<function>_<scenario>_<expected>` |
| Test structure | Arrange-Act-Assert with comments |
| Multiple assertions | Use `pytest-check` for soft assertions |
| Test data | Inline in each test or parameterize with `@pytest.mark.parametrize`; fixtures are for dependency instances |
| Multiple inputs | Use `@pytest.mark.parametrize` |
| Related tests | Group in test classes |

## Anti-Patterns to Avoid

| Anti-Pattern | Guidance |
|--------------|----------|
| Coverage-driven tests | Test meaningful behavior, not lines |
| Implementation testing | Test observable behavior; tests should survive refactoring |
| Order-dependent tests | Tests must be independent; never rely on execution order |
| Multiple bare asserts | Use `pytest-check` so all assertions run even if early ones fail |
| Fixturized test data | Define test data inline in each test; fixtures are for dependency instances |
| Fixture duplication | Extend or generalize existing fixtures |
| Homogeneous test data | Vary data types, include edge values (nulls, dates, large numbers, empty strings) |

## Test Organization

Mirror source structure:

```
src/my_library/retrieval/embeddings.py
tests/retrieval/test_embeddings.py
```

## Test Naming

**Pattern**: `test_<function>_<scenario>_<expected_result>`

```python
# CORRECT - descriptive name following pattern
def test_calculate_similarity_identical_vectors_returns_one() -> None:
    """Identical vectors should have similarity of 1.0."""
    vec = [1.0, 0.0, 0.0]
    assert calculate_similarity(vec, vec) == 1.0


def test_calculate_similarity_mismatched_dimensions_raises_value_error() -> None:
    """Vectors with different dimensions should raise ValueError."""
    with pytest.raises(ValueError, match="dimension"):
        calculate_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


# INCORRECT - vague names
def test_similarity():  # Missing scenario and expected result
    ...

def test_error():  # No context about what's being tested
    ...
```

## Test Structure: Arrange-Act-Assert

Always organize tests with clear AAA sections:

```python
# CORRECT - clear AAA structure with comments
def test_search_returns_results_sorted_by_score() -> None:
    """Search results should be sorted by relevance score descending."""
    # Arrange
    index = SearchIndex()
    index.add_documents(sample_documents)

    # Act
    results = index.search("python async", limit=10)

    # Assert
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


# INCORRECT - mixed arrangement and assertions
def test_search_sorting() -> None:
    index = SearchIndex()
    assert index is not None  # Asserting during arrangement
    index.add_documents(sample_documents)
    results = index.search("python async", limit=10)
    assert len(results) > 0
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
```

## Multiple Assertions with pytest-check

Use `pytest-check` for soft assertions when verifying multiple properties. This ensures all assertions run even if earlier ones fail, giving complete feedback in a single test run.

```python
from pytest_check import check


# CORRECT - pytest-check for multiple related assertions
def test_user_profile_contains_required_fields() -> None:
    """User profile should contain all required fields with correct types."""
    # Arrange
    user_data = {"name": "Alice", "email": "alice@example.com", "age": 30}

    # Act
    profile = UserProfile.from_dict(user_data)

    # Assert - all checks run even if some fail
    with check:
        assert profile.name == "Alice"
    with check:
        assert profile.email == "alice@example.com"
    with check:
        assert profile.age == 30
    with check:
        assert profile.is_active is True


# CORRECT - pytest-check with descriptive messages
def test_search_result_structure() -> None:
    """Search results should have correct structure and values."""
    # Arrange
    index = SearchIndex()
    index.add_documents(sample_documents)

    # Act
    results = index.search("python", limit=5)

    # Assert
    with check:
        assert len(results) <= 5, "Should respect limit"
    with check:
        assert all(r.score >= 0 for r in results), "Scores should be non-negative"
    with check:
        assert results == sorted(results, key=lambda r: r.score, reverse=True), (
            "Results should be sorted by score descending"
        )


# INCORRECT - multiple bare asserts stop at first failure
def test_user_profile_fields() -> None:
    profile = UserProfile.from_dict(user_data)
    assert profile.name == "Alice"      # If this fails...
    assert profile.email == "alice@example.com"  # ...this never runs
    assert profile.age == 30            # ...nor this
```

**When to use pytest-check:**
- Testing multiple independent properties of an object
- Validating structure with several fields
- Any test where seeing all failures at once aids debugging

**When regular assert is fine:**
- Single assertion per test
- Assertions that logically depend on each other (if A fails, B is meaningless)
- Guard assertions in Arrange phase (prefer `pytest.raises` or skip these)

## Test Data Variety

Define test data **inline in each test** so the reader sees inputs and expected outputs together without jumping to fixtures. Vary data across tests to exercise different code paths and edge cases.

```python
# CORRECT - inline data with variety across tests
def test_summarize_scores_with_normal_values() -> None:
    """Summarize should compute mean for typical numeric data."""
    # Arrange - data defined right here, easy to reason about
    df = pl.DataFrame({"score": [85, 92, 78, 95, 88]})

    # Act
    result = summarize_scores(df)

    # Assert
    with check:
        assert result["mean"] == pytest.approx(87.6)


def test_summarize_scores_with_nulls_and_extremes() -> None:
    """Summarize should handle nulls, large values, and negative zero."""
    # Arrange - different data shape exercises different paths
    df = pl.DataFrame({"score": [None, -0.0, 1e15, None, float("inf")]})

    # Act
    result = summarize_scores(df)

    # Assert
    with check:
        assert result["null_count"] == 2


# INCORRECT - same simple integers in every test, no variety
def test_summarize_a():
    df = pl.DataFrame({"score": [1, 2, 3]})
    ...

def test_summarize_b():
    df = pl.DataFrame({"score": [1, 2, 3]})  # identical data!
    ...
```

**What to vary**: column types (strings, dates, floats, booleans), null density, edge values (empty strings, `float("inf")`, `float("nan")`, `-0.0`, very large numbers), and DataFrame shapes (empty, single-row, many-row).

## Fixtures

Fixtures are for **instantiating dependency instances** (database connections, service objects, toolkit instances) — not for defining test data. Test data belongs inline in each test so the reader can see inputs and expected outputs together.

Keep fixtures close to their usage. Use `conftest.py` only for widely shared fixtures.

```python
# CORRECT - fixture for a dependency instance (reusable setup)
@pytest.fixture
def search_index() -> SearchIndex:
    """Create and populate a search index for testing."""
    index = SearchIndex()
    for i, emb in enumerate([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]):
        index.add(f"doc_{i}", emb)
    return index


# CORRECT - test data defined inline, fixture only for the dependency
def test_search_returns_nearest_match(search_index: SearchIndex) -> None:
    """Search should return the nearest embedding."""
    # Arrange - test-specific data defined inline
    query_vector = [0.9, 0.1, 0.0]

    # Act
    results = search_index.search(query_vector, limit=1)

    # Assert
    with check:
        assert results[0].id == "doc_0"


# INCORRECT - fixture used to define test data
@pytest.fixture
def single_vector() -> list[float]:
    return [1.0, 0.0, 0.0]

def test_something(single_vector):  # Data hidden in fixture — define inline instead
    ...


# INCORRECT - fixture used for simple test inputs
@pytest.fixture
def user_data() -> dict:
    return {"name": "Alice", "email": "alice@example.com"}

def test_create_user(user_data):  # Reader must look at fixture to understand test
    ...
```

**When to use a fixture**: The setup creates a stateful object (connection, client, index) that multiple tests share, or requires teardown.

**When NOT to use a fixture**: The data is a simple value, dict, or DataFrame that is specific to the test's scenario.

## Parametrized Tests

Use for testing multiple inputs with the same logic:

```python
# CORRECT - parametrized test with descriptive IDs
@pytest.mark.parametrize(
    ("input_text", "expected_tokens"),
    [
        ("hello world", ["hello", "world"]),
        ("", []),
        ("  spaces  ", ["spaces"]),
        ("UPPERCASE", ["uppercase"]),
    ],
)
def test_tokenize(input_text: str, expected_tokens: list[str]) -> None:
    """Tokenizer should handle various input formats."""
    assert tokenize(input_text) == expected_tokens


# INCORRECT - separate tests for each case
def test_tokenize_simple():
    assert tokenize("hello world") == ["hello", "world"]

def test_tokenize_empty():
    assert tokenize("") == []

def test_tokenize_spaces():
    assert tokenize("  spaces  ") == ["spaces"]
```

## Test Classes

Group related tests in classes. Use fixtures for the dependency instance under test; define test data inline.

```python
from pytest_check import check


class TestDataProcessor:
    """Test suite for DataProcessor class."""

    @pytest.fixture
    def processor(self) -> DataProcessor:
        """Create a DataProcessor instance for testing."""
        return DataProcessor(max_size=1000, validate=True)

    def test_load_data_success(self, processor: DataProcessor) -> None:
        """Test successful data loading with valid input."""
        # Arrange - test data inline so reader sees exactly what's loaded
        sample_data = [
            {"id": 1, "value": 10.5, "name": "Alice"},
            {"id": 2, "value": 20.0, "name": "Bob"},
        ]

        # Act
        processor.load_data(sample_data)

        # Assert - use pytest-check for multiple assertions
        with check:
            assert processor.record_count == 2
        with check:
            assert processor.is_loaded

    def test_load_data_exceeds_max_size(self, processor: DataProcessor) -> None:
        """Test that loading data exceeding max_size raises ValueError."""
        # Arrange
        large_data = [{"id": i} for i in range(2000)]

        # Act/Assert
        with pytest.raises(ValueError, match="exceeds maximum size"):
            processor.load_data(large_data)
```

## Coverage Requirements

| Scope | Target |
|-------|--------|
| Core logic | >= 90% |
| Public APIs | 100% |

## Validation Commands

For full validation (lint + format + type + docstring + tests), use the `validate-code` skill:
```bash
uv run python .claude/scripts/validate_code.py
```

For test-specific commands during development:

| Task | Command |
|------|---------|
| Run all tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov` |
| Run specific test file | `uv run pytest tests/path/to/test_module.py` |
| Run specific test function | `uv run pytest tests/path/to/test_module.py::test_function_name` |
| Run tests matching pattern | `uv run pytest -k "pattern"` |
| Run tests with verbose output | `uv run pytest -v` |
| Run tests and stop on first failure | `uv run pytest -x` |
| Show local variables in tracebacks | `uv run pytest -l` |

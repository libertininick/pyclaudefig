# Example Plan: Text Sanitization Utility

This example demonstrates a **simple feature** (single module, 3 functions). For larger features, scale by adding more phases - see [Scaling for Complex Features](#scaling-for-complex-features) at the end.

---

## Feature Overview
Add a text sanitization utility module to clean and normalize user input before processing in LangChain agents. This feature will provide three functions for common text cleaning operations.

## Goals
- Remove unwanted characters and formatting from text input
- Normalize whitespace and line breaks
- Validate text length and content
- Provide a consistent API for text preprocessing

## Phases

- [ ] [1. Setup: Create module structure](#1-setup-create-module-structure)
- [ ] [2. Function 1: `remove_control_characters`](#2-function-1-remove_control_characters)
- [ ] [3. Function 2: `normalize_whitespace`](#3-function-2-normalize_whitespace)
- [ ] [4. Function 3: `validate_text_length`](#4-function-3-validate_text_length)
- [ ] [5. Integration and finalization](#5-integration-and-finalization)

## Architecture Decisions

### Module Location
**Decision:** Create `src/my_library/utils/text_sanitizer.py`
**Reason:** Groups utility functions together, keeps core logic separate from agent code

### Function Design
**Decision:** Three standalone functions rather than a class
**Reason:** Simple utility functions don't need state or instance methods. Following functional programming principles makes them easier to test and compose.

## Implementation Plan

Follow the **write → test → validate** cycle for each function before moving to the next.

### 1. Setup: Create module structure

**Action:** Create empty module files
- Create `src/my_library/utils/text_sanitizer.py` with module docstring
- Create `tests/utils/test_text_sanitizer.py` with basic structure

**Module docstring:**
```python
"""Text sanitization utilities for cleaning and normalizing user input.

Provides functions for removing control characters, normalizing whitespace,
and validating text length before processing in agents.
"""
```

---

### 2. Function 1: `remove_control_characters`

#### 2.1 Implement the function
**File:** `src/my_library/utils/text_sanitizer.py`

**Implementation requirements:**
- Function signature: `remove_control_characters(text: str) -> str`
- Remove non-printable control characters using regex `[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]`
- Preserve intentional whitespace (\n, \r, \t)
- Handle empty strings (return unchanged)
- Add Google-style docstring with example
- Include type hints

#### 2.2 Test the function
**File:** `tests/utils/test_text_sanitizer.py`

**Use `python-test-writer` sub-agent to create tests covering:**
- Normal text passes through unchanged
- Control characters are removed
- Intentional whitespace (tabs, newlines) is preserved
- Empty string returns empty string
- Unicode text is handled correctly

#### 2.3 Validate the function
**Run validation commands:**
```bash
uv run pytest tests/utils/test_text_sanitizer.py::test_remove_control_characters -v
uv run ty check src/my_library/utils/text_sanitizer.py
uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/utils/text_sanitizer.py
```

**Acceptance criteria:**
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Docstring format is valid
- [ ] Function behaves as expected with edge cases

---

### 3. Function 2: `normalize_whitespace`

#### 3.1 Implement the function
**File:** `src/my_library/utils/text_sanitizer.py`

**Implementation requirements:**
- Function signature: `normalize_whitespace(text: str, max_consecutive: int = 2) -> str`
- Replace multiple spaces with single space
- Normalize line breaks (convert \r\n to \n)
- Limit consecutive line breaks to `max_consecutive` parameter
- Strip leading/trailing whitespace
- Handle empty strings (return unchanged)
- Add Google-style docstring with example
- Include type hints

#### 3.2 Test the function
**File:** `tests/utils/test_text_sanitizer.py`

**Use `python-test-writer` sub-agent to create tests covering:**
- Multiple spaces become single space
- Line breaks are normalized (\r\n → \n)
- Consecutive line breaks respect max_consecutive limit
- Leading/trailing whitespace is stripped
- Empty string returns empty string
- Custom max_consecutive values work correctly

#### 3.3 Validate the function
**Run validation commands:**
```bash
uv run pytest tests/utils/test_text_sanitizer.py::test_normalize_whitespace -v
uv run ty check src/my_library/utils/text_sanitizer.py
uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/utils/text_sanitizer.py
```

**Acceptance criteria:**
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Docstring format is valid
- [ ] Function behaves as expected with edge cases

---

### 4. Function 3: `validate_text_length`

#### 4.1 Implement the function
**File:** `src/my_library/utils/text_sanitizer.py`

**Implementation requirements:**
- Function signature: `validate_text_length(text: str, min_length: int = 1, max_length: int = 10000) -> str`
- Check text is within length bounds
- Raise `ValueError` with clear message if validation fails (include actual and expected lengths)
- Return text unchanged if valid
- Add Google-style docstring with example
- Include type hints

#### 4.2 Test the function
**File:** `tests/utils/test_text_sanitizer.py`

**Use `python-test-writer` sub-agent to create tests covering:**
- Text within bounds passes validation
- Text below min_length raises ValueError
- Text above max_length raises ValueError
- Error messages include actual and expected lengths
- Empty string validation with min_length=0
- Custom min/max values work correctly
- Boundary conditions (exactly min_length, exactly max_length)

#### 4.3 Validate the function
**Run validation commands:**
```bash
uv run pytest tests/utils/test_text_sanitizer.py::test_validate_text_length -v
uv run ty check src/my_library/utils/text_sanitizer.py
uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/utils/text_sanitizer.py
```

**Acceptance criteria:**
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Docstring format is valid
- [ ] Function behaves as expected with edge cases
- [ ] Error messages are clear and helpful

---

### 5. Integration and finalization

#### 5.1 Add integration test
**File:** `tests/utils/test_text_sanitizer.py`

**Use `python-test-writer` sub-agent to create integration test:**
- Chain all three functions together
- Verify they compose correctly
- Test realistic workflow: messy input → all sanitizers → clean output

#### 5.2 Update package exports (if needed)
**File:** `src/my_library/utils/__init__.py`

- Add imports for the three new functions
- Update `__all__` list if it exists

#### 5.3 Format and final validation
**Run final validation commands:**
```bash
uv run ruff check --fix && uv run ruff format
uv run pytest tests/utils/test_text_sanitizer.py -v
uv run ty check .
uv tool run pydoclint --style=google --allow-init-docstring=True src/my_library/utils/
```

**Final acceptance criteria:**
- [ ] All tests pass (individual + integration)
- [ ] Code is properly formatted
- [ ] Type checking passes
- [ ] Docstrings are valid
- [ ] Module exports are updated

## Non-Goals (Out of Scope)
- HTML/XML sanitization (use existing libraries like bleach)
- Language detection or translation
- Advanced text normalization (Unicode normalization forms)
- Performance optimization for very large texts

## Future Considerations
- If used frequently in prompts, could add a LangChain utility function
- Could extend with additional sanitizers as needed
- Monitor for performance issues with large texts

## Files to Create
1. `src/my_library/utils/text_sanitizer.py` - Main implementation (created in step 1, populated iteratively)
2. `tests/utils/test_text_sanitizer.py` - Test suite (created in step 1, populated iteratively)

## Files to Modify
1. `src/my_library/utils/__init__.py` - Add exports (step 5.2, if file exists)

## Summary of Validation Points

Each function goes through validation before moving to the next:
- **After each function:** Tests pass, types check, docstrings valid
- **Final validation:** All tests pass, code formatted, integration works

This iterative approach ensures each piece is solid before building the next.

---

## Scaling for Complex Features

This template scales naturally for features of any complexity. Here's how to adapt it:

### Simple Features (1-5 functions, single module)
Use the pattern shown above: one phase per function with write → test → validate cycles.

### Medium Features (multiple modules, classes, or APIs)
Organize by **component** rather than function:
- **Phase 1:** Core data models/types
- **Phase 2:** Primary business logic module
- **Phase 3:** Secondary module (depends on Phase 2)
- **Phase 4:** API layer or integration
- **Phase 5:** End-to-end validation

Each phase follows the same write → test → validate pattern, but at the module or component level.

### Complex Features (multi-module systems, external integrations)
Add additional structure:
- **Explicit dependencies** between phases
- **Architecture Analysis** section documenting current state and proposed changes
- **Design Decisions** section for key technical choices with rationale
- **File Inventory** listing all files to create/modify/delete
- **Integration phases** between major components
- **Performance and security considerations**

See `example-refactor.md` for a comprehensive template structure suitable for complex features.

### Key Principles (Any Complexity)
1. **One phase = one complete, testable component** (function, class, module, or integration)
2. **Write → Test → Validate** cycle for each phase
3. **Dependencies must be explicit** - Phase N shouldn't start until its dependencies complete
4. **Final phase is always E2E validation** - verify all components work together
5. **Acceptance criteria are specific and measurable** - no vague "works correctly" statements

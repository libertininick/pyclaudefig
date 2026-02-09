# Example PR: Extract Validation Logic into Separate Module

## PR Title

```
refactor: Extract validation logic into dedicated validators module
```

---

## Summary

Extracts validation logic from the monolithic `processor.py` (800+ lines) into a dedicated `validators/` module with focused, single-responsibility classes. This improves testability, enables reuse of validators across different processors, and reduces cognitive load when working with processing code. No behavioral changes - all existing tests pass without modification.

## What's Included

**Source Code:**
- `src/my_library/pipeline/validators/__init__.py` - New module exports
- `src/my_library/pipeline/validators/schema.py` - Schema validation (extracted from processor.py)
- `src/my_library/pipeline/validators/type_coercion.py` - Type coercion validation (extracted)
- `src/my_library/pipeline/validators/constraints.py` - Constraint validation (extracted)
- `src/my_library/pipeline/validators/base.py` - Base validator protocol and utilities
- `src/my_library/pipeline/processor.py` - Removed validation logic, now imports from validators

**Tests:**
- `tests/pipeline/validators/test_schema.py` - Dedicated tests for schema validator
- `tests/pipeline/validators/test_type_coercion.py` - Dedicated tests for type coercion
- `tests/pipeline/validators/test_constraints.py` - Dedicated tests for constraints
- `tests/pipeline/test_processor.py` - Unchanged (validates no behavioral changes)

**Documentation:**
- `docs/pipeline/validators.md` - New documentation for validators module
- `docs/pipeline/processor.md` - Updated to reference validators module

**Configuration:**
- No changes

## Key Design Decisions

1. **Protocol-based validator interface**: Used `typing.Protocol` to define `Validator` interface rather than ABC. This allows duck-typing and doesn't require inheritance, making it easier to create ad-hoc validators for testing.

2. **One file per validator type**: Separated schema, type coercion, and constraint validation into distinct files. While this increases file count, each file is now <150 lines and has a single responsibility.

3. **Preserved public API**: The `processor.py` public interface is unchanged. Validators are an internal detail - external code continues to use `Processor.validate()` as before.

4. **Moved tests alongside code**: Created `tests/pipeline/validators/` mirroring the source structure. Old validation tests in `test_processor.py` remain to verify integration still works.

## Critical Areas for Review

1. **`src/my_library/pipeline/validators/base.py`** - The `Validator` protocol definition. This is the contract all validators must follow. Please verify the interface is minimal and doesn't leak implementation details.

2. **`src/my_library/pipeline/processor.py:L45-L60`** - The integration point where processor calls validators. Verify the orchestration logic is correct and validators are called in the right order.

3. **Import structure** - Please verify no circular imports were introduced. The dependency direction should be: `processor` -> `validators` (never the reverse).

## Breaking Changes

**Internal breaking changes only** (no public API changes):

- `processor._validate_schema()` - Removed (now use `validators.SchemaValidator`)
- `processor._validate_types()` - Removed (now use `validators.TypeCoercionValidator`)
- `processor._coerce_constraints()` - Removed (now use `validators.ConstraintValidator`)

These were private methods (underscore prefix) and should not be used by external code.

## Testing Notes

To verify no behavioral changes:

```bash
# All existing processor tests should pass unchanged
uv run pytest tests/pipeline/test_processor.py -v

# New validator tests
uv run pytest tests/pipeline/validators/ -v

# Full pipeline test suite
uv run pytest tests/pipeline/ -v
```

---

## Why This Example Works

This example demonstrates:

1. **Clear scope**: States exactly what's being restructured and why
2. **Behavior preservation**: Emphasizes "no behavioral changes"
3. **Design rationale**: Explains architectural decisions (protocols vs ABC, file structure)
4. **API stability**: Documents that public API is unchanged
5. **Internal breaking changes**: Documents private changes for team awareness
6. **Verification instructions**: Shows how to confirm refactor correctness

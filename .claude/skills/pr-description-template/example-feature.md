# Example PR: Add Batch Processing for Data Pipeline

## PR Title

```
feat: Add batch processing for data pipeline
```

---

## Summary

Adds batch processing support for the data pipeline, enabling processing of up to 10,000 records in a single operation. This addresses the performance bottleneck reported in issue #123 where large datasets caused timeouts. The implementation uses chunked processing with configurable batch sizes and includes automatic retry logic for transient failures.

## What's Included

**Source Code:**
- `src/my_library/pipeline/batch_processor.py` - New batch processing module with `BatchProcessor` class
- `src/my_library/pipeline/processor.py` - Updated to support batch mode via `batch_size` parameter
- `src/my_library/pipeline/retry.py` - New retry logic with exponential backoff
- `src/my_library/pipeline/__init__.py` - Export new public APIs

**Tests:**
- `tests/pipeline/test_batch_processor.py` - Unit tests for `BatchProcessor` class
- `tests/pipeline/test_processor_batch_mode.py` - Integration tests for batch processing
- `tests/pipeline/test_retry.py` - Unit tests for retry logic

**Documentation:**
- `docs/pipeline/batch-processing.md` - Usage guide and configuration options

**Configuration:**
- `pyproject.toml` - No new dependencies required

## Key Design Decisions

1. **Chunked processing over streaming**: Chose chunked processing with in-memory batches over streaming because our data sources don't support cursor-based pagination. Chunked processing gives us better control over memory usage and simpler error recovery.

2. **Configurable batch size with sensible default**: Default batch size of 1,000 records balances memory usage with throughput. Made configurable (100-10,000) to accommodate different deployment environments.

3. **Exponential backoff for retries**: Used exponential backoff (1s, 2s, 4s, max 30s) instead of fixed intervals to prevent thundering herd on transient failures. Max 3 retries before failing the batch.

4. **Fail-fast on validation errors**: Validation errors fail immediately without retry (retries only for transient network/timeout errors). This prevents wasting resources on data that will never succeed.

## Critical Areas for Review

1. **`src/my_library/pipeline/batch_processor.py:L45-L78`** - Core batch chunking logic. Please verify the boundary conditions are correct, especially for the last partial batch.

2. **`src/my_library/pipeline/retry.py:L20-L35`** - Exception classification logic that determines which errors trigger retries. Important for reliability - wrong classification could cause infinite retries or premature failures.

3. **Memory management** - The `BatchProcessor` holds one chunk in memory at a time. For 10K records with our average record size of 2KB, peak memory is ~20MB. Please verify this is acceptable for production.

## Future Phases

The following capabilities are planned for future PRs:
- **Parallel batch processing**: Process multiple batches concurrently (blocked on thread-safety audit)
- **Progress reporting**: Callback hooks for progress tracking in long-running jobs
- **Checkpoint/resume**: Save progress to enable resumption after failures

---

## Why This Example Works

This example demonstrates:

1. **Clear summary**: States what, why, and how in 3 sentences
2. **Organized file list**: Grouped by category, brief descriptions
3. **Numbered decisions**: Easy to reference in review comments ("re: decision #2, should we...")
4. **Specific review areas**: Line numbers, memory concerns, clear reasoning
5. **Future context**: Helps reviewers understand what's intentionally deferred

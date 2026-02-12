---
name: fetch-docs
description: Fetch framework documentation when uncertain about APIs. Use when you need up-to-date docs for approved frameworks.
user-invocable: true
argument-hint: <framework-or-query>
---

# Fetch Documentation

Fetch up-to-date framework documentation for approved libraries.

## Quick Start

To look up documentation for an approved framework:

1. Find the library's **doc ID** from the `frameworks` skill Quick Reference table
2. Query docs using the doc ID and a specific topic

## Operations

### Query Documentation

Fetch documentation for a known library on a specific topic.

**Required**: Library doc ID (from `frameworks` skill) and a query describing what you need.

```
mcp__context7__query-docs(libraryId="<doc-id>", query="<topic>")
```

**Example**:
```
mcp__context7__query-docs(libraryId="/pydantic/pydantic", query="field validators")
```

### Resolve Library ID

Find the doc ID for a library by name. Use when adding a new framework or when the doc ID is unknown.

```
mcp__context7__resolve-library-id(libraryName="<name>", query="<name> documentation")
```

**Example**:
```
mcp__context7__resolve-library-id(libraryName="httpx", query="httpx documentation")
```

## When to Use

| Situation | Action |
|-----------|--------|
| Uncertain about an API for an approved framework | Query docs using its doc ID |
| Adding a new framework (`/add-framework`) | Resolve library ID first, then query docs |
| Need usage examples for a library feature | Query docs with specific topic |

## Important

- **Doc IDs** are stored in the `frameworks` skill Quick Reference table
- Always prefer querying docs over guessing at API details
- If the doc provider returns no results, fall back to `WebSearch`

## Provider Notes

This skill currently uses [Context7](https://context7.com) MCP as its documentation provider. The doc IDs in the `frameworks` skill table (e.g., `/pydantic/pydantic`) are Context7-specific identifiers. To swap providers, update both:

1. **This file** — replace the MCP tool calls with the new provider's API
2. **`frameworks/SKILL.md`** — replace all Doc ID values with the new provider's identifiers

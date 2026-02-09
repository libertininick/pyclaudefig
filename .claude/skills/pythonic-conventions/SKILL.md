---
name: pythonic-conventions
version: 1.1.0
description: Essential Pythonic idioms and conventions. Apply when writing or reviewing Python code to ensure idiomatic patterns like comprehensions, built-in functions, context managers, and unpacking.
user-invocable: false
layers:
  rules: rules.md
  examples: examples.md
---

# Pythonic Conventions

Essential Python idioms that make code more readable, concise, and efficient.

**Layers**:
- `rules.md` - Quick reference and concise rules
- `examples.md` - Detailed code examples

## Quick Reference

| Pattern | Use Instead Of |
|---------|----------------|
| List/dict/set comprehensions | Manual loops to build collections |
| `enumerate()` | Manual index tracking |
| `zip()` | Manual parallel iteration |
| `any()` / `all()` | Loop with flag variable |
| Context managers (`with`) | Manual resource cleanup |
| Unpacking | Index access for known structures |
| `in` operator | Manual membership loops |
| Walrus operator (`:=`) | Separate assignment + condition |
| Generator expressions | List comprehension when iterating once |
| `defaultdict` / `Counter` | Manual dict initialization |

For rules: see `rules.md`
For examples: see `examples.md`

---
name: class-design
version: 1.1.0
description: Python class design conventions for this codebase. Apply when writing or reviewing classes including interfaces, inheritance, composition, and attribute access.
user-invocable: false
layers:
  rules: rules.md
  examples: examples.md
---

# Class Design Conventions

Favor composition over inheritance. Use Protocol classes for interfaces and dependency injection for shared behavior.

**Layers**:
- `rules.md` - Quick reference and decision flow
- `examples.md` - Detailed code examples

## Quick Reference

| Principle | Pattern |
|-----------|---------|
| Interfaces | `Protocol` classes for duck typing |
| Shared behavior | Dependency injection or mixins |
| Inheritance depth | Maximum 2 levels |
| Framework base classes | OK to inherit (`BaseModel`, `nn.Module`) |
| Concrete inheritance | Forbidden—use mixins instead |
| Static methods | Avoid—use module-level functions |
| Internal APIs | Design for extension, not restriction |
| Private attributes | Only to avoid subclass naming conflicts |
| Getters/setters | Use plain attributes instead |

For rules: see `rules.md`
For examples: see `examples.md`

# Class Design: Rules

Favor composition over inheritance. Use Protocol classes for interfaces and dependency injection for shared behavior.

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

---

## Protocol Classes for Interfaces

**Rule**: Use `Protocol` to define interfaces. Enables duck typing with static type checking.

| Use Case | Choice |
|----------|--------|
| Define interface for type checking | `Protocol` |
| Duck typing with static analysis | `Protocol` |
| Need `isinstance()` checks at runtime | `ABC` with `@runtime_checkable` |
| Framework requires inheritance | `ABC` |

---

## Composition via Dependency Injection

**Rule**: Inject dependencies rather than inheriting behavior.

- Dependencies are explicit and visible in `__init__`
- Easy to test with fakes/mocks
- Clear ownership of behavior

---

## Inheritance Rules

### Maximum Depth: 2 Levels

```
BaseClass → ChildClass  ✅ OK
BaseClass → ChildClass → GrandchildClass  ❌ Forbidden
```

### Framework Base Classes: Allowed

Inherit from framework base classes that provide essential functionality:
- `pydantic.BaseModel`
- `torch.nn.Module`
- `typing.NamedTuple`
- `dataclasses.dataclass`

### Concrete Class Inheritance: Forbidden

Never inherit from concrete (non-abstract, non-framework) classes. Use composition instead.

---

## Mixins for Shared Behavior

**Rule**: Use mixins only when composition isn't practical.

Mixins must:
- Be small and focused on one capability
- Not maintain state
- Use clear naming (`*Mixin` suffix)

---

## Avoid Static Methods

**Rule**: Use module-level functions instead of `@staticmethod`.

Why:
- Static methods don't use class or instance state
- Module functions are simpler and more Pythonic
- Easier to import and test

---

## Plain Attributes Over Getters/Setters

**Rule**: Use plain attributes. Add `@property` only for computed values or validation.

---

## Decision Flow

```
Need to define an interface?
├── Yes → Use Protocol
└── No → Need shared behavior?
    ├── Yes → Can inject as dependency?
    │   ├── Yes → Use composition (dependency injection)
    │   └── No → Use a focused Mixin
    └── No → Inheriting from framework base class?
        ├── Yes → OK (BaseModel, nn.Module, etc.)
        └── No → Is it concrete?
            ├── Yes → Forbidden - refactor to composition
            └── No → OK if depth ≤ 2 levels
```

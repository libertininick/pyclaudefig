# Pythonic Conventions: Rules

Essential Python idioms. For examples, see `examples.md`.

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

---

## Comprehensions

**Use comprehensions** to build lists, dicts, and sets. More readable and often faster.

- **List**: `[x ** 2 for x in range(10)]`
- **Dict**: `{name: len(name) for name in names}`
- **Set**: `{len(word) for word in words}`

**Avoid** when logic is complex (nested loops + multiple conditions). Use explicit loops instead.

---

## Built-in Functions

| Function | Purpose | Pattern |
|----------|---------|---------|
| `enumerate()` | Index + value | `for i, item in enumerate(items)` |
| `zip()` | Parallel iteration | `for a, b in zip(list1, list2, strict=True)` |
| `any()` | Any element matches | `any(x < 0 for x in nums)` |
| `all()` | All elements match | `all(x > 0 for x in nums)` |
| `sum()` | Sum with generator | `sum(item.value for item in items)` |
| `sorted()` | Sort with key | `sorted(items, key=lambda x: x.name)` |

---

## Context Managers

Always use `with` for resource management:

```python
with open("file.txt") as f:
    data = f.read()
```

Common uses: files, locks, database cursors, temporary directories.

---

## Unpacking

- **Tuple/list**: `x, y = point`
- **Swap**: `a, b = b, a`
- **Extended**: `first, *rest = items`
- **Dict merge**: `{**defaults, **overrides}`
- **In loops**: `for key, value in pairs:`

---

## Membership Testing

Use `in` operator, not loops:

```python
found = target in items
if role in {"admin", "moderator"}:
    ...
```

---

## Walrus Operator

Use `:=` to avoid redundant calls:

```python
if match := pattern.search(text):
    process(match.group())
```

---

## Generators

Use generator expressions (no brackets) when iterating once:

```python
total = sum(x ** 2 for x in range(1_000_000))
```

---

## Collections Module

| Class | Purpose |
|-------|---------|
| `defaultdict(list)` | Auto-initialize missing keys |
| `Counter(items)` | Count occurrences |

---

## String Operations

- **Join**: `" ".join(words)` not concatenation in loop
- **F-strings**: `f"Hello, {name}!"` not `.format()` or `%`

---

## Boolean Expressions

| Pattern | Instead Of |
|---------|------------|
| `if items:` | `if len(items) > 0:` |
| `if not items:` | `if len(items) == 0:` |
| `if value is None:` | `if value == None:` |
| `if 0 < x < 10:` | `if x > 0 and x < 10:` |

---

## Conditional Expressions

```python
value = x if condition else y
```

---

## Dictionary Operations

- **Get with default**: `d.get(key, default)`
- **Lazy init**: Use `defaultdict` over `setdefault`

---

## Exception Handling

- **EAFP** (Easier to Ask Forgiveness): Try/except over if checks
- **Specific exceptions**: Catch `ValueError`, not bare `except:`

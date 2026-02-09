---
name: plan
version: 1.0.0
description: Create comprehensive implementation plan before coding
depends_on_agents:
  - planner
---

# Create Implementation Plan

Create a comprehensive implementation plan for: $ARGUMENTS

> If `$ARGUMENTS` is `--help`, show only the **Usage** and **Examples** sections below, then stop.

## What This Does

This command invokes the **planner agent** to create a detailed, actionable implementation plan **before writing any code**.

The planner will:
1. **Analyze requirements** - Clarify what needs to be built and ask questions if unclear
2. **Explore codebase** - Review existing patterns, conventions, and similar implementations
3. **Design solution** - Break down implementation into phases with specific, testable steps
4. **Create plan document** - Write comprehensive plan to `.claude/agent-outputs/plans/<YYYY-MM-DDTHHmmssZ>-<scope>-plan.md`
5. **Iterate with feedback** - Refine plan based on your input until approved

## When to Use This Command

Use `/plan` when starting:
- ✅ New features or capabilities
- ✅ Significant architectural changes
- ✅ Complex refactoring work
- ✅ Comprehensive bug fixes affecting multiple components

**Skip planning for**:
- ❌ Simple one-line fixes
- ❌ Trivial updates or typos
- ❌ Pure research tasks (use exploration agents instead)

## Usage

```
/plan <description of what to build>
```

## Examples

```
/plan Add JWT-based authentication to the API endpoints
/plan Refactor the parser module to support async operations
/plan Fix race condition in the background task queue
```

## What You Get

A complete plan document containing:
- **Requirements Analysis**: Functional and non-functional requirements, assumptions, constraints
- **Architecture Review**: Current state, proposed changes, design decisions
- **File Inventory**: Files to create, modify, or delete
- **Implementation Steps**: Organized by phase with specific actions and validation criteria
- **Testing Requirements**: Unit tests, integration tests, performance tests
- **Acceptance Criteria**: Measurable success criteria for QA validation

## Plan Document Structure

Plans are organized by **phases**, where each phase = one complete feature/function/component:

```
Phase 1: Feature A
  ├── Implementation Steps (write the code)
  ├── Test Steps (write unit tests)
  ├── Integration Tests (verify compatibility)
  └── Validation Steps (verify quality)

Phase 2: Feature B
  └── [same structure]

Phase N: End-to-End Validation
  └── Verify all phases work together
```

## After Planning

Once the plan is approved, use:
- **`/implement <phase-number> from <plan-path>`** - Implement specific phase(s) from the plan
- Or **manually reference** the plan document when implementing

## CRITICAL: Planner Does NOT Write Code

The planner agent:
- ✅ Creates detailed plans with step-by-step instructions
- ✅ Identifies files, functions, and validation criteria
- ✅ Asks clarifying questions and iterates on feedback
- ❌ **Does NOT write any implementation code**
- ❌ **Does NOT write tests**
- ❌ **Does NOT make any code changes**

The plan serves as the **source of truth** for coding agents to follow.

---

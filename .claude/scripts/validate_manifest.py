#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the Claude Code manifest.json file.

This script validates the structure and contents of the manifest.json file,
checking for required fields, valid references, and correct formatting.

Usage:
    uv run python .claude/scripts/validate_manifest.py

Exit codes:
    0 - Manifest is valid
    1 - Validation errors found
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Final

CLAUDE_DIR: Final[Path] = Path(__file__).parent.parent
MANIFEST_PATH: Final[Path] = CLAUDE_DIR / "manifest.json"

SEMVER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d+\.\d+\.\d+$")

SKILL_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset({
    "name",
    "category",
    "description",
    "user_invocable",
    "version",
})

AGENT_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset({
    "name",
    "description",
    "model",
    "version",
    "depends_on_skills",
})

COMMAND_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset({
    "name",
    "description",
    "version",
})


def load_manifest() -> dict[str, Any] | None:
    """Load and parse the manifest.json file.

    Returns:
        dict[str, Any] | None: The parsed manifest data, or None if parsing
            fails.
    """
    try:
        with MANIFEST_PATH.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON syntax error: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"Manifest file not found: {MANIFEST_PATH}", file=sys.stderr)
        return None


def is_valid_semver(version: str) -> bool:
    """Check if a version string matches semver format (e.g., '1.0.0').

    Args:
        version (str): The version string to validate.

    Returns:
        bool: True if version matches semver format.
    """
    return bool(SEMVER_PATTERN.match(version))


def validate_required_fields(
    entry: dict[str, Any],
    required_fields: frozenset[str],
    entry_type: str,
    entry_name: str,
) -> list[str]:
    """Validate that an entry has all required fields.

    Args:
        entry (dict[str, Any]): The entry dictionary to validate.
        required_fields (frozenset[str]): Set of required field names.
        entry_type (str): Type of entry (e.g., 'skill', 'agent', 'command').
        entry_name (str): Name of the entry for error messages.

    Returns:
        list[str]: List of validation error messages.
    """
    missing_fields = required_fields - set(entry.keys())
    if missing_fields:
        return [f"{entry_type} '{entry_name}' missing required fields: {', '.join(sorted(missing_fields))}"]
    return []


def validate_version_format(
    entry: dict[str, Any],
    entry_type: str,
    entry_name: str,
) -> list[str]:
    """Validate that an entry's version field has semver format.

    Args:
        entry (dict[str, Any]): The entry dictionary to validate.
        entry_type (str): Type of entry (e.g., 'skill', 'agent', 'command').
        entry_name (str): Name of the entry for error messages.

    Returns:
        list[str]: List of validation error messages.
    """
    version = entry.get("version")
    if version is not None and not is_valid_semver(str(version)):
        return [f"{entry_type} '{entry_name}' has invalid version format: '{version}' (expected semver like '1.0.0')"]
    return []


def validate_skills(
    manifest: dict[str, Any],
    valid_categories: set[str],
) -> tuple[list[str], set[str]]:
    """Validate all skills in the manifest.

    Checks for duplicate names, required fields, version format, and valid
    categories.

    Args:
        manifest (dict[str, Any]): The manifest data.
        valid_categories (set[str]): Set of valid category names.

    Returns:
        tuple[list[str], set[str]]: Tuple of (errors, skill_names).
    """
    errors: list[str] = []
    skill_names: set[str] = set()
    skills = manifest.get("skills", [])

    for skill in skills:
        skill_name = skill.get("name", "<unnamed>")

        # Check for duplicate names
        if skill_name in skill_names:
            errors.append(f"Duplicate skill name: '{skill_name}'")
        skill_names.add(skill_name)

        # Check required fields
        errors.extend(validate_required_fields(skill, SKILL_REQUIRED_FIELDS, "Skill", skill_name))

        # Check version format
        errors.extend(validate_version_format(skill, "Skill", skill_name))

        # Check category is valid
        category = skill.get("category")
        if category is not None and category not in valid_categories:
            errors.append(
                f"Skill '{skill_name}' has invalid category: '{category}' "
                f"(valid: {', '.join(sorted(valid_categories))})"
            )

    return errors, skill_names


def validate_agents(
    manifest: dict[str, Any],
    valid_skill_names: set[str],
) -> tuple[list[str], set[str]]:
    """Validate all agents in the manifest.

    Checks for duplicate names, required fields, version format, and valid
    dependency references.

    Args:
        manifest (dict[str, Any]): The manifest data.
        valid_skill_names (set[str]): Set of valid skill names for dependency
            checking.

    Returns:
        tuple[list[str], set[str]]: Tuple of (errors, agent_names).
    """
    errors: list[str] = []
    agent_names: set[str] = set()
    agents = manifest.get("agents", [])

    for agent in agents:
        agent_name = agent.get("name", "<unnamed>")

        # Check for duplicate names
        if agent_name in agent_names:
            errors.append(f"Duplicate agent name: '{agent_name}'")
        agent_names.add(agent_name)

        # Check required fields
        errors.extend(validate_required_fields(agent, AGENT_REQUIRED_FIELDS, "Agent", agent_name))

        # Check version format
        errors.extend(validate_version_format(agent, "Agent", agent_name))

        # Check depends_on_skills references existing skills
        depends_on = agent.get("depends_on_skills", [])
        for dep in depends_on:
            if dep not in valid_skill_names:
                errors.append(f"Agent '{agent_name}' depends on unknown skill: '{dep}'")

    return errors, agent_names


def _validate_dependency_references(
    dependencies: list[str],
    valid_names: set[str],
    entry_name: str,
    dependency_type: str,
) -> list[str]:
    """Validate that all dependencies reference existing entries.

    Args:
        dependencies (list[str]): List of dependency names to check.
        valid_names (set[str]): Set of valid names the dependencies should
            reference.
        entry_name (str): Name of the entry being validated (for error
            messages).
        dependency_type (str): Type of dependency being checked (e.g.,
            'skill', 'agent').

    Returns:
        list[str]: List of validation error messages for unknown dependencies.
    """
    return [
        f"Command '{entry_name}' depends on unknown {dependency_type}: '{dep}'"
        for dep in dependencies
        if dep not in valid_names
    ]


def validate_commands(
    manifest: dict[str, Any],
    valid_skill_names: set[str],
    valid_agent_names: set[str],
) -> list[str]:
    """Validate all commands in the manifest.

    Checks for duplicate names, required fields, version format, and valid
    skill/agent dependency references.

    Args:
        manifest (dict[str, Any]): The manifest data.
        valid_skill_names (set[str]): Set of valid skill names for dependency
            checking.
        valid_agent_names (set[str]): Set of valid agent names for dependency
            checking.

    Returns:
        list[str]: List of validation error messages.
    """
    errors: list[str] = []
    command_names: set[str] = set()
    commands = manifest.get("commands", [])

    for command in commands:
        command_name = command.get("name", "<unnamed>")

        # Check for duplicate names
        if command_name in command_names:
            errors.append(f"Duplicate command name: '{command_name}'")
        command_names.add(command_name)

        # Check required fields
        errors.extend(validate_required_fields(command, COMMAND_REQUIRED_FIELDS, "Command", command_name))

        # Check version format
        errors.extend(validate_version_format(command, "Command", command_name))

        # Check depends_on_skills references existing skills
        errors.extend(
            _validate_dependency_references(
                command.get("depends_on_skills", []), valid_skill_names, command_name, "skill"
            )
        )

        # Check depends_on_agents references existing agents
        errors.extend(
            _validate_dependency_references(
                command.get("depends_on_agents", []), valid_agent_names, command_name, "agent"
            )
        )

    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate the complete manifest structure.

    Args:
        manifest (dict[str, Any]): The manifest data to validate.

    Returns:
        list[str]: List of all validation error messages.
    """
    errors: list[str] = []

    # Extract valid categories
    categories = manifest.get("categories", {})
    valid_categories = set(categories.keys())

    # Validate skills and collect names
    skill_errors, valid_skill_names = validate_skills(manifest, valid_categories)
    errors.extend(skill_errors)

    # Validate agents and collect names
    agent_errors, valid_agent_names = validate_agents(manifest, valid_skill_names)
    errors.extend(agent_errors)

    # Validate commands
    command_errors = validate_commands(manifest, valid_skill_names, valid_agent_names)
    errors.extend(command_errors)

    return errors


def main() -> None:
    """Entry point for the manifest validation script."""
    manifest = load_manifest()
    if manifest is None:
        sys.exit(1)
        return  # Unreachable, but helps type narrowing

    errors = validate_manifest(manifest)

    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print("Manifest valid")
    sys.exit(0)


if __name__ == "__main__":
    main()

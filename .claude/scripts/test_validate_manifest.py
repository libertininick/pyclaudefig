"""Tests for the manifest validation script.

This module provides comprehensive tests for validate_manifest.py, covering
valid manifests, invalid JSON, missing fields, invalid categories, missing
dependencies, and duplicate names.
"""

# ruff: noqa: PLR6301, S101 # this is a test module

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import validate_manifest
from pytest_check import check

# region Fixtures


@pytest.fixture
def valid_manifest() -> dict[str, Any]:
    """Provide a valid manifest with all required fields and valid references.

    Returns:
        dict[str, Any]: A complete, valid manifest structure.
    """
    return {
        "categories": {
            "conventions": {"description": "Coding conventions and standards"},
            "utilities": {"description": "Utility skills"},
        },
        "skills": [
            {
                "name": "naming-conventions",
                "category": "conventions",
                "description": "Python naming conventions",
            },
            {
                "name": "run-python-safely",
                "category": "utilities",
                "description": "Execute Python safely",
            },
        ],
        "agents": [
            {
                "name": "python-code-writer",
                "description": "Writes Python code",
                "depends_on_skills": ["naming-conventions"],
            },
        ],
        "commands": [
            {
                "name": "clean",
                "description": "Clean Python code",
                "depends_on_skills": ["naming-conventions"],
                "depends_on_agents": ["python-code-writer"],
            },
        ],
    }


@pytest.fixture
def manifest_file(tmp_path: Path, valid_manifest: dict[str, Any]) -> Path:
    """Create a temporary manifest file.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.
        valid_manifest (dict[str, Any]): The valid manifest fixture.

    Returns:
        Path: Path to the temporary manifest file.
    """
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(valid_manifest, indent=2))
    return manifest_path


# endregion

# region Test: Valid Manifest


class TestValidManifest:
    """Tests for valid manifest validation."""

    def test_validate_manifest_valid_returns_no_errors(
        self, valid_manifest: dict[str, Any]
    ) -> None:
        """Valid manifest should return empty error list.

        Args:
            valid_manifest (dict[str, Any]): Valid manifest fixture.
        """
        # Act
        errors = validate_manifest.validate_manifest(valid_manifest)

        # Assert
        assert errors == []

    def test_validate_manifest_empty_lists_returns_no_errors(self) -> None:
        """Manifest with empty skills/agents/commands should be valid."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [],
            "agents": [],
            "commands": [],
        }

        # Act
        errors = validate_manifest.validate_manifest(manifest)

        # Assert
        assert errors == []

    def test_validate_manifest_missing_top_level_keys_returns_no_errors(self) -> None:
        """Manifest missing optional top-level keys should be valid."""
        # Arrange
        manifest: dict[str, Any] = {"categories": {}}

        # Act
        errors = validate_manifest.validate_manifest(manifest)

        # Assert
        assert errors == []


# endregion

# region Test: Invalid JSON Syntax


class TestInvalidJsonSyntax:
    """Tests for invalid JSON syntax detection."""

    def test_load_manifest_invalid_json_returns_none(self, tmp_path: Path) -> None:
        """Invalid JSON syntax should return None from load_manifest.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{invalid json: without quotes}")

        # Act
        result = validate_manifest.load_manifest(manifest_path)

        # Assert
        assert result is None

    def test_load_manifest_file_not_found_returns_none(self, tmp_path: Path) -> None:
        """Missing manifest file should return None from load_manifest.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent_path = tmp_path / "nonexistent.json"

        # Act
        result = validate_manifest.load_manifest(nonexistent_path)

        # Assert
        assert result is None

    def test_load_manifest_valid_json_returns_dict(
        self, manifest_file: Path, valid_manifest: dict[str, Any]
    ) -> None:
        """Valid JSON file should return parsed dictionary.

        Args:
            manifest_file (Path): Temporary manifest file fixture.
            valid_manifest (dict[str, Any]): Valid manifest fixture.
        """
        # Act
        result = validate_manifest.load_manifest(manifest_file)

        # Assert
        assert result == valid_manifest


# endregion

# region Test: Missing Required Fields


class TestMissingRequiredFields:
    """Tests for detection of missing required fields."""

    def test_validate_skills_missing_name_returns_error(self) -> None:
        """Skill missing 'name' field should produce error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "category": "conventions",
                    "description": "Test skill",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "missing required fields" in errors[0]
        with check:
            assert "name" in errors[0]

    def test_validate_skills_empty_name_passes_validation(self) -> None:
        """Skill with empty string name passes required-fields check (key exists)."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "",
                    "category": "conventions",
                    "description": "Test skill",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert errors == []

    def test_validate_skills_missing_description_returns_error(self) -> None:
        """Skill missing description field should list missing field."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": "conventions",
                    # Missing: description
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]

    def test_validate_skills_missing_multiple_fields_returns_all_errors(self) -> None:
        """Skill missing multiple fields should list all missing fields in one error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    # Missing: category, description
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "category" in errors[0]
        with check:
            assert "description" in errors[0]

    def test_validate_agents_missing_required_fields_returns_error(self) -> None:
        """Agent missing required fields should produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "test-agent",
                    # Missing: description, depends_on_skills
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_agents(manifest, set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]
        with check:
            assert "depends_on_skills" in errors[0]

    def test_validate_commands_missing_required_fields_returns_error(self) -> None:
        """Command missing required fields should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    # Missing: description
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]


# endregion

# region Test: Invalid Categories


class TestInvalidCategories:
    """Tests for detection of invalid skill categories."""

    def test_validate_skills_invalid_category_returns_error(self) -> None:
        """Skill with invalid category should produce error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": "nonexistent-category",
                    "description": "Test skill",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "invalid category" in errors[0]
        with check:
            assert "nonexistent-category" in errors[0]
        with check:
            assert "conventions" in errors[0]  # Lists valid categories

    def test_validate_skills_valid_category_returns_no_error(self) -> None:
        """Skill with valid category should not produce category error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": "conventions",
                    "description": "Test skill",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert errors == []

    def test_validate_skills_none_category_returns_no_error(self) -> None:
        """Skill with None category passes validation (category check skips None)."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": None,
                    "description": "Test skill",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert errors == []


# endregion

# region Test: Missing Dependencies


class TestMissingDependencies:
    """Tests for detection of missing dependency references."""

    def test_validate_agents_unknown_skill_dependency_returns_error(self) -> None:
        """Agent depending on unknown skill should produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "test-agent",
                    "description": "Test agent",
                    "depends_on_skills": ["nonexistent-skill"],
                }
            ],
        }
        valid_skill_names = {"existing-skill"}

        # Act
        errors, _ = validate_manifest.validate_agents(manifest, valid_skill_names)

        # Assert
        assert len(errors) == 1
        with check:
            assert "unknown skill" in errors[0]
        with check:
            assert "nonexistent-skill" in errors[0]

    def test_validate_agents_valid_skill_dependency_returns_no_error(self) -> None:
        """Agent depending on existing skill should not produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "test-agent",
                    "description": "Test agent",
                    "depends_on_skills": ["existing-skill"],
                }
            ],
        }
        valid_skill_names = {"existing-skill"}

        # Act
        errors, _ = validate_manifest.validate_agents(manifest, valid_skill_names)

        # Assert
        assert errors == []

    def test_validate_commands_unknown_skill_dependency_returns_error(self) -> None:
        """Command depending on unknown skill should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    "description": "Test command",
                    "depends_on_skills": ["nonexistent-skill"],
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(
            manifest, {"existing-skill"}, set()
        )

        # Assert
        assert len(errors) == 1
        with check:
            assert "unknown skill" in errors[0]
        with check:
            assert "nonexistent-skill" in errors[0]

    def test_validate_commands_unknown_agent_dependency_returns_error(self) -> None:
        """Command depending on unknown agent should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    "description": "Test command",
                    "depends_on_agents": ["nonexistent-agent"],
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(
            manifest, set(), {"existing-agent"}
        )

        # Assert
        assert len(errors) == 1
        with check:
            assert "unknown agent" in errors[0]
        with check:
            assert "nonexistent-agent" in errors[0]

    def test_validate_commands_multiple_unknown_dependencies_returns_all_errors(
        self,
    ) -> None:
        """Command with multiple unknown dependencies should produce error for each."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    "description": "Test command",
                    "depends_on_skills": ["unknown-skill-1", "unknown-skill-2"],
                    "depends_on_agents": ["unknown-agent"],
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), set())

        # Assert
        assert len(errors) == 3
        skill_errors = [e for e in errors if "skill" in e]
        agent_errors = [e for e in errors if "agent" in e]
        with check:
            assert len(skill_errors) == 2
        with check:
            assert len(agent_errors) == 1


# endregion

# region Test: Duplicate Names


class TestDuplicateNames:
    """Tests for detection of duplicate names within a type."""

    def test_validate_skills_duplicate_name_returns_error(self) -> None:
        """Duplicate skill names should produce error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "duplicate-skill",
                    "category": "conventions",
                    "description": "First skill",
                },
                {
                    "name": "duplicate-skill",
                    "category": "conventions",
                    "description": "Second skill",
                },
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "Duplicate skill name" in errors[0]
        with check:
            assert "duplicate-skill" in errors[0]

    def test_validate_agents_duplicate_name_returns_error(self) -> None:
        """Duplicate agent names should produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "duplicate-agent",
                    "description": "First agent",
                    "depends_on_skills": [],
                },
                {
                    "name": "duplicate-agent",
                    "description": "Second agent",
                    "depends_on_skills": [],
                },
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_agents(manifest, set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "Duplicate agent name" in errors[0]
        with check:
            assert "duplicate-agent" in errors[0]

    def test_validate_commands_duplicate_name_returns_error(self) -> None:
        """Duplicate command names should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "duplicate-command",
                    "description": "First command",
                },
                {
                    "name": "duplicate-command",
                    "description": "Second command",
                },
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "Duplicate command name" in errors[0]
        with check:
            assert "duplicate-command" in errors[0]


# endregion

# region Test: Main Function Exit Codes


class TestMainExitCodes:
    """Tests for main() function exit codes."""

    def test_main_valid_manifest_exits_zero(self, manifest_file: Path) -> None:
        """Valid manifest should cause main() to exit with code 0.

        Args:
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act/Assert
        with pytest.raises(SystemExit) as exc_info:
            validate_manifest.main(manifest_file)

        assert exc_info.value.code == 0

    def test_main_invalid_json_exits_one(self, tmp_path: Path) -> None:
        """Invalid JSON should cause main() to exit with code 1.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{invalid json}")

        # Act/Assert
        with pytest.raises(SystemExit) as exc_info:
            validate_manifest.main(manifest_path)

        assert exc_info.value.code == 1

    def test_main_missing_file_exits_one(self, tmp_path: Path) -> None:
        """Missing manifest file should cause main() to exit with code 1.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent_path = tmp_path / "nonexistent.json"

        # Act/Assert
        with pytest.raises(SystemExit) as exc_info:
            validate_manifest.main(nonexistent_path)

        assert exc_info.value.code == 1

    def test_main_validation_errors_exits_one(self, tmp_path: Path) -> None:
        """Manifest with validation errors should cause main() to exit with code 1.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        manifest_path = tmp_path / "manifest.json"
        invalid_manifest = {
            "categories": {},
            "skills": [
                {
                    "name": "test-skill",
                    # Missing required fields
                }
            ],
        }
        manifest_path.write_text(json.dumps(invalid_manifest))

        # Act/Assert
        with pytest.raises(SystemExit) as exc_info:
            validate_manifest.main(manifest_path)

        assert exc_info.value.code == 1


# endregion

# region Test: Helper Functions


class TestHelperFunctions:
    """Tests for the validate_required_fields helper function."""

    def test_validate_required_fields_all_present_returns_empty_list(self) -> None:
        """Entry with all required fields should return empty error list."""
        # Arrange
        entry = {"name": "test", "description": "Test"}
        required_fields = frozenset({"name", "description"})

        # Act
        errors = validate_manifest.validate_required_fields(
            entry, required_fields, "Test", "test-entry"
        )

        # Assert
        assert errors == []

    def test_validate_required_fields_missing_returns_error(self) -> None:
        """Entry missing required fields should return error list."""
        # Arrange
        entry = {"name": "test"}
        required_fields = frozenset({"name", "description"})

        # Act
        errors = validate_manifest.validate_required_fields(
            entry, required_fields, "Test", "test-entry"
        )

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]


# endregion

# region Test: Integration - Full Manifest Validation


class TestFullManifestValidation:
    """Integration tests for complete manifest validation."""

    def test_validate_manifest_cascading_dependencies_valid(self) -> None:
        """Manifest where commands depend on agents that depend on skills should validate."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "skill-a",
                    "category": "conventions",
                    "description": "Skill A",
                },
            ],
            "agents": [
                {
                    "name": "agent-a",
                    "description": "Agent A",
                    "depends_on_skills": ["skill-a"],
                },
            ],
            "commands": [
                {
                    "name": "command-a",
                    "description": "Command A",
                    "depends_on_skills": ["skill-a"],
                    "depends_on_agents": ["agent-a"],
                },
            ],
        }

        # Act
        errors = validate_manifest.validate_manifest(manifest)

        # Assert
        assert errors == []

    def test_validate_manifest_multiple_errors_returns_all(self) -> None:
        """Manifest with multiple issues should return all errors."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "skill-a",
                    "category": "invalid-category",  # Error: invalid category
                    "description": "Skill A",
                },
                {
                    "name": "skill-a",  # Error: duplicate name
                    "category": "conventions",
                    "description": "Duplicate",
                },
            ],
            "agents": [
                {
                    "name": "agent-a",
                    "description": "Agent A",
                    "depends_on_skills": ["nonexistent-skill"],  # Error: unknown skill
                },
            ],
            "commands": [
                {
                    "name": "command-a",
                    # Missing: description  # Error: missing fields
                },
            ],
        }

        # Act
        errors = validate_manifest.validate_manifest(manifest)

        # Assert - should have multiple errors
        with check:
            assert len(errors) == 4
        with check:
            assert any("invalid category" in e for e in errors)
        with check:
            assert any("Duplicate skill name" in e for e in errors)
        with check:
            assert any("unknown skill" in e for e in errors)
        with check:
            assert any("missing required fields" in e for e in errors)


# endregion

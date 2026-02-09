"""Tests for the manifest validation script.

This module provides comprehensive tests for validate_manifest.py, covering
valid manifests, invalid JSON, missing fields, invalid categories, missing
dependencies, duplicate names, and invalid version formats.
"""

# ruff: noqa: PLR6301, S101 # this is a test module

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import validate_manifest
from pytest_check import check

# ============================================================================
# Fixtures
# ============================================================================


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
                "user_invocable": True,
                "version": "1.0.0",
            },
            {
                "name": "run-python-safely",
                "category": "utilities",
                "description": "Execute Python safely",
                "user_invocable": True,
                "version": "2.1.0",
            },
        ],
        "agents": [
            {
                "name": "python-code-writer",
                "description": "Writes Python code",
                "model": "opus",
                "version": "1.0.0",
                "depends_on_skills": ["naming-conventions"],
            },
        ],
        "commands": [
            {
                "name": "clean",
                "description": "Clean Python code",
                "version": "1.0.0",
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


# ============================================================================
# Test: Valid Manifest
# ============================================================================


class TestValidManifest:
    """Tests for valid manifest validation."""

    def test_validate_manifest_valid_returns_no_errors(self, valid_manifest: dict[str, Any]) -> None:
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


# ============================================================================
# Test: Invalid JSON Syntax
# ============================================================================


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
        with patch.object(validate_manifest, "MANIFEST_PATH", manifest_path):
            result = validate_manifest.load_manifest()

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
        with patch.object(validate_manifest, "MANIFEST_PATH", nonexistent_path):
            result = validate_manifest.load_manifest()

        # Assert
        assert result is None

    def test_load_manifest_valid_json_returns_dict(self, manifest_file: Path, valid_manifest: dict[str, Any]) -> None:
        """Valid JSON file should return parsed dictionary.

        Args:
            manifest_file (Path): Temporary manifest file fixture.
            valid_manifest (dict[str, Any]): Valid manifest fixture.
        """
        # Act
        with patch.object(validate_manifest, "MANIFEST_PATH", manifest_file):
            result = validate_manifest.load_manifest()

        # Assert
        assert result == valid_manifest


# ============================================================================
# Test: Missing Required Fields
# ============================================================================


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
                    "user_invocable": True,
                    "version": "1.0.0",
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

    def test_validate_skills_missing_multiple_fields_returns_all_missing(self) -> None:
        """Skill missing multiple fields should list all missing fields."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": "conventions",
                    # Missing: description, user_invocable, version
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]
        with check:
            assert "user_invocable" in errors[0]
        with check:
            assert "version" in errors[0]

    def test_validate_agents_missing_required_fields_returns_error(self) -> None:
        """Agent missing required fields should produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "test-agent",
                    # Missing: description, model, version, depends_on_skills
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
            assert "model" in errors[0]
        with check:
            assert "version" in errors[0]
        with check:
            assert "depends_on_skills" in errors[0]

    def test_validate_commands_missing_required_fields_returns_error(self) -> None:
        """Command missing required fields should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    # Missing: description, version
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "description" in errors[0]
        with check:
            assert "version" in errors[0]


# ============================================================================
# Test: Invalid Categories
# ============================================================================


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
                    "user_invocable": True,
                    "version": "1.0.0",
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
                    "user_invocable": True,
                    "version": "1.0.0",
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert errors == []


# ============================================================================
# Test: Missing Dependencies
# ============================================================================


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
                    "model": "opus",
                    "version": "1.0.0",
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
                    "model": "opus",
                    "version": "1.0.0",
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
                    "version": "1.0.0",
                    "depends_on_skills": ["nonexistent-skill"],
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, {"existing-skill"}, set())

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
                    "version": "1.0.0",
                    "depends_on_agents": ["nonexistent-agent"],
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), {"existing-agent"})

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
                    "version": "1.0.0",
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


# ============================================================================
# Test: Duplicate Names
# ============================================================================


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
                    "user_invocable": True,
                    "version": "1.0.0",
                },
                {
                    "name": "duplicate-skill",
                    "category": "conventions",
                    "description": "Second skill",
                    "user_invocable": True,
                    "version": "1.0.0",
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
                    "model": "opus",
                    "version": "1.0.0",
                    "depends_on_skills": [],
                },
                {
                    "name": "duplicate-agent",
                    "description": "Second agent",
                    "model": "sonnet",
                    "version": "1.0.0",
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
                    "version": "1.0.0",
                },
                {
                    "name": "duplicate-command",
                    "description": "Second command",
                    "version": "1.0.0",
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


# ============================================================================
# Test: Invalid Version Format
# ============================================================================


class TestInvalidVersionFormat:
    """Tests for detection of invalid version formats."""

    @pytest.mark.parametrize(
        ("version", "expected_valid"),
        [
            ("1.0.0", True),
            ("0.0.1", True),
            ("10.20.30", True),
            ("1.0", False),
            ("1", False),
            ("v1.0.0", False),
            ("1.0.0-beta", False),
            ("1.0.0.0", False),
            ("", False),
            ("abc", False),
        ],
    )
    def test_is_valid_semver(self, version: str, *, expected_valid: bool) -> None:
        """Test semver validation with various version formats.

        Args:
            version (str): Version string to validate.
            expected_valid (bool): Whether the version should be valid.
        """
        # Act
        result = validate_manifest.is_valid_semver(version)

        # Assert
        assert result == expected_valid

    def test_validate_skills_invalid_version_returns_error(self) -> None:
        """Skill with invalid version format should produce error."""
        # Arrange
        manifest = {
            "categories": {"conventions": {"description": "Test"}},
            "skills": [
                {
                    "name": "test-skill",
                    "category": "conventions",
                    "description": "Test skill",
                    "user_invocable": True,
                    "version": "v1.0",  # Invalid format
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_skills(manifest, {"conventions"})

        # Assert
        assert len(errors) == 1
        with check:
            assert "invalid version format" in errors[0]
        with check:
            assert "v1.0" in errors[0]

    def test_validate_agents_invalid_version_returns_error(self) -> None:
        """Agent with invalid version format should produce error."""
        # Arrange
        manifest = {
            "agents": [
                {
                    "name": "test-agent",
                    "description": "Test agent",
                    "model": "opus",
                    "version": "1.0",  # Invalid format
                    "depends_on_skills": [],
                }
            ],
        }

        # Act
        errors, _ = validate_manifest.validate_agents(manifest, set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "invalid version format" in errors[0]
        with check:
            assert "1.0" in errors[0]

    def test_validate_commands_invalid_version_returns_error(self) -> None:
        """Command with invalid version format should produce error."""
        # Arrange
        manifest = {
            "commands": [
                {
                    "name": "test-command",
                    "description": "Test command",
                    "version": "latest",  # Invalid format
                }
            ],
        }

        # Act
        errors = validate_manifest.validate_commands(manifest, set(), set())

        # Assert
        assert len(errors) == 1
        with check:
            assert "invalid version format" in errors[0]
        with check:
            assert "latest" in errors[0]


# ============================================================================
# Test: Main Function Exit Codes
# ============================================================================


class TestMainExitCodes:
    """Tests for main() function exit codes."""

    def test_main_valid_manifest_exits_zero(self, manifest_file: Path) -> None:
        """Valid manifest should cause main() to exit with code 0.

        Args:
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act/Assert
        with (
            patch.object(validate_manifest, "MANIFEST_PATH", manifest_file),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_manifest.main()

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
        with (
            patch.object(validate_manifest, "MANIFEST_PATH", manifest_path),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_manifest.main()

        assert exc_info.value.code == 1

    def test_main_missing_file_exits_one(self, tmp_path: Path) -> None:
        """Missing manifest file should cause main() to exit with code 1.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent_path = tmp_path / "nonexistent.json"

        # Act/Assert
        with (
            patch.object(validate_manifest, "MANIFEST_PATH", nonexistent_path),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_manifest.main()

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
        with (
            patch.object(validate_manifest, "MANIFEST_PATH", manifest_path),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_manifest.main()

        assert exc_info.value.code == 1


# ============================================================================
# Test: Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_validate_required_fields_all_present_returns_empty_list(self) -> None:
        """Entry with all required fields should return empty error list."""
        # Arrange
        entry = {"name": "test", "version": "1.0.0", "description": "Test"}
        required_fields = frozenset({"name", "version", "description"})

        # Act
        errors = validate_manifest.validate_required_fields(entry, required_fields, "Test", "test-entry")

        # Assert
        assert errors == []

    def test_validate_required_fields_missing_returns_error(self) -> None:
        """Entry missing required fields should return error list."""
        # Arrange
        entry = {"name": "test"}
        required_fields = frozenset({"name", "version", "description"})

        # Act
        errors = validate_manifest.validate_required_fields(entry, required_fields, "Test", "test-entry")

        # Assert
        assert len(errors) == 1
        with check:
            assert "version" in errors[0]
        with check:
            assert "description" in errors[0]

    def test_validate_version_format_valid_returns_empty_list(self) -> None:
        """Entry with valid version should return empty error list."""
        # Arrange
        entry = {"version": "1.0.0"}

        # Act
        errors = validate_manifest.validate_version_format(entry, "Test", "test-entry")

        # Assert
        assert errors == []

    def test_validate_version_format_missing_returns_empty_list(self) -> None:
        """Entry without version field should return empty error list."""
        # Arrange
        entry: dict[str, Any] = {}

        # Act
        errors = validate_manifest.validate_version_format(entry, "Test", "test-entry")

        # Assert
        assert errors == []

    def test_validate_version_format_invalid_returns_error(self) -> None:
        """Entry with invalid version should return error list."""
        # Arrange
        entry = {"version": "bad-version"}

        # Act
        errors = validate_manifest.validate_version_format(entry, "Test", "test-entry")

        # Assert
        assert len(errors) == 1
        with check:
            assert "invalid version format" in errors[0]
        with check:
            assert "bad-version" in errors[0]

    def test_validate_dependency_references_all_valid_returns_empty_list(self) -> None:
        """Valid dependencies should return empty error list."""
        # Arrange
        dependencies = ["skill-a", "skill-b"]
        valid_names = {"skill-a", "skill-b", "skill-c"}

        # Act
        errors = validate_manifest._validate_dependency_references(dependencies, valid_names, "test-command", "skill")

        # Assert
        assert errors == []

    def test_validate_dependency_references_invalid_returns_errors(self) -> None:
        """Invalid dependencies should return error list."""
        # Arrange
        dependencies = ["skill-a", "unknown-skill"]
        valid_names = {"skill-a"}

        # Act
        errors = validate_manifest._validate_dependency_references(dependencies, valid_names, "test-command", "skill")

        # Assert
        assert len(errors) == 1
        with check:
            assert "unknown skill" in errors[0]
        with check:
            assert "unknown-skill" in errors[0]


# ============================================================================
# Test: Integration - Full Manifest Validation
# ============================================================================


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
                    "user_invocable": True,
                    "version": "1.0.0",
                },
            ],
            "agents": [
                {
                    "name": "agent-a",
                    "description": "Agent A",
                    "model": "opus",
                    "version": "1.0.0",
                    "depends_on_skills": ["skill-a"],
                },
            ],
            "commands": [
                {
                    "name": "command-a",
                    "description": "Command A",
                    "version": "1.0.0",
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
                    "user_invocable": True,
                    "version": "bad",  # Error: invalid version
                },
                {
                    "name": "skill-a",  # Error: duplicate name
                    "category": "conventions",
                    "description": "Duplicate",
                    "user_invocable": True,
                    "version": "1.0.0",
                },
            ],
            "agents": [
                {
                    "name": "agent-a",
                    "description": "Agent A",
                    "model": "opus",
                    "version": "1.0.0",
                    "depends_on_skills": ["nonexistent-skill"],  # Error: unknown skill
                },
            ],
            "commands": [
                {
                    "name": "command-a",
                    # Missing: description, version  # Error: missing fields
                },
            ],
        }

        # Act
        errors = validate_manifest.validate_manifest(manifest)

        # Assert - should have multiple errors
        with check:
            assert len(errors) >= 5  # At least 5 distinct errors
        with check:
            assert any("invalid category" in e for e in errors)
        with check:
            assert any("invalid version format" in e for e in errors)
        with check:
            assert any("Duplicate skill name" in e for e in errors)
        with check:
            assert any("unknown skill" in e for e in errors)
        with check:
            assert any("missing required fields" in e for e in errors)

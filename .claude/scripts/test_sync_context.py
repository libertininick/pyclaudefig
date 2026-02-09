"""Tests for the sync_context script.

This module provides comprehensive tests for sync_context.py, covering
frontmatter parsing, filesystem scanning, manifest operations, CLAUDE.md
section generation, bundle regeneration, and the main entry point.
"""

# ruff: noqa: PLR6301, S101 # this is a test module

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import sync_context
from pytest_check import check
from sync_context import (
    AgentInfo,
    CommandInfo,
    SkillInfo,
    _generate_agents_section,  # noqa: PLC2701
    _generate_bundles_section,  # noqa: PLC2701
    _generate_commands_section,  # noqa: PLC2701
    _generate_skills_section,  # noqa: PLC2701
    generate_claude_md_sections,
    load_manifest,
    parse_frontmatter,
    regenerate_bundles,
    scan_agents,
    scan_commands,
    scan_skills,
    update_claude_md,
    update_manifest,
)

# ============================================================================
# Helpers
# ============================================================================


def _write_skill(skill_dir: Path, frontmatter: str, body: str = "") -> None:
    """Write a SKILL.md file into the given skill directory.

    Args:
        skill_dir (Path): Directory to create SKILL.md in.
        frontmatter (str): YAML frontmatter content (without delimiters).
        body (str): Markdown body content after frontmatter.
    """
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"---\n{frontmatter}\n---\n{body}"
    (skill_dir / "SKILL.md").write_text(content)


def _write_md_file(directory: Path, filename: str, frontmatter: str, body: str = "") -> None:
    """Write a markdown file with frontmatter into the given directory.

    Args:
        directory (Path): Directory to create the file in.
        filename (str): Name of the markdown file.
        frontmatter (str): YAML frontmatter content (without delimiters).
        body (str): Markdown body content after frontmatter.
    """
    directory.mkdir(parents=True, exist_ok=True)
    content = f"---\n{frontmatter}\n---\n{body}"
    (directory / filename).write_text(content)


# ============================================================================
# Test: _parse_value
# ============================================================================


class TestParseValue:
    """Tests for _parse_value private helper that converts frontmatter value strings."""

    @pytest.mark.parametrize(
        ("input_value", "expected"),
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
        ],
    )
    def test_parse_value_boolean_strings_returns_bool(self, *, input_value: str, expected: bool) -> None:
        """Boolean strings should be converted to Python bool regardless of case.

        Args:
            input_value (str): Input string like "true" or "False".
            expected (bool): Expected boolean result.
        """
        # Act
        parsed = sync_context._parse_value(input_value)

        # Assert
        assert parsed is expected

    def test_parse_value_inline_list_returns_list(self) -> None:
        """Bracket-delimited list should be parsed into a Python list of strings."""
        # Act
        parsed = sync_context._parse_value("[alpha, beta, gamma]")

        # Assert
        with check:
            assert isinstance(parsed, list)
        with check:
            assert parsed == ["alpha", "beta", "gamma"]

    def test_parse_value_inline_list_with_quotes_strips_quotes(self) -> None:
        """Quoted items in inline list should have quotes stripped."""
        # Act
        parsed = sync_context._parse_value("[\" alpha \", 'beta']")

        # Assert
        assert parsed == [" alpha ", "beta"]

    def test_parse_value_empty_inline_list_returns_empty_list(self) -> None:
        """Empty bracket list should return an empty list."""
        # Act
        parsed = sync_context._parse_value("[]")

        # Assert
        assert parsed == []

    def test_parse_value_regular_string_returns_string(self) -> None:
        """Non-boolean, non-list values should be returned as-is."""
        # Act
        parsed = sync_context._parse_value("some description text")

        # Assert
        with check:
            assert isinstance(parsed, str)
        with check:
            assert parsed == "some description text"

    def test_parse_value_quoted_string_preserves_quotes(self) -> None:
        """Quoted standalone string should NOT have quotes stripped by _parse_value.

        Quote stripping happens in parse_frontmatter at the key-value level,
        not in _parse_value. This documents that _parse_value is pass-through for quotes.
        """
        # Act
        parsed = sync_context._parse_value('"quoted"')

        # Assert
        assert parsed == '"quoted"'

    @pytest.mark.parametrize(
        ("input_value", "expected"),
        [
            ("", ""),
            (" true ", " true "),
        ],
    )
    def test_parse_value_non_boolean_lookalikes_returns_string(self, *, input_value: str, expected: str) -> None:
        """Empty string and whitespace-padded booleans should pass through as strings.

        Args:
            input_value (str): Input that looks like it could be boolean.
            expected (str): Expected string result (not converted to bool).
        """
        # Act
        parsed = sync_context._parse_value(input_value)

        # Assert
        assert parsed == expected


# ============================================================================
# Test: parse_frontmatter
# ============================================================================


class TestParseFrontmatter:
    """Tests for parse_frontmatter that extracts YAML frontmatter from markdown."""

    def test_parse_frontmatter_valid_content_returns_metadata_and_body(self) -> None:
        """Content with valid frontmatter should return parsed dict and remaining body."""
        # Arrange
        content = "---\nname: my-skill\nversion: 1.0.0\n---\n# Body content"

        # Act
        frontmatter, body = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter["name"] == "my-skill"
        with check:
            assert frontmatter["version"] == "1.0.0"
        with check:
            assert body == "# Body content"

    def test_parse_frontmatter_boolean_values_returns_python_bools(self) -> None:
        """Boolean values in frontmatter should be converted to Python booleans."""
        # Arrange
        content = "---\nuser-invocable: true\ndeprecated: false\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter["user-invocable"] is True
        with check:
            assert frontmatter["deprecated"] is False

    def test_parse_frontmatter_inline_list_returns_python_list(self) -> None:
        """Inline bracket list values should be parsed into Python lists."""
        # Arrange
        content = "---\ndepends_on_skills: [skill-a, skill-b, skill-c]\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        assert frontmatter["depends_on_skills"] == ["skill-a", "skill-b", "skill-c"]

    def test_parse_frontmatter_multiline_list_returns_python_list(self) -> None:
        """Multi-line indented list items should be parsed into a Python list."""
        # Arrange
        content = "---\ndepends_on_skills:\n  - skill-a\n  - skill-b\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        assert frontmatter["depends_on_skills"] == ["skill-a", "skill-b"]

    def test_parse_frontmatter_quoted_values_strips_quotes(self) -> None:
        """Quoted values should have surrounding quotes stripped."""
        # Arrange
        content = "---\nname: \"my-skill\"\ndescription: 'A skill'\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter["name"] == "my-skill"
        with check:
            assert frontmatter["description"] == "A skill"

    def test_parse_frontmatter_no_frontmatter_returns_empty_dict(self) -> None:
        """Content without frontmatter delimiters should return empty dict and full content."""
        # Arrange
        content = "# Just a heading\n\nSome body text."

        # Act
        frontmatter, body = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter == {}
        with check:
            assert body == content

    def test_parse_frontmatter_incomplete_delimiters_returns_empty_dict(self) -> None:
        """Content with only one --- delimiter should return empty dict and full content."""
        # Arrange
        content = "---\nname: my-skill\nNo closing delimiter"

        # Act
        frontmatter, body = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter == {}
        with check:
            assert body == content

    def test_parse_frontmatter_empty_content_returns_empty_dict(self) -> None:
        """Empty string should return empty dict and empty string."""
        # Act
        frontmatter, body = parse_frontmatter("")

        # Assert
        with check:
            assert frontmatter == {}
        with check:
            assert not body

    def test_parse_frontmatter_empty_frontmatter_block_returns_empty_dict(self) -> None:
        """Frontmatter block with no key-value pairs should return empty dict."""
        # Arrange
        content = "---\n---\nBody text"

        # Act
        frontmatter, body = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter == {}
        with check:
            assert body == "Body text"

    def test_parse_frontmatter_colon_in_value_preserves_full_value(self) -> None:
        """Values containing colons (e.g., URLs) should preserve everything after the first colon."""
        # Arrange
        content = "---\ndescription: See http://example.com for details\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        assert frontmatter["description"] == "See http://example.com for details"

    def test_parse_frontmatter_multiline_list_at_end_returns_list(self) -> None:
        """Multi-line list as the last key in frontmatter should be captured correctly."""
        # Arrange
        content = "---\nname: test\nitems:\n  - one\n  - two\n---\nBody"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        with check:
            assert frontmatter["name"] == "test"
        with check:
            assert frontmatter["items"] == ["one", "two"]

    def test_parse_frontmatter_inline_list_with_quoted_items(self) -> None:
        """Inline list with quoted items should survive the full parse pipeline."""
        # Arrange
        content = "---\nitems: [\" alpha \", 'beta']\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert
        assert frontmatter["items"] == [" alpha ", "beta"]

    def test_parse_frontmatter_value_with_apostrophe_at_end(self) -> None:
        """Trailing apostrophe is stripped by the greedy strip in parse_frontmatter."""
        # Arrange
        content = "---\ndescription: It's a test'\n---\n"

        # Act
        frontmatter, _ = parse_frontmatter(content)

        # Assert - documents current behavior: trailing apostrophe is stripped
        assert frontmatter["description"] == "It's a test"


# ============================================================================
# Test: scan_skills
# ============================================================================


class TestScanSkills:
    """Tests for scan_skills that discovers skill metadata from the filesystem."""

    @pytest.fixture(autouse=True)
    def _patch_skills_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch SKILLS_DIR to tmp_path for all tests in this class.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        monkeypatch.setattr(sync_context, "SKILLS_DIR", tmp_path)

    def test_scan_skills_valid_directory_returns_skill_info(self, tmp_path: Path) -> None:
        """Directory with valid SKILL.md files should return populated SkillInfo dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_skill(
            tmp_path / "my-skill",
            "name: my-skill\ndescription: A test skill\nversion: 2.0.0\nuser-invocable: false",
        )

        # Act
        skills = scan_skills()

        # Assert
        with check:
            assert "my-skill" in skills
        with check:
            assert skills["my-skill"].name == "my-skill"
        with check:
            assert skills["my-skill"].description == "A test skill"
        with check:
            assert skills["my-skill"].version == "2.0.0"
        with check:
            assert skills["my-skill"].user_invocable is False

    def test_scan_skills_multiple_skills_returns_all(self, tmp_path: Path) -> None:
        """Directory with multiple skill subdirs should return all of them.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_skill(tmp_path / "alpha", "name: alpha\ndescription: Alpha skill")
        _write_skill(tmp_path / "beta", "name: beta\ndescription: Beta skill")

        # Act
        skills = scan_skills()

        # Assert
        with check:
            assert len(skills) == 2
        with check:
            assert "alpha" in skills
        with check:
            assert "beta" in skills

    def test_scan_skills_empty_directory_returns_empty_dict(self) -> None:
        """Empty skills directory should return empty dict."""
        # Act
        skills = scan_skills()

        # Assert
        assert skills == {}

    def test_scan_skills_nonexistent_directory_returns_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-existent skills directory should return empty dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        nonexistent = tmp_path / "does-not-exist"
        monkeypatch.setattr(sync_context, "SKILLS_DIR", nonexistent)

        # Act
        skills = scan_skills()

        # Assert
        assert skills == {}

    def test_scan_skills_missing_skill_md_skips_directory(self, tmp_path: Path) -> None:
        """Skill subdirectory without SKILL.md should be silently skipped.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        (tmp_path / "no-skill-file").mkdir()
        _write_skill(tmp_path / "valid-skill", "name: valid-skill\ndescription: Valid")

        # Act
        skills = scan_skills()

        # Assert
        with check:
            assert len(skills) == 1
        with check:
            assert "valid-skill" in skills

    def test_scan_skills_no_description_falls_back_to_content_line(self, tmp_path: Path) -> None:
        """Skill without description frontmatter should use first non-header content line.

        The fallback logic iterates all lines of the file (including frontmatter).
        Lines starting with '#' or '-' are skipped. The first non-empty, non-skipped
        line becomes the description -- which is the first frontmatter key-value line.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange - the fallback iterates full file content, so frontmatter
        # lines like "name: no-desc" are candidates (they don't start with # or -)
        _write_skill(
            tmp_path / "no-desc",
            "name: no-desc\nversion: 1.0.0",
            body="\n# Heading\n\nThis is the fallback description line.",
        )

        # Act
        skills = scan_skills()

        # Assert - first non-empty line not starting with # or - is "name: no-desc"
        assert skills["no-desc"].description == "name: no-desc"

    def test_scan_skills_no_description_body_only_text_returns_body_line(self, tmp_path: Path) -> None:
        """Skill without description and with body text should pick up a content line.

        When the frontmatter has no description and the file body has plain text
        lines (not starting with # or -), the first such line from the full content
        is used. If frontmatter keys come first, they win the fallback.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange - create a SKILL.md with no frontmatter at all, so fallback
        # iterates from the body directly
        skill_dir = tmp_path / "plain-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Heading\n\nPlain description text here.")

        # Act
        skills = scan_skills()

        # Assert - first line not starting with # or - is "Plain description text here."
        assert skills["plain-skill"].description == "Plain description text here."

    def test_scan_skills_defaults_name_to_directory_name(self, tmp_path: Path) -> None:
        """Skill without name in frontmatter should default to directory name.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_skill(tmp_path / "dir-name-skill", "description: A skill without a name key")

        # Act
        skills = scan_skills()

        # Assert
        assert "dir-name-skill" in skills

    def test_scan_skills_does_not_propagate_category_from_frontmatter(self, tmp_path: Path) -> None:
        """Category in SKILL.md frontmatter should be ignored; always defaults to 'conventions'.

        The manifest is the source of truth for skill categories, not the SKILL.md file.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_skill(
            tmp_path / "my-skill",
            "name: my-skill\ndescription: Test\ncategory: utilities",
        )

        # Act
        skills = scan_skills()

        # Assert - category should always be the dataclass default, not frontmatter value
        assert skills["my-skill"].category == "conventions"

    def test_scan_skills_file_in_skills_dir_not_subdir_is_skipped(self, tmp_path: Path) -> None:
        """Plain files in the skills directory (not subdirs) should be skipped.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        (tmp_path / "stray-file.md").write_text("Not a skill directory")

        # Act
        skills = scan_skills()

        # Assert
        assert skills == {}


# ============================================================================
# Test: scan_agents
# ============================================================================


class TestScanAgents:
    """Tests for scan_agents that discovers agent metadata from the filesystem."""

    def test_scan_agents_valid_directory_returns_agent_info(self, tmp_path: Path) -> None:
        """Directory with valid agent markdown files should return populated AgentInfo dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(
            tmp_path,
            "my-agent.md",
            "name: my-agent\ndescription: Test agent\nmodel: sonnet\nversion: 1.1.0",
        )

        # Act
        with patch.object(sync_context, "AGENTS_DIR", tmp_path):
            agents = scan_agents()

        # Assert
        with check:
            assert "my-agent" in agents
        with check:
            assert agents["my-agent"].description == "Test agent"
        with check:
            assert agents["my-agent"].model == "sonnet"
        with check:
            assert agents["my-agent"].version == "1.1.0"

    def test_scan_agents_empty_directory_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty agents directory should return empty dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Act
        with patch.object(sync_context, "AGENTS_DIR", tmp_path):
            agents = scan_agents()

        # Assert
        assert agents == {}

    def test_scan_agents_nonexistent_directory_returns_empty_dict(self, tmp_path: Path) -> None:
        """Non-existent agents directory should return empty dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent = tmp_path / "does-not-exist"

        # Act
        with patch.object(sync_context, "AGENTS_DIR", nonexistent):
            agents = scan_agents()

        # Assert
        assert agents == {}

    def test_scan_agents_defaults_name_to_stem(self, tmp_path: Path) -> None:
        """Agent without name in frontmatter should default to file stem.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(tmp_path, "code-writer.md", "description: Writes code\nmodel: opus")

        # Act
        with patch.object(sync_context, "AGENTS_DIR", tmp_path):
            agents = scan_agents()

        # Assert
        assert "code-writer" in agents

    def test_scan_agents_skips_non_md_files(self, tmp_path: Path) -> None:
        """Non-.md files in the agents directory should be ignored.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(tmp_path, "valid-agent.md", "name: valid-agent\ndescription: Valid\nmodel: opus")
        (tmp_path / "notes.txt").write_text("not an agent")
        (tmp_path / "config.json").write_text("{}")

        # Act
        with patch.object(sync_context, "AGENTS_DIR", tmp_path):
            agents = scan_agents()

        # Assert
        with check:
            assert len(agents) == 1
        with check:
            assert "valid-agent" in agents

    def test_scan_agents_with_depends_on_skills_returns_list(self, tmp_path: Path) -> None:
        """Agent with depends_on_skills should parse them into a list.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(
            tmp_path,
            "my-agent.md",
            "name: my-agent\ndescription: Agent\nmodel: opus\ndepends_on_skills: [skill-a, skill-b]",
        )

        # Act
        with patch.object(sync_context, "AGENTS_DIR", tmp_path):
            agents = scan_agents()

        # Assert
        assert agents["my-agent"].depends_on_skills == ["skill-a", "skill-b"]


# ============================================================================
# Test: scan_commands
# ============================================================================


class TestScanCommands:
    """Tests for scan_commands that discovers command metadata from the filesystem."""

    def test_scan_commands_valid_directory_returns_command_info(self, tmp_path: Path) -> None:
        """Directory with valid command markdown files should return populated CommandInfo dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(
            tmp_path,
            "clean.md",
            "name: clean\ndescription: Clean code\nversion: 1.2.0",
        )

        # Act
        with patch.object(sync_context, "COMMANDS_DIR", tmp_path):
            commands = scan_commands()

        # Assert
        with check:
            assert "clean" in commands
        with check:
            assert commands["clean"].description == "Clean code"
        with check:
            assert commands["clean"].version == "1.2.0"

    def test_scan_commands_empty_directory_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty commands directory should return empty dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Act
        with patch.object(sync_context, "COMMANDS_DIR", tmp_path):
            commands = scan_commands()

        # Assert
        assert commands == {}

    def test_scan_commands_nonexistent_directory_returns_empty_dict(self, tmp_path: Path) -> None:
        """Non-existent commands directory should return empty dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent = tmp_path / "does-not-exist"

        # Act
        with patch.object(sync_context, "COMMANDS_DIR", nonexistent):
            commands = scan_commands()

        # Assert
        assert commands == {}

    def test_scan_commands_defaults_name_to_stem(self, tmp_path: Path) -> None:
        """Command without name in frontmatter should default to file stem.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(tmp_path, "review.md", "description: Code review")

        # Act
        with patch.object(sync_context, "COMMANDS_DIR", tmp_path):
            commands = scan_commands()

        # Assert
        assert "review" in commands

    def test_scan_commands_skips_non_md_files(self, tmp_path: Path) -> None:
        """Non-.md files in the commands directory should be ignored.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(tmp_path, "valid-cmd.md", "name: valid-cmd\ndescription: Valid")
        (tmp_path / "notes.txt").write_text("not a command")
        (tmp_path / "config.json").write_text("{}")

        # Act
        with patch.object(sync_context, "COMMANDS_DIR", tmp_path):
            commands = scan_commands()

        # Assert
        with check:
            assert len(commands) == 1
        with check:
            assert "valid-cmd" in commands

    def test_scan_commands_with_dependencies_returns_lists(self, tmp_path: Path) -> None:
        """Command with depends_on_agents and depends_on_skills should parse both lists.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        _write_md_file(
            tmp_path,
            "deploy.md",
            "name: deploy\ndescription: Deploy\ndepends_on_agents: [agent-a]\ndepends_on_skills: [skill-x, skill-y]",
        )

        # Act
        with patch.object(sync_context, "COMMANDS_DIR", tmp_path):
            commands = scan_commands()

        # Assert
        with check:
            assert commands["deploy"].depends_on_agents == ["agent-a"]
        with check:
            assert commands["deploy"].depends_on_skills == ["skill-x", "skill-y"]


# ============================================================================
# Test: load_manifest
# ============================================================================


class TestLoadManifest:
    """Tests for load_manifest that reads manifest.json from disk."""

    def test_load_manifest_existing_file_returns_parsed_json(self, tmp_path: Path) -> None:
        """Existing valid manifest file should return parsed JSON dict.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {"version": "1.0.0", "skills": [{"name": "test"}]}
        manifest_path.write_text(json.dumps(manifest_data))

        # Act
        with patch.object(sync_context, "MANIFEST_PATH", manifest_path):
            loaded = load_manifest()

        # Assert
        assert loaded == manifest_data

    def test_load_manifest_nonexistent_file_returns_default(self, tmp_path: Path) -> None:
        """Non-existent manifest file should return the default manifest structure.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent = tmp_path / "nonexistent.json"

        # Act
        with patch.object(sync_context, "MANIFEST_PATH", nonexistent):
            loaded = load_manifest()

        # Assert
        with check:
            assert "skills" in loaded
        with check:
            assert "agents" in loaded
        with check:
            assert "commands" in loaded
        with check:
            assert loaded["skills"] == []

    def test_load_manifest_default_not_corrupted_after_mutation(self, tmp_path: Path) -> None:
        """Mutating a loaded default manifest must not corrupt subsequent loads.

        load_manifest uses deepcopy so nested lists (skills, agents, commands)
        are independent across calls. Without deepcopy, the shared _DEFAULT_MANIFEST
        lists would be permanently corrupted.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent = tmp_path / "nonexistent.json"

        with patch.object(sync_context, "MANIFEST_PATH", nonexistent):
            # Act - load, directly mutate, then load again
            first = load_manifest()
            first["skills"].append({"name": "corrupted"})

            second = load_manifest()

        # Assert - second load must still have empty lists
        with check:
            assert second["skills"] == []
        with check:
            assert second["agents"] == []
        with check:
            assert second["commands"] == []


# ============================================================================
# Test: update_manifest
# ============================================================================


class TestUpdateManifest:
    """Tests for update_manifest that synchronizes manifest with discovered items."""

    def test_update_manifest_add_new_skill_reports_change(self) -> None:
        """Adding a new skill should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}
        skills = {"new-skill": SkillInfo(name="new-skill", description="New skill")}

        # Act
        updated, changes = update_manifest(manifest, skills, {}, {})

        # Assert
        with check:
            assert len(updated["skills"]) == 1
        with check:
            assert updated["skills"][0]["name"] == "new-skill"
        with check:
            assert any("Added skill: new-skill" in c for c in changes)
        with check:
            assert updated is manifest

    def test_update_manifest_remove_deleted_skill_reports_change(self) -> None:
        """Removing a skill no longer on disk should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [{"name": "old-skill", "description": "Old", "category": "conventions", "version": "1.0.0"}],
            "agents": [],
            "commands": [],
        }

        # Act
        updated, changes = update_manifest(manifest, {}, {}, {})

        # Assert
        with check:
            assert updated["skills"] == []
        with check:
            assert any("Removed skill: old-skill" in c for c in changes)

    def test_update_manifest_preserves_existing_skill_description(self) -> None:
        """Existing manifest entries should be preserved (manifest is source of truth)."""
        # Arrange
        existing_entry = {
            "name": "my-skill",
            "description": "Manifest description (source of truth)",
            "category": "conventions",
            "version": "1.0.0",
            "user_invocable": True,
        }
        manifest: dict[str, Any] = {"skills": [existing_entry], "agents": [], "commands": []}
        skills = {"my-skill": SkillInfo(name="my-skill", description="Disk description")}

        # Act
        updated, changes = update_manifest(manifest, skills, {}, {})

        # Assert
        with check:
            assert updated["skills"][0]["description"] == "Manifest description (source of truth)"
        with check:
            assert changes == []

    def test_update_manifest_add_new_agent_reports_change(self) -> None:
        """Adding a new agent should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}
        agents = {"new-agent": AgentInfo(name="new-agent", description="Agent", model="opus")}

        # Act
        updated, changes = update_manifest(manifest, {}, agents, {})

        # Assert
        with check:
            assert len(updated["agents"]) == 1
        with check:
            assert any("Added agent: new-agent" in c for c in changes)

    def test_update_manifest_remove_deleted_agent_reports_change(self) -> None:
        """Removing an agent no longer on disk should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [],
            "agents": [{"name": "old-agent", "description": "Old", "model": "opus", "version": "1.0.0"}],
            "commands": [],
        }

        # Act
        updated, changes = update_manifest(manifest, {}, {}, {})

        # Assert
        with check:
            assert updated["agents"] == []
        with check:
            assert any("Removed agent: old-agent" in c for c in changes)

    def test_update_manifest_add_new_command_reports_change(self) -> None:
        """Adding a new command should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}
        commands = {"new-cmd": CommandInfo(name="new-cmd", description="Command")}

        # Act
        updated, changes = update_manifest(manifest, {}, {}, commands)

        # Assert
        with check:
            assert len(updated["commands"]) == 1
        with check:
            assert any("Added command: new-cmd" in c for c in changes)

    def test_update_manifest_remove_deleted_command_reports_change(self) -> None:
        """Removing a command no longer on disk should appear in the changes list."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [],
            "agents": [],
            "commands": [{"name": "old-cmd", "description": "Old", "version": "1.0.0"}],
        }

        # Act
        updated, changes = update_manifest(manifest, {}, {}, {})

        # Assert
        with check:
            assert updated["commands"] == []
        with check:
            assert any("Removed command: old-cmd" in c for c in changes)

    def test_update_manifest_no_changes_returns_empty_changes(self) -> None:
        """When disk matches manifest, changes list should be empty."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [{"name": "s1", "description": "S1", "category": "conventions", "version": "1.0.0"}],
            "agents": [{"name": "a1", "description": "A1", "model": "opus", "version": "1.0.0"}],
            "commands": [{"name": "c1", "description": "C1", "version": "1.0.0"}],
        }
        skills = {"s1": SkillInfo(name="s1", description="S1")}
        agents = {"a1": AgentInfo(name="a1", description="A1", model="opus")}
        commands = {"c1": CommandInfo(name="c1", description="C1")}

        # Act
        updated, changes = update_manifest(manifest, skills, agents, commands)

        # Assert
        with check:
            assert changes == []
        with check:
            assert updated is manifest

    def test_update_manifest_concurrent_add_and_remove(self) -> None:
        """Adding one skill while removing another in a single call should report both changes."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [{"name": "old-skill", "description": "Old", "category": "conventions", "version": "1.0.0"}],
            "agents": [],
            "commands": [],
        }
        skills = {"new-skill": SkillInfo(name="new-skill", description="New")}

        # Act
        updated, changes = update_manifest(manifest, skills, {}, {})

        # Assert
        skill_names = [s["name"] for s in updated["skills"]]
        with check:
            assert "new-skill" in skill_names
        with check:
            assert "old-skill" not in skill_names
        with check:
            assert any("Added skill: new-skill" in c for c in changes)
        with check:
            assert any("Removed skill: old-skill" in c for c in changes)
        with check:
            assert len(changes) == 2

    def test_update_manifest_command_with_dependencies_includes_them(self) -> None:
        """New command with dependencies should include them in the manifest entry."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}
        commands = {
            "deploy": CommandInfo(
                name="deploy",
                description="Deploy",
                depends_on_agents=["agent-a"],
                depends_on_skills=["skill-x"],
            )
        }

        # Act
        updated, _ = update_manifest(manifest, {}, {}, commands)

        # Assert
        entry = updated["commands"][0]
        with check:
            assert entry["depends_on_agents"] == ["agent-a"]
        with check:
            assert entry["depends_on_skills"] == ["skill-x"]

    def test_update_manifest_command_without_dependencies_omits_keys(self) -> None:
        """New command without dependencies should not include dependency keys."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}
        commands = {"simple": CommandInfo(name="simple", description="Simple")}

        # Act
        updated, _ = update_manifest(manifest, {}, {}, commands)

        # Assert
        entry = updated["commands"][0]
        with check:
            assert "depends_on_agents" not in entry
        with check:
            assert "depends_on_skills" not in entry


# ============================================================================
# Test: generate_claude_md_sections
# ============================================================================


class TestGenerateClaudeMdSections:
    """Tests for generate_claude_md_sections that produces section content."""

    def test_generate_claude_md_sections_returns_expected_keys(self) -> None:
        """Section dict should contain all expected section names."""
        # Arrange
        manifest: dict[str, Any] = {"skills": [], "agents": [], "commands": []}

        # Act
        with patch.object(sync_context, "PROJECT_ROOT", Path("/nonexistent")):
            sections = generate_claude_md_sections({}, {}, {}, manifest)

        # Assert
        expected_keys = {"Commands", "Agents", "Context Bundles", "Skills"}
        assert set(sections.keys()) == expected_keys

    def test_generate_claude_md_sections_content_is_populated(self) -> None:
        """Sections should contain populated content, not just empty strings."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [{"name": "test-skill", "category": "conventions"}],
            "agents": [{"name": "test-agent", "description": "Agent", "model": "opus"}],
            "commands": [{"name": "test-cmd", "description": "Command"}],
        }
        skills = {"test-skill": SkillInfo(name="test-skill", description="A skill")}
        agents = {"test-agent": AgentInfo(name="test-agent", description="Agent", model="opus")}
        commands = {"test-cmd": CommandInfo(name="test-cmd", description="Command")}

        # Act
        with patch.object(sync_context, "PROJECT_ROOT", Path("/nonexistent")):
            sections = generate_claude_md_sections(skills, agents, commands, manifest)

        # Assert - verify sections contain populated content, not just keys
        with check:
            assert "`test-skill`" in sections["Skills"]
        with check:
            assert "`test-agent`" in sections["Agents"]
        with check:
            assert "`/test-cmd`" in sections["Commands"]


# ============================================================================
# Test: _generate_commands_section
# ============================================================================


class TestGenerateCommandsSection:
    """Tests for _generate_commands_section that produces the Commands table."""

    def test_generate_commands_section_table_format(self) -> None:
        """Commands section should produce a valid markdown table with sorted entries."""
        # Arrange
        commands = {
            "clean": CommandInfo(name="clean", description="Clean code"),
            "review": CommandInfo(name="review", description="Review code"),
        }
        manifest: dict[str, Any] = {"commands": []}

        # Act
        section = _generate_commands_section(commands, manifest)

        # Assert
        with check:
            assert "| Command | Purpose |" in section
        with check:
            assert "| `/clean` |" in section
        with check:
            assert "| `/review` |" in section

    def test_generate_commands_section_uses_manifest_description(self) -> None:
        """Commands section should prefer manifest descriptions over disk descriptions."""
        # Arrange
        commands = {"clean": CommandInfo(name="clean", description="Disk desc")}
        manifest: dict[str, Any] = {
            "commands": [{"name": "clean", "description": "Manifest desc"}],
        }

        # Act
        section = _generate_commands_section(commands, manifest)

        # Assert
        assert "Manifest desc" in section

    def test_generate_commands_section_empty_commands(self) -> None:
        """Empty commands should produce a table with only headers."""
        # Act
        section = _generate_commands_section({}, {"commands": []})

        # Assert
        with check:
            assert "| Command | Purpose |" in section
        with check:
            assert section.count("| `/") == 0


# ============================================================================
# Test: _generate_agents_section
# ============================================================================


class TestGenerateAgentsSection:
    """Tests for _generate_agents_section that produces the Agents table."""

    def test_generate_agents_section_table_format(self) -> None:
        """Agents section should produce a valid markdown table with model display."""
        # Arrange
        agents = {
            "code-writer": AgentInfo(name="code-writer", description="Writes code", model="opus"),
            "reviewer": AgentInfo(name="reviewer", description="Reviews code", model="sonnet"),
        }
        manifest: dict[str, Any] = {"agents": []}

        # Act
        section = _generate_agents_section(agents, manifest)

        # Assert
        with check:
            assert "| Agent | Scope |" in section
        with check:
            assert "| `code-writer` | Writes code |" in section
        with check:
            assert "| `reviewer` | Reviews code |" in section

    def test_generate_agents_section_uses_manifest_description(self) -> None:
        """Agents section should prefer manifest descriptions over disk descriptions."""
        # Arrange
        agents = {"writer": AgentInfo(name="writer", description="Disk", model="opus")}
        manifest: dict[str, Any] = {
            "agents": [{"name": "writer", "description": "Manifest agent desc"}],
        }

        # Act
        section = _generate_agents_section(agents, manifest)

        # Assert
        assert "Manifest agent desc" in section


# ============================================================================
# Test: _generate_bundles_section
# ============================================================================


class TestGenerateBundlesSection:
    """Tests for _generate_bundles_section that produces the Context Bundles table."""

    def test_generate_bundles_section_table_format(self) -> None:
        """Bundles section should produce a table with full and compact bundle paths."""
        # Arrange
        agents = {
            "code-writer": AgentInfo(name="code-writer", description="Writes code", model="opus"),
        }

        # Act
        section = _generate_bundles_section(agents)

        # Assert
        with check:
            assert "| Agent | Full Bundle | Compact Bundle |" in section
        with check:
            assert "`bundles/code-writer.md`" in section
        with check:
            assert "`bundles/code-writer-compact.md`" in section

    def test_generate_bundles_section_includes_regenerate_instructions(self) -> None:
        """Bundles section should include regeneration instructions."""
        # Act
        section = _generate_bundles_section({})

        # Assert
        with check:
            assert "Regenerate bundles" in section
        with check:
            assert "generate_bundles.py" in section


# ============================================================================
# Test: _generate_skills_section
# ============================================================================


class TestGenerateSkillsSection:
    """Tests for _generate_skills_section that produces the Skills listing."""

    def test_generate_skills_section_groups_by_category(self) -> None:
        """Skills section should group skills under their category headings."""
        # Arrange
        skills = {
            "naming": SkillInfo(name="naming", description="Naming", category="conventions"),
            "runner": SkillInfo(name="runner", description="Runner", category="utilities"),
        }
        manifest: dict[str, Any] = {
            "skills": [
                {"name": "naming", "category": "conventions"},
                {"name": "runner", "category": "utilities"},
            ],
        }

        # Act
        section = _generate_skills_section(skills, manifest)

        # Assert
        with check:
            assert "**Conventions**:" in section
        with check:
            assert "`naming`" in section
        with check:
            assert "**Utilities**:" in section
        with check:
            assert "`runner`" in section

    def test_generate_skills_section_empty_categories_omitted(self) -> None:
        """Empty categories should not appear in the section output."""
        # Arrange
        skills = {"naming": SkillInfo(name="naming", description="Naming", category="conventions")}
        manifest: dict[str, Any] = {
            "skills": [{"name": "naming", "category": "conventions"}],
        }

        # Act
        section = _generate_skills_section(skills, manifest)

        # Assert
        with check:
            assert "**Conventions**:" in section
        with check:
            assert "**Assessment**:" not in section
        with check:
            assert "**Templates**:" not in section
        with check:
            assert "**Utilities**:" not in section


# ============================================================================
# Test: update_claude_md
# ============================================================================


class TestUpdateClaudeMd:
    """Tests for update_claude_md that replaces sections in CLAUDE.md."""

    def test_update_claude_md_updates_changed_section(self, tmp_path: Path) -> None:
        """Section with changed content should be replaced and reported.

        Verifies the complete file content to ensure surrounding sections and
        section boundaries are preserved correctly.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Title\n\n## Commands\n\nOld content here\n\n---\n\n## Other\n\nStuff")
        sections = {"Commands": "New content here"}

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", claude_md):
            changes = update_claude_md(sections)

        # Assert
        result = claude_md.read_text()
        with check:
            assert len(changes) == 1
        with check:
            assert "Commands" in changes[0]
        with check:
            assert "New content here" in result
        with check:
            assert "Old content here" not in result
        # Adjacent section must be preserved
        with check:
            assert "## Other\n\nStuff" in result

    def test_update_claude_md_multiple_sections_simultaneously(self, tmp_path: Path) -> None:
        """Updating multiple sections in one call should replace all of them.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Title\n\n## Commands\n\nOld commands\n\n---\n\n## Agents\n\nOld agents\n\n---\n\n## Footer\n\nEnd"
        )
        sections = {
            "Commands": "New commands content",
            "Agents": "New agents content",
        }

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", claude_md):
            changes = update_claude_md(sections)

        # Assert
        result = claude_md.read_text()
        with check:
            assert len(changes) == 2
        with check:
            assert "New commands content" in result
        with check:
            assert "New agents content" in result
        with check:
            assert "Old commands" not in result
        with check:
            assert "Old agents" not in result
        # Untouched section preserved
        with check:
            assert "## Footer\n\nEnd" in result

    def test_update_claude_md_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """Dry run should report changes but not modify the file.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        original_content = "# Title\n\n## Commands\n\nOld content\n\n---\n"
        claude_md.write_text(original_content)
        sections = {"Commands": "New content"}

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", claude_md):
            changes = update_claude_md(sections, dry_run=True)

        # Assert
        with check:
            assert len(changes) == 1
        with check:
            assert claude_md.read_text() == original_content

    def test_update_claude_md_no_changes_when_content_matches(self, tmp_path: Path) -> None:
        """Section with identical content should not report changes.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Title\n\n## Commands\n\nExact content\n\n---\n")
        sections = {"Commands": "Exact content"}

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", claude_md):
            changes = update_claude_md(sections)

        # Assert
        assert changes == []

    def test_update_claude_md_nonexistent_file_returns_error(self, tmp_path: Path) -> None:
        """Non-existent CLAUDE.md should return an error message.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent = tmp_path / "CLAUDE.md"

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", nonexistent):
            changes = update_claude_md({"Commands": "Content"})

        # Assert
        with check:
            assert len(changes) == 1
        with check:
            assert "does not exist" in changes[0]

    def test_update_claude_md_nonexistent_section_returns_no_changes(self, tmp_path: Path) -> None:
        """Section name not present in CLAUDE.md should silently return no changes.

        Documents intentional behavior: sections that don't exist in the file
        are silently skipped rather than raising an error.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Title\n\n## Commands\n\nContent\n\n---\n")
        sections = {"NonexistentSection": "New content"}

        # Act
        with patch.object(sync_context, "CLAUDE_MD_PATH", claude_md):
            changes = update_claude_md(sections)

        # Assert
        assert changes == []


# ============================================================================
# Test: regenerate_bundles
# ============================================================================


class TestRegenerateBundles:
    """Tests for regenerate_bundles that runs the bundle generation script."""

    def test_regenerate_bundles_dry_run_returns_would_message(self) -> None:
        """Dry run should return 'Would regenerate bundles' without running subprocess."""
        # Act
        changes = regenerate_bundles(dry_run=True)

        # Assert
        assert changes == ["Would regenerate bundles"]

    def test_regenerate_bundles_missing_script_returns_error(self, tmp_path: Path) -> None:
        """Missing script should return error message.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        nonexistent_script = tmp_path / "generate_bundles.py"

        # Act
        with patch.object(sync_context, "GENERATE_BUNDLES_SCRIPT", nonexistent_script):
            changes = regenerate_bundles()

        # Assert
        assert changes == ["generate_bundles.py not found"]

    def test_regenerate_bundles_success_returns_regenerated_message(self, tmp_path: Path) -> None:
        """Successful subprocess run should return 'Regenerated bundles'.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        script = tmp_path / "generate_bundles.py"
        script.write_text("")
        mock_result = MagicMock(returncode=0, stdout="", stderr="")

        # Act
        with (
            patch.object(sync_context, "GENERATE_BUNDLES_SCRIPT", script),
            patch("sync_context.subprocess.run", return_value=mock_result) as mock_run,
        ):
            changes = regenerate_bundles()

        # Assert
        with check:
            assert changes == ["Regenerated bundles"]
        with check:
            assert mock_run.call_args[0][0] == ["uv", "run", "python", str(script)]
        with check:
            assert mock_run.call_args[1]["cwd"] == sync_context.PROJECT_ROOT
        with check:
            assert mock_run.call_args[1]["capture_output"] is True

    def test_regenerate_bundles_failure_returns_error_with_stderr(self, tmp_path: Path) -> None:
        """Failed subprocess should return error message with stderr content.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        script = tmp_path / "generate_bundles.py"
        script.write_text("")
        mock_result = MagicMock(returncode=1, stdout="", stderr="ImportError: no module")

        # Act
        with (
            patch.object(sync_context, "GENERATE_BUNDLES_SCRIPT", script),
            patch("sync_context.subprocess.run", return_value=mock_result),
        ):
            changes = regenerate_bundles()

        # Assert
        with check:
            assert len(changes) == 1
        with check:
            assert "Bundle generation failed" in changes[0]
        with check:
            assert "ImportError" in changes[0]


# ============================================================================
# Test: _sync_skills (private helper, tested for edge cases)
# ============================================================================


class TestSyncSkillsHelper:
    """Tests for _sync_skills private helper that merges skill lists."""

    def test_sync_skills_new_skill_includes_all_fields(self) -> None:
        """Newly added skill entry should contain all expected fields."""
        # Arrange
        manifest: dict[str, Any] = {"skills": []}
        skills = {
            "new": SkillInfo(
                name="new",
                description="A new skill",
                version="2.0.0",
                user_invocable=False,
                category="utilities",
            )
        }

        # Act
        new_skills, changes = sync_context._sync_skills(manifest, skills)

        # Assert
        entry = new_skills[0]
        with check:
            assert entry["name"] == "new"
        with check:
            assert entry["description"] == "A new skill"
        with check:
            assert entry["version"] == "2.0.0"
        with check:
            assert entry["user_invocable"] is False
        with check:
            assert entry["category"] == "utilities"
        with check:
            assert len(changes) == 1


# ============================================================================
# Test: _sync_agents (private helper, tested for edge cases)
# ============================================================================


class TestSyncAgentsHelper:
    """Tests for _sync_agents private helper that merges agent lists."""

    def test_sync_agents_new_agent_includes_depends_on_skills(self) -> None:
        """Newly added agent entry should include its skill dependencies."""
        # Arrange
        manifest: dict[str, Any] = {"agents": []}
        agents = {
            "new": AgentInfo(
                name="new",
                description="Agent",
                model="sonnet",
                depends_on_skills=["skill-a", "skill-b"],
            )
        }

        # Act
        new_agents, changes = sync_context._sync_agents(manifest, agents)

        # Assert
        entry = new_agents[0]
        with check:
            assert entry["depends_on_skills"] == ["skill-a", "skill-b"]
        with check:
            assert entry["model"] == "sonnet"
        with check:
            assert len(changes) == 1


# ============================================================================
# Test: _sync_commands (private helper, tested for edge cases)
# ============================================================================


class TestSyncCommandsHelper:
    """Tests for _sync_commands private helper that merges command lists."""

    def test_sync_commands_with_no_dependencies_omits_keys(self) -> None:
        """Command without dependencies should not have dependency keys in its entry."""
        # Arrange
        manifest: dict[str, Any] = {"commands": []}
        commands = {"simple": CommandInfo(name="simple", description="Simple cmd")}

        # Act
        new_commands, _ = sync_context._sync_commands(manifest, commands)

        # Assert
        entry = new_commands[0]
        with check:
            assert "depends_on_agents" not in entry
        with check:
            assert "depends_on_skills" not in entry

    def test_sync_commands_with_both_dependencies_includes_both(self) -> None:
        """Command with both agent and skill dependencies should include both."""
        # Arrange
        manifest: dict[str, Any] = {"commands": []}
        commands = {
            "complex": CommandInfo(
                name="complex",
                description="Complex",
                depends_on_agents=["agent-a"],
                depends_on_skills=["skill-x"],
            )
        }

        # Act
        new_commands, _ = sync_context._sync_commands(manifest, commands)

        # Assert
        entry = new_commands[0]
        with check:
            assert entry["depends_on_agents"] == ["agent-a"]
        with check:
            assert entry["depends_on_skills"] == ["skill-x"]


# ============================================================================
# Test: main
# ============================================================================


class TestMain:
    """Integration tests for main() entry point."""

    @pytest.fixture(autouse=True)
    def _stub_scanning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub out filesystem scanning functions for all main() tests.

        Args:
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        monkeypatch.setattr(sync_context, "scan_skills", lambda: {})
        monkeypatch.setattr(sync_context, "scan_agents", lambda: {})
        monkeypatch.setattr(sync_context, "scan_commands", lambda: {})
        monkeypatch.setattr(
            sync_context,
            "load_manifest",
            lambda: {"skills": [], "agents": [], "commands": []},
        )
        monkeypatch.setattr(
            sync_context,
            "generate_claude_md_sections",
            lambda _s, _a, _c, _m: {},
        )

    def test_main_check_returns_1_when_changes_exist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """--check should return exit code 1 when changes are detected.

        Args:
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        monkeypatch.setattr("sys.argv", ["sync_context.py", "--check", "--skip-bundles"])
        monkeypatch.setattr(
            sync_context,
            "update_manifest",
            lambda m, _s, _a, _c: (m, ["Added skill: test"]),
        )
        monkeypatch.setattr(sync_context, "update_claude_md", lambda _sections, **_kwargs: [])

        # Act
        result = sync_context.main()

        # Assert
        assert result == 1

    def test_main_check_returns_0_when_in_sync(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """--check should return exit code 0 when no changes needed.

        Args:
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        monkeypatch.setattr("sys.argv", ["sync_context.py", "--check", "--skip-bundles"])
        monkeypatch.setattr(sync_context, "update_manifest", lambda m, _s, _a, _c: (m, []))
        monkeypatch.setattr(sync_context, "update_claude_md", lambda _sections, **_kwargs: [])

        # Act
        result = sync_context.main()

        # Assert
        assert result == 0

    def test_main_dry_run_does_not_write_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--dry-run should not write manifest to disk even when changes exist.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        monkeypatch.setattr("sys.argv", ["sync_context.py", "--dry-run", "--skip-bundles"])
        manifest_path = tmp_path / "manifest.json"
        monkeypatch.setattr(sync_context, "MANIFEST_PATH", manifest_path)
        monkeypatch.setattr(
            sync_context,
            "update_manifest",
            lambda m, _s, _a, _c: (m, ["Added skill: test"]),
        )
        mock_update_claude_md = MagicMock(return_value=[])
        monkeypatch.setattr(sync_context, "update_claude_md", mock_update_claude_md)

        # Act
        sync_context.main()

        # Assert
        with check:
            assert not manifest_path.exists()
        with check:
            assert mock_update_claude_md.call_args[1]["dry_run"] is True

    def test_main_skip_bundles_does_not_call_regenerate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """--skip-bundles should not call regenerate_bundles.

        Args:
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        monkeypatch.setattr("sys.argv", ["sync_context.py", "--skip-bundles"])
        monkeypatch.setattr(sync_context, "update_manifest", lambda m, _s, _a, _c: (m, []))
        monkeypatch.setattr(sync_context, "update_claude_md", lambda _sections, **_kwargs: [])
        mock_regenerate = MagicMock()
        monkeypatch.setattr(sync_context, "regenerate_bundles", mock_regenerate)

        # Act
        sync_context.main()

        # Assert
        mock_regenerate.assert_not_called()

    def test_main_writes_manifest_when_changes_exist(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() should write manifest to disk when changes are detected and no flags set.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
            monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture.
        """
        # Arrange
        monkeypatch.setattr("sys.argv", ["sync_context.py", "--skip-bundles"])
        manifest_path = tmp_path / "manifest.json"
        monkeypatch.setattr(sync_context, "MANIFEST_PATH", manifest_path)
        monkeypatch.setattr(
            sync_context,
            "update_manifest",
            lambda m, _s, _a, _c: (m, ["Added skill: test"]),
        )
        monkeypatch.setattr(sync_context, "update_claude_md", lambda _sections, **_kwargs: [])

        # Act
        sync_context.main()

        # Assert
        assert manifest_path.exists()

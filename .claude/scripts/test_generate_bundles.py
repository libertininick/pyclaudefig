"""Tests for the bundle generation script.

This module provides comprehensive tests for generate_bundles.py, covering
all public and private functions including the SkillContent dataclass,
frontmatter parsing, layer loading, bundle generation, and CLI argument parsing.
"""

# ruff: noqa: PLR6301, S101 # this is a test module

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import generate_bundles
import pytest
import yaml
from pytest_check import check

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Provide a temporary skills directory with sample skill files.

    Creates a skills directory with two skills: one with layers (has
    frontmatter referencing rules.md and examples.md) and one without.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.

    Returns:
        Path: Path to the temporary skills directory.
    """
    skills = tmp_path / "skills"
    skills.mkdir()

    # Skill with layers
    layered = skills / "test-skill"
    layered.mkdir()
    (layered / "SKILL.md").write_text(
        "---\nlayers:\n  rules: rules.md\n  examples: examples.md\n---\n"
        "# Test Skill\n\nMain content here.\n\n"
        "## Quick Reference\n\n| Col | Val |\n|-----|-----|\n| A | B |\n\n"
        "## Details\n\nMore details.\n"
    )
    (layered / "rules.md").write_text("Rule 1: Do this.\nRule 2: Do that.")
    (layered / "examples.md").write_text("Example A\nExample B")

    # Skill without layers
    simple = skills / "simple-skill"
    simple.mkdir()
    (simple / "SKILL.md").write_text(
        "# Simple Skill\n\nSimple content.\n\n"
        "## Quick Reference\n\n| Item | Value |\n|------|-------|\n| X | Y |\n\n"
        "## Other Section\n\nOther content.\n"
    )

    # Skill without Quick Reference section
    no_qr = skills / "no-qr-skill"
    no_qr.mkdir()
    (no_qr / "SKILL.md").write_text("# No QR Skill\n\nJust content, no quick ref.\n")

    return skills


@pytest.fixture
def manifest_data() -> dict[str, Any]:
    """Provide a minimal valid manifest for testing.

    Returns:
        dict[str, Any]: A manifest structure with skills and one agent.
    """
    return {
        "skills": [
            {
                "name": "test-skill",
                "category": "conventions",
                "description": "A test skill with layers",
                "user_invocable": True,
                "version": "1.0.0",
            },
            {
                "name": "simple-skill",
                "category": "conventions",
                "description": "A simple skill without layers",
                "user_invocable": True,
                "version": "1.0.0",
            },
            {
                "name": "no-qr-skill",
                "category": "conventions",
                "description": "A skill without Quick Reference",
                "user_invocable": True,
                "version": "1.0.0",
            },
        ],
        "agents": [
            {
                "name": "test-agent",
                "description": "Test agent",
                "model": "opus",
                "version": "1.0.0",
                "depends_on_skills": ["test-skill", "simple-skill"],
            },
        ],
    }


@pytest.fixture
def manifest_file(tmp_path: Path, manifest_data: dict[str, Any]) -> Path:
    """Create a temporary manifest.json file.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.
        manifest_data (dict[str, Any]): The manifest data fixture.

    Returns:
        Path: Path to the temporary manifest file.
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir(exist_ok=True)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2))
    return manifest_path


@pytest.fixture
def bundles_dir(tmp_path: Path) -> Path:
    """Provide a temporary bundles directory.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.

    Returns:
        Path: Path to the temporary bundles directory.
    """
    bundles = tmp_path / "bundles"
    bundles.mkdir()
    return bundles


# ============================================================================
# Test: load_manifest
# ============================================================================


class TestLoadManifest:
    """Tests for manifest file loading and error handling."""

    def test_load_manifest_valid_file_returns_data(self, manifest_file: Path) -> None:
        """Valid manifest.json should return parsed dict with expected keys.

        Args:
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with patch.object(generate_bundles, "MANIFEST_PATH", manifest_file):
            result = generate_bundles.load_manifest()

        # Assert
        with check:
            assert "skills" in result
        with check:
            assert "agents" in result

    def test_load_manifest_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        """Missing manifest.json should raise FileNotFoundError.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        missing_path = tmp_path / "nonexistent" / "manifest.json"

        # Act / Assert
        with patch.object(generate_bundles, "MANIFEST_PATH", missing_path), pytest.raises(FileNotFoundError):
            generate_bundles.load_manifest()

    def test_load_manifest_invalid_json_raises_decode_error(self, tmp_path: Path) -> None:
        """Invalid JSON in manifest should raise JSONDecodeError.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        bad_manifest = tmp_path / "manifest.json"
        bad_manifest.write_text("{ invalid json }")

        # Act / Assert
        with patch.object(generate_bundles, "MANIFEST_PATH", bad_manifest), pytest.raises(json.JSONDecodeError):
            generate_bundles.load_manifest()


# ============================================================================
# Test: SkillContent Dataclass
# ============================================================================


class TestSkillContent:
    """Tests for the SkillContent dataclass."""

    def test_has_layers_empty_dict_returns_false(self) -> None:
        """SkillContent with empty layers dict should report no layers."""
        # Arrange
        skill = generate_bundles.SkillContent(main_content="content", layers={})

        # Act
        has_layers = skill.has_layers

        # Assert
        assert has_layers is False

    def test_has_layers_non_empty_dict_returns_true(self) -> None:
        """SkillContent with populated layers dict should report has layers."""
        # Arrange
        skill = generate_bundles.SkillContent(
            main_content="content",
            layers={"rules": "some rules"},
        )

        # Act
        has_layers = skill.has_layers

        # Assert
        assert has_layers is True


# ============================================================================
# Test: _parse_frontmatter
# ============================================================================


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_frontmatter_with_valid_frontmatter_returns_dict(self) -> None:
        """Content with valid YAML frontmatter should return parsed dict."""
        # Arrange
        content = "---\nlayers:\n  rules: rules.md\n  examples: examples.md\n---\n# Title\n"

        # Act
        frontmatter = generate_bundles._parse_frontmatter(content)

        # Assert
        with check:
            assert "layers" in frontmatter
        with check:
            assert frontmatter["layers"]["rules"] == "rules.md"
        with check:
            assert frontmatter["layers"]["examples"] == "examples.md"

    def test_parse_frontmatter_without_frontmatter_returns_empty_dict(self) -> None:
        """Content without frontmatter should return empty dict."""
        # Arrange
        content = "# Title\n\nSome content.\n"

        # Act
        frontmatter = generate_bundles._parse_frontmatter(content)

        # Assert
        assert frontmatter == {}

    def test_parse_frontmatter_with_empty_frontmatter_returns_empty_dict(self) -> None:
        """Content with empty frontmatter block should return empty dict."""
        # Arrange
        content = "---\n\n---\n# Title\n"

        # Act
        frontmatter = generate_bundles._parse_frontmatter(content)

        # Assert
        assert frontmatter == {}

    def test_parse_frontmatter_malformed_yaml_raises_error(self) -> None:
        """Malformed YAML in frontmatter should raise yaml.YAMLError."""
        # Arrange - unclosed bracket is invalid YAML
        content = "---\n[unclosed bracket\n---\n# Title\n"

        # Act / Assert
        with pytest.raises(yaml.YAMLError):
            generate_bundles._parse_frontmatter(content)


# ============================================================================
# Test: _remove_frontmatter
# ============================================================================


class TestRemoveFrontmatter:
    """Tests for frontmatter removal from markdown content."""

    def test_remove_frontmatter_with_frontmatter_strips_it(self) -> None:
        """Content with frontmatter should have frontmatter block removed."""
        # Arrange
        content = "---\nlayers:\n  rules: rules.md\n---\n# Title\n\nBody.\n"

        # Act
        cleaned = generate_bundles._remove_frontmatter(content)

        # Assert
        with check:
            assert "---" not in cleaned
        with check:
            assert cleaned.startswith("# Title")

    def test_remove_frontmatter_without_frontmatter_returns_unchanged(self) -> None:
        """Content without frontmatter should be returned unchanged."""
        # Arrange
        content = "# Title\n\nBody content.\n"

        # Act
        cleaned = generate_bundles._remove_frontmatter(content)

        # Assert
        assert cleaned == content

    def test_remove_frontmatter_preserves_horizontal_rules_in_body(self) -> None:
        """Horizontal rules (---) in body content should be preserved after frontmatter removal."""
        # Arrange
        content = "---\nlayers:\n  rules: rules.md\n---\n# Title\n\n---\n\nBody after rule.\n"

        # Act
        cleaned = generate_bundles._remove_frontmatter(content)

        # Assert
        with check:
            assert cleaned.startswith("# Title")
        with check:
            assert "---" in cleaned
        with check:
            assert "Body after rule." in cleaned


# ============================================================================
# Test: _load_layer_files
# ============================================================================


class TestLoadLayerFiles:
    """Tests for loading layer files from a skill directory."""

    def test_load_layer_files_existing_files_returns_content(self, tmp_path: Path) -> None:
        """Layer files that exist should have their content loaded.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "rules.md").write_text("Rule content")
        (skill_dir / "examples.md").write_text("Example content")
        layers_config = {"rules": "rules.md", "examples": "examples.md"}

        # Act
        layers = generate_bundles._load_layer_files(skill_dir, layers_config)

        # Assert
        with check:
            assert layers["rules"] == "Rule content"
        with check:
            assert layers["examples"] == "Example content"

    def test_load_layer_files_missing_file_skips_layer(self, tmp_path: Path) -> None:
        """Missing layer file should be skipped with a warning.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        layers_config = {"rules": "nonexistent.md"}

        # Act
        layers = generate_bundles._load_layer_files(skill_dir, layers_config)

        # Assert
        assert layers == {}

    def test_load_layer_files_mixed_existing_and_missing(self, tmp_path: Path) -> None:
        """Only existing layer files should be loaded; missing ones are skipped.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "rules.md").write_text("Rule content")
        layers_config = {"rules": "rules.md", "examples": "missing.md"}

        # Act
        layers = generate_bundles._load_layer_files(skill_dir, layers_config)

        # Assert
        with check:
            assert "rules" in layers
        with check:
            assert "examples" not in layers


# ============================================================================
# Test: load_skill_content
# ============================================================================


class TestLoadSkillContent:
    """Tests for loading complete skill content including layers."""

    def test_load_skill_content_with_layers_returns_skill(self, skills_dir: Path) -> None:
        """Skill with frontmatter layers should load main content and layers.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
        """
        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            skill = generate_bundles.load_skill_content("test-skill")

        # Assert
        assert skill is not None
        with check:
            assert "Main content here." in skill.main_content
        with check:
            assert skill.has_layers is True
        with check:
            assert "Rule 1: Do this." in skill.layers["rules"]
        with check:
            assert "Example A" in skill.layers["examples"]

    def test_load_skill_content_without_layers_returns_skill(self, skills_dir: Path) -> None:
        """Skill without frontmatter layers should load with empty layers dict.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
        """
        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            skill = generate_bundles.load_skill_content("simple-skill")

        # Assert
        assert skill is not None
        with check:
            assert "Simple content." in skill.main_content
        with check:
            assert skill.has_layers is False
        with check:
            assert skill.layers == {}

    def test_load_skill_content_missing_skill_returns_none(self, skills_dir: Path) -> None:
        """Non-existent skill should return None.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
        """
        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            skill = generate_bundles.load_skill_content("nonexistent-skill")

        # Assert
        assert skill is None


# ============================================================================
# Test: extract_quick_reference
# ============================================================================


class TestExtractQuickReference:
    """Tests for Quick Reference section extraction."""

    def test_extract_quick_reference_present_returns_section(self) -> None:
        """Content with a Quick Reference section should return that section."""
        # Arrange
        content = (
            "# Skill\n\nIntro.\n\n"
            "## Quick Reference\n\n| Col | Val |\n|-----|-----|\n| A | B |\n\n"
            "## Other\n\nOther content.\n"
        )

        # Act
        quick_ref = generate_bundles.extract_quick_reference(content)

        # Assert
        assert quick_ref is not None
        with check:
            assert "## Quick Reference" in quick_ref
        with check:
            assert "| A | B |" in quick_ref
        with check:
            assert "Other content" not in quick_ref

    def test_extract_quick_reference_absent_returns_none(self) -> None:
        """Content without a Quick Reference section should return None."""
        # Arrange
        content = "# Skill\n\nJust content, no quick reference.\n"

        # Act
        quick_ref = generate_bundles.extract_quick_reference(content)

        # Assert
        assert quick_ref is None

    def test_extract_quick_reference_at_end_of_content_returns_section(self) -> None:
        """Quick Reference at the very end of content should still be extracted."""
        # Arrange
        content = "# Skill\n\n## Quick Reference\n\n| Col | Val |\n|-----|-----|\n| X | Y |"

        # Act
        quick_ref = generate_bundles.extract_quick_reference(content)

        # Assert
        assert quick_ref is not None
        with check:
            assert "| X | Y |" in quick_ref


# ============================================================================
# Test: _order_layers
# ============================================================================


class TestOrderLayers:
    """Tests for layer ordering by priority."""

    def test_order_layers_rules_first_examples_second(self) -> None:
        """Rules layer should come first, examples second, then alphabetical."""
        # Arrange
        layers = {
            "zebra": "Z content",
            "examples": "E content",
            "rules": "R content",
            "alpha": "A content",
        }

        # Act
        ordered = generate_bundles._order_layers(layers)

        # Assert
        names = [name for name, _ in ordered]
        with check:
            assert names[0] == "rules"
        with check:
            assert names[1] == "examples"
        with check:
            assert names[2] == "alpha"
        with check:
            assert names[3] == "zebra"

    def test_order_layers_without_priority_layers_sorts_alphabetically(self) -> None:
        """Layers without rules or examples should be sorted alphabetically."""
        # Arrange
        layers = {"charlie": "C", "alpha": "A", "bravo": "B"}

        # Act
        ordered = generate_bundles._order_layers(layers)

        # Assert
        names = [name for name, _ in ordered]
        assert names == ["alpha", "bravo", "charlie"]

    def test_order_layers_empty_dict_returns_empty_list(self) -> None:
        """Empty layers dict should return empty list."""
        # Arrange
        layers: dict[str, str] = {}

        # Act
        ordered = generate_bundles._order_layers(layers)

        # Assert
        assert ordered == []

    def test_order_layers_only_rules_returns_rules(self) -> None:
        """Single rules layer should return just that layer."""
        # Arrange
        layers = {"rules": "R content"}

        # Act
        ordered = generate_bundles._order_layers(layers)

        # Assert
        assert len(ordered) == 1
        assert ordered[0] == ("rules", "R content")


# ============================================================================
# Test: _format_layers
# ============================================================================


class TestFormatLayers:
    """Tests for formatting layer content for bundles."""

    def test_format_layers_empty_dict_returns_empty_list(self) -> None:
        """Empty layers dict should return empty list."""
        # Arrange / Act
        lines = generate_bundles._format_layers("my-skill", {})

        # Assert
        assert lines == []

    def test_format_layers_with_content_includes_headers(self) -> None:
        """Non-empty layers should include HTML comment headers."""
        # Arrange
        layers = {"rules": "Rule content here."}

        # Act
        lines = generate_bundles._format_layers("my-skill", layers)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "<!-- my-skill/rules -->" in joined
        with check:
            assert "Rule content here." in joined

    def test_format_layers_preserves_order(self) -> None:
        """Formatted layers should follow priority ordering."""
        # Arrange
        layers = {"examples": "Example content", "rules": "Rule content"}

        # Act
        lines = generate_bundles._format_layers("my-skill", layers)

        # Assert
        joined = "\n".join(lines)
        rules_pos = joined.index("my-skill/rules")
        examples_pos = joined.index("my-skill/examples")
        assert rules_pos < examples_pos


# ============================================================================
# Test: _build_bundle_header
# ============================================================================


class TestBuildBundleHeader:
    """Tests for bundle header generation."""

    def test_build_bundle_header_contains_agent_name_and_timestamp(self) -> None:
        """Header should include agent name and ISO timestamp."""
        # Arrange
        agent_name = "test-agent"
        timestamp = "2025-01-15T12:00:00Z"

        # Act
        lines = generate_bundles._build_bundle_header(agent_name, timestamp)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "# test-agent Context Bundle" in joined
        with check:
            assert "Auto-generated from manifest.json dependencies." in joined
        with check:
            assert "Generated: 2025-01-15T12:00:00Z" in joined
        with check:
            assert "---" in joined


# ============================================================================
# Test: _build_table_of_contents
# ============================================================================


class TestBuildTableOfContents:
    """Tests for table of contents generation."""

    def test_build_table_of_contents_with_descriptions(self) -> None:
        """TOC should include skill names and descriptions from lookup."""
        # Arrange
        dependencies = ["skill-a", "skill-b"]
        skills_lookup: dict[str, dict[str, Any]] = {
            "skill-a": {"name": "skill-a", "description": "First skill"},
            "skill-b": {"name": "skill-b", "description": "Second skill"},
        }

        # Act
        lines = generate_bundles._build_table_of_contents(dependencies, skills_lookup)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "## Included Skills" in joined
        with check:
            assert "**skill-a**: First skill" in joined
        with check:
            assert "**skill-b**: Second skill" in joined

    def test_build_table_of_contents_missing_skill_in_lookup_uses_empty_description(
        self,
    ) -> None:
        """Skill not in lookup should use empty description string."""
        # Arrange
        dependencies = ["missing-skill"]
        skills_lookup: dict[str, dict[str, Any]] = {}

        # Act
        lines = generate_bundles._build_table_of_contents(dependencies, skills_lookup)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "**missing-skill**: " in joined


# ============================================================================
# Test: _format_skill_section
# ============================================================================


class TestFormatSkillSection:
    """Tests for skill section formatting in both full and compact modes."""

    def test_format_skill_section_full_mode_includes_main_content(self) -> None:
        """Full mode should include skill comment header and main content."""
        # Arrange
        skill = generate_bundles.SkillContent(
            main_content="# My Skill\n\nFull content.",
            layers={},
        )

        # Act
        lines = generate_bundles._format_skill_section("my-skill", skill, compact=False)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "<!-- skill: my-skill -->" in joined
        with check:
            assert "Full content." in joined
        with check:
            assert "---" in joined

    def test_format_skill_section_full_mode_includes_layers(self) -> None:
        """Full mode with layers should include layer content after main."""
        # Arrange
        skill = generate_bundles.SkillContent(
            main_content="# My Skill\n\nMain content.",
            layers={"rules": "Rule layer content."},
        )

        # Act
        lines = generate_bundles._format_skill_section("my-skill", skill, compact=False)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "Main content." in joined
        with check:
            assert "<!-- my-skill/rules -->" in joined
        with check:
            assert "Rule layer content." in joined

    def test_format_skill_section_compact_mode_with_quick_ref(self) -> None:
        """Compact mode should include only the Quick Reference section."""
        # Arrange
        skill = generate_bundles.SkillContent(
            main_content=(
                "# My Skill\n\nIntro.\n\n"
                "## Quick Reference\n\n| Col | Val |\n|-----|-----|\n| A | B |\n\n"
                "## Details\n\nMore details.\n"
            ),
            layers={"rules": "Rule content."},
        )

        # Act
        lines = generate_bundles._format_skill_section("my-skill", skill, compact=True)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "## my-skill" in joined
        with check:
            assert "| A | B |" in joined
        with check:
            assert "More details." not in joined
        with check:
            assert "Rule content." not in joined

    def test_format_skill_section_compact_mode_without_quick_ref_falls_back(self) -> None:
        """Compact mode without Quick Reference should fall back to full content."""
        # Arrange
        skill = generate_bundles.SkillContent(
            main_content="# No QR Skill\n\nJust content here.",
            layers={},
        )

        # Act
        lines = generate_bundles._format_skill_section("no-qr-skill", skill, compact=True)

        # Assert
        joined = "\n".join(lines)
        with check:
            assert "Just content here." in joined
        with check:
            assert "---" in joined


# ============================================================================
# Test: generate_bundle
# ============================================================================


class TestGenerateBundle:
    """Tests for full bundle generation."""

    def test_generate_bundle_full_mode_includes_all_skills(self, skills_dir: Path) -> None:
        """Full bundle should include header, TOC, and all skill content.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
        """
        # Arrange
        agent_config: dict[str, Any] = {
            "name": "test-agent",
            "depends_on_skills": ["test-skill", "simple-skill"],
        }
        skills_lookup: dict[str, dict[str, Any]] = {
            "test-skill": {"name": "test-skill", "description": "Test skill"},
            "simple-skill": {"name": "simple-skill", "description": "Simple skill"},
        }

        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            bundle = generate_bundles.generate_bundle("test-agent", agent_config, skills_lookup, compact=False)

        # Assert
        with check:
            assert "# test-agent Context Bundle" in bundle
        with check:
            assert "## Included Skills" in bundle
        with check:
            assert "<!-- skill: test-skill -->" in bundle
        with check:
            assert "Main content here." in bundle
        with check:
            assert "<!-- skill: simple-skill -->" in bundle
        with check:
            assert "Simple content." in bundle

    def test_generate_bundle_compact_mode_uses_quick_ref(self, skills_dir: Path) -> None:
        """Compact bundle should use Quick Reference sections where available.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
        """
        # Arrange
        agent_config: dict[str, Any] = {
            "name": "test-agent",
            "depends_on_skills": ["simple-skill"],
        }
        skills_lookup: dict[str, dict[str, Any]] = {
            "simple-skill": {"name": "simple-skill", "description": "Simple skill"},
        }

        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            bundle = generate_bundles.generate_bundle("test-agent", agent_config, skills_lookup, compact=True)

        # Assert
        with check:
            assert "# test-agent Context Bundle" in bundle
        with check:
            assert "| Item | Value |" in bundle
        with check:
            assert "Other content." not in bundle

    def test_generate_bundle_skips_missing_skills(self, skills_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Bundle generation should exclude missing skills from both TOC and content.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            capsys (pytest.CaptureFixture[str]): Pytest output capture fixture.
        """
        # Arrange
        agent_config: dict[str, Any] = {
            "name": "test-agent",
            "depends_on_skills": ["nonexistent-skill", "simple-skill"],
        }
        skills_lookup: dict[str, dict[str, Any]] = {
            "simple-skill": {"name": "simple-skill", "description": "Simple skill"},
        }

        # Act
        with patch.object(generate_bundles, "SKILLS_DIR", skills_dir):
            bundle = generate_bundles.generate_bundle("test-agent", agent_config, skills_lookup, compact=False)

        # Assert - missing skill excluded from entire bundle (TOC and content)
        with check:
            assert "<!-- skill: simple-skill -->" in bundle
        with check:
            assert "nonexistent-skill" not in bundle

        # Assert - warning printed for missing skill
        captured = capsys.readouterr()
        with check:
            assert "Warning: Skill not found: nonexistent-skill" in captured.out


# ============================================================================
# Test: _build_skills_lookup
# ============================================================================


class TestBuildSkillsLookup:
    """Tests for building the skills name-to-config mapping."""

    def test_build_skills_lookup_converts_list_to_dict(self) -> None:
        """Skills list should be converted to dict keyed by name."""
        # Arrange
        manifest: dict[str, Any] = {
            "skills": [
                {"name": "skill-a", "description": "First"},
                {"name": "skill-b", "description": "Second"},
            ]
        }

        # Act
        lookup = generate_bundles._build_skills_lookup(manifest)

        # Assert
        with check:
            assert "skill-a" in lookup
        with check:
            assert lookup["skill-a"]["description"] == "First"
        with check:
            assert "skill-b" in lookup
        with check:
            assert lookup["skill-b"]["description"] == "Second"

    def test_build_skills_lookup_empty_skills_returns_empty_dict(self) -> None:
        """Manifest with empty skills list should return empty dict."""
        # Arrange
        manifest: dict[str, Any] = {"skills": []}

        # Act
        lookup = generate_bundles._build_skills_lookup(manifest)

        # Assert
        assert lookup == {}

    def test_build_skills_lookup_missing_skills_key_returns_empty_dict(self) -> None:
        """Manifest without skills key should return empty dict."""
        # Arrange
        manifest: dict[str, Any] = {}

        # Act
        lookup = generate_bundles._build_skills_lookup(manifest)

        # Assert
        assert lookup == {}


# ============================================================================
# Test: _write_bundle
# ============================================================================


class TestWriteBundle:
    """Tests for writing bundle files to disk."""

    def test_write_bundle_creates_file_with_content(self, tmp_path: Path) -> None:
        """Bundle file should be created with the provided content.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange
        bundle_path = tmp_path / "test-bundle.md"
        content = "# Test Bundle\n\nContent here.\n"

        # Act
        with patch.object(generate_bundles, "CLAUDE_DIR", tmp_path):
            generate_bundles._write_bundle(bundle_path, content)

        # Assert
        with check:
            assert bundle_path.exists()
        with check:
            assert bundle_path.read_text() == content

    def test_write_bundle_prints_relative_path(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Write should print the relative path from CLAUDE_DIR.

        Args:
            tmp_path (Path): Pytest temporary directory fixture.
            capsys (pytest.CaptureFixture[str]): Pytest output capture fixture.
        """
        # Arrange
        bundle_path = tmp_path / "bundles" / "agent.md"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        content = "# Bundle\n"

        # Act
        with patch.object(generate_bundles, "CLAUDE_DIR", tmp_path):
            generate_bundles._write_bundle(bundle_path, content)

        # Assert
        captured = capsys.readouterr()
        assert "bundles/agent.md" in captured.out


# ============================================================================
# Test: _process_agent
# ============================================================================


class TestProcessAgent:
    """Tests for processing a single agent's bundle generation."""

    def test_process_agent_dry_run_does_not_write_files(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Dry run mode should not create any files on disk.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            capsys (pytest.CaptureFixture[str]): Pytest output capture fixture.
        """
        # Arrange
        agent_config: dict[str, Any] = {
            "name": "test-agent",
            "depends_on_skills": ["simple-skill"],
        }
        skills_lookup: dict[str, dict[str, Any]] = {
            "simple-skill": {"name": "simple-skill", "description": "Simple"},
        }

        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
        ):
            generate_bundles._process_agent(agent_config, skills_lookup, dry_run=True)

        # Assert
        captured = capsys.readouterr()
        with check:
            assert "Would write" in captured.out
        with check:
            assert not (bundles_dir / "test-agent.md").exists()
        with check:
            assert not (bundles_dir / "test-agent-compact.md").exists()

    def test_process_agent_normal_mode_writes_both_bundles(
        self,
        skills_dir: Path,
        bundles_dir: Path,
    ) -> None:
        """Normal mode should write both full and compact bundle files.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
        """
        # Arrange
        agent_config: dict[str, Any] = {
            "name": "test-agent",
            "depends_on_skills": ["simple-skill"],
        }
        skills_lookup: dict[str, dict[str, Any]] = {
            "simple-skill": {"name": "simple-skill", "description": "Simple"},
        }

        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles._process_agent(agent_config, skills_lookup, dry_run=False)

        # Assert
        with check:
            assert (bundles_dir / "test-agent.md").exists()
        with check:
            assert (bundles_dir / "test-agent-compact.md").exists()

        full_content = (bundles_dir / "test-agent.md").read_text()
        compact_content = (bundles_dir / "test-agent-compact.md").read_text()
        with check:
            assert "# test-agent Context Bundle" in full_content
        with check:
            assert "# test-agent Context Bundle" in compact_content


# ============================================================================
# Test: generate_all_bundles
# ============================================================================


class TestGenerateAllBundles:
    """Tests for the top-level bundle generation orchestrator."""

    def test_generate_all_bundles_with_agent_filter(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        manifest_file: Path,
    ) -> None:
        """Agent filter should only generate bundles for the matching agent.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_file),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.generate_all_bundles(dry_run=False, agent_filter="test-agent")

        # Assert
        with check:
            assert (bundles_dir / "test-agent.md").exists()
        with check:
            assert (bundles_dir / "test-agent-compact.md").exists()

    def test_generate_all_bundles_filter_nonexistent_agent_writes_nothing(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        manifest_file: Path,
    ) -> None:
        """Filtering for a non-existent agent should produce no bundle files.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_file),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.generate_all_bundles(dry_run=False, agent_filter="nonexistent-agent")

        # Assert - only the pre-existing bundles dir, no new files
        bundle_files = list(bundles_dir.glob("*.md"))
        assert bundle_files == []

    def test_generate_all_bundles_dry_run_creates_no_files(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        manifest_file: Path,
    ) -> None:
        """Dry run should not create any bundle files.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_file),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.generate_all_bundles(dry_run=True, agent_filter=None)

        # Assert
        bundle_files = list(bundles_dir.glob("*.md"))
        assert bundle_files == []

    def test_generate_all_bundles_no_agents_key_writes_nothing(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Manifest without 'agents' key should produce no bundle files.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange - manifest with skills but no agents key
        manifest = {
            "skills": [
                {"name": "simple-skill", "description": "Simple", "version": "1.0.0"},
            ]
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_path),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.generate_all_bundles(dry_run=False, agent_filter=None)

        # Assert
        bundle_files = list(bundles_dir.glob("*.md"))
        assert bundle_files == []

    def test_generate_all_bundles_without_filter_generates_for_all_agents(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Without filter, bundles should be generated for all agents in the manifest.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            tmp_path (Path): Pytest temporary directory fixture.
        """
        # Arrange - manifest with two agents
        manifest = {
            "skills": [
                {"name": "simple-skill", "description": "Simple", "version": "1.0.0"},
            ],
            "agents": [
                {
                    "name": "agent-one",
                    "description": "First",
                    "model": "opus",
                    "version": "1.0.0",
                    "depends_on_skills": ["simple-skill"],
                },
                {
                    "name": "agent-two",
                    "description": "Second",
                    "model": "sonnet",
                    "version": "1.0.0",
                    "depends_on_skills": ["simple-skill"],
                },
            ],
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        # Act
        with (
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_path),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.generate_all_bundles(dry_run=False, agent_filter=None)

        # Assert
        with check:
            assert (bundles_dir / "agent-one.md").exists()
        with check:
            assert (bundles_dir / "agent-one-compact.md").exists()
        with check:
            assert (bundles_dir / "agent-two.md").exists()
        with check:
            assert (bundles_dir / "agent-two-compact.md").exists()


# ============================================================================
# Test: _parse_args
# ============================================================================


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_parse_args_no_arguments_returns_defaults(self) -> None:
        """No arguments should return dry_run=False and agent=None."""
        # Act
        with patch("sys.argv", ["generate_bundles.py"]):
            args = generate_bundles._parse_args()

        # Assert
        with check:
            assert args.dry_run is False
        with check:
            assert args.agent is None

    def test_parse_args_dry_run_flag_sets_true(self) -> None:
        """The --dry-run flag should set dry_run to True."""
        # Act
        with patch("sys.argv", ["generate_bundles.py", "--dry-run"]):
            args = generate_bundles._parse_args()

        # Assert
        assert args.dry_run is True

    def test_parse_args_agent_flag_sets_value(self) -> None:
        """The --agent flag should capture the agent name."""
        # Act
        with patch("sys.argv", ["generate_bundles.py", "--agent", "my-agent"]):
            args = generate_bundles._parse_args()

        # Assert
        assert args.agent == "my-agent"

    def test_parse_args_both_flags_combined(self) -> None:
        """Both --dry-run and --agent should work together."""
        # Act
        with patch("sys.argv", ["generate_bundles.py", "--dry-run", "--agent", "my-agent"]):
            args = generate_bundles._parse_args()

        # Assert
        with check:
            assert args.dry_run is True
        with check:
            assert args.agent == "my-agent"


# ============================================================================
# Test: main
# ============================================================================


class TestMain:
    """Integration tests for the main entry point."""

    def test_main_runs_generate_all_bundles(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        manifest_file: Path,
    ) -> None:
        """Main should parse args and call generate_all_bundles.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with (
            patch("sys.argv", ["generate_bundles.py", "--agent", "test-agent"]),
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_file),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.main()

        # Assert
        with check:
            assert (bundles_dir / "test-agent.md").exists()
        with check:
            assert (bundles_dir / "test-agent-compact.md").exists()

    def test_main_dry_run_creates_no_files(
        self,
        skills_dir: Path,
        bundles_dir: Path,
        manifest_file: Path,
    ) -> None:
        """Main with --dry-run should not write any files.

        Args:
            skills_dir (Path): Temporary skills directory fixture.
            bundles_dir (Path): Temporary bundles directory fixture.
            manifest_file (Path): Temporary manifest file fixture.
        """
        # Act
        with (
            patch("sys.argv", ["generate_bundles.py", "--dry-run"]),
            patch.object(generate_bundles, "SKILLS_DIR", skills_dir),
            patch.object(generate_bundles, "BUNDLES_DIR", bundles_dir),
            patch.object(generate_bundles, "MANIFEST_PATH", manifest_file),
            patch.object(generate_bundles, "CLAUDE_DIR", bundles_dir.parent),
        ):
            generate_bundles.main()

        # Assert
        bundle_files = list(bundles_dir.glob("*.md"))
        assert bundle_files == []

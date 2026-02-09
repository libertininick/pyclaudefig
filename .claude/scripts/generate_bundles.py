#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Generate context bundles for agents from manifest dependencies.

This script reads the manifest.json and generates pre-composed context files
for each agent, containing all the skills they depend on. Supports layered
skills that split content across multiple files (SKILL.md, rules.md, examples.md).

Usage:
    uv run python .claude/scripts/generate_bundles.py
    uv run python .claude/scripts/generate_bundles.py --agent python-code-writer
    uv run python .claude/scripts/generate_bundles.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import yaml

CLAUDE_DIR: Final[Path] = Path(__file__).parent.parent
SKILLS_DIR: Final[Path] = CLAUDE_DIR / "skills"
MANIFEST_PATH: Final[Path] = CLAUDE_DIR / "manifest.json"
BUNDLES_DIR: Final[Path] = CLAUDE_DIR / "bundles"

FRONTMATTER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
QUICK_REFERENCE_PATTERN: Final[re.Pattern[str]] = re.compile(r"(## Quick Reference\n.*?)(?=\n## |\Z)", re.DOTALL)


@dataclass
class SkillContent:
    """Container for skill content with optional layers.

    Attributes:
        main_content (str): The main SKILL.md content (without frontmatter).
        layers (dict[str, str]): Dict mapping layer names to their content.
    """

    main_content: str
    layers: dict[str, str]

    @property
    def has_layers(self) -> bool:
        """Check if this skill has any layer content.

        Returns:
            bool: True if layers dict is non-empty.
        """
        return bool(self.layers)


def load_manifest() -> dict[str, Any]:
    """Load the manifest.json file.

    Returns:
        dict[str, Any]: The parsed manifest data.
    """
    with MANIFEST_PATH.open() as f:
        return json.load(f)


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content (str): Markdown content that may contain frontmatter.

    Returns:
        dict[str, Any]: Parsed frontmatter data, or empty dict if none found.
    """
    if match := FRONTMATTER_PATTERN.match(content):
        yaml_content = match.group(1)
        return yaml.safe_load(yaml_content) or {}
    return {}


def _remove_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content.

    Args:
        content (str): Markdown content that may contain frontmatter.

    Returns:
        str: Content with frontmatter removed.
    """
    return FRONTMATTER_PATTERN.sub("", content)


def _load_layer_files(skill_dir: Path, layers_config: dict[str, str]) -> dict[str, str]:
    """Load layer files specified in the frontmatter.

    Args:
        skill_dir (Path): Path to the skill directory.
        layers_config (dict[str, str]): Dict mapping layer names to filenames.

    Returns:
        dict[str, str]: Dict mapping layer names to their content.
    """
    layers: dict[str, str] = {}
    for layer_name, filename in layers_config.items():
        layer_path = skill_dir / filename
        if layer_path.exists():
            layers[layer_name] = layer_path.read_text().strip()
        else:
            print(f"  Warning: Layer file not found: {layer_path}")
    return layers


def load_skill_content(skill_name: str) -> SkillContent | None:
    """Load the content of a skill including any layers.

    Args:
        skill_name (str): Name of the skill directory.

    Returns:
        SkillContent | None: The skill content with layers, or None if not found.
    """
    skill_dir = SKILLS_DIR / skill_name
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        print(f"  Warning: Skill not found: {skill_name}")
        return None

    content = skill_path.read_text()
    frontmatter = _parse_frontmatter(content)
    main_content = _remove_frontmatter(content).strip()

    layers_config = frontmatter.get("layers", {})
    layers = _load_layer_files(skill_dir, layers_config) if layers_config else {}

    return SkillContent(main_content=main_content, layers=layers)


def extract_quick_reference(content: str) -> str | None:
    """Extract just the Quick Reference section from skill content.

    Args:
        content (str): Full skill content.

    Returns:
        str | None: Quick Reference section if found, None otherwise.
    """
    if match := QUICK_REFERENCE_PATTERN.search(content):
        return match.group(1).strip()
    return None


def _order_layers(layers: dict[str, str]) -> list[tuple[str, str]]:
    """Order layers by priority: rules first, examples second, then alphabetical.

    Args:
        layers (dict[str, str]): Dict mapping layer names to their content.

    Returns:
        list[tuple[str, str]]: List of (layer_name, content) tuples in priority order.
    """
    priority_order = ["rules", "examples"]
    priority_set = set(priority_order)

    priority_layers = [(name, layers[name]) for name in priority_order if name in layers]
    other_layers = [(name, layers[name]) for name in sorted(layers.keys()) if name not in priority_set]

    return [*priority_layers, *other_layers]


def _format_layers(skill_name: str, layers: dict[str, str]) -> list[str]:
    """Format layer content for inclusion in a bundle.

    Layers are formatted in a consistent order: rules first, then examples,
    then any other layers alphabetically.

    Args:
        skill_name (str): Name of the skill (for headers).
        layers (dict[str, str]): Dict mapping layer names to their content.

    Returns:
        list[str]: Lines for the layer sections.
    """
    if not layers:
        return []

    lines: list[str] = []
    for layer_name, layer_content in _order_layers(layers):
        lines.extend([
            f"<!-- {skill_name}/{layer_name} -->",
            "",
            layer_content,
            "",
        ])
    return lines


def _build_bundle_header(agent_name: str, timestamp: str) -> list[str]:
    """Build the header section of a bundle.

    Args:
        agent_name (str): Name of the agent.
        timestamp (str): ISO format timestamp.

    Returns:
        list[str]: Lines for the bundle header.
    """
    return [
        f"# {agent_name} Context Bundle",
        "",
        "Auto-generated from manifest.json dependencies.",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
    ]


def _build_table_of_contents(
    dependencies: list[str],
    skills_lookup: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    """Build the table of contents section listing included skills.

    Args:
        dependencies (list[str]): List of skill names.
        skills_lookup (Mapping[str, Mapping[str, Any]]): Skill name to config mapping.

    Returns:
        list[str]: Lines for the table of contents.
    """
    lines = ["## Included Skills", ""]
    for skill_name in dependencies:
        skill_config = skills_lookup.get(skill_name, {})
        description = skill_config.get("description", "")
        lines.append(f"- **{skill_name}**: {description}")
    lines.extend(["", "---", ""])
    return lines


def _format_skill_section(skill_name: str, skill: SkillContent, *, compact: bool) -> list[str]:
    """Format a single skill's content for inclusion in a bundle.

    For compact bundles, only the Quick Reference section is included.
    For full bundles, the main content is included followed by any layers.

    Args:
        skill_name (str): Name of the skill.
        skill (SkillContent): The skill content with optional layers.
        compact (bool): If True, only include Quick Reference sections.

    Returns:
        list[str]: Lines for the skill section.
    """
    if compact:
        quick_ref = extract_quick_reference(skill.main_content)
        if quick_ref:
            return [f"## {skill_name}", "", quick_ref, "", "---", ""]
        # Fall back to full content if no Quick Reference
        return [skill.main_content, "", "---", ""]

    # Full bundle: add skill name as context header, then main content, then layers
    lines = [f"<!-- skill: {skill_name} -->", "", skill.main_content, ""]

    if skill.has_layers:
        lines.extend(_format_layers(skill_name, skill.layers))

    lines.extend(["---", ""])
    return lines


def generate_bundle(
    agent_name: str,
    agent_config: Mapping[str, Any],
    skills_lookup: Mapping[str, Mapping[str, Any]],
    *,
    compact: bool = False,
) -> str:
    """Generate a context bundle for an agent.

    Args:
        agent_name (str): Name of the agent.
        agent_config (Mapping[str, Any]): Agent configuration from manifest.
        skills_lookup (Mapping[str, Mapping[str, Any]]): Skill name to config mapping.
        compact (bool): If True, only include Quick Reference sections.

    Returns:
        str: The generated bundle content.
    """
    dependencies: list[str] = agent_config.get("depends_on_skills", [])
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Load skills first to filter missing ones from both TOC and content
    loaded_skills: dict[str, SkillContent] = {}
    for skill_name in dependencies:
        skill = load_skill_content(skill_name)
        if skill is not None:
            loaded_skills[skill_name] = skill

    lines: list[str] = [
        *_build_bundle_header(agent_name, timestamp),
        *_build_table_of_contents(list(loaded_skills.keys()), skills_lookup),
    ]

    for skill_name, skill in loaded_skills.items():
        lines.extend(_format_skill_section(skill_name, skill, compact=compact))

    return "\n".join(lines)


def _build_skills_lookup(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a lookup dict mapping skill names to their configurations.

    Args:
        manifest (Mapping[str, Any]): The loaded manifest data.

    Returns:
        dict[str, dict[str, Any]]: Mapping of skill names to configurations.
    """
    return {skill["name"]: skill for skill in manifest.get("skills", [])}


def _write_bundle(path: Path, content: str) -> None:
    """Write bundle content to file and print status.

    Args:
        path (Path): Path to write the bundle file.
        content (str): Bundle content to write.
    """
    path.write_text(content, encoding="utf-8")
    print(f"  Wrote: {path.relative_to(CLAUDE_DIR)}")


def _process_agent(
    agent_config: Mapping[str, Any],
    skills_lookup: Mapping[str, Mapping[str, Any]],
    *,
    dry_run: bool,
) -> None:
    """Generate and write bundles for a single agent.

    Args:
        agent_config (Mapping[str, Any]): Agent configuration from manifest.
        skills_lookup (Mapping[str, Mapping[str, Any]]): Skill name to config mapping.
        dry_run (bool): If True, print what would be generated without writing.
    """
    agent_name: str = agent_config["name"]
    dependencies: list[str] = agent_config.get("depends_on_skills", [])

    print(f"\nGenerating bundle for: {agent_name}")
    print(f"  Dependencies: {len(dependencies)} skills")

    full_content = generate_bundle(agent_name, agent_config, skills_lookup, compact=False)
    compact_content = generate_bundle(agent_name, agent_config, skills_lookup, compact=True)

    if dry_run:
        print(f"  Would write: bundles/{agent_name}.md ({len(full_content)} chars)")
        print(f"  Would write: bundles/{agent_name}-compact.md ({len(compact_content)} chars)")
        return

    _write_bundle(BUNDLES_DIR / f"{agent_name}.md", full_content)
    _write_bundle(BUNDLES_DIR / f"{agent_name}-compact.md", compact_content)


def generate_all_bundles(*, dry_run: bool = False, agent_filter: str | None = None) -> None:
    """Generate bundles for all agents in the manifest.

    Args:
        dry_run (bool): If True, print what would be generated without writing.
        agent_filter (str | None): If provided, only generate bundle for this agent.
    """
    manifest = load_manifest()
    skills_lookup = _build_skills_lookup(manifest)

    if not dry_run:
        BUNDLES_DIR.mkdir(exist_ok=True)

    for agent_config in manifest.get("agents", []):
        agent_name = agent_config["name"]
        if agent_filter and agent_name != agent_filter:
            continue
        _process_agent(agent_config, skills_lookup, dry_run=dry_run)


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Generate context bundles for agents from manifest dependencies.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be generated without writing files.",
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Generate bundle for a specific agent only.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the bundle generator script."""
    args = _parse_args()
    generate_all_bundles(dry_run=args.dry_run, agent_filter=args.agent)


if __name__ == "__main__":
    main()

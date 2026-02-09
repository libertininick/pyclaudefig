#!/usr/bin/env python3
"""Synchronize Claude context files with actual skills, agents, and commands on disk.

This script:
1. Scans .claude/skills/, .claude/agents/, .claude/commands/ for files
2. Parses frontmatter to extract metadata
3. Updates manifest.json with discovered items
4. Updates CLAUDE.md sections to reflect current state
5. Optionally regenerates bundles
"""
# ruff: noqa: C901, S404

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import validate_manifest

# =============================================================================
# Constants
# =============================================================================


def _find_claude_dir() -> Path:
    """Find the .claude directory closest to this file in the path.

    Returns:
        Path: The .claude directory path.
    """
    parts = Path(__file__).resolve().parts
    parts_last_to_first = list(reversed(parts))
    last_claude_idx = (len(parts) - 1) - parts_last_to_first.index(".claude")
    return Path(*parts[: last_claude_idx + 1])


CLAUDE_DIR = _find_claude_dir()
SKILLS_DIR = CLAUDE_DIR / "skills"
AGENTS_DIR = CLAUDE_DIR / "agents"
COMMANDS_DIR = CLAUDE_DIR / "commands"
BUNDLES_DIR = CLAUDE_DIR / "bundles"
MANIFEST_PATH = CLAUDE_DIR / "manifest.json"
CLAUDE_MD_PATH = CLAUDE_DIR / "CLAUDE.md"
GENERATE_BUNDLES_SCRIPT = CLAUDE_DIR / "scripts" / "generate_bundles.py"
PROJECT_ROOT = CLAUDE_DIR.parent

_SKILL_CATEGORIES = ("conventions", "assessment", "templates", "utilities")

_CATEGORY_DISPLAY_NAMES = {
    "conventions": "Conventions",
    "assessment": "Assessment",
    "templates": "Templates",
    "utilities": "Utilities",
}

_DEFAULT_MANIFEST = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "description": "Claude Code configuration manifest",
    "version": "1.1.0",
    "skills": [],
    "agents": [],
    "commands": [],
    "categories": {
        "conventions": "Coding standards that define how code should be written",
        "assessment": "Criteria used by reviewers to assess code quality",
        "templates": "Format specifications for agent outputs",
        "utilities": "Tools and scripts for common operations",
    },
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SkillInfo:
    """Metadata for a skill parsed from SKILL.md frontmatter.

    Attributes:
        name (str): Skill identifier used in manifest and file paths.
        description (str): Human-readable description of the skill's purpose.
        version (str): Semantic version string.
        user_invocable (bool): Whether users can invoke this skill directly.
        category (str): Category for grouping in CLAUDE.md.
    """

    name: str
    description: str
    version: str = "1.0.0"
    user_invocable: bool = True
    category: str = "conventions"


@dataclass
class AgentInfo:
    """Metadata for an agent parsed from frontmatter.

    Attributes:
        name (str): Agent identifier used in manifest and file paths.
        description (str): Human-readable description of the agent's purpose.
        model (str): Model to use (e.g., "opus", "sonnet").
        version (str): Semantic version string.
        depends_on_skills (list[str]): List of skill names this agent requires.
    """

    name: str
    description: str
    model: str
    version: str = "1.0.0"
    depends_on_skills: list[str] = field(default_factory=list)


@dataclass
class CommandInfo:
    """Metadata for a command parsed from frontmatter.

    Attributes:
        name (str): Command identifier used in manifest and file paths.
        description (str): Human-readable description of the command's purpose.
        version (str): Semantic version string.
        depends_on_agents (list[str]): List of agent names this command uses.
        depends_on_skills (list[str]): List of skill names this command uses.
    """

    name: str
    description: str
    version: str = "1.0.0"
    depends_on_agents: list[str] = field(default_factory=list)
    depends_on_skills: list[str] = field(default_factory=list)


# =============================================================================
# Public Interface - Parsing
# =============================================================================


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content (str): Markdown content with optional YAML frontmatter.

    Returns:
        tuple[dict[str, Any], str]: Tuple of (frontmatter dict, remaining content).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    remaining = parts[2].strip()

    frontmatter: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] = []

    for raw_line in frontmatter_text.split("\n"):
        stripped_line = raw_line.rstrip()
        if not stripped_line:
            continue

        # Check for list item
        if stripped_line.startswith("  - ") and current_key:
            current_list.append(stripped_line[4:].strip().strip("\"'"))
            continue

        # Save previous list if any
        if current_list and current_key:
            frontmatter[current_key] = current_list
            current_list = []

        # Parse key: value
        if ":" in stripped_line:
            key, _, value = stripped_line.partition(":")
            key = key.strip()
            value = value.strip().strip("\"'")

            if not value:
                current_key = key
            else:
                frontmatter[key] = _parse_value(value)
                current_key = key

    # Save final list if any
    if current_list and current_key:
        frontmatter[current_key] = current_list

    return frontmatter, remaining


# =============================================================================
# Public Interface - Scanning
# =============================================================================


def scan_skills() -> dict[str, SkillInfo]:
    """Scan skills directory and parse metadata from each SKILL.md.

    Returns:
        dict[str, SkillInfo]: Dict mapping skill name to SkillInfo.
    """
    skills: dict[str, SkillInfo] = {}

    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        content = skill_file.read_text()
        frontmatter, _ = parse_frontmatter(content)

        name = frontmatter.get("name", skill_dir.name)
        description = frontmatter.get("description", "")

        if not description:
            lines = content.split("\n")
            for content_line in lines:
                if content_line and not content_line.startswith(("#", "-")):
                    description = content_line.strip()
                    break

        skills[name] = SkillInfo(
            name=name,
            description=description,
            version=frontmatter.get("version", "1.0.0"),
            user_invocable=frontmatter.get("user-invocable", True),
        )

    return skills


def scan_agents() -> dict[str, AgentInfo]:
    """Scan agents directory and parse metadata from each agent file.

    Returns:
        dict[str, AgentInfo]: Dict mapping agent name to AgentInfo.
    """
    agents: dict[str, AgentInfo] = {}

    if not AGENTS_DIR.exists():
        return agents

    for agent_file in sorted(AGENTS_DIR.glob("*.md")):
        content = agent_file.read_text()
        frontmatter, _ = parse_frontmatter(content)

        name = frontmatter.get("name", agent_file.stem)
        agents[name] = AgentInfo(
            name=name,
            description=frontmatter.get("description", ""),
            model=frontmatter.get("model", "opus"),
            version=frontmatter.get("version", "1.0.0"),
            depends_on_skills=frontmatter.get("depends_on_skills", []),
        )

    return agents


def scan_commands() -> dict[str, CommandInfo]:
    """Scan commands directory and parse metadata from each command file.

    Returns:
        dict[str, CommandInfo]: Dict mapping command name to CommandInfo.
    """
    commands: dict[str, CommandInfo] = {}

    if not COMMANDS_DIR.exists():
        return commands

    for cmd_file in sorted(COMMANDS_DIR.glob("*.md")):
        content = cmd_file.read_text()
        frontmatter, _ = parse_frontmatter(content)

        name = frontmatter.get("name", cmd_file.stem)
        commands[name] = CommandInfo(
            name=name,
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            depends_on_agents=frontmatter.get("depends_on_agents", []),
            depends_on_skills=frontmatter.get("depends_on_skills", []),
        )

    return commands


# =============================================================================
# Public Interface - Manifest Operations
# =============================================================================


def load_manifest() -> dict[str, Any]:
    """Load existing manifest.json.

    Returns:
        dict[str, Any]: Manifest dict, or default structure if file doesn't exist.
    """
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return copy.deepcopy(_DEFAULT_MANIFEST)


def update_manifest(
    manifest: dict[str, Any],
    skills: dict[str, SkillInfo],
    agents: dict[str, AgentInfo],
    commands: dict[str, CommandInfo],
) -> tuple[dict[str, Any], list[str]]:
    """Update manifest with discovered items, preserving existing data.

    The manifest.json descriptions are the source of truth (short summaries).
    This function only adds new items and removes deleted ones.

    Args:
        manifest (dict[str, Any]): Current manifest dict.
        skills (dict[str, SkillInfo]): Discovered skills from disk.
        agents (dict[str, AgentInfo]): Discovered agents from disk.
        commands (dict[str, CommandInfo]): Discovered commands from disk.

    Returns:
        tuple[dict[str, Any], list[str]]: Tuple of (updated manifest, list of changes made).
    """
    all_changes: list[str] = []

    new_skills, skill_changes = _sync_skills(manifest, skills)
    all_changes.extend(skill_changes)
    manifest["skills"] = new_skills

    new_agents, agent_changes = _sync_agents(manifest, agents)
    all_changes.extend(agent_changes)
    manifest["agents"] = new_agents

    new_commands, command_changes = _sync_commands(manifest, commands)
    all_changes.extend(command_changes)
    manifest["commands"] = new_commands

    return manifest, all_changes


# =============================================================================
# Public Interface - CLAUDE.md Operations
# =============================================================================


def generate_claude_md_sections(
    skills: dict[str, SkillInfo],
    agents: dict[str, AgentInfo],
    commands: dict[str, CommandInfo],
    manifest: dict[str, Any],
) -> dict[str, str]:
    """Generate updated sections for CLAUDE.md.

    Uses manifest.json as the source of truth for descriptions.

    Args:
        skills (dict[str, SkillInfo]): Discovered skills.
        agents (dict[str, AgentInfo]): Discovered agents.
        commands (dict[str, CommandInfo]): Discovered commands.
        manifest (dict[str, Any]): Current manifest.

    Returns:
        dict[str, str]: Dict mapping section name to content.
    """
    return {
        "Commands": _generate_commands_section(commands, manifest),
        "Agents": _generate_agents_section(agents, manifest),
        "Context Bundles": _generate_bundles_section(agents),
        "Skills": _generate_skills_section(skills, manifest),
    }


def update_claude_md(sections: dict[str, str], *, dry_run: bool = False) -> list[str]:
    """Update CLAUDE.md with new section content.

    Args:
        sections (dict[str, str]): Dict mapping section name to new content.
        dry_run (bool): If True, don't write changes.

    Returns:
        list[str]: List of changes made.
    """
    changes: list[str] = []

    if not CLAUDE_MD_PATH.exists():
        changes.append("CLAUDE.md does not exist")
        return changes

    content = CLAUDE_MD_PATH.read_text()

    for section_name, new_content in sections.items():
        # Match section content up to: subsection (###), separator (---), next section (##), or end
        pattern = rf"(## {re.escape(section_name)}\n\n)(.*?)(\n\n###|\n\n---|\n\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            old_content = match.group(2).strip()
            if old_content != new_content.strip():
                content = content[: match.start(2)] + new_content + "\n" + content[match.end(2) :]
                changes.append(f"Updated CLAUDE.md section: {section_name}")

    if changes and not dry_run:
        CLAUDE_MD_PATH.write_text(content)

    return changes


# =============================================================================
# Public Interface - Bundle Operations
# =============================================================================


def regenerate_bundles(*, dry_run: bool = False) -> list[str]:
    """Run the generate_bundles.py script.

    Args:
        dry_run (bool): If True, don't actually regenerate.

    Returns:
        list[str]: List of changes/output.
    """
    if not GENERATE_BUNDLES_SCRIPT.exists():
        return ["generate_bundles.py not found"]

    if dry_run:
        return ["Would regenerate bundles"]

    result = subprocess.run(  # noqa: S603
        ["uv", "run", "python", str(GENERATE_BUNDLES_SCRIPT)],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        return [f"Bundle generation failed: {result.stderr}"]

    return ["Regenerated bundles"]


# =============================================================================
# Public Interface - Entry Point
# =============================================================================


def main() -> int:
    """Main entry point.

    Returns:
        int: Exit code (0 for success, 1 if check mode finds changes).
    """
    parser = argparse.ArgumentParser(
        description="Synchronize Claude context files with skills, agents, and commands on disk."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    parser.add_argument("--check", action="store_true", help="Exit with error code if files need updating")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--skip-bundles", action="store_true", help="Skip bundle regeneration")
    args = parser.parse_args()

    all_changes: list[str] = []

    print("Scanning directories...")

    skills = scan_skills()
    agents = scan_agents()
    commands = scan_commands()

    if args.verbose:
        print(f"  Found {len(skills)} skills")
        print(f"  Found {len(agents)} agents")
        print(f"  Found {len(commands)} commands")

    print("Updating manifest.json...")
    manifest = load_manifest()
    manifest, manifest_changes = update_manifest(manifest, skills, agents, commands)
    all_changes.extend(manifest_changes)

    if manifest_changes and not args.dry_run and not args.check:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print("Updating CLAUDE.md...")
    sections = generate_claude_md_sections(skills, agents, commands, manifest)
    claude_md_changes = update_claude_md(sections, dry_run=args.dry_run or args.check)
    all_changes.extend(claude_md_changes)

    if not args.skip_bundles:
        print("Regenerating bundles...")
        bundle_changes = regenerate_bundles(dry_run=args.dry_run or args.check)
        all_changes.extend(bundle_changes)

    if all_changes:
        print("\nChanges:")
        for change in all_changes:
            print(f"  - {change}")

        if args.check:
            print("\nFiles need updating. Run without --check to apply changes.")
            return 1
        if args.dry_run:
            print("\nDry run complete. Run without --dry-run to apply changes.")
    else:
        print("\nNo changes needed. All files are in sync.")

    print("\nValidating manifest...")
    validation_errors = validate_manifest.validate_manifest(manifest)
    if validation_errors:
        print("WARNING: Manifest has validation errors:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
    else:
        print("Manifest valid.")

    return 0


# =============================================================================
# Private Helpers - Parsing
# =============================================================================


def _parse_value(value: str) -> str | bool | list[str]:
    """Parse a frontmatter value string into appropriate type.

    Args:
        value (str): The value string to parse.

    Returns:
        str | bool | list[str]: Parsed value as bool, list, or string.
    """
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [item.strip().strip("\"'") for item in items if item.strip()]
    return value


# =============================================================================
# Private Helpers - Manifest Sync
# =============================================================================


def _sync_skills(
    manifest: dict[str, Any],
    skills: dict[str, SkillInfo],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sync skills in manifest with discovered skills on disk.

    Args:
        manifest (dict[str, Any]): Current manifest dict.
        skills (dict[str, SkillInfo]): Discovered skills from disk.

    Returns:
        tuple[list[dict[str, Any]], list[str]]: Tuple of (new skills list, changes list).
    """
    changes: list[str] = []
    existing = {s["name"]: s for s in manifest.get("skills", [])}

    new_skills = []
    for name, info in skills.items():
        if name in existing:
            new_skills.append(existing[name])
        else:
            new_skills.append({
                "name": info.name,
                "category": info.category,
                "description": info.description,
                "user_invocable": info.user_invocable,
                "version": info.version,
            })
            changes.append(f"Added skill: {name}")

    for name in existing:
        if name not in skills:
            changes.append(f"Removed skill: {name}")

    return new_skills, changes


def _sync_agents(
    manifest: dict[str, Any],
    agents: dict[str, AgentInfo],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sync agents in manifest with discovered agents on disk.

    Args:
        manifest (dict[str, Any]): Current manifest dict.
        agents (dict[str, AgentInfo]): Discovered agents from disk.

    Returns:
        tuple[list[dict[str, Any]], list[str]]: Tuple of (new agents list, changes list).
    """
    changes: list[str] = []
    existing = {a["name"]: a for a in manifest.get("agents", [])}

    new_agents = []
    for name, info in agents.items():
        if name in existing:
            new_agents.append(existing[name])
        else:
            new_agents.append({
                "name": info.name,
                "description": info.description,
                "model": info.model,
                "version": info.version,
                "depends_on_skills": info.depends_on_skills,
            })
            changes.append(f"Added agent: {name}")

    for name in existing:
        if name not in agents:
            changes.append(f"Removed agent: {name}")

    return new_agents, changes


def _sync_commands(
    manifest: dict[str, Any],
    commands: dict[str, CommandInfo],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sync commands in manifest with discovered commands on disk.

    Args:
        manifest (dict[str, Any]): Current manifest dict.
        commands (dict[str, CommandInfo]): Discovered commands from disk.

    Returns:
        tuple[list[dict[str, Any]], list[str]]: Tuple of (new commands list, changes list).
    """
    changes: list[str] = []
    existing = {c["name"]: c for c in manifest.get("commands", [])}

    new_commands = []
    for name, info in commands.items():
        if name in existing:
            new_commands.append(existing[name])
        else:
            entry: dict[str, Any] = {
                "name": info.name,
                "description": info.description,
                "version": info.version,
            }
            if info.depends_on_agents:
                entry["depends_on_agents"] = info.depends_on_agents
            if info.depends_on_skills:
                entry["depends_on_skills"] = info.depends_on_skills
            new_commands.append(entry)
            changes.append(f"Added command: {name}")

    for name in existing:
        if name not in commands:
            changes.append(f"Removed command: {name}")

    return new_commands, changes


# =============================================================================
# Private Helpers - Section Generation
# =============================================================================


def _generate_commands_section(
    commands: dict[str, CommandInfo],
    manifest: dict[str, Any],
) -> str:
    """Generate the Commands section content.

    Args:
        commands (dict[str, CommandInfo]): Discovered commands.
        manifest (dict[str, Any]): Current manifest for descriptions.

    Returns:
        str: Formatted markdown section content.
    """
    manifest_commands = {c["name"]: c for c in manifest.get("commands", [])}
    lines = [
        "Reusable workflows in `.claude/commands/`. See each file for details.",
        "",
        "| Command | Purpose |",
        "|---------|---------|",
    ]
    for name in sorted(commands.keys()):
        desc = manifest_commands.get(name, {}).get("description", commands[name].description)
        lines.append(f"| `/{name}` | {desc} |")
    return "\n".join(lines)


def _generate_agents_section(
    agents: dict[str, AgentInfo],
    manifest: dict[str, Any],
) -> str:
    """Generate the Agents section content.

    Args:
        agents (dict[str, AgentInfo]): Discovered agents.
        manifest (dict[str, Any]): Current manifest for descriptions.

    Returns:
        str: Formatted markdown section content.
    """
    manifest_agents = {a["name"]: a for a in manifest.get("agents", [])}
    lines = [
        "Specialized sub-agents in `.claude/agents/`. See each file for details.",
        "",
        "| Agent | Scope |",
        "|-------|-------|",
    ]
    for name, info in sorted(agents.items()):
        desc = manifest_agents.get(name, {}).get("description", info.description)
        lines.append(f"| `{name}` | {desc} |")
    return "\n".join(lines)


def _generate_bundles_section(agents: dict[str, AgentInfo]) -> str:
    """Generate the Context Bundles section content.

    Args:
        agents (dict[str, AgentInfo]): Discovered agents.

    Returns:
        str: Formatted markdown section content.
    """
    lines = [
        "Pre-composed skill content for agents. Bundles provide exactly the context each agent needs.",
        "",
        "| Agent | Full Bundle | Compact Bundle |",
        "|-------|-------------|----------------|",
    ]
    for name in sorted(agents.keys()):
        lines.append(f"| `{name}` | `bundles/{name}.md` | `bundles/{name}-compact.md` |")
    lines.extend([
        "",
        "**Regenerate bundles** after modifying skills:",
        "```bash",
        "uv run python .claude/scripts/generate_bundles.py",
        "```",
    ])
    return "\n".join(lines)


def _generate_skills_section(
    skills: dict[str, SkillInfo],
    manifest: dict[str, Any],
) -> str:
    """Generate the Skills section content.

    Args:
        skills (dict[str, SkillInfo]): Discovered skills.
        manifest (dict[str, Any]): Current manifest for category info.

    Returns:
        str: Formatted markdown section content.
    """
    categories: dict[str, list[str]] = {cat: [] for cat in _SKILL_CATEGORIES}

    skill_categories = {s["name"]: s.get("category", "conventions") for s in manifest.get("skills", [])}

    for name in sorted(skills.keys()):
        cat = skill_categories.get(name, "conventions")
        if cat in categories:
            categories[cat].append(f"`{name}`")

    lines = [
        "Skills provide coding standards and conventions. See `.claude/manifest.json` for the complete catalog.",
        "",
        "**Categories**:",
    ]

    for cat_key, cat_name in _CATEGORY_DISPLAY_NAMES.items():
        if categories[cat_key]:
            lines.append(f"- **{cat_name}**: {', '.join(categories[cat_key])}")

    lines.extend([
        "",
        "**Note**: Agents should load their context bundles (above) rather than invoking skills individually.",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())

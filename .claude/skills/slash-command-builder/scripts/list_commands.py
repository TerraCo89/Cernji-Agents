#!/usr/bin/env python3
"""
Slash Command Lister - Lists and analyzes slash commands

Usage:
    list_commands.py [options]

Options:
    --category <name>    Filter by category
    --pattern <pattern>  Filter by pattern (simple, complex, nested)
    --show-tools         Show allowed tools for each command
    --path <path>        Custom path to commands directory (default: .claude/commands)

Examples:
    list_commands.py
    list_commands.py --category career
    list_commands.py --show-tools
    list_commands.py --path custom/commands
"""

import sys
from pathlib import Path
import re
from typing import List, Dict, Optional
from collections import defaultdict


class CommandInfo:
    """Information about a slash command."""

    def __init__(self, file_path: Path, commands_root: Path):
        self.file_path = file_path
        self.commands_root = commands_root
        self.name = self._extract_name()
        self.category = self._extract_category()
        self.description = ""
        self.allowed_tools = []
        self.argument_hint = ""
        self.pattern = ""
        self._parse_file()

    def _extract_name(self) -> str:
        """Extract command name from file path."""
        return self.file_path.stem

    def _extract_category(self) -> Optional[str]:
        """Extract category from file path."""
        # Get relative path from commands root
        rel_path = self.file_path.relative_to(self.commands_root)

        # If in subdirectory, first part is category
        parts = rel_path.parts
        if len(parts) > 1:
            return parts[0]
        return None

    def _parse_file(self):
        """Parse command file to extract metadata."""
        try:
            content = self.file_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter fields
        for line in frontmatter.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Description
            desc_match = re.match(r'^description:\s*(.+)$', line)
            if desc_match:
                self.description = desc_match.group(1).strip()
                continue

            # Allowed tools
            tools_match = re.match(r'^allowed-tools:\s*(.+)$', line)
            if tools_match:
                tools_str = tools_match.group(1).strip()
                self.allowed_tools = [t.strip() for t in tools_str.split(',')]
                continue

            # Argument hint
            arg_match = re.match(r'^argument-hint:\s*(.+)$', line)
            if arg_match:
                self.argument_hint = arg_match.group(1).strip()
                continue

        # Determine pattern
        self._detect_pattern(content)

    def _detect_pattern(self, content: str):
        """Detect command pattern from content."""
        # Check for skill invocation
        if re.search(r'Skill:\s+[a-z-]+', content, re.IGNORECASE):
            self.pattern = "simple"
        # Check for complex workflow ($ARGUMENTS)
        elif '$ARGUMENTS' in content:
            self.pattern = "complex"
        # Check for nested command
        elif self.category:
            self.pattern = "nested"
        else:
            self.pattern = "unknown"

    @property
    def full_name(self) -> str:
        """Get full command name with category."""
        if self.category:
            return f"{self.category}:{self.name}"
        return self.name

    @property
    def display_name(self) -> str:
        """Get display name for command."""
        return f"/{self.full_name}"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.display_name:<30} - {self.description}"


def find_commands(commands_path: Path) -> List[CommandInfo]:
    """
    Find all slash commands in directory.

    Args:
        commands_path: Path to commands directory

    Returns:
        List of CommandInfo objects
    """
    if not commands_path.exists():
        return []

    command_files = sorted(commands_path.rglob('*.md'))
    return [CommandInfo(f, commands_path) for f in command_files]


def group_by_category(commands: List[CommandInfo]) -> Dict[Optional[str], List[CommandInfo]]:
    """
    Group commands by category.

    Args:
        commands: List of CommandInfo objects

    Returns:
        Dictionary mapping category to commands
    """
    grouped = defaultdict(list)
    for cmd in commands:
        grouped[cmd.category].append(cmd)
    return dict(grouped)


def filter_commands(
    commands: List[CommandInfo],
    category: Optional[str] = None,
    pattern: Optional[str] = None
) -> List[CommandInfo]:
    """
    Filter commands by criteria.

    Args:
        commands: List of CommandInfo objects
        category: Filter by category
        pattern: Filter by pattern

    Returns:
        Filtered list of commands
    """
    filtered = commands

    if category:
        filtered = [c for c in filtered if c.category == category]

    if pattern:
        filtered = [c for c in filtered if c.pattern == pattern]

    return filtered


def display_commands(commands: List[CommandInfo], show_tools: bool = False):
    """
    Display commands in organized format.

    Args:
        commands: List of CommandInfo objects
        show_tools: Whether to show allowed tools
    """
    if not commands:
        print("No slash commands found.")
        return

    # Group by category
    grouped = group_by_category(commands)

    print(f"Slash Commands in .claude/commands/")
    print("=" * 70)
    print()

    # Display general commands (no category)
    if None in grouped:
        print("General Commands:")
        for cmd in sorted(grouped[None], key=lambda c: c.name):
            print(f"  {cmd}")
            if show_tools and cmd.allowed_tools:
                print(f"    Tools: {', '.join(cmd.allowed_tools)}")
        print()

    # Display categorized commands
    categories = sorted([k for k in grouped.keys() if k is not None])
    for category in categories:
        category_display = category.replace('_', ' ').replace('-', ' ').title()
        print(f"{category_display} Commands ({category}/):")
        for cmd in sorted(grouped[category], key=lambda c: c.name):
            print(f"  {cmd}")
            if show_tools and cmd.allowed_tools:
                print(f"    Tools: {', '.join(cmd.allowed_tools)}")
        print()

    # Summary
    print("=" * 70)
    print(f"Total: {len(commands)} command(s)")

    # Pattern breakdown
    pattern_counts = defaultdict(int)
    for cmd in commands:
        pattern_counts[cmd.pattern] += 1

    if pattern_counts:
        print()
        print("By Pattern:")
        for pattern, count in sorted(pattern_counts.items()):
            print(f"  {pattern:<15} - {count}")


def main():
    # Parse arguments
    show_tools = '--show-tools' in sys.argv
    commands_path = '.claude/commands'
    category_filter = None
    pattern_filter = None

    # Parse options
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]

        if arg == '--category' and i + 1 < len(args):
            category_filter = args[i + 1]
            i += 2
        elif arg == '--pattern' and i + 1 < len(args):
            pattern_filter = args[i + 1]
            i += 2
        elif arg == '--path' and i + 1 < len(args):
            commands_path = args[i + 1]
            i += 2
        elif arg == '--show-tools':
            i += 1
        elif arg in ['--help', '-h']:
            print("Usage: list_commands.py [options]")
            print()
            print("Options:")
            print("  --category <name>    Filter by category")
            print("  --pattern <pattern>  Filter by pattern (simple, complex, nested)")
            print("  --show-tools         Show allowed tools for each command")
            print("  --path <path>        Custom path to commands directory")
            print()
            print("Examples:")
            print("  list_commands.py")
            print("  list_commands.py --category career")
            print("  list_commands.py --show-tools")
            print("  list_commands.py --path custom/commands")
            sys.exit(0)
        else:
            print(f"Unknown option: {arg}")
            print("Use --help for usage information")
            sys.exit(1)

    # Find commands
    path = Path(commands_path).resolve()
    if not path.exists():
        print(f"Error: Commands path does not exist: {path}")
        sys.exit(1)

    commands = find_commands(path)

    # Apply filters
    commands = filter_commands(commands, category_filter, pattern_filter)

    # Display
    display_commands(commands, show_tools)


if __name__ == "__main__":
    main()

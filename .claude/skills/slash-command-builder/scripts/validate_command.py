#!/usr/bin/env python3
"""
Slash Command Validator - Validates slash command structure and quality

Usage:
    validate_command.py <path-to-commands> [--strict]

Options:
    --strict    Enable strict validation (treat warnings as errors)

Examples:
    validate_command.py .claude/commands
    validate_command.py .claude/commands/career --strict
    validate_command.py .claude/commands/my-command.md
"""

import sys
from pathlib import Path
import re
from typing import List, Tuple, Dict


class ValidationResult:
    """Represents validation result for a command."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add informational message."""
        self.info.append(message)

    def is_valid(self, strict: bool = False) -> bool:
        """Check if validation passed."""
        if self.errors:
            return False
        if strict and self.warnings:
            return False
        return True

    def __str__(self) -> str:
        """Format validation result."""
        status = "VALID" if self.is_valid() else "INVALID"
        parts = [f"{status}: {self.file_path.name}"]

        if self.errors:
            parts.append(f"  Errors ({len(self.errors)}):")
            for error in self.errors:
                parts.append(f"    - {error}")

        if self.warnings:
            parts.append(f"  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                parts.append(f"    - {warning}")

        if self.info and not self.errors and not self.warnings:
            parts.append(f"  Info:")
            for info in self.info:
                parts.append(f"    - {info}")

        return '\n'.join(parts)


def extract_frontmatter(content: str) -> Tuple[str, str]:
    """
    Extract YAML frontmatter and body from markdown content.

    Returns:
        Tuple of (frontmatter, body)
    """
    # Match YAML frontmatter between --- markers
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        return match.group(1), match.group(2)
    else:
        return "", content


def parse_frontmatter(frontmatter: str) -> Dict[str, str]:
    """
    Parse YAML frontmatter into dictionary.

    Returns:
        Dictionary of key-value pairs
    """
    data = {}
    for line in frontmatter.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Match key: value pattern
        match = re.match(r'^([a-z-]+):\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            data[key] = value

    return data


def validate_frontmatter(frontmatter: str, result: ValidationResult):
    """Validate YAML frontmatter structure."""
    if not frontmatter:
        result.add_error("Missing YAML frontmatter (should start with ---)")
        return

    # Parse frontmatter
    data = parse_frontmatter(frontmatter)

    # Check required fields
    if 'description' not in data:
        result.add_error("Missing required field: description")
    else:
        desc = data['description']
        if len(desc) < 10:
            result.add_warning("Description is too short (< 10 characters)")
        if desc.startswith('[TODO'):
            result.add_warning("Description contains TODO placeholder")

    # Check optional fields
    if 'allowed-tools' in data:
        tools = data['allowed-tools']
        # Basic validation: should be comma-separated list
        if not re.match(r'^[a-zA-Z0-9_:,\s]+$', tools):
            result.add_warning("allowed-tools field contains unexpected characters")

    if 'argument-hint' in data:
        arg_hint = data['argument-hint']
        # Should be in brackets or angle brackets
        if not (arg_hint.startswith('[') or arg_hint.startswith('<')):
            result.add_warning("argument-hint should use [brackets] or <angle-brackets>")


def validate_structure(body: str, result: ValidationResult):
    """Validate markdown structure and content."""
    # Check for main heading
    if not re.search(r'^#\s+.+$', body, re.MULTILINE):
        result.add_warning("Missing main heading (# Title)")

    # Check for common sections
    common_sections = ['Purpose', 'Syntax', 'Process', 'Examples']
    for section in common_sections:
        if not re.search(rf'^##\s+{section}', body, re.MULTILINE):
            result.add_info(f"Missing common section: ## {section}")

    # Check for TODO markers
    todo_count = len(re.findall(r'\[TODO.*?\]', body))
    if todo_count > 0:
        result.add_warning(f"Contains {todo_count} TODO marker(s) - command may be incomplete")

    # Check for code blocks
    if not re.search(r'```', body):
        result.add_info("No code blocks found - consider adding usage examples")

    # Check for $ARGUMENTS placeholder (complex workflow pattern)
    if '$ARGUMENTS' in body:
        result.add_info("Uses $ARGUMENTS pattern (complex workflow)")


def validate_examples(body: str, result: ValidationResult):
    """Validate examples section."""
    examples_section = re.search(r'##\s+Examples.*?(?=##|\Z)', body, re.DOTALL)

    if not examples_section:
        result.add_info("No Examples section found")
        return

    examples_content = examples_section.group(0)

    # Count example subsections
    example_count = len(re.findall(r'###\s+Example', examples_content))

    if example_count == 0:
        result.add_warning("Examples section exists but contains no examples")
    elif example_count == 1:
        result.add_info("Contains 1 example - consider adding more")
    else:
        result.add_info(f"Contains {example_count} examples")


def validate_command_file(file_path: Path, strict: bool = False) -> ValidationResult:
    """
    Validate a single slash command file.

    Args:
        file_path: Path to command file
        strict: Enable strict validation

    Returns:
        ValidationResult object
    """
    result = ValidationResult(file_path)

    # Read file content
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result.add_error(f"Failed to read file: {e}")
        return result

    # Extract frontmatter and body
    frontmatter, body = extract_frontmatter(content)

    # Validate frontmatter
    validate_frontmatter(frontmatter, result)

    # Validate structure
    validate_structure(body, result)

    # Validate examples
    validate_examples(body, result)

    return result


def find_command_files(path: Path) -> List[Path]:
    """
    Find all command files in path.

    Args:
        path: Path to search (file or directory)

    Returns:
        List of command file paths
    """
    if path.is_file():
        if path.suffix == '.md':
            return [path]
        else:
            return []

    # Find all .md files in directory
    return sorted(path.rglob('*.md'))


def validate_commands(commands_path: str, strict: bool = False):
    """
    Validate all slash commands in path.

    Args:
        commands_path: Path to commands directory or file
        strict: Enable strict validation
    """
    path = Path(commands_path).resolve()

    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    # Find command files
    command_files = find_command_files(path)

    if not command_files:
        print(f"No command files found in: {path}")
        sys.exit(0)

    print(f"Validating {len(command_files)} slash command(s)...")
    print()

    # Validate each command
    results = []
    for command_file in command_files:
        result = validate_command_file(command_file, strict)
        results.append(result)

    # Display results
    for result in results:
        print(result)
        print()

    # Summary
    valid_count = sum(1 for r in results if r.is_valid(strict))
    warning_count = sum(len(r.warnings) for r in results)
    error_count = sum(len(r.errors) for r in results)

    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total commands: {len(results)}")
    print(f"Valid: {valid_count}")
    if warning_count > 0:
        print(f"Warnings: {warning_count}")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print()

    # Exit code
    if error_count > 0:
        print("Validation FAILED")
        sys.exit(1)
    elif strict and warning_count > 0:
        print("Validation FAILED (strict mode - warnings treated as errors)")
        sys.exit(1)
    else:
        print("Validation PASSED")
        sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_command.py <path-to-commands> [--strict]")
        print()
        print("Options:")
        print("  --strict    Enable strict validation (treat warnings as errors)")
        print()
        print("Examples:")
        print("  validate_command.py .claude/commands")
        print("  validate_command.py .claude/commands/career --strict")
        print("  validate_command.py .claude/commands/my-command.md")
        sys.exit(1)

    commands_path = sys.argv[1]
    strict = '--strict' in sys.argv

    validate_commands(commands_path, strict)


if __name__ == "__main__":
    main()

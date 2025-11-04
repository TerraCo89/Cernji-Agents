#!/usr/bin/env python3
"""
Slash Command Initializer - Creates a new slash command from template

Usage:
    init_command.py <command-name> --pattern <pattern> [--category <category>]

Patterns:
    simple    - Simple delegation to existing skill
    complex   - Complex workflow with scripts and validation
    nested    - Nested command in a category

Examples:
    init_command.py analyze-code --pattern simple
    init_command.py deploy-staging --pattern nested --category devops
    init_command.py generate-spec --pattern complex
"""

import sys
from pathlib import Path
import re


# Template for simple delegation pattern
SIMPLE_TEMPLATE = """---
description: {description}
allowed-tools: Skill
{argument_hint}---

# {title}

## Purpose
{purpose}

## Syntax
```
/{command_name}{args_example}

Options:
{options_list}

Examples:
{usage_examples}
```

## Process

**IMPORTANT:** Invoke the `{skill_name}` skill to handle this request.

```
Skill: {skill_name}
```

After invoking the skill, the skill will:
1. [TODO: Describe what the skill does]
2. [TODO: Describe the process]
3. [TODO: Describe the output]

## Expected Arguments

Parse the following from the user's command:

{expected_args}

## Examples

### Example 1: Basic Usage
```
User: /{command_name} [TODO: example argument]
Result: [TODO: Expected outcome]
```

### Example 2: With Options
```
User: /{command_name} [TODO: argument] --option=value
Result: [TODO: Expected outcome]
```

## Error Handling

If arguments are malformed or missing:
- Missing required argument: "Please provide [argument]: /{command_name} <argument>"
- Invalid option format: "Invalid option format. Use --option=value"
- Unknown option: "Unknown option: --xyz. Valid options: [list]"

For all other errors, the {skill_name} skill will handle them appropriately.
"""

# Template for complex workflow pattern
COMPLEX_TEMPLATE = """---
description: {description}
{argument_hint}---

# {title}

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/{command_name}` in the triggering message **is** the input. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that input, do this:

1. **[TODO: Step 1 Description]**
   - [TODO: Substep details]
   - [TODO: What to extract/process]

2. **[TODO: Step 2 Description]**
   - [TODO: Run script or tool]
   - [TODO: Parse output]
   - [TODO: Validation checks]

3. **[TODO: Step 3 Description]**
   - [TODO: Process results]
   - [TODO: Handle errors]
   - [TODO: Generate output]

4. **[TODO: Step 4 Description]**
   - [TODO: Final validation]
   - [TODO: Report results]

## Validation

**[TODO: Validation Step Name]**

After [processing], validate the output:

1. Check for [condition 1]
2. Verify [condition 2]
3. Ensure [condition 3]

If validation fails:
- [TODO: Error handling steps]
- [TODO: Retry logic]
- [TODO: User notification]

## Output Format

```
[TODO: Define the output structure]

Example:
RESULTS
=======

Item 1: [Details]
Item 2: [Details]

SUMMARY
-------
[Summary information]
```

## Error Handling

**Scenario 1: [Error Type]**
```
Error: [Error message]

Possible causes:
1. [Cause 1]
2. [Cause 2]

Solutions:
1. [Solution 1]
2. [Solution 2]
```

**Scenario 2: [Error Type]**
```
[TODO: Error handling for scenario 2]
```

## General Guidelines

- [TODO: Guideline 1]
- [TODO: Guideline 2]
- [TODO: Guideline 3]
"""

# Template for nested command pattern
NESTED_TEMPLATE = """---
description: {description}
allowed-tools: {tools}
argument-hint: {arg_hint}
---

# {title}

{purpose_section}

## Syntax
```
/{full_command}{args_example}

Options:
{options_list}

Examples:
{usage_examples}
```

## Process

{process_description}

## Expected Arguments

Parse the following from the user's command:

{expected_args}

## Examples

### Example 1: {example1_title}
```
User: /{full_command} {example1_args}
Result: {example1_result}
```

### Example 2: {example2_title}
```
User: /{full_command} {example2_args}
Result: {example2_result}
```

## Output Format

{output_format}

## Error Handling

If arguments are malformed or missing:
{error_cases}

## Integration

{integration_notes}
"""


def to_title_case(name):
    """Convert kebab-case to Title Case."""
    return ' '.join(word.capitalize() for word in name.split('-'))


def to_snake_case(name):
    """Convert kebab-case to snake_case."""
    return name.replace('-', '_')


def validate_command_name(name):
    """Validate command name follows conventions."""
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name):
        return False, "Command name must be lowercase with hyphens only (e.g., 'analyze-code')"
    if len(name) > 40:
        return False, "Command name must be 40 characters or less"
    if name.startswith('-') or name.endswith('-'):
        return False, "Command name cannot start or end with hyphen"
    return True, None


def generate_simple_command(command_name, command_data):
    """Generate a simple delegation command."""
    title = to_title_case(command_name)
    skill_name = to_snake_case(command_data.get('skill_name', command_name))

    # Build argument hint
    arg_hint = command_data.get('argument_hint', '[arguments]')
    argument_hint = f"argument-hint: {arg_hint}\n" if arg_hint != '[arguments]' else ""

    # Build options list
    options = command_data.get('options', [])
    options_list = '\n'.join([f"  {opt['flag']:<25} # {opt['desc']}" for opt in options])
    if not options_list:
        options_list = "  (no options)"

    # Build usage examples
    usage_examples = '\n'.join([f"  /{command_name} {ex}" for ex in command_data.get('usage_examples', ['<argument>'])])

    # Build expected arguments
    expected_args = command_data.get('expected_args', [
        "- `argument` (required): [TODO: Description]",
        "- `--option` (optional): [TODO: Description]"
    ])
    if isinstance(expected_args, list):
        expected_args = '\n'.join(expected_args)

    return SIMPLE_TEMPLATE.format(
        description=command_data.get('description', f'[TODO: Complete description for {command_name}]'),
        argument_hint=argument_hint,
        title=title,
        purpose=command_data.get('purpose', f'[TODO: Describe what {command_name} accomplishes]'),
        command_name=command_name,
        args_example=f" {arg_hint}",
        options_list=options_list,
        usage_examples=usage_examples,
        skill_name=skill_name,
        expected_args=expected_args
    )


def generate_complex_command(command_name, command_data):
    """Generate a complex workflow command."""
    title = to_title_case(command_name)

    # Build argument hint
    arg_hint = command_data.get('argument_hint', '[arguments]')
    argument_hint = f"argument-hint: {arg_hint}\n" if arg_hint != '[arguments]' else ""

    return COMPLEX_TEMPLATE.format(
        description=command_data.get('description', f'[TODO: Complete description for {command_name}]'),
        argument_hint=argument_hint,
        title=title,
        command_name=command_name
    )


def generate_nested_command(command_name, category, command_data):
    """Generate a nested command in a category."""
    title = to_title_case(command_name)
    full_command = f"{category}:{command_name}"

    # Build argument hint
    arg_hint = command_data.get('argument_hint', '[arguments]')

    # Build tools list
    tools = command_data.get('tools', ['SlashCommand', 'Task'])
    tools_str = ', '.join(tools)

    # Build options list
    options = command_data.get('options', [])
    options_list = '\n'.join([f"  {opt['flag']:<25} # {opt['desc']}" for opt in options])
    if not options_list:
        options_list = "  (no options)"

    # Build usage examples
    usage_examples = '\n'.join([f"  /{full_command} {ex}" for ex in command_data.get('usage_examples', ['<argument>'])])

    # Build expected arguments
    expected_args = command_data.get('expected_args', [
        "- `argument` (required): [TODO: Description]"
    ])
    if isinstance(expected_args, list):
        expected_args = '\n'.join(expected_args)

    return NESTED_TEMPLATE.format(
        description=command_data.get('description', f'[TODO: Complete description for {full_command}]'),
        tools=tools_str,
        arg_hint=arg_hint,
        title=title,
        full_command=full_command,
        purpose_section=command_data.get('purpose_section', f'## Purpose\n[TODO: Describe what {full_command} accomplishes]'),
        args_example=f" {arg_hint}",
        options_list=options_list,
        usage_examples=usage_examples,
        process_description=command_data.get('process', '[TODO: Describe the process steps]'),
        expected_args=expected_args,
        example1_title=command_data.get('example1_title', 'Basic Usage'),
        example1_args=command_data.get('example1_args', '<argument>'),
        example1_result=command_data.get('example1_result', '[TODO: Expected outcome]'),
        example2_title=command_data.get('example2_title', 'With Options'),
        example2_args=command_data.get('example2_args', '<argument> --option=value'),
        example2_result=command_data.get('example2_result', '[TODO: Expected outcome]'),
        output_format=command_data.get('output_format', '[TODO: Define output structure]'),
        error_cases=command_data.get('error_cases', '- Missing argument: "Please provide [argument]"'),
        integration_notes=command_data.get('integration', '[TODO: How this command integrates with other commands/tools]')
    )


def init_command(command_name, pattern, category=None, commands_path='.claude/commands'):
    """
    Initialize a new slash command from template.

    Args:
        command_name: Name of the command
        pattern: Command pattern (simple, complex, nested)
        category: Category for nested commands
        commands_path: Path to commands directory

    Returns:
        Path to created command file, or None if error
    """
    # Validate command name
    valid, error = validate_command_name(command_name)
    if not valid:
        print(f"Error: {error}")
        return None

    # Determine file path
    commands_dir = Path(commands_path).resolve()

    if pattern == 'nested':
        if not category:
            print("Error: Nested commands require --category parameter")
            return None
        category_dir = commands_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        command_file = category_dir / f"{command_name}.md"
    else:
        command_file = commands_dir / f"{command_name}.md"

    # Check if file already exists
    if command_file.exists():
        print(f"Error: Command file already exists: {command_file}")
        return None

    # Generate command content based on pattern
    command_data = {}  # Can be extended with user input in the future

    if pattern == 'simple':
        content = generate_simple_command(command_name, command_data)
    elif pattern == 'complex':
        content = generate_complex_command(command_name, command_data)
    elif pattern == 'nested':
        content = generate_nested_command(command_name, category, command_data)
    else:
        print(f"Error: Unknown pattern '{pattern}'. Use: simple, complex, or nested")
        return None

    # Write command file
    try:
        command_file.write_text(content, encoding='utf-8')
        print(f"Created slash command: /{category}:{command_name}" if category else f"Created slash command: /{command_name}")
        print(f"Location: {command_file}")
        print()
        print("Next steps:")
        print("1. Edit the command file to complete TODO items")
        print("2. Update the description in YAML frontmatter")
        print("3. Fill in examples and error handling")
        if pattern == 'simple':
            print(f"4. Create or reference the companion skill: {to_snake_case(command_data.get('skill_name', command_name))}")
        print()
        print(f"Test it by typing: /{category}:{command_name} [arguments]" if category else f"Test it by typing: /{command_name} [arguments]")
        return command_file
    except Exception as e:
        print(f"Error creating command file: {e}")
        return None


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--pattern':
        print("Usage: init_command.py <command-name> --pattern <pattern> [--category <category>]")
        print()
        print("Patterns:")
        print("  simple    - Simple delegation to existing skill")
        print("  complex   - Complex workflow with scripts and validation")
        print("  nested    - Nested command in a category")
        print()
        print("Command name requirements:")
        print("  - Kebab-case (e.g., 'analyze-code')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print()
        print("Examples:")
        print("  init_command.py analyze-code --pattern simple")
        print("  init_command.py deploy-staging --pattern nested --category devops")
        print("  init_command.py generate-spec --pattern complex")
        sys.exit(1)

    command_name = sys.argv[1]
    pattern = sys.argv[3]

    # Parse optional category
    category = None
    if len(sys.argv) >= 6 and sys.argv[4] == '--category':
        category = sys.argv[5]

    print(f"Initializing slash command: /{command_name}")
    print(f"Pattern: {pattern}")
    if category:
        print(f"Category: {category}")
    print()

    result = init_command(command_name, pattern, category)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

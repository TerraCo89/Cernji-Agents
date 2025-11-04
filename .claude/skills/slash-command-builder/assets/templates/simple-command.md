---
description: [Brief description of what this command does - under 100 characters]
allowed-tools: Skill
argument-hint: [optional-argument]
---

# [Command Name]

## Purpose

[1-2 sentences explaining what this command accomplishes and why a user would use it]

## Syntax

```
/[command-name] [arguments] [options]

Options:
  --option1=<value>          # Description of option 1
  --option2=<value>          # Description of option 2
  --flag                     # Description of boolean flag

Examples:
  /[command-name] simple-argument
  /[command-name] argument --option1=value
  /[command-name] argument --option1=value --flag
```

## Process

**IMPORTANT:** Invoke the `[skill-name]` skill to handle this request.

```
Skill: [skill-name]
```

After invoking the skill, the skill will:

1. **[Step 1 Name]**: [What the skill does in this step]
2. **[Step 2 Name]**: [What the skill does in this step]
3. **[Step 3 Name]**: [What the skill does in this step]
4. **[Final Step]**: [Return results to user]

For detailed workflow, see the `[skill-name]` skill documentation.

## Expected Arguments

Parse the following from the user's command:

- `argument` (required): [Description of what this argument represents]
  - Format: [Expected format, e.g., "file path", "URL", "name"]
  - Example: `example-value`

- `--option1` (optional): [Description of this option]
  - Values: [List of valid values or format]
  - Default: `default-value`
  - Example: `--option1=example`

- `--option2` (optional): [Description of this option]
  - Values: [List of valid values or format]
  - Default: `default-value`
  - Example: `--option2=example`

- `--flag` (optional): [Description of this boolean flag]
  - Effect: [What this flag does when present]
  - Example: `--flag`

## Examples

### Example 1: Basic Usage

```
User: /[command-name] basic-argument

Process:
1. Parse argument: basic-argument
2. Invoke [skill-name] skill
3. Skill processes request
4. Return results

Result:
[Expected output or behavior]
```

### Example 2: With Option

```
User: /[command-name] argument --option1=custom-value

Process:
1. Parse argument: argument
2. Parse option1: custom-value
3. Invoke [skill-name] skill with custom option
4. Return results with custom behavior

Result:
[Expected output showing how option affects behavior]
```

### Example 3: With Multiple Options

```
User: /[command-name] argument --option1=value1 --option2=value2 --flag

Process:
1. Parse all arguments and options
2. Invoke [skill-name] skill with full configuration
3. Return comprehensive results

Result:
[Expected output with all options applied]
```

## Error Handling

If arguments are malformed or missing:

- **Missing required argument**: "Please provide [argument]: /[command-name] <argument>"
  - Show correct usage format
  - Provide example

- **Invalid option format**: "Invalid option format. Use --option=value"
  - Expected format: `--option=value`
  - Example: `--option1=example-value`

- **Unknown option**: "Unknown option: --xyz. Valid options: --option1, --option2, --flag"
  - List all valid options
  - Suggest correct spelling if close match

- **Invalid option value**: "Invalid value for --option1. Expected: [list of valid values]"
  - Show valid values or format
  - Provide example

For all other errors, the `[skill-name]` skill will handle them appropriately and provide detailed error messages.

## Integration

This command integrates with:

- **[Related Command 1]**: [How they work together]
- **[Related Command 2]**: [How they work together]
- **[Related Skill]**: [How the skill extends functionality]

## Notes

- [Any special considerations or caveats]
- [Performance notes if relevant]
- [When to use this command vs alternatives]

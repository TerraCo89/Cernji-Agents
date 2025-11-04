---
description: [Brief description of what this command does - under 100 characters]
allowed-tools: [List of tools this command uses]
argument-hint: [argument-description]
---

# [Command Name]

**Category:** [category-name]
**Full Command:** `/[category]:[command-name]`

## Purpose

[1-2 sentences explaining what this command accomplishes within the context of its category]

## Syntax

```
/[category]:[command-name] [arguments] [options]

Arguments:
  <required-arg>             Required argument description
  [optional-arg]             Optional argument description

Options:
  --option1=<value>          # Description of option 1
  --option2=<value>          # Description of option 2
  --flag                     # Description of boolean flag

Examples:
  /[category]:[command-name] required-value
  /[category]:[command-name] required-value optional-value
  /[category]:[command-name] required-value --option1=custom
  /[category]:[command-name] required-value --option1=value --flag
```

## Process

This command performs the following steps:

### Step 1: [Step Name]

[Description of what happens in this step]

- [Substep or detail 1]
- [Substep or detail 2]
- [Substep or detail 3]

### Step 2: [Step Name]

[Description of what happens in this step]

**Tools used:**
- `[Tool 1]`: [Purpose]
- `[Tool 2]`: [Purpose]

**Process:**
1. [Substep 1]
2. [Substep 2]
3. [Substep 3]

### Step 3: [Step Name]

[Description of what happens in this step]

**Output:**
- [What gets produced]
- [Where it gets stored]
- [How it's formatted]

## Expected Arguments

Parse the following from the user's command:

- `required-arg` (required): [Description of required argument]
  - Format: [Expected format]
  - Validation: [How to validate]
  - Example: `example-value`
  - Error if missing: "Please provide [argument]: /[category]:[command-name] <required-arg>"

- `optional-arg` (optional): [Description of optional argument]
  - Format: [Expected format]
  - Default: [Default value if not provided]
  - Example: `example-value`

- `--option1` (optional): [Description of option]
  - Values: [Valid values or format]
  - Default: `default-value`
  - Example: `--option1=example`

- `--option2` (optional): [Description of option]
  - Values: [Valid values or format]
  - Default: `default-value`
  - Example: `--option2=example`

- `--flag` (optional): [Description of flag]
  - Effect: [What this flag does]
  - Default: `false`

## Examples

### Example 1: [Example Scenario - e.g., "Basic Usage"]

```
User: /[category]:[command-name] example-argument

Process:
1. [What happens first]
2. [What happens second]
3. [What happens third]

Result:
[Expected output or behavior]
```

### Example 2: [Example Scenario - e.g., "With Optional Argument"]

```
User: /[category]:[command-name] required-arg optional-arg

Process:
1. Parse both arguments
2. [Process with optional arg]
3. [Enhanced behavior]

Result:
[Expected output showing difference from Example 1]
```

### Example 3: [Example Scenario - e.g., "With Options"]

```
User: /[category]:[command-name] required-arg --option1=custom --flag

Process:
1. Parse arguments and options
2. Apply custom configuration
3. Execute with flag behavior

Result:
[Expected output with custom behavior]
```

## Output Format

```
[Define the expected output structure]

Example:

[HEADER]
========

Section 1: [Name]
- Item 1: [Details]
- Item 2: [Details]

Section 2: [Name]
- Item 1: [Details]
- Item 2: [Details]

[FOOTER/SUMMARY]
----------------
[Summary information]
[Next steps]
```

## Error Handling

### Missing Required Argument

```
Error: Missing required argument

Usage: /[category]:[command-name] <required-arg> [optional-arg] [options]

Example: /[category]:[command-name] example-value
```

### Invalid Argument Format

```
Error: Invalid format for [argument-name]

Expected: [format description]
Received: [what was provided]

Example: /[category]:[command-name] correct-format
```

### Invalid Option Value

```
Error: Invalid value for --option1

Valid values: [list of valid values]
Received: [invalid value]

Example: /[category]:[command-name] arg --option1=valid-value
```

### [Command-Specific Error]

```
Error: [Specific error message]

Cause: [What caused the error]

Solution:
1. [How to fix]
2. [Alternative approach]

Help: See /[category]:[related-command] or [documentation link]
```

## Integration

This command is part of the **[category-name]** workflow and integrates with:

### Related Commands in Category

- **`/[category]:[command-1]`**: [How it relates - before/after/alternative]
- **`/[category]:[command-2]`**: [How it relates - before/after/alternative]
- **`/[category]:[command-3]`**: [How it relates - before/after/alternative]

### Typical Workflow

```
1. /[category]:[command-1]  [first-step-description]
   ↓
2. /[category]:[command-name]  ← YOU ARE HERE
   ↓
3. /[category]:[command-3]  [next-step-description]
```

### Integration with Other Categories

- **`/[other-category]:[command]`**: [How it integrates across categories]
- **[Tool/System]**: [External integrations]

## Category Context

**[Category Name]** commands provide:

- [Purpose 1 of category]
- [Purpose 2 of category]
- [Purpose 3 of category]

This command specifically handles: [specific responsibility within category]

## Notes

- **When to use**: [Situations where this command is appropriate]
- **When not to use**: [Situations to use alternatives]
- **Alternatives**: [Other commands or approaches]
- **Prerequisites**: [What needs to exist before running]
- **Side effects**: [What this command changes or affects]
- **Idempotency**: [Safe to run multiple times? What changes?]

## Best Practices

1. **[Best Practice 1]**: [Why and how]
2. **[Best Practice 2]**: [Why and how]
3. **[Best Practice 3]**: [Why and how]

## Troubleshooting

**Issue: [Common Issue 1]**
- Symptom: [How to recognize this issue]
- Cause: [What causes it]
- Solution: [How to fix]

**Issue: [Common Issue 2]**
- Symptom: [How to recognize this issue]
- Cause: [What causes it]
- Solution: [How to fix]

**Issue: [Common Issue 3]**
- Symptom: [How to recognize this issue]
- Cause: [What causes it]
- Solution: [How to fix]

## See Also

- [Link to category documentation or main command]
- [Link to related skills]
- [Link to external documentation]

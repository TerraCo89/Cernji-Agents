---
name: slash-command-builder
description: Guide for creating and managing slash commands. Use this skill when users want to create new slash commands or manage/organize existing slash commands. Provides interactive workflows, templates, and validation tools.
---

# Slash Command Builder

Expert skill for creating, managing, and organizing slash commands in Claude Code. Provides interactive workflows, validation tools, and best practices for building effective slash commands.

## When to Use This Skill

Use this skill when the user:
- Wants to create a new slash command
- Asks how to create a slash command
- Needs to organize or refactor existing slash commands
- Wants to validate slash command structure
- Asks about slash command patterns or best practices
- Needs to list or explore existing commands

**Trigger phrases:**
- "Create a slash command for..."
- "I want to add a new slash command"
- "How do I create a slash command?"
- "List all my slash commands"
- "Organize my slash commands"
- "Validate my slash commands"
- "What slash command patterns exist?"

## What This Skill Does

Provides comprehensive support for slash command development:

1. **Interactive Creation**: Guided workflow with questions to create well-structured slash commands
2. **Pattern Templates**: Multiple templates for different command patterns
3. **Validation**: Automated checks for YAML frontmatter, structure, and quality
4. **Management**: Tools to list, organize, and refactor existing commands
5. **Best Practices**: Guidelines and examples from your existing codebase

## Core Workflow: Creating a New Slash Command

When a user wants to create a new slash command, follow this interactive workflow:

### Step 1: Understand the Purpose

Ask the user to clarify what the command should do:

```
What should this slash command do?

Examples:
- "Analyze code quality and suggest improvements"
- "Generate API documentation from code"
- "Run security checks on dependencies"
- "Deploy to staging environment"
```

**Key questions to ask:**
1. What is the command's primary purpose?
2. Who will use it? (developers, stakeholders, automation)
3. What's the expected output?

### Step 2: Determine the Command Pattern

Based on the purpose, identify the appropriate pattern:

**Pattern 1: Simple Delegation** (delegate to existing skill)
- When: The command just invokes an existing skill with arguments
- Example: `/fetch-docs` delegates to `doc-fetcher` skill
- Use when: Core logic already exists in a skill

**Pattern 2: Skill Invocation** (invoke skill with parameters)
- When: The command invokes a skill that needs user input
- Example: `/research` invokes `deep-researcher` skill
- Use when: Skill handles complex multi-step workflow

**Pattern 3: Complex Workflow** (multi-step process with validation)
- When: Command orchestrates multiple tools/scripts with validation steps
- Example: `/speckit.specify` runs scripts, validates output, handles errors
- Use when: Need tight integration with scripts, validation, error handling

**Pattern 4: Nested Command** (part of a category)
- When: Command belongs to a logical grouping
- Example: `/career:analyze-job`, `/career:tailor-resume`
- Use when: Multiple related commands share a domain

Ask the user which pattern fits best, or suggest one based on their description.

### Step 3: Determine Command Name

Generate a command name following conventions:

**Naming rules:**
- Use kebab-case: `analyze-code`, `generate-docs`
- Be descriptive but concise (2-4 words)
- Use verb-noun format when possible: `fetch-docs`, `analyze-job`
- For nested commands: `category:action` (e.g., `career:analyze-job`)

**Ask the user:**
```
Suggested command name: /your-suggested-name

Is this name okay, or would you prefer something else?
```

### Step 4: Identify Required Tools

Determine what tools the command needs:

**Common tool categories:**
- Read-only: `Read`, `Grep`, `Glob`, `WebFetch`, `WebSearch`
- File modification: `Write`, `Edit`
- Execution: `Bash`
- Delegation: `SlashCommand`, `Skill`, `Task`
- MCP tools: `mcp__*` tools for specific integrations

**Ask the user:**
```
What tools should this command use?

Based on your description, I suggest:
- [List of relevant tools]

Should I add any others?
```

### Step 5: Determine Arguments

Define the command's arguments:

**Argument types:**
- Required: `<arg-name>`
- Optional: `[arg-name]`
- Flags: `--flag-name`
- Key-value: `--key=value`

**Ask the user:**
```
What arguments should this command accept?

Examples:
- /your-command <required-arg> [optional-arg]
- /your-command [file-path] --option=value
- /your-command (no arguments)

Your preference?
```

### Step 6: Create the Command File

Use the appropriate template based on the pattern selected:

**For Simple Delegation:**
```markdown
---
description: Brief description of what this command does
allowed-tools: Skill
---

# Command Name

## Purpose
[What this command accomplishes]

## Syntax
\`\`\`
/command-name [arguments]
\`\`\`

## Process

**IMPORTANT:** Invoke the `skill-name` skill to handle this request.

\`\`\`
Skill: skill-name
\`\`\`

After invoking the skill, the skill will:
1. [Step 1]
2. [Step 2]
3. [Return results]

## Expected Arguments

Parse the following from the user's command:
- `arg1` (required): Description
- `--option` (optional): Description

## Examples

### Example 1: Basic Usage
\`\`\`
User: /command-name basic-arg
Result: [Expected outcome]
\`\`\`

## Error Handling

If arguments are malformed or missing:
- Missing required arg: "Please provide [arg]: /command-name <arg>"
- Invalid format: "Invalid [arg] format. Expected: [format]"
```

**For Complex Workflow:**
Use `.claude/commands/speckit.specify.md` as reference - includes script execution, validation steps, error handling.

**For Nested Command:**
Create in subdirectory: `.claude/commands/category/command-name.md`

### Step 7: Generate the File

1. **Determine file path:**
   - Simple: `.claude/commands/command-name.md`
   - Nested: `.claude/commands/category/command-name.md`

2. **Fill in template:**
   - Replace placeholders with actual values
   - Add concrete examples
   - Document error cases
   - Include usage notes

3. **Create the file** using Write tool

4. **Report success:**
   ```
   Created slash command: /command-name
   Location: .claude/commands/command-name.md

   Test it by typing: /command-name [arguments]
   ```

### Step 8: Optional - Create Companion Skill

If the command needs a companion skill (Pattern 2 or 3), ask:

```
This command would benefit from a dedicated skill to handle the logic.

Should I create a companion skill called "skill-name"?

The skill would:
- [Capability 1]
- [Capability 2]
- [Capability 3]
```

If yes, use the `skill-creator` skill to create it.

## Management Workflows

### List All Slash Commands

Use the bundled `list_commands.py` script:

```bash
python .claude/skills/slash-command-builder/scripts/list_commands.py
```

**Output format:**
```
Slash Commands in .claude/commands/
=====================================

General Commands:
  /fetch-docs              - Fetch library documentation from Context7
  /research                - Conduct parallel multi-angle research

Career Commands (career/):
  /career:analyze-job      - Analyze job posting requirements
  /career:tailor-resume    - Tailor resume for specific job
  /career:cover-letter     - Generate cover letter
  [... more career commands]

Speckit Commands:
  /speckit.specify         - Create feature specification
  /speckit.plan            - Generate implementation plan
  /speckit.tasks           - Generate task list
  [... more speckit commands]

Total: 32 commands
```

### Validate Slash Commands

Use the bundled `validate_command.py` script:

```bash
python .claude/skills/slash-command-builder/scripts/validate_command.py .claude/commands/
```

**Checks performed:**
- YAML frontmatter syntax
- Required fields (description)
- Markdown structure
- Tool references (if `allowed-tools` specified)
- Argument hint format

**Output:**
```
Validating slash commands...

✓ fetch-docs.md - Valid
✓ research.md - Valid
⚠ career/analyze-job.md - Warning: Missing allowed-tools
✗ custom-command.md - Error: Invalid YAML frontmatter

Summary: 30 valid, 1 warning, 1 error
```

### Organize Commands

When commands become disorganized, suggest creating categories:

**Identify categories:**
1. Group related commands by domain
2. Suggest category names
3. Create subdirectories
4. Move commands

**Example:**
```
I notice you have many career-related commands. Should I organize them?

Suggested structure:
  career/
    - analyze-job.md
    - tailor-resume.md
    - cover-letter.md
    - find-examples.md
    [... more]

This would change:
  /analyze-job → /career:analyze-job
  /tailor-resume → /career:tailor-resume

Proceed?
```

## Command Patterns Reference

For detailed patterns and examples, see [references/command-patterns.md](./references/command-patterns.md).

### Quick Pattern Guide

| Pattern | When to Use | Example | Complexity |
|---------|-------------|---------|------------|
| Simple Delegation | Invoke existing skill | `/fetch-docs` | Low |
| Skill Invocation | Skill needs parameters | `/research` | Low-Medium |
| Complex Workflow | Multi-step with validation | `/speckit.specify` | High |
| Nested Command | Part of category | `/career:analyze-job` | Low-Medium |

## Best Practices

For comprehensive guidelines, see [references/best-practices.md](./references/best-practices.md).

### Quick Guidelines

**Do:**
- Use clear, descriptive names
- Document all arguments
- Provide concrete examples
- Handle errors gracefully
- Link to related skills/commands

**Don't:**
- Create commands that duplicate existing ones
- Use vague descriptions
- Skip error handling
- Forget to test with real arguments
- Overcomplicate simple tasks

### When to Create a Slash Command vs Skill

**Create a Slash Command when:**
- Providing user-facing interface to existing functionality
- Need quick access to common workflows
- Want to simplify complex skill invocations
- Creating domain-specific shortcuts

**Create a Skill when:**
- Need reusable logic across multiple commands
- Providing deep domain expertise
- Bundling scripts, references, and assets
- Building interactive workflows

**Create Both when:**
- Command needs dedicated workflow logic (command delegates to skill)
- Example: `/fetch-docs` command → `doc-fetcher` skill

## Bundled Resources

### Scripts

- **`scripts/init_command.py`**: Initialize new slash command from template
  - Usage: `python scripts/init_command.py <command-name> --pattern <pattern> [--category <category>]`
  - Patterns: `simple`, `complex`, `nested`
  - Creates file with appropriate template

- **`scripts/validate_command.py`**: Validate slash command structure
  - Usage: `python scripts/validate_command.py <path-to-commands>`
  - Checks YAML, structure, references
  - Returns validation report

- **`scripts/list_commands.py`**: List and analyze slash commands
  - Usage: `python scripts/list_commands.py [--category <category>]`
  - Shows command hierarchy
  - Filters by category

### References

- **`references/command-patterns.md`**: Detailed explanation of command patterns with annotated examples
- **`references/best-practices.md`**: Comprehensive guidelines for effective slash commands
- **`references/example-commands.md`**: Real-world examples from the codebase with analysis

### Assets

- **`assets/templates/simple-command.md`**: Template for simple delegation pattern
- **`assets/templates/complex-command.md`**: Template for complex workflow pattern
- **`assets/templates/nested-command.md`**: Template for nested command pattern

## Examples

### Example 1: Create Simple Command

**User:** "Create a slash command to analyze code complexity"

**Workflow:**
1. Ask: "What should this command do?"
   - User: "Run complexity analysis and suggest refactoring"
2. Determine pattern: Simple Delegation (create skill first, then command)
3. Suggest name: `/analyze-complexity`
4. Identify tools: `Skill`, `Read`, `Grep`
5. Arguments: `[file-path]` (optional, default to current directory)
6. Create skill first using skill-creator
7. Create command that delegates to skill
8. Test with example file

### Example 2: Create Nested Command

**User:** "I want to add a deployment command to my devops workflow"

**Workflow:**
1. Ask: "What should this command do?"
   - User: "Deploy to staging environment and run health checks"
2. Determine pattern: Nested Command (part of devops category)
3. Suggest name: `/devops:deploy-staging`
4. Identify tools: `Bash`, `WebFetch`
5. Arguments: `[--skip-checks]` (optional)
6. Create `.claude/commands/devops/` directory if needed
7. Create `deploy-staging.md` in devops directory
8. Document workflow and error handling

### Example 3: Organize Existing Commands

**User:** "List all my slash commands"

**Workflow:**
1. Run `list_commands.py` script
2. Display organized list with categories
3. Identify potential improvements:
   - Suggest grouping related commands
   - Identify missing documentation
   - Detect duplicate functionality
4. Ask: "I notice several data-related commands. Should I create a `/data:` category?"
5. If yes, reorganize and update command paths

## Troubleshooting

**Issue: Command not recognized**
- Verify file exists in `.claude/commands/`
- Check YAML frontmatter is valid
- Ensure description field is present
- Restart Claude Code if needed

**Issue: Arguments not parsing correctly**
- Check argument-hint in YAML matches documentation
- Verify $ARGUMENTS is used correctly in command
- Test with various argument formats

**Issue: Tool not allowed**
- Add tool to `allowed-tools` in YAML frontmatter
- Verify tool name is correct (check available tools)
- Consider if tool should be in skill instead

**Issue: Command too complex**
- Consider breaking into multiple commands
- Create dedicated skill for complex logic
- Use nested commands for related workflows

## Validation Checklist

Before finalizing a slash command:

- [ ] YAML frontmatter is valid and complete
- [ ] Description is clear and concise
- [ ] Command name follows conventions
- [ ] Arguments are documented
- [ ] Examples are provided
- [ ] Error handling is documented
- [ ] Tools are listed in allowed-tools
- [ ] Links to skills/references are correct
- [ ] File is in correct location
- [ ] Tested with real arguments

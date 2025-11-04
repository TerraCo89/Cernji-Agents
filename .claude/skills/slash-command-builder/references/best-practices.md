# Slash Command Best Practices

Comprehensive guidelines for creating effective, maintainable slash commands.

## Core Principles

### 1. Clear Purpose

Every slash command should have a single, well-defined purpose.

**Good:**
```markdown
/analyze-code - Analyze code complexity and suggest refactoring
```

**Bad:**
```markdown
/do-stuff - Analyze code, run tests, deploy to prod, make coffee
```

**Guidelines:**
- One command = one primary task
- If you find yourself describing multiple unrelated things, split into multiple commands
- Command name should clearly indicate purpose

### 2. Intuitive Naming

Command names should be:
- Descriptive but concise
- Use verb-noun format when possible
- Follow kebab-case convention
- 2-4 words maximum

**Good examples:**
- `/fetch-docs` (verb-noun)
- `/analyze-job` (verb-noun)
- `/tailor-resume` (verb-noun)
- `/generate-spec` (verb-noun)

**Bad examples:**
- `/d` (too cryptic)
- `/fetch-the-documentation-from-context7` (too verbose)
- `/FetchDocs` (wrong case)
- `/fetch_docs` (wrong separator)

### 3. Consistent Documentation

Every command must have:
- ✓ Clear description in YAML frontmatter
- ✓ Purpose section explaining what it does
- ✓ Syntax with examples
- ✓ Expected arguments documentation
- ✓ At least 2-3 usage examples
- ✓ Error handling guidance

**Template:**
```markdown
---
description: Brief, clear description under 100 characters
allowed-tools: Tool1, Tool2
argument-hint: [optional-arg]
---

# Command Name

## Purpose
[1-2 sentences explaining what this accomplishes]

## Syntax
[Usage patterns with examples]

## Process
[How the command works]

## Expected Arguments
[All arguments documented]

## Examples
[Multiple concrete examples]

## Error Handling
[Common errors and solutions]
```

---

## Naming Conventions

### Command Names

**Format:** `kebab-case`

**Rules:**
- Lowercase only
- Hyphens to separate words
- No underscores
- No special characters
- Start with letter
- Max 40 characters

**Examples:**
```
analyze-code          ✓
fetch-docs            ✓
generate-report       ✓
analyze_code          ✗ (underscore)
AnalyzeCode          ✗ (camelCase)
analyze-code-quality-and-suggest-improvements  ✗ (too long)
```

### Nested Commands

**Format:** `category:command` or `category.command`

**Rules:**
- Pick one separator and stick with it (`:` or `.`)
- Category is lowercase, single word or kebab-case
- Keep category hierarchy flat (avoid: `cat1:cat2:command`)

**Examples:**
```
career:analyze-job     ✓
career:tailor-resume   ✓
speckit.specify        ✓
speckit.plan           ✓
dev:ops:deploy         ✗ (too nested)
```

### Category Organization

**When to create a category:**
- You have 3+ related commands
- Commands share a common domain
- Logical grouping improves discoverability

**Category examples:**
- `career/` - Career application commands
- `devops/` - Deployment and infrastructure
- `data/` - Data processing and analysis
- `japanese/` - Language learning tools

---

## Argument Design

### Argument Types

**Required Arguments:** `<arg-name>`
```
/command <required-input>
```

**Optional Arguments:** `[arg-name]`
```
/command [optional-input]
```

**Flags:** `--flag-name`
```
/command --verbose
```

**Key-Value Options:** `--key=value`
```
/command --depth=thorough
```

### Argument Hints

Use `argument-hint` in YAML frontmatter to show expected arguments:

```yaml
argument-hint: [job-url]               # Optional URL
argument-hint: <file-path>             # Required path
argument-hint: [query] [--option]      # Optional query with flag
```

**Guidelines:**
- Match your documentation
- Use brackets/angles correctly: `[]` = optional, `<>` = required
- Keep hints concise
- Show most common usage

### Validation

Always validate arguments:

```markdown
## Expected Arguments

Parse the following from the user's command:

- `job_url` (required): URL to job posting
  - Format: https://company.com/jobs/123
  - Validation: Must be valid URL
  - Error: "Invalid job URL. Expected format: https://..."

- `--depth` (optional): Research depth (quick, medium, thorough)
  - Default: medium
  - Validation: Must be one of: quick, medium, thorough
  - Error: "Invalid depth. Use: quick, medium, or thorough"
```

---

## Documentation Standards

### Description Field

**YAML frontmatter `description` field:**
- Clear and concise (under 100 characters)
- Describes what, not how
- Uses active voice
- Avoids implementation details

**Good:**
```yaml
description: Fetch library documentation from Context7 and save to ai_docs/
```

**Bad:**
```yaml
description: Uses mcp__context7 tools to resolve library ID and get docs
```

### Examples Section

**Every command needs 2-3 examples minimum:**

**Example structure:**
```markdown
## Examples

### Example 1: Basic Usage
```
User: /command basic-arg
Result: [Expected outcome with details]
```

### Example 2: With Options
```
User: /command arg --option=value
Result: [Expected outcome showing how option affects behavior]
```

### Example 3: Error Case
```
User: /command invalid-arg
Result: Error: [Error message and guidance]
```
```

**Guidelines:**
- Show realistic usage
- Include expected output
- Cover edge cases
- Demonstrate options
- Show error handling

---

## Error Handling

### Required Sections

Every command must document error handling:

```markdown
## Error Handling

If arguments are malformed or missing:
- Missing required argument: "Please provide <argument>: /command <arg>"
- Invalid format: "Invalid format for <arg>. Expected: [format]"
- Unknown option: "Unknown option: --xyz. Valid options: [list]"

For specific error scenarios:
1. [Error type]: [Error message and solution]
2. [Error type]: [Error message and solution]
```

### Error Message Guidelines

**Good error messages:**
- Clear about what went wrong
- Suggest how to fix
- Show correct usage
- Actionable

**Good:**
```
Error: Invalid job URL
Expected format: https://company.com/jobs/123
Example: /career:analyze-job https://example.com/careers/engineer
```

**Bad:**
```
Error: Invalid input
```

---

## Tool Selection

### Allowed Tools

**Document all tools in frontmatter:**

```yaml
allowed-tools: Read, Write, Grep, Bash, WebFetch
```

**Guidelines:**
- Only list tools the command actually uses
- Keep list minimal (delegate to skills when possible)
- Order by importance/frequency of use

### Tool Categories

**Read-only tools:**
- `Read`, `Grep`, `Glob` - File operations
- `WebFetch`, `WebSearch` - Web content
- `Bash` (read-only commands) - Info gathering

**Modification tools:**
- `Write`, `Edit` - File changes
- `Bash` (write commands) - System changes

**Delegation tools:**
- `Skill` - Invoke skills
- `SlashCommand` - Invoke other commands
- `Task` - Launch agents

**MCP tools:**
- `mcp__context7__*` - Context7 integration
- `mcp__sqlite__*` - Database operations
- `mcp__linear__*` - Linear integration

### When to Use Skills vs Tools

**Use Skill when:**
- Logic is complex and reusable
- Multiple steps required
- Need bundled resources
- Want to separate concerns

**Use Tools directly when:**
- Simple, one-off operations
- Command-specific logic
- Quick file operations
- Direct tool invocation is clearer

---

## Pattern-Specific Guidelines

### Simple Delegation

**Best practices:**
- Document what skill does
- Don't duplicate skill documentation
- Link to skill for details
- Focus on user interface

**Template:**
```markdown
## Process

**IMPORTANT:** Invoke the `skill-name` skill to handle this request.

After invoking the skill, the skill will:
1. [High-level step]
2. [High-level step]
3. [Return results]

For detailed workflow, see the skill-name skill documentation.
```

### Complex Workflow

**Best practices:**
- Document every step clearly
- Show script execution
- Explain validation stages
- Handle all error cases
- Provide detailed output format

**Required sections:**
- User Input (with $ARGUMENTS)
- Outline (step-by-step workflow)
- Validation (what gets checked)
- Output Format (structured results)
- Error Handling (comprehensive)

### Nested Commands

**Best practices:**
- Maintain category consistency
- Document category in command
- Link to related commands in category
- Use consistent separator (`:` or `.`)

**Example:**
```markdown
## Integration

This command is part of the career application workflow:

Related commands:
- `/career:analyze-job` - Analyze job requirements
- `/career:tailor-resume` - Tailor resume for job
- `/career:cover-letter` - Generate cover letter
- `/career:apply` - Complete application workflow
```

---

## Testing Commands

### Before Committing

**Checklist:**
- [ ] Validate YAML frontmatter syntax
- [ ] Test with valid arguments
- [ ] Test with invalid arguments
- [ ] Test with missing arguments
- [ ] Test with edge cases
- [ ] Verify error messages
- [ ] Check tool permissions
- [ ] Validate documentation completeness

**Use validation script:**
```bash
python .claude/skills/slash-command-builder/scripts/validate_command.py .claude/commands/your-command.md
```

### Real User Testing

**Test scenarios:**
1. **Happy path**: Command works as expected
2. **Missing args**: Graceful error handling
3. **Invalid args**: Clear error messages
4. **Edge cases**: Boundary conditions work

**Example test log:**
```
Test 1: /analyze-code src/main.py
✓ Analyzed successfully, showed metrics

Test 2: /analyze-code
✗ Error message unclear
→ Fix: Improve error to show expected usage

Test 3: /analyze-code nonexistent.py
✓ Error: "File not found: nonexistent.py"

Test 4: /analyze-code . --depth=thorough
✓ Analyzed entire directory with detailed output
```

---

## Maintenance

### Versioning

When updating commands:

1. **Minor updates** (documentation, examples):
   - Update directly
   - No version tracking needed

2. **Major changes** (arguments, behavior):
   - Document in commit message
   - Update all affected documentation
   - Test thoroughly
   - Consider backward compatibility

### Deprecation

When retiring a command:

1. **Mark as deprecated** in description:
   ```yaml
   description: [DEPRECATED] Use /new-command instead - Old functionality
   ```

2. **Add deprecation notice** in command:
   ```markdown
   ## ⚠️ DEPRECATED

   This command is deprecated. Please use `/new-command` instead.

   Migration guide:
   - Old: /old-command <arg>
   - New: /new-command <arg> --option
   ```

3. **Grace period**: Keep deprecated command for 1-2 weeks

4. **Remove**: Delete file after grace period

---

## Common Pitfalls

### ❌ Avoid

1. **Vague descriptions**
   ```yaml
   description: Does stuff  # ✗
   description: Analyzes code complexity and suggests refactoring  # ✓
   ```

2. **Missing error handling**
   ```markdown
   # No error handling documented  # ✗
   ## Error Handling with detailed cases  # ✓
   ```

3. **No examples**
   ```markdown
   # Just syntax, no examples  # ✗
   ## Examples with 3+ realistic scenarios  # ✓
   ```

4. **Incomplete argument documentation**
   ```markdown
   Arguments: <input>  # ✗

   ## Expected Arguments
   - `input` (required): Path to input file
     - Format: Absolute or relative path
     - Validation: Must exist and be readable
     - Example: /path/to/file.txt
   ```

5. **Tools not listed**
   ```yaml
   # Uses WebFetch but not in allowed-tools  # ✗
   allowed-tools: WebFetch, Read  # ✓
   ```

6. **TODO placeholders in production**
   ```markdown
   [TODO: Add description]  # ✗ - Complete before committing
   ```

---

## Command Lifecycle

### 1. Planning
- Identify purpose
- Choose pattern
- Design arguments
- Plan examples

### 2. Creation
- Use init script or template
- Fill in documentation
- Implement workflow
- Add error handling

### 3. Validation
- Run validation script
- Check frontmatter
- Verify structure
- Test examples

### 4. Testing
- Test with real arguments
- Verify error handling
- Check edge cases
- Get user feedback

### 5. Maintenance
- Update as needed
- Fix issues promptly
- Improve documentation
- Deprecate when obsolete

---

## Quick Reference Card

```
✓ DO:
  - Use clear, descriptive names
  - Document all arguments
  - Provide 2-3+ examples
  - Handle errors gracefully
  - Test before committing
  - Keep commands focused
  - Use skills for complex logic
  - Link to related commands

✗ DON'T:
  - Use vague descriptions
  - Skip error handling
  - Forget argument validation
  - Create duplicate functionality
  - Mix multiple purposes
  - Use inconsistent naming
  - Leave TODO placeholders
  - Forget to test
```

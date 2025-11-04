# Slash Command Patterns

This document explains the four main patterns for slash commands with detailed examples from your codebase.

## Pattern Overview

| Pattern | Complexity | Use Case | Example |
|---------|------------|----------|---------|
| Simple Delegation | Low | Invoke existing skill | `/fetch-docs` |
| Skill Invocation | Low-Medium | Skill needs parameters | `/research` |
| Complex Workflow | High | Multi-step with validation | `/speckit.specify` |
| Nested Command | Low-Medium | Part of category | `/career:analyze-job` |

---

## Pattern 1: Simple Delegation

**When to use:**
- The command just invokes an existing skill
- No complex argument parsing needed
- Skill handles all logic and workflow
- Command is primarily a user-friendly interface

**Structure:**
```markdown
---
description: Brief description
allowed-tools: Skill
---

# Command Name

## Purpose
What this accomplishes

## Process
**IMPORTANT:** Invoke the `skill-name` skill to handle this request.

```
Skill: skill-name
```

## Expected Arguments
- Arguments passed to skill
```

### Real Example: `/fetch-docs`

**File:** `.claude/commands/fetch-docs.md`

**Analysis:**
- **Purpose**: Fetch library documentation from Context7
- **Pattern**: Pure delegation to `doc-fetcher` skill
- **Workflow**:
  1. Parse command arguments (library name, options)
  2. Invoke `doc-fetcher` skill
  3. Skill handles resolution, fetching, saving
  4. Report results

**Key Features:**
- Clean separation: command handles UI, skill handles logic
- Argument parsing documented in "Expected Arguments"
- Multiple usage examples
- Clear error handling delegation

**When to use this pattern:**
- You have a robust skill that handles all logic
- Command provides syntactic sugar for users
- No need for complex validation before skill invocation

---

## Pattern 2: Skill Invocation

**When to use:**
- Similar to Simple Delegation, but skill needs structured input
- Command may do some pre-processing
- Skill is invoked with specific parameters

**Structure:**
```markdown
---
description: Brief description
allowed-tools: Task, Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# Command Name

## Purpose
What this accomplishes

## Process
**IMPORTANT:** Invoke the `skill-name` skill to handle this request.

```
Skill: skill-name
```

After invoking, the skill will:
1. [Specific step]
2. [Specific step]
3. [Specific step]
```

### Real Example: `/research`

**File:** `.claude/commands/research.md`

**Analysis:**
- **Purpose**: Conduct parallel multi-angle research
- **Pattern**: Delegates to `deep-researcher` skill
- **Workflow**:
  1. Parse research topic and options
  2. Invoke `deep-researcher` skill
  3. Skill decomposes into research avenues
  4. Launches parallel agents
  5. Synthesizes findings

**Key Features:**
- Command documents what skill will do
- Clear option parsing (--depth, --avenues, --focus)
- Examples show different usage patterns
- Integration notes for related commands

**When to use this pattern:**
- Skill handles complex multi-step workflow
- User needs to understand what skill will do
- Command provides structured interface to skill capabilities

---

## Pattern 3: Complex Workflow

**When to use:**
- Multi-step process with validation
- Script execution with output parsing
- Tight integration between command and tooling
- Need extensive error handling

**Structure:**
```markdown
---
description: Brief description
argument-hint: [arguments]
---

# Command Name

## User Input
```text
$ARGUMENTS
```

## Outline
1. Parse input from $ARGUMENTS
2. Execute script/tool
3. Validate output
4. Process results
5. Handle errors

## Validation
- Check condition 1
- Verify condition 2
- Ensure condition 3

## Output Format
[Structured output definition]
```

### Real Example: `/speckit.specify`

**File:** `.claude/commands/speckit.specify.md`

**Analysis:**
- **Purpose**: Create feature specification from natural language
- **Pattern**: Complex workflow with validation
- **Workflow**:
  1. Generate short name from description
  2. Run PowerShell script to create feature branch and files
  3. Parse JSON output for paths
  4. Load templates
  5. Fill specification sections
  6. Validate specification quality
  7. Create checklist
  8. Handle clarifications interactively
  9. Report completion

**Key Features:**
- Uses `$ARGUMENTS` for direct input
- Script integration with JSON parsing
- Multi-stage validation
- Interactive clarification workflow
- Comprehensive error handling
- Quality checklist creation

**When to use this pattern:**
- Need tight control over execution flow
- Script execution is critical
- Multiple validation stages required
- Interactive user input needed
- Complex state management

**Complexity indicators:**
- Script execution with output parsing
- Validation checklists
- User prompts for clarification
- File generation with templates
- Multi-iteration workflows

---

## Pattern 4: Nested Command

**When to use:**
- Command belongs to logical grouping
- Related commands share a domain
- Want to organize by category
- Create a cohesive command namespace

**Structure:**
```markdown
---
description: Brief description
allowed-tools: Tool1, Tool2, Tool3
argument-hint: [arguments]
---

# Command Name

## Purpose
What this accomplishes (within category context)

## Syntax
/category:command-name [arguments]

## Process
[Steps specific to this command]
```

### Real Example: `/career:analyze-job`

**File:** `.claude/commands/career/analyze-job.md`

**Analysis:**
- **Category**: `career`
- **Command**: `analyze-job`
- **Full name**: `/career:analyze-job`
- **Purpose**: Analyze job posting and assess match
- **Workflow**:
  1. Process job into RAG pipeline
  2. Fetch and cache job data
  3. Load job analysis and master resume
  4. Query RAG for deeper insights
  5. Perform match assessment
  6. Generate recommendation

**Key Features:**
- Part of career command family
- Integrates with other career commands
- Uses multiple tools (SlashCommand, Task)
- Clear category-specific workflow
- Related to `/career:tailor-resume`, `/career:cover-letter`, etc.

**When to use this pattern:**
- You have multiple related commands
- Commands share a domain or purpose
- Want to namespace commands logically
- Users benefit from grouping

**Category examples:**
- `career/` - Career application commands
- `speckit.` - Feature specification commands (uses dot notation)
- `japanese/` - Japanese learning commands
- `devops/` - Deployment and infrastructure commands

**Naming conventions:**
- Directory: `category/command.md`
- Command: `/category:command` or `/category.command`
- Use consistent separator (`:` or `.`) within category

---

## Pattern Selection Guide

### Decision Tree

```
Do you have an existing skill that handles the logic?
├─ YES → Use Pattern 1 (Simple Delegation) or Pattern 2 (Skill Invocation)
│         Does the skill need structured parameters?
│         ├─ YES → Pattern 2
│         └─ NO  → Pattern 1
│
└─ NO → Do you need to execute scripts or perform validation?
          ├─ YES → Use Pattern 3 (Complex Workflow)
          └─ NO  → Is this command part of a related group?
                    ├─ YES → Use Pattern 4 (Nested Command)
                    └─ NO  → Create skill first, then use Pattern 1
```

### Quick Checklist

**Use Simple Delegation (Pattern 1) when:**
- ✓ Skill already exists
- ✓ Command is just a user-friendly alias
- ✓ No complex preprocessing needed

**Use Skill Invocation (Pattern 2) when:**
- ✓ Skill exists and is robust
- ✓ Skill needs structured input
- ✓ Users benefit from understanding workflow

**Use Complex Workflow (Pattern 3) when:**
- ✓ Need to execute scripts
- ✓ Multi-stage validation required
- ✓ Interactive user input needed
- ✓ Tight integration with tooling

**Use Nested Command (Pattern 4) when:**
- ✓ Command belongs to a category
- ✓ Related commands exist or planned
- ✓ Want organized namespace

---

## Mixing Patterns

Commands can combine patterns. For example:

**Nested + Simple Delegation:**
```
/career:analyze-job (nested command that delegates to skill)
```

**Nested + Complex Workflow:**
```
/speckit.specify (nested with dot notation, complex workflow)
```

**Key principle:** Choose the pattern that makes the command most maintainable and user-friendly.

---

## Anti-Patterns

**Don't:**
- Create commands without skills for complex logic
- Mix multiple patterns unnecessarily
- Duplicate functionality across patterns
- Create deeply nested categories (`/cat1:cat2:command`)
- Skip documentation for "simple" commands
- Forget error handling

**Do:**
- Keep commands focused and single-purpose
- Document all patterns clearly
- Use skills for reusable logic
- Provide comprehensive examples
- Handle errors gracefully
- Test with real arguments

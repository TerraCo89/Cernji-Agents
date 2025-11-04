# Example Slash Commands

Annotated real-world examples from your codebase with analysis and lessons learned.

## Example 1: `/fetch-docs` - Simple Delegation Pattern

**File:** `.claude/commands/fetch-docs.md`

### Full Command

```markdown
---
description: Fetch library documentation from Context7 and save it to ai_docs/ with proper categorization
allowed-tools: mcp__context7__resolve-library-id, mcp__context7__get-library-docs, Write, Bash
---

# Fetch Library Documentation

## Purpose
Fetch library documentation from Context7 and organize it in `ai_docs/` with category-based structure and metadata tracking.

## Syntax
```
/fetch-docs <library-name> [options]

Options:
  --topic=<topic>           # Fetch specific topic documentation
  --version=<version>       # Fetch specific version
  --tokens=<count>          # Override default token count (default: 5000)
  --refresh                 # Refresh existing documentation

Examples:
  /fetch-docs langgraph
  /fetch-docs nextjs --topic=routing
```

## Process

**IMPORTANT:** Invoke the `doc-fetcher` skill to handle this request.

```
Skill: doc-fetcher
```

[... rest of command ...]
```

### Analysis

**Pattern:** Simple Delegation

**Why this pattern works:**
- ✓ Clear delegation to `doc-fetcher` skill
- ✓ Comprehensive syntax documentation with options
- ✓ Multiple examples showing different usage patterns
- ✓ Skill handles all complex logic
- ✓ Command focuses on user interface

**What makes this excellent:**

1. **Clear description** (under 100 chars)
   ```yaml
   description: Fetch library documentation from Context7 and save it to ai_docs/ with proper categorization
   ```

2. **Comprehensive options** with clear format
   ```
   --topic=<topic>           # Fetch specific topic documentation
   --version=<version>       # Fetch specific version
   --tokens=<count>          # Override default token count (default: 5000)
   --refresh                 # Refresh existing documentation
   ```

3. **Multiple examples** showing progressive complexity
   ```
   /fetch-docs langgraph                              # Basic
   /fetch-docs nextjs --topic=routing                 # With topic
   /fetch-docs react --version=18                     # With version
   /fetch-docs playwright --topic=testing --tokens=8000  # Multiple options
   ```

4. **Tool listing** includes MCP-specific tools
   ```yaml
   allowed-tools: mcp__context7__resolve-library-id, mcp__context7__get-library-docs, Write, Bash
   ```

**Lessons:**
- Document all options clearly with defaults
- Show progression from simple to complex usage
- List specific MCP tools when using MCP servers
- Delegate complex logic to skills

---

## Example 2: `/research` - Skill Invocation Pattern

**File:** `.claude/commands/research.md`

### Key Sections

```markdown
---
description: Conduct parallel multi-angle research on programming topics by breaking down complex questions into specific investigation avenues
allowed-tools: Task, Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# Deep Research Command

## Purpose
Conduct comprehensive, parallel research on programming topics by breaking down complex questions into 3-10 specific investigation avenues and delegating to specialized sub-agents.

## Syntax
```
/research <research-topic> [options]

Options:
  --depth=<quick|medium|thorough>  # Research depth (default: medium)
  --avenues=<number>               # Number of research avenues (3-10, default: auto)
  --focus=<aspect>                 # Specific aspect to focus on
```

## Process

**IMPORTANT:** Invoke the `deep-researcher` skill to handle this request.

After invoking the skill, it will:
1. **Decompose**: Break the research topic into 3-10 specific investigation avenues
2. **Research in Parallel**: Launch specialized agents for each avenue
3. **Synthesize**: Combine findings into cohesive research report
4. **Present**: Formatted report with executive summary and recommendations
```

### Analysis

**Pattern:** Skill Invocation

**Why this pattern works:**
- ✓ Documents what skill will do after invocation
- ✓ Explains multi-step workflow clearly
- ✓ Shows user what to expect
- ✓ Provides context for complex process

**What makes this excellent:**

1. **Descriptive documentation** of skill behavior
   - Shows 4 main steps: Decompose, Research, Synthesize, Present
   - Explains parallelization
   - Sets expectations

2. **Option design** with clear choices
   ```
   --depth=<quick|medium|thorough>   # Enumerated options
   --avenues=<number>                # Numeric range
   --focus=<aspect>                  # Free-form text
   ```

3. **Use case documentation**
   ```markdown
   ## When to Use

   Use this command when you need to:
   - Investigate errors: Multiple potential root causes
   - Compare solutions: Different libraries, patterns
   - Research best practices: Official docs, community patterns
   - Explore implementations: Code examples from GitHub
   ```

4. **Integration notes** with related commands
   ```markdown
   ## Integration with Other Commands

   - /fetch-docs: Fetch detailed documentation after identifying libraries
   - /career:find-examples: Find portfolio examples after researching technologies
   ```

**Lessons:**
- Document skill workflow for transparency
- Enumerate options when choices are limited
- Explain when to use the command
- Link to related commands for workflows

---

## Example 3: `/speckit.specify` - Complex Workflow Pattern

**File:** `.claude/commands/speckit.specify.md`

### Key Sections

```markdown
---
description: Create or update the feature specification from a natural language feature description.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the branch
2. Run the script `.specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS"` with the short-name argument
3. Load `.specify/templates/spec-template.md` to understand required sections
4. Follow this execution flow:
   1. Parse user description from Input
   2. Extract key concepts from description
   3. For unclear aspects, make informed guesses (max 3 clarifications)
   4. Fill User Scenarios & Testing section
   5. Generate Functional Requirements
   6. Define Success Criteria
   7. Identify Key Entities
   8. Return: SUCCESS

5. Write the specification to SPEC_FILE
6. **Specification Quality Validation**:
   a. Create Spec Quality Checklist
   b. Run Validation Check
   c. Handle Validation Results

[... detailed validation workflow ...]
```

### Analysis

**Pattern:** Complex Workflow

**Why this pattern works:**
- ✓ Detailed step-by-step execution flow
- ✓ Script integration with JSON parsing
- ✓ Multi-stage validation
- ✓ Interactive clarification handling
- ✓ Comprehensive error handling

**What makes this excellent:**

1. **Uses `$ARGUMENTS`** for direct input access
   ```markdown
   ## User Input
   ```text
   $ARGUMENTS
   ```

   You **MUST** consider the user input before proceeding.
   ```

2. **Step-by-step execution** with numbered substeps
   ```markdown
   4. Follow this execution flow:
      1. Parse user description from Input
      2. Extract key concepts
      3. For unclear aspects, make informed guesses
      [...]
   ```

3. **Validation workflow** with detailed process
   ```markdown
   6. **Specification Quality Validation**:
      a. Create Spec Quality Checklist
      b. Run Validation Check
      c. Handle Validation Results
         - If all items pass: proceed
         - If items fail: fix and retry (max 3 iterations)
         - If clarifications needed: present options to user
   ```

4. **Structured clarification** with table format
   ```markdown
   ## Question [N]: [Topic]

   | Option | Answer | Implications |
   |--------|--------|--------------|
   | A      | [Option A] | [What this means] |
   | B      | [Option B] | [What this means] |
   | C      | [Option C] | [What this means] |
   ```

**Lessons:**
- Use `$ARGUMENTS` for complex input
- Number all steps for clarity
- Document validation stages explicitly
- Provide structured user interaction
- Limit iterations to prevent loops

---

## Example 4: `/career:analyze-job` - Nested Command Pattern

**File:** `.claude/commands/career/analyze-job.md`

### Key Sections

```markdown
---
description: Analyze a job posting to understand requirements and assess match with your background
allowed-tools: SlashCommand, Task
argument-hint: [job-url]
---

# Analyze Job Posting

Job URL: $ARGUMENTS

## Purpose
Assesses how well your background matches a job posting by comparing the structured job requirements against your master resume.

## Process

**Step 1: Process Job Posting into RAG Pipeline**
1. Run `/career:process-website $ARGUMENTS --type=job_posting`
2. Then run `/career:fetch-job $ARGUMENTS`
3. This is idempotent - if already cached, it will reuse existing data

**Step 2: Load Job Data and Master Resume**
Use the Task tool with subagent_type="data-access-agent" to load both datasets

**Step 2.5: Query RAG for Additional Insights (NEW)**
Use the RAG pipeline to extract deeper insights:
1. Query for requirements
2. Query for company culture
3. Query for responsibilities
4. Combine insights

**Step 3: Perform Match Assessment**
Compare your background to the job requirements and provide:
- Match Score (1-10)
- Skills Match Analysis
- Experience Match
- Keyword Coverage
- Application Strategy
```

### Analysis

**Pattern:** Nested Command (category: `career`)

**Why this pattern works:**
- ✓ Part of cohesive career workflow
- ✓ Integrates with other career commands
- ✓ Clear category namespace
- ✓ Shows relationship to workflow

**What makes this excellent:**

1. **Category organization**
   - File path: `.claude/commands/career/analyze-job.md`
   - Full name: `/career:analyze-job`
   - Related: `/career:tailor-resume`, `/career:cover-letter`, `/career:apply`

2. **Integration with other commands**
   ```markdown
   **Step 1: Process Job Posting into RAG Pipeline**
   1. Run `/career:process-website $ARGUMENTS --type=job_posting`
   2. Then run `/career:fetch-job $ARGUMENTS`
   ```

3. **Structured output format**
   ```markdown
   ## Output Format

   ```
   MATCH ASSESSMENT
   ================

   Company: {company}
   Role: {job_title}
   Match Score: {score}/10

   STRENGTHS
   ---------
   ✓ [List matching qualifications]

   GAPS
   ----
   ✗ [List missing requirements]
   ```
   ```

4. **Clear workflow steps** with semantic versioning (Step 2.5)
   - Shows evolution of command
   - Maintains backward compatibility
   - Documents new features

**Lessons:**
- Group related commands in categories
- Show integration points clearly
- Document output format explicitly
- Use semantic step numbering for additions

---

## Example 5: `/fetch-docs` vs `/research` - When to Choose Patterns

### `/fetch-docs` - Simple Delegation

**Scenario:** User needs library documentation

**Design decisions:**
- ✓ Single, well-defined task
- ✓ Existing skill handles complexity
- ✓ Command is UI layer only
- ✓ No complex preprocessing needed

**Result:** Clean delegation to `doc-fetcher` skill

### `/research` - Skill Invocation

**Scenario:** User needs multi-angle research

**Design decisions:**
- ✓ Complex multi-step workflow
- ✓ User benefits from understanding process
- ✓ Skill orchestrates parallel agents
- ✓ Command documents workflow clearly

**Result:** Skill invocation with detailed workflow documentation

**Key difference:**
- `/fetch-docs`: User doesn't need to know details → Simple Delegation
- `/research`: User benefits from understanding → Skill Invocation

---

## Example 6: Command Evolution - `/career:analyze-job`

### Version 1 (Initial)

```markdown
## Process

**Step 1: Process Job Posting**
1. Run `/career:fetch-job $ARGUMENTS`

**Step 2: Load Data**
Load job analysis and master resume

**Step 3: Perform Match Assessment**
Compare and provide match score
```

### Version 2 (Added RAG)

```markdown
## Process

**Step 1: Process Job Posting into RAG Pipeline**
1. Run `/career:process-website $ARGUMENTS --type=job_posting`
2. Then run `/career:fetch-job $ARGUMENTS`

**Step 2: Load Job Data and Master Resume**
[Same as before]

**Step 2.5: Query RAG for Additional Insights (NEW)**
Use the RAG pipeline to extract deeper insights

**Step 3: Perform Match Assessment**
[Enhanced with RAG insights]
```

**Evolution analysis:**
- ✓ Maintained backward compatibility
- ✓ Added RAG without breaking existing workflow
- ✓ Used "Step 2.5" to insert new step
- ✓ Marked new section with "(NEW)" label
- ✓ Enhanced output without changing format

**Lessons for command evolution:**
- Maintain backward compatibility when possible
- Use fractional step numbers for insertions
- Mark new features clearly
- Document changes in commit messages

---

## Quick Comparison Table

| Command | Pattern | Complexity | Key Feature |
|---------|---------|------------|-------------|
| `/fetch-docs` | Simple Delegation | Low | Clean skill delegation |
| `/research` | Skill Invocation | Medium | Workflow transparency |
| `/speckit.specify` | Complex Workflow | High | Multi-stage validation |
| `/career:analyze-job` | Nested | Medium | Category integration |

---

## Common Patterns Summary

### Simple Delegation Best For:
- Single-purpose commands
- Existing skill handles logic
- User doesn't need implementation details
- **Example:** `/fetch-docs`

### Skill Invocation Best For:
- Multi-step workflows
- User benefits from understanding process
- Skill orchestrates complex operations
- **Example:** `/research`

### Complex Workflow Best For:
- Script execution required
- Multi-stage validation needed
- Interactive user input
- **Example:** `/speckit.specify`

### Nested Command Best For:
- Related command groups
- Domain-specific workflows
- Integration with category
- **Example:** `/career:analyze-job`

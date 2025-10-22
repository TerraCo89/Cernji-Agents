# Skill Authoring Best Practices - Complete Guide

## Core Principles

### Conciseness is Critical
The context window is shared across system prompts, conversation history, other Skills, and user requests. Only SKILL.md metadata loads at startup; the full file loads when relevant. "Default assumption: Claude is already very smart" — avoid explaining concepts Claude understands.

**Good approach** (~50 tokens): Provide minimal, direct code examples
**Bad approach** (~150 tokens): Over-explain basic concepts like what PDFs are

### Degrees of Freedom
Match specificity to task fragility:
- **High freedom**: Text instructions for multi-approach tasks (code reviews)
- **Medium freedom**: Pseudocode with parameters (template-based workflows)
- **Low freedom**: Exact scripts for error-prone operations (database migrations)

### Multi-Model Testing
Test Skills with Claude Haiku, Sonnet, and Opus. What works for powerful models may need more guidance for faster ones.

---

## Skill Structure & Naming

### YAML Frontmatter Requirements
```yaml
---
name: [64 characters max]
description: [1024 characters max, include what it does and when to use]
---
```

### Naming Conventions
Use gerund form (verb + -ing):
- "Processing PDFs" ✓
- "Analyzing spreadsheets" ✓
- "Helper" or "Utils" ✗

### Effective Descriptions
Write in third person. Include both capability and trigger conditions.

*Good*: "Extracts text and tables from PDF files, fills forms. Use when working with PDFs or document extraction."

*Bad*: "Helps with documents"

---

## Progressive Disclosure Patterns

Keep SKILL.md under 500 lines. Split complex content into separate files loaded on-demand.

### Pattern 1: High-Level Guide with References
```markdown
# PDF Processing

## Quick start
[Core instructions]

## Advanced features
See [FORMS.md](FORMS.md) for form filling
See [REFERENCE.md](REFERENCE.md) for API
```

### Pattern 2: Domain-Specific Organization
Organize reference files by domain (finance.md, sales.md, product.md) so Claude loads only relevant context.

### Pattern 3: Conditional Details
Show basic content, link to specialized guides for advanced features.

### Critical Rules
- Avoid deeply nested references (keep one level deep from SKILL.md)
- Structure long files (100+ lines) with table of contents
- Use forward slashes in paths (`reference/guide.md`), never backslashes

---

## Workflows & Feedback Loops

### Complex Task Workflows
Break operations into clear steps. For multi-step processes, provide checklists Claude can copy and check off:

```
Task Progress:
- [ ] Step 1: Analyze the form
- [ ] Step 2: Create field mapping
- [ ] Step 3: Validate mapping
- [ ] Step 4: Fill the form
- [ ] Step 5: Verify output
```

### Validation Patterns
Implement validator → fix errors → repeat cycles to catch problems early before changes apply.

---

## Content Guidelines

### Avoid Time-Sensitive Information
Use "old patterns" sections for deprecated methods instead of date-based conditionals.

### Consistent Terminology
Pick one term per concept and use it throughout (not mixing "API endpoint," "URL," "route").

---

## Common Patterns

### Templates
Strict requirements: "ALWAYS use this exact structure"
Flexible guidance: "Use this sensible default, adapt as needed"

### Examples
Provide input/output pairs showing desired style and detail level.

### Conditional Workflows
Guide Claude through decision points with clear branching paths.

---

## Evaluation & Iteration

### Build Evaluations First
Create test scenarios BEFORE extensive documentation to ensure Skills solve real problems. Structure evaluations with clear expected behaviors.

### Iterative Development with Claude
1. Complete tasks manually to identify reusable context
2. Ask Claude to create a Skill capturing that pattern
3. Test with fresh Claude instance using the Skill
4. Observe behaviors and refine based on real usage

### Observation Focus
- Unexpected file navigation patterns
- Missed references or connections
- Overreliance on specific sections
- Ignored content

---

## Anti-Patterns to Avoid

- Windows-style paths (`\`) — use Unix forward slashes
- Too many options without defaults ("you can use X, Y, or Z...")
- Time-sensitive conditionals in documentation

---

## Advanced: Executable Code

### Error Handling
Scripts should solve problems, not punt to Claude. Handle errors explicitly with helpful messages.

### Utility Scripts
Provide pre-made scripts for deterministic operations rather than asking Claude to generate them. Benefits: reliability, token efficiency, consistency.

### Validation Pattern
For critical operations, use: analyze → create plan → validate → execute → verify

### Dependencies
List required packages explicitly and verify availability in code execution documentation.

### MCP Tool References
Use fully qualified names: `ServerName:tool_name` to avoid "tool not found" errors.

---

## Technical Notes

### Token Budget
Keep SKILL.md body under 500 lines for optimal performance.

### Runtime Environment
- File paths function as a filesystem; Claude reads on-demand
- Utility scripts execute without loading contents into context
- Reference files bundle complete resources with zero cost until accessed
- Progressive disclosure enabled through filesystem structure

---

## Effectiveness Checklist

**Core Quality**
- Description is specific with key terms
- Includes when to use the Skill
- SKILL.md under 500 lines
- No time-sensitive information
- Consistent terminology throughout
- Concrete examples provided
- References one level deep

**Code & Scripts**
- Scripts solve problems explicitly
- Error handling is helpful and clear
- All values justified (no "magic numbers")
- Required packages listed and verified
- No Windows paths

**Testing**
- At least three evaluations created
- Tested with Haiku, Sonnet, and Opus
- Real usage scenarios included
- Team feedback incorporated

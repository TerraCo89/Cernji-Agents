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

Examples:
  /research how to implement retry logic in Python
  /research file upload handling in Node.js --depth=thorough
  /research React state management --avenues=5 --focus=performance
  /research error: ECONNREFUSED when connecting to database
  /research compare Tailwind vs styled-components --depth=quick
```

## Process

**IMPORTANT:** Invoke the `deep-researcher` skill to handle this request. The skill provides comprehensive parallel research with agent orchestration, synthesis, and reporting.

```
Skill: deep-researcher
```

## Expected Arguments

Parse the following from the user's command:

- `research_topic` (required): The main research question or topic (all text after /research until first --)
- `--depth` (optional): Research depth level
  - `quick`: 3-5 avenues, surface-level research
  - `medium`: 5-7 avenues, balanced research (default)
  - `thorough`: 7-10 avenues, comprehensive research
- `--avenues` (optional): Explicit number of research avenues (3-10)
- `--focus` (optional): Specific aspect to emphasize (e.g., "performance", "security", "production-ready")

## When to Use

Use this command when you need to:
- **Investigate errors**: Multiple potential root causes requiring parallel investigation
- **Compare solutions**: Different libraries, patterns, or approaches
- **Research best practices**: Official docs, community patterns, production examples
- **Explore implementations**: Code examples from GitHub, documentation
- **Evaluate trade-offs**: Performance, security, complexity considerations

## Workflow Overview

After invoking the deep-researcher skill, it will:

1. **Decompose**: Break the research topic into 3-10 specific investigation avenues
   - Each avenue represents a distinct approach, perspective, or potential solution
   - Number of avenues based on topic complexity and depth setting

2. **Research in Parallel**: Launch specialized agents for each avenue
   - All agents run simultaneously for efficiency
   - Each agent finds authoritative sources, working code, and documentation

3. **Synthesize**: Combine findings into cohesive research report
   - Compare and evaluate all approaches
   - Highlight trade-offs and when to use each
   - Provide clear recommendations

4. **Present**: Formatted report with:
   - Executive summary with key insights
   - Detailed findings for each avenue
   - Working code examples
   - Source links and references
   - Actionable recommendations

## Examples

### Example 1: Error Investigation
```
User: /research error: Cannot find module '@langchain/core'
Process:
  1. Decompose into avenues:
     - Installation issues (missing dependency)
     - Import path problems
     - Version compatibility
     - Package.json configuration
     - Module resolution in build tools
  2. Launch 5 parallel research agents
  3. Synthesize findings with working solutions
  4. Present report with root cause and fixes
```

### Example 2: Implementation Comparison
```
User: /research compare Prisma vs TypeORM vs Drizzle --depth=thorough
Process:
  1. Decompose into 8 avenues:
     - Prisma: features, ecosystem, DX
     - TypeORM: features, ecosystem, DX
     - Drizzle: features, ecosystem, DX
     - Performance benchmarks
     - Type safety comparison
     - Migration strategies
     - Community support & maintenance
     - Production case studies
  2. Launch 8 parallel research agents
  3. Synthesize with detailed comparison matrix
  4. Present report with clear recommendations per use case
```

### Example 3: Best Practices Research
```
User: /research authentication patterns in Next.js 15 --focus=security
Process:
  1. Decompose into 6 avenues:
     - NextAuth.js v5 (official solution)
     - Clerk (managed auth service)
     - Supabase Auth (backend + auth)
     - Custom JWT implementation
     - OAuth provider integration
     - Security best practices & hardening
  2. Launch 6 parallel agents with security focus
  3. Synthesize findings with security analysis
  4. Present report emphasizing security trade-offs
```

### Example 4: Quick Investigation
```
User: /research retry logic libraries in Python --depth=quick
Process:
  1. Decompose into 3 avenues:
     - tenacity (most popular)
     - backoff (lightweight)
     - built-in approaches
  2. Launch 3 parallel research agents
  3. Quick synthesis with basic comparison
  4. Present concise report with recommendation
```

## Output Format

The deep-researcher skill will produce a structured report:

```markdown
# Research Report: [Topic]

## Summary
[Key insights and recommendations]

## Investigation Avenues

### 1. [Avenue Name]
[Detailed findings]

**Code Example:**
[Working code with comments]

**Sources:**
- [Documentation links]
- [GitHub repositories]
- [Blog posts/articles]

**Evaluation:** [When to use, pros/cons]

---

[Repeat for each avenue]

## Recommendations

**Best for most cases:** [Primary recommendation]
**Best for [specific scenario]:** [Alternative]
**Avoid if:** [Anti-patterns]

## Next Steps
[Actionable recommendations]
```

## Error Handling

If arguments are malformed or missing:
- Missing topic: "Please provide a research topic: /research <topic>"
- Invalid depth: "Invalid depth. Use: quick, medium, or thorough"
- Invalid avenues: "Avenues must be between 3 and 10"
- Conflicting options: "Cannot specify both --depth and --avenues (depth auto-determines avenues)"

## Tips for Effective Research

1. **Be specific**: "implement OAuth2 in FastAPI" is better than "authentication"
2. **Include context**: "error: ECONNREFUSED Redis" is better than just "Redis error"
3. **State constraints**: Use `--focus` to emphasize specific concerns
4. **Choose appropriate depth**:
   - Use `quick` for simple questions with known solutions
   - Use `medium` for most research tasks (balanced)
   - Use `thorough` for critical architecture decisions

## Integration with Other Commands

This command works well with:
- `/fetch-docs`: Fetch detailed documentation after identifying libraries
- `/career:find-examples`: Find portfolio examples after researching technologies
- Project-specific commands after researching implementation approaches

## Notes

- Research agents run in parallel for maximum efficiency
- All code examples are working, tested implementations
- Sources include official docs, GitHub repos, and authoritative blogs
- Synthesis includes comparison, trade-off analysis, and clear recommendations
- Report format is optimized for quick scanning and decision-making

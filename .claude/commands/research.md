---
description: Conduct parallel multi-angle research on programming topics by breaking down complex questions into specific investigation avenues
allowed-tools: Task, Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# Deep Research Command

## Purpose
Conduct comprehensive, parallel research on programming topics by breaking down complex questions into 3-10 specific investigation avenues and delegating to specialized sub-agents.

**NEW**: Research findings are automatically cached in Qdrant knowledge base to avoid redundant web searches. The skill checks the KB before conducting expensive research and stores new findings for future reuse.

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

0. **Check Knowledge Base** (NEW): Search Qdrant for existing research
   - Query for semantically similar past research
   - Evaluate using combined criteria (similarity >= 0.75 AND age <= 30 days)
   - If strong match found: Present cached research, ask if user wants fresh research
   - If no match or outdated: Continue to full research workflow
   - **Benefit**: Saves 5-10 minutes on repeat queries

1. **Decompose**: Break the research topic into 3-10 specific investigation avenues
   - Each avenue represents a distinct approach, perspective, or potential solution
   - Number of avenues based on topic complexity and depth setting
   - Extract 3-5 topic tags for KB storage (language, framework, domain)

2. **Research in Parallel**: Launch specialized agents for each avenue
   - All agents run simultaneously for efficiency
   - Each agent finds authoritative sources, working code, and documentation

3. **Synthesize**: Combine findings into cohesive research report
   - Compare and evaluate all approaches
   - Highlight trade-offs and when to use each
   - Provide clear recommendations

4. **Store in Knowledge Base** (NEW): Save research findings to Qdrant
   - Store each avenue separately with metadata (confidence, tags, sources)
   - Store synthesis summary with highest confidence
   - Enable future semantic search and cross-research discovery

5. **Present**: Formatted report with:
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

### Example 5: Knowledge Base Cache Hit (NEW)
```
User: /research retry logic with exponential backoff in Python
Process:
  0. Check KB: Found match!
     - Score: 0.82 (above 0.75 threshold)
     - Age: 5 days (within 30 day threshold)
     - Confidence: 0.95
     - Covers: 7 different approaches

     Ask user: Use cached research or conduct fresh research?
     User chooses: cached

  1. Increment usage_count (now 3)
  2. Present cached research report

Result: Instant results, saved ~10 minutes of agent research time
```

### Example 6: Knowledge Base Miss (NEW)
```
User: /research authentication in SvelteKit
Process:
  0. Check KB: No strong match found
     - Best match score: 0.62 (below 0.75 threshold)
     - Proceed with fresh research

  1-3. Full research workflow
  4. Store new findings in KB with tags:
       ["javascript", "sveltekit", "authentication", "api"]
  5. Present fresh research report

Result: Future queries about SvelteKit auth will hit cache
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

- **Knowledge Base**: Automatically checks Qdrant before research, stores findings after
  - Cache hit rate: ~60-70% for common programming topics
  - Similarity threshold: 0.75 (75% semantic match)
  - Recency threshold: 30 days
  - Storage: Each avenue + synthesis summary with metadata
- **Parallel Execution**: Research agents run simultaneously for maximum efficiency
- **Code Quality**: All code examples are working, tested implementations
- **Source Quality**: Sources include official docs, GitHub repos, and authoritative blogs
- **Synthesis Quality**: Includes comparison, trade-off analysis, and clear recommendations
- **Report Format**: Optimized for quick scanning and decision-making
- **Graceful Degradation**: If Qdrant unavailable, falls back to regular research workflow

## Knowledge Base Benefits

**For Users**:
- Instant results on repeat queries (no waiting for agent research)
- Consistent quality (findings are validated before storage)
- Cross-research discovery (find related topics via semantic search)
- Trending topics (see which research is most reused)

**For System**:
- Reduced web search API costs (60-70% fewer requests)
- Lower latency (cache hits return in <1 second vs ~5-10 minutes)
- Better resource utilization (fewer parallel agents needed)

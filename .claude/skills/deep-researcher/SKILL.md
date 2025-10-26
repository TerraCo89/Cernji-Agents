---
name: deep-researcher
description: Conduct parallel multi-angle research on programming topics. Break down complex research questions into 3-10 specific investigation avenues, delegate each to parallel sub-agents, and synthesize findings with working code examples and sources. Use when investigating error messages, comparing solutions, or exploring implementation approaches.
---

# Deep Researcher

Conduct comprehensive, parallel research on programming topics by breaking down complex questions into specific investigation avenues and delegating to specialized sub-agents.

## When to Use This Skill

Use this skill when:
- Investigating programming error messages or bugs with multiple potential root causes
- Comparing different implementation approaches or libraries
- Researching best practices for a specific programming task
- Exploring GitHub code examples for specific technologies
- Analyzing library documentation to find solutions
- Finding alternate solutions to technical problems

**Trigger phrases:**
- "Research different ways to [solve problem X]"
- "Investigate error: [error message]"
- "Find examples of [technology/pattern]"
- "Compare approaches for [task]"
- "Deep dive into [programming topic]"
- "What are the best practices for [X]?"

---

## Research Workflow

### Step 1: Decompose the Research Topic

Analyze the user's research question and break it into 3-10 specific investigation avenues. Each avenue should represent a distinct approach, perspective, or potential solution.

**Decomposition Strategy:**

For **error investigation**:
- Root cause analysis (what's causing the error?)
- Known issues and bug reports (has this been reported?)
- Configuration problems (is the setup correct?)
- Version compatibility (are dependencies compatible?)
- Alternative approaches (how else can this be accomplished?)

For **implementation comparison**:
- Approach A: [specific library/pattern]
- Approach B: [alternative library/pattern]
- Approach C: [different paradigm]
- Performance considerations
- Production readiness and community support

For **best practices research**:
- Official documentation recommendations
- Community patterns (GitHub examples, Stack Overflow)
- Performance optimization techniques
- Security considerations
- Error handling and edge cases

**Example Decomposition:**

*User query:* "Research how to handle file uploads in Node.js"

*Research avenues:*
1. Multer middleware approach (most popular)
2. Busboy streaming approach (low-level control)
3. Formidable library (simple API)
4. Native Node.js HTTP parsing (no dependencies)
5. Express-fileupload (Express-specific)
6. Cloud storage integration patterns (S3, GCS)
7. Security best practices for file uploads
8. Large file handling and streaming

**Determining Number of Avenues:**

Use 3-10 avenues based on:
- **3-5 avenues**: Simple topics with limited approaches (specific API usage, straightforward errors)
- **5-8 avenues**: Moderate complexity (comparing libraries, investigating common errors)
- **8-10 avenues**: Complex topics (architectural decisions, multi-faceted problems)

**See:** `references/decomposition-patterns.md` for detailed examples by topic type

### Step 2: Launch Parallel Research Agents

For each research avenue, launch a specialized research agent using the Task tool with `subagent_type: "general-purpose"`.

**Critical Requirements:**

1. **Launch agents in parallel** - Use a single message with multiple Task tool calls
2. **Provide specific, detailed prompts** - Each agent needs clear research objectives
3. **Request structured output** - Specify the required format (description, code, sources)
4. **Set appropriate depth** - Indicate whether to do quick research or deep investigation

**Agent Prompt Template:**

```
Research [specific avenue] for [original topic].

Your task:
1. Find the most relevant and authoritative information about [specific aspect]
2. Provide working code examples demonstrating [specific technique]
3. Include all source URLs (documentation, GitHub repos, blog posts)

Required output format:
## Solution Description
[2-3 paragraph explanation of this approach]

## Working Code Example
[Complete, runnable code with comments]

## Sources
- [URL 1]: [Brief description]
- [URL 2]: [Brief description]
- [URL 3]: [Brief description]

Focus on: [specific sub-questions or criteria for this avenue]
```

**Example Agent Launch:**

```
For "Research file upload handling in Node.js" with 3 avenues:

Agent 1 prompt: "Research the Multer middleware approach for file uploads in Node.js.

Your task:
1. Find the most current Multer documentation and best practices
2. Provide a complete working example with Express.js
3. Include GitHub repositories using Multer in production
4. Explain configuration options and security considerations

Required output format:
## Solution Description
[Explanation of Multer approach]

## Working Code Example
[Complete Express + Multer example]

## Sources
[Documentation and example links]

Focus on: Production-ready configuration, file size limits, file type validation, error handling."

Agent 2 prompt: [Similar structure for Busboy]
Agent 3 prompt: [Similar structure for Formidable]
```

**Task Tool Usage:**

Launch all agents in a **single message** with multiple Task tool calls:

```
I'm launching 3 parallel research agents to investigate different file upload approaches:

[Task tool call 1 - Multer research]
[Task tool call 2 - Busboy research]
[Task tool call 3 - Formidable research]
```

### Step 3: Synthesize Research Findings

Once all agents complete, synthesize their findings into a cohesive research report.

**Synthesis Structure:**

```markdown
# Research Report: [Original Topic]

## Summary
[1-2 paragraph overview of all findings, key insights, and recommendations]

## Investigation Avenues

### 1. [Avenue Name]
[Agent's solution description]

**Code Example:**
```language
[Agent's code example]
```

**Sources:**
[Agent's source links]

**Evaluation:** [Your assessment - when to use this, pros/cons, production readiness]

---

### 2. [Avenue Name]
[Repeat structure]

---

## Recommendations

**Best choice for most cases:** [Recommendation with rationale]

**Best for [specific use case]:** [Alternative recommendation]

**Avoid if:** [Anti-patterns or situations where approaches fail]

## Next Steps
[Actionable recommendations for the user]
```

**Synthesis Guidelines:**

1. **Don't just concatenate** - Add value by comparing and evaluating approaches
2. **Highlight trade-offs** - Explain when each approach is appropriate
3. **Note conflicts** - If agents found contradictory information, investigate and clarify
4. **Provide actionable recommendations** - Help user make a decision
5. **Validate code examples** - Ensure examples are complete and runnable

**See:** `assets/solution-template.md` for the complete markdown template

### Step 4: Present Results

Present the synthesized research report to the user with:
- Clear section headings
- Formatted code blocks with syntax highlighting
- Clickable source URLs
- Summary recommendations at the end

**Formatting Requirements:**

- Use `###` for avenue headings
- Use language-specific code fences (```javascript, ```python, etc.)
- Format links as `[Description](URL)`
- Use bold for emphasis on key points
- Add horizontal rules (`---`) between avenues for readability

## Best Practices

### Research Quality

1. **Prioritize authoritative sources:**
   - Official documentation first
   - Well-maintained GitHub repositories (check stars, recent commits)
   - Recognized technical blogs (engineering blogs, known experts)
   - Avoid outdated Stack Overflow answers unless verified

2. **Verify code examples:**
   - Ensure examples are complete and runnable
   - Include necessary imports and dependencies
   - Test critical code paths when possible
   - Note any version-specific requirements

3. **Document limitations:**
   - Mention browser compatibility issues
   - Note deprecated APIs
   - Highlight security considerations
   - Flag experimental features

### Agent Management

1. **Use descriptive avenue names** - Helps track which agent is researching what
2. **Avoid duplicate research** - Ensure each avenue is distinct
3. **Balance breadth and depth** - Don't create too many surface-level avenues
4. **Monitor agent progress** - Check for timeouts or errors

### Output Quality

1. **Consistent formatting** - Follow the template structure
2. **Complete code examples** - No pseudocode or partial snippets
3. **Active source links** - Verify URLs are accessible
4. **Clear recommendations** - Help user make informed decisions

## Common Research Patterns

### Error Message Investigation

**Avenues to consider:**
1. Root cause analysis (what's actually broken?)
2. Known issues in library/framework issue tracker
3. Version compatibility problems
4. Configuration errors
5. Workarounds and patches
6. Alternative approaches avoiding the error

**Focus:** Finding the underlying cause, not just symptoms

### Library/Tool Comparison

**Avenues to consider:**
1. Option A features and ecosystem
2. Option B features and ecosystem
3. Option C features and ecosystem
4. Performance benchmarks
5. Community support and maintenance
6. Production case studies

**Focus:** Objective comparison with clear trade-offs

### Implementation Patterns

**Avenues to consider:**
1. Official documentation approach
2. Community best practices (GitHub trending repos)
3. Performance-optimized approach
4. Security-hardened approach
5. Testing strategies
6. Edge case handling

**Focus:** Production-ready, maintainable code

**See:** `references/decomposition-patterns.md` for detailed examples

## Bundled Resources

### References

- **`references/decomposition-patterns.md`**: Detailed examples of topic decomposition by research type (error investigation, library comparison, best practices). Use this to learn effective decomposition strategies.

### Assets

- **`assets/solution-template.md`**: Complete markdown template for formatting research findings. Copy this structure when presenting results to ensure consistency.

## Example Workflow

**User request:** "Research how to implement retry logic with exponential backoff in Python"

**Step 1 - Decompose:**
1. Built-in library approach (`time.sleep` + manual implementation)
2. `tenacity` library (declarative retry)
3. `backoff` library (lightweight)
4. `celery` task retry (distributed systems)
5. Cloud provider SDKs (AWS Boto3, etc.)
6. Custom implementation with jitter
7. Testing retry logic

**Step 2 - Launch (single message with 7 Task calls):**
```
Launching 7 parallel research agents to investigate Python retry strategies:

[Task 1: Built-in approach]
[Task 2: tenacity library]
[Task 3: backoff library]
[Task 4: celery retry]
[Task 5: cloud SDK retry]
[Task 6: custom with jitter]
[Task 7: testing strategies]
```

**Step 3 - Synthesize:**
- Compare approaches
- Evaluate trade-offs (complexity vs features)
- Note when to use each
- Provide recommendations

**Step 4 - Present:**
- Formatted markdown report
- Working code examples for each approach
- Source links
- "Best for most cases: `tenacity`" recommendation

## Troubleshooting

**Issue: Too many research avenues**
- **Solution:** Consolidate related avenues (e.g., merge library variations into one comparative avenue)

**Issue: Agents returning generic information**
- **Solution:** Make prompts more specific with clear success criteria

**Issue: Conflicting recommendations from agents**
- **Solution:** Investigate conflicts in synthesis phase, prioritize authoritative sources

**Issue: Outdated code examples**
- **Solution:** Check library versions, verify examples against current documentation

**Issue: Missing sources**
- **Solution:** Re-prompt agent to provide specific URLs for claims made

## Quick Start

1. **Analyze user's research question**
2. **Decompose into 3-10 specific avenues**
3. **Launch parallel agents** (single message, multiple Task calls)
4. **Wait for all agents to complete**
5. **Synthesize findings** with comparisons and recommendations
6. **Present formatted report** using solution template

## Support

For questions or issues:
- Review example decompositions: `references/decomposition-patterns.md`
- Use solution template: `assets/solution-template.md`
- Refer to skill creator guidance for skill improvements

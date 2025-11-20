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

## Knowledge Base Integration

This skill automatically checks the Qdrant knowledge base before performing expensive web searches and stores new research findings for future reuse.

### Research Metadata Schema

Each research finding stored in Qdrant includes the following metadata:

```json
{
  "type": "research_finding",
  "query": "original research query text",
  "topic_tags": ["python", "retry-logic", "exponential-backoff"],
  "confidence_score": 0.85,
  "usage_count": 0,
  "timestamp": "2025-11-20T10:30:00Z",
  "sources": ["https://docs.python.org/...", "https://github.com/..."],
  "avenues_count": 5,
  "depth": "medium",
  "avenue_name": "tenacity library approach"
}
```

**Field Descriptions:**

- **type**: Always `"research_finding"` to distinguish from other knowledge base entries
- **query**: The original user research question (for traceability)
- **topic_tags**: 3-5 extracted tags (language, framework, domain) for cross-research discovery
- **confidence_score**: 0.0-1.0 rating of research quality and completeness
- **usage_count**: Number of times this research has been referenced (starts at 0)
- **timestamp**: ISO 8601 datetime when research was conducted
- **sources**: Array of authoritative source URLs used in the research
- **avenues_count**: Total number of investigation avenues in the full research
- **depth**: Research depth level ("quick", "medium", "thorough")
- **avenue_name**: Specific investigation avenue name (e.g., "Multer middleware approach")

### Knowledge Base Behavior

**Automatic Checking**: The skill automatically checks Qdrant before launching research agents (transparent to user).

**Combined Evaluation**: Results are evaluated using:
- **Similarity threshold**: >= 0.75 (75% semantic match)
- **Recency threshold**: Within last 30 days

**When KB results are sufficient**: Present cached research and ask if user wants fresh research.

**When KB results are insufficient**: Proceed with full research workflow and store new findings.

**Collection**: Uses the shared `resume-agent-chunks` Qdrant collection.

---

## Research Workflow

### Step 0: Check Knowledge Base

**IMPORTANT**: Before launching expensive web research, ALWAYS check the Qdrant knowledge base for relevant past research.

**Process:**

1. **Query Qdrant for similar research:**
   ```
   Use mcp__qdrant-vectors__qdrant-find(
       query="<user's research question>"
   )
   ```

2. **Evaluate results using combined criteria:**

   For each result, check:
   - **Similarity score**: Is it >= 0.75 (75% semantic match)?
   - **Recency**: Is timestamp within last 30 days?
   - **Metadata match**: Do topic_tags align with the current query?

3. **Decision logic:**

   **Case A: Strong match found** (score >= 0.75 AND age <= 30 days)
   - Present cached research to user
   - Show: avenue findings, code examples, sources
   - Increment `usage_count` in metadata (see Step 5 for implementation)
   - Ask: "I found relevant research from [X days ago]. Would you like me to:
     - Use this cached research (instant)
     - Conduct fresh research (may find newer information)"
   - If user chooses cached: Skip to Step 5 (presentation)
   - If user chooses fresh: Continue to Step 1

   **Case B: Weak or no match** (score < 0.75 OR age > 30 days OR no results)
   - Inform user: "No recent research found for this topic. Conducting fresh research..."
   - Continue to Step 1 (Decompose)

4. **Handle multiple matches:**
   - If multiple results meet criteria (>= 0.75, <= 30 days), choose highest score
   - If scores are similar (within 0.05), prefer more recent research
   - If research covers different avenues, consider combining insights

**Example:**

```markdown
User query: "Research retry logic with exponential backoff in Python"

Qdrant results:
1. Score: 0.82, Age: 15 days, Tags: ["python", "retry-logic", "exponential-backoff"]
   → Strong match! Present to user

2. Score: 0.68, Age: 10 days, Tags: ["python", "error-handling"]
   → Weak match (score too low), proceed with fresh research

3. Score: 0.85, Age: 45 days, Tags: ["python", "retry-logic", "tenacity"]
   → Outdated (>30 days), proceed with fresh research
```

**When to skip KB check:**
- Never skip automatically
- User must explicitly request `/research --skip-kb` (future enhancement)

**Troubleshooting:**

- **Qdrant connection error**: Log warning, continue to Step 1 (graceful degradation)
- **Empty collection**: Continue to Step 1, this is first research
- **Timeout**: After 5 seconds, continue to Step 1

### Step 2: Decompose the Research Topic

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

### Step 3: Launch Parallel Research Agents

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

### Step 4: Synthesize Research Findings

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

### Step 5: Store Research Findings

**IMPORTANT**: After synthesizing research, ALWAYS store findings in Qdrant for future reuse.

**Storage Strategy:**

Store each investigation avenue separately plus a summary entry. This enables:
- Granular retrieval (find specific approaches)
- Cross-research discovery (link related topics)
- Usage tracking (identify valuable patterns)

**For each investigation avenue:**

```python
# Extract topic tags from the research question and avenue
topic_tags = extract_topic_tags(
    query="<user's research question>",
    avenue="<avenue name>"
)

# Calculate confidence score based on:
# - Number of authoritative sources (0-5 sources = 0.0-0.5)
# - Code example completeness (has working code = +0.2)
# - Source diversity (multiple source types = +0.15)
# - Recency of sources (all sources < 1 year old = +0.15)
confidence_score = calculate_confidence(
    sources=avenue_sources,
    has_code=True/False,
    source_diversity=["docs", "github", "blog"]
)

# Store in Qdrant
mcp__qdrant-vectors__qdrant-store(
    information=f"""
# {avenue_name}

## Description
{avenue_description}

## Code Example
{code_example}

## Sources
{formatted_sources}

## Evaluation
{pros_cons_assessment}
""",
    metadata=json.dumps({
        "type": "research_finding",
        "query": original_user_query,
        "topic_tags": topic_tags,
        "confidence_score": confidence_score,
        "usage_count": 0,
        "timestamp": datetime.now().isoformat(),
        "sources": source_urls,
        "avenues_count": total_avenues,
        "depth": depth_level,
        "avenue_name": avenue_name
    })
)
```

**For the synthesis summary:**

```python
# Store high-level summary with higher confidence
mcp__qdrant-vectors__qdrant-store(
    information=f"""
# Research Summary: {original_query}

{synthesis_overview}

## Recommendations
{recommendations}

## All Avenues Investigated
{list_of_all_avenues}
""",
    metadata=json.dumps({
        "type": "research_finding",
        "query": original_user_query,
        "topic_tags": topic_tags,
        "confidence_score": 0.95,  # Summary has highest confidence
        "usage_count": 0,
        "timestamp": datetime.now().isoformat(),
        "sources": all_unique_sources,
        "avenues_count": total_avenues,
        "depth": depth_level,
        "avenue_name": "synthesis_summary"
    })
)
```

**Topic Tag Extraction** (see detailed logic below):

Extract 3-5 tags covering:
1. **Programming language**: python, typescript, javascript, go, rust, etc.
2. **Framework/library**: fastapi, react, django, express, spring, etc.
3. **Domain/pattern**: authentication, retry-logic, file-upload, websockets, etc.
4. **Technology type**: api, database, caching, messaging, etc.

Example: "Research retry logic with exponential backoff in Python"
→ Tags: `["python", "retry-logic", "exponential-backoff", "error-handling", "resilience"]`

**Confidence Score Calculation:**

Base score starts at 0.5, then:
- +0.1 per authoritative source (max 0.5 for 5+ sources)
- +0.2 if has complete, runnable code example
- +0.15 if sources are diverse (docs + github + blog)
- +0.15 if all sources are recent (< 1 year old)
- Max score: 1.0

Example:
- 5 sources (official docs, 2 GitHub repos, 1 blog, 1 Stack Overflow) = 0.5
- Has complete code = +0.2
- Diverse sources = +0.15
- All recent = +0.15
- **Total: 1.0**

**Error Handling:**

```python
try:
    # Store each avenue
    for avenue in research_avenues:
        mcp__qdrant-vectors__qdrant-store(...)

    # Store synthesis summary
    mcp__qdrant-vectors__qdrant-store(...)

except Exception as e:
    # Log error but don't fail the research workflow
    print(f"Warning: Failed to store research in Qdrant: {e}")
    print("Research will still be presented to user.")
    # Continue to Step 6 (Present Results)
```

**Validation:**

Before storing, verify:
- Topic tags are not empty (fallback: extract from query if needed)
- Confidence score is between 0.0 and 1.0
- Timestamp is valid ISO 8601
- Sources array is not empty
- Avenue name is descriptive and unique

### Step 6: Present Results

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

## Knowledge Base Implementation

### Topic Tag Extraction Logic

**Purpose**: Extract 3-5 meaningful tags from research query and avenue to enable cross-research discovery.

**Extraction Strategy**:

1. **Analyze the query and avenue name** for key terms
2. **Categorize terms** into: language, framework, domain, technology
3. **Normalize** to lowercase, hyphenated format (e.g., "retry-logic")
4. **Limit** to 3-5 most relevant tags

**Implementation Pattern**:

```python
def extract_topic_tags(query: str, avenue: str = "") -> list[str]:
    """
    Extract 3-5 topic tags from research query and avenue.

    Returns tags in order of specificity:
    1. Programming language
    2. Framework/library
    3. Domain/pattern (most specific first)
    """
    tags = []
    combined_text = f"{query} {avenue}".lower()

    # 1. Extract programming language
    languages = {
        "python": ["python", "py", "django", "flask", "fastapi"],
        "javascript": ["javascript", "js", "node", "nodejs"],
        "typescript": ["typescript", "ts"],
        "go": ["golang", "go"],
        "rust": ["rust"],
        "java": ["java", "spring"],
        "csharp": ["c#", "csharp", ".net", "dotnet"],
        "ruby": ["ruby", "rails"],
        "php": ["php", "laravel"]
    }

    for lang, indicators in languages.items():
        if any(indicator in combined_text for indicator in indicators):
            tags.append(lang)
            break

    # 2. Extract framework/library (specific names)
    frameworks = [
        "fastapi", "django", "flask", "express", "react", "vue",
        "angular", "nextjs", "spring", "laravel", "rails",
        "tenacity", "backoff", "celery", "multer", "busboy"
    ]

    for framework in frameworks:
        if framework in combined_text:
            tags.append(framework)

    # 3. Extract domain/pattern keywords (2-3 tags max)
    domain_patterns = {
        "retry-logic": ["retry", "retries", "retrying"],
        "exponential-backoff": ["exponential backoff", "backoff"],
        "authentication": ["auth", "authentication", "login"],
        "authorization": ["authorization", "permissions", "rbac"],
        "file-upload": ["file upload", "upload", "multipart"],
        "websockets": ["websocket", "ws", "real-time"],
        "error-handling": ["error handling", "exception"],
        "testing": ["test", "testing", "unittest", "pytest"],
        "api": ["api", "rest", "graphql"],
        "database": ["database", "db", "sql", "postgres", "mongodb"],
        "caching": ["cache", "caching", "redis"],
        "security": ["security", "xss", "csrf", "injection"],
        "performance": ["performance", "optimization", "speed"]
    }

    for pattern, indicators in domain_patterns.items():
        if any(indicator in combined_text for indicator in indicators):
            tags.append(pattern)
            if len(tags) >= 5:
                break

    # 4. Ensure 3-5 tags (extract from query words if needed)
    if len(tags) < 3:
        # Fallback: extract significant words from query
        import re
        words = re.findall(r'\b[a-z]{4,}\b', combined_text)
        for word in words:
            if word not in tags and word not in ['with', 'using', 'implement', 'research']:
                tags.append(word)
                if len(tags) >= 3:
                    break

    # Limit to 5 tags
    return tags[:5]
```

**Example Extractions**:

| Query | Avenue | Tags |
|-------|--------|------|
| "Research retry logic with exponential backoff in Python" | "tenacity library" | `["python", "tenacity", "retry-logic", "exponential-backoff", "error-handling"]` |
| "File upload handling in Node.js" | "Multer middleware" | `["javascript", "multer", "file-upload", "api"]` |
| "Authentication patterns in FastAPI" | "OAuth2 implementation" | `["python", "fastapi", "authentication", "api"]` |

### Usage Tracking Implementation

**Purpose**: Track how often research findings are reused to identify valuable patterns.

**When to increment `usage_count`**:

1. When KB cache hit occurs (Step 0) and user chooses to use cached research
2. When KB results are shown to user (even if they choose fresh research)

**Implementation Pattern**:

```python
def increment_usage_count(qdrant_point_id: str):
    """
    Increment usage_count for a research finding.

    Note: Qdrant MCP server doesn't directly support metadata updates,
    so we need to re-store the point with updated metadata.

    Workaround:
    1. Retrieve current point data
    2. Parse metadata, increment usage_count
    3. Re-store with same point ID
    """

    # Step 0: Query to get current data
    results = mcp__qdrant-vectors__qdrant-find(
        query=original_query  # Use same query to find the point
    )

    # Find the specific point we want to update
    for result in results:
        if result["id"] == qdrant_point_id:
            # Parse current metadata
            import json
            metadata = json.loads(result["metadata"])

            # Increment usage count
            metadata["usage_count"] = metadata.get("usage_count", 0) + 1

            # Re-store with updated metadata
            mcp__qdrant-vectors__qdrant-store(
                information=result["content"],  # Same content
                metadata=json.dumps(metadata)   # Updated metadata
            )

            print(f"✓ Updated usage_count to {metadata['usage_count']}")
            break
```

**Alternative: Manual Tracking**:

If Qdrant MCP server doesn't support point updates, track usage in a separate SQLite database:

```python
# Track in local SQLite
import sqlite3
conn = sqlite3.connect("data/research-usage.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS research_usage (
    query_hash TEXT PRIMARY KEY,
    query TEXT,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Increment usage
cursor.execute("""
INSERT INTO research_usage (query_hash, query, usage_count)
VALUES (?, ?, 1)
ON CONFLICT(query_hash) DO UPDATE SET
    usage_count = usage_count + 1,
    last_used = CURRENT_TIMESTAMP
""", (hash(query), query))

conn.commit()
```

**Usage Analytics**:

Track these metrics:
- **Most researched topics** (highest usage_count)
- **Average reuse rate** (KB hits / total research queries)
- **Staleness** (time since last usage)
- **Research ROI** (avenues_count × usage_count)

**Example Output**:

```
Research Knowledge Base Stats:
- Total research entries: 147
- Cache hit rate: 62% (saved 93 web searches)
- Most reused topics:
  1. "Python retry logic" - 12 uses
  2. "FastAPI authentication" - 9 uses
  3. "React state management" - 7 uses
```

### Confidence Score Guidelines

**High Confidence (0.8-1.0)**:
- 5+ authoritative sources
- Complete, tested code examples
- Official documentation + production examples
- All sources < 6 months old

**Medium Confidence (0.6-0.79)**:
- 3-4 good sources
- Working code examples
- Mix of official + community sources
- Sources < 1 year old

**Low Confidence (0.4-0.59)**:
- 1-2 sources
- Partial code examples
- Mostly community sources
- Some sources > 1 year old

**Very Low (<0.4)**:
- Single source
- No code examples
- Questionable source quality
- Outdated information

**Usage**:

Filter KB results by confidence when retrieving:
- For production decisions: Only show results with confidence >= 0.7
- For exploration: Show all results, but warn on low confidence
- For learning: Show all results with confidence scores displayed

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

**Step 0 - Check Knowledge Base:**
```
Checking Qdrant for existing research on "retry logic with exponential backoff in Python"...

Found 1 result:
- Score: 0.68 (below 0.75 threshold)
- Age: 12 days
- Tags: ["python", "error-handling", "resilience"]

→ Weak match. Proceeding with fresh research.
```

**Step 2 - Decompose:**
1. Built-in library approach (`time.sleep` + manual implementation)
2. `tenacity` library (declarative retry)
3. `backoff` library (lightweight)
4. `celery` task retry (distributed systems)
5. Cloud provider SDKs (AWS Boto3, etc.)
6. Custom implementation with jitter
7. Testing retry logic

Extracted tags: `["python", "retry-logic", "exponential-backoff", "error-handling", "resilience"]`

**Step 3 - Launch (single message with 7 Task calls):**
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

**Step 4 - Synthesize:**
- Compare approaches
- Evaluate trade-offs (complexity vs features)
- Note when to use each
- Provide recommendations

**Step 5 - Store in Qdrant:**
```
Storing 7 avenue findings + 1 synthesis summary in Qdrant...

Avenue 1: "tenacity library"
- Confidence: 0.92 (5 sources, complete code, diverse sources)
- Tags: ["python", "tenacity", "retry-logic", "exponential-backoff", "error-handling"]
✓ Stored

Avenue 2: "backoff library"
- Confidence: 0.85 (4 sources, complete code)
- Tags: ["python", "backoff", "retry-logic", "exponential-backoff"]
✓ Stored

... (5 more avenues)

Synthesis Summary:
- Confidence: 0.95 (comprehensive overview)
- Tags: ["python", "retry-logic", "exponential-backoff", "error-handling", "resilience"]
✓ Stored

Total: 8 entries added to knowledge base
```

**Step 6 - Present:**
- Formatted markdown report
- Working code examples for each approach
- Source links
- "Best for most cases: `tenacity`" recommendation

---

**Example: KB Cache Hit**

**User request:** "How do I implement retry logic in Python?"

**Step 0 - Check Knowledge Base:**
```
Checking Qdrant for existing research on "implement retry logic in Python"...

Found strong match:
- Score: 0.82 (above 0.75 threshold)
- Age: 3 days (within 30 day threshold)
- Tags: ["python", "retry-logic", "exponential-backoff", "error-handling"]
- Confidence: 0.95
- Avenues researched: 7

I found relevant research from 3 days ago covering 7 different approaches to Python retry logic.

Would you like me to:
A) Use this cached research (instant)
B) Conduct fresh research (may find newer information)

→ User chooses A

Incrementing usage_count (now 2)...
Presenting cached research...
```

Result: Saved ~10 minutes of agent research time!

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

**Issue: Qdrant connection error**
- **Solution:** Verify Qdrant Docker container is running (`docker ps`), gracefully degrade to regular research workflow

**Issue: KB results seem outdated**
- **Solution:** Check recency threshold (30 days default), consider lowering confidence requirement or conducting fresh research

**Issue: Too many KB matches**
- **Solution:** Choose highest scoring match, or combine insights from multiple matches if they cover different aspects

**Issue: Failed to store research in Qdrant**
- **Solution:** Check Qdrant connection, verify metadata format, continue with presentation (storage is non-critical)

## Quick Start

1. **Check Qdrant knowledge base** for existing research (mcp__qdrant-vectors__qdrant-find)
2. **Evaluate results**: score >= 0.75 AND age <= 30 days?
   - Yes: Present cached research, ask user if they want fresh research
   - No: Continue to step 3
3. **Decompose into 3-10 specific avenues** with topic tag extraction
4. **Launch parallel agents** (single message, multiple Task calls)
5. **Wait for all agents to complete**
6. **Synthesize findings** with comparisons and recommendations
7. **Store in Qdrant** (each avenue + synthesis summary with metadata)
8. **Present formatted report** using solution template

## Support

For questions or issues:
- Review example decompositions: `references/decomposition-patterns.md`
- Use solution template: `assets/solution-template.md`
- Refer to skill creator guidance for skill improvements

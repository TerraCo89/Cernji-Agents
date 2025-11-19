---
name: error-analyzer
description: Analyze development errors, identify root causes, and propose systemic improvements to prevent recurrence
---

# Error Analyzer Skill

## Purpose

This skill analyzes development errors to identify root causes and propose systemic improvements. It helps prevent recurring errors by addressing underlying issues in:
- Documentation gaps
- Missing code examples
- Overly broad agent scope
- Configuration/dependency issues

## When to Use

Use this skill when:
- A development error occurs during Claude Code sessions
- Error patterns emerge in ELK stack logs
- You want to understand why a specific error happened
- You need recommendations to prevent future similar errors

**Trigger methods**:
1. **Manual**: Via `/analyze-error` slash command with error details
2. **Automatic**: Triggered by high error rates in ELK stack (via Kibana alerts)

## Prerequisites

Ensure the following MCP servers are configured:
- ✅ **error-analysis** - Elasticsearch querying (required)
- ✅ **linear** - Issue tracking (required)
- ✅ **qdrant-vectors** - Knowledge base (required)
- ⚠️ **github** - Code fixes (optional, for proposing PRs)

## Root Cause Analysis Workflow

### Phase 1: Error Context Gathering

**Inputs**:
- Error message (stack trace, exception type)
- Service name (e.g., "resume-agent", "agent-chat-ui")
- Timestamp or time range
- Optional: Trace ID for full context

**Steps**:

1. **Query ELK Stack for Error Patterns**
   ```
   Use mcp__error-analysis__search_errors(
       time_range="24h",
       service=<service_name>,
       log_level="error"
   )
   ```

   Determine:
   - Is this a new error or recurring pattern?
   - How many times has it occurred?
   - What's the error trend (increasing/stable/decreasing)?

2. **Get Full Error Context** (if trace ID available)
   ```
   Use mcp__error-analysis__get_error_context(
       trace_id=<trace_id>,
       include_related=true
   )
   ```

   Analyze:
   - What was happening before the error?
   - Are there related warnings or info logs?
   - What was the execution flow?

3. **Search Knowledge Base for Similar Errors**
   ```
   Use mcp__qdrant-vectors__qdrant-find(
       query=<error_message>
   )
   ```

   Check:
   - Have we seen this error before?
   - What was the previous solution?
   - Did the solution work (error still occurring)?

### Phase 2: Root Cause Classification

Classify the error into one or more categories:

#### Category 1: Documentation Gap

**Indicators**:
- Error involves using an API/library incorrectly
- Common patterns: `AttributeError`, `TypeError` with valid-looking code
- Developer likely didn't know about correct usage

**Examples**:
- `AttributeError: 'NoneType' object has no attribute 'invoke'` → Missing null check documentation
- `TypeError: argument must be str, not dict` → API signature documentation unclear

**Analysis steps**:
1. Search existing documentation for the module/API
   ```
   Use Grep(pattern="<module_name>", path="ai_docs/", output_mode="files_with_matches")
   ```

2. Check if documentation exists but is incomplete
3. Identify what documentation would have prevented this error

**Recommended actions**:
- Create/update documentation in `ai_docs/` or `library-docs/`
- Add code examples showing correct usage
- Update skill documentation if relevant
- **Create Linear issue**: "Add documentation for [module/API]"

#### Category 2: Missing Code Examples

**Indicators**:
- Error shows attempted pattern that *almost* works
- Common patterns: Implementation is close but missing key details
- Similar working code exists elsewhere in codebase

**Examples**:
- Using `invoke()` instead of `ainvoke()` for async operations
- Missing `await` keyword in async functions
- Incorrect tool binding pattern

**Analysis steps**:
1. Search codebase for working examples
   ```
   Use Grep(pattern="<working_pattern>", output_mode="content", -B=3, -C=3)
   ```

2. Compare error-causing code with working examples
3. Identify the missing piece or incorrect pattern

**Recommended actions**:
- Add code example to knowledge base (Qdrant)
  ```
  Use mcp__qdrant-vectors__qdrant-store(
      information="Error: <error_msg>\nSolution: <working_code>\nContext: <when_to_use>",
      metadata={
          "type": "code_example",
          "error_type": "<error_class>",
          "solution_pattern": "<pattern_name>"
      }
  )
  ```
- Create skill with reusable pattern
- **Create Linear issue**: "Add code example for [pattern]"

#### Category 3: Overly Broad Agent Scope

**Indicators**:
- Agent attempting to do too many things in one workflow
- Error occurs late in complex multi-step process
- Agent state becomes inconsistent or too complex
- Common patterns: State management errors, coordination failures

**Examples**:
- Agent tries to fetch job, analyze, tailor resume, and create PR in one graph
- Too many conditional branches in StateGraph
- Agent loses context mid-workflow

**Analysis steps**:
1. Analyze agent workflow complexity
   ```
   Use Read(<agent_graph_file>) to examine StateGraph structure
   ```

2. Count nodes, edges, conditional branches
3. Identify if agent should be split into:
   - Multiple specialized agents (coordinator pattern)
   - Sequential workflows with clear boundaries
   - Separate skills for sub-tasks

**Recommended actions**:
- Propose agent decomposition:
  ```markdown
  **Current**: Single agent doing A → B → C → D
  **Proposed**:
  - Agent 1: A → B (focused, simple)
  - Agent 2: C → D (focused, simple)
  - Coordinator: Orchestrate Agent 1 → Agent 2
  ```

- Create architecture diagram (can use Miro MCP if needed)
- **Create Linear issue**: "Refactor [agent] into specialized sub-agents"

#### Category 4: Configuration/Dependency Issues

**Indicators**:
- `ModuleNotFoundError`, `ImportError`
- Version conflicts or missing dependencies
- Environment-specific errors (works locally, fails in prod)
- Common patterns: Missing environment variables, incorrect paths

**Examples**:
- `ModuleNotFoundError: No module named 'fastmcp'` → Missing dependency
- `playwright._impl._errors.TargetClosedError` → Browser not installed
- `ConnectionRefusedError: [Errno 61]` → Service not running

**Analysis steps**:
1. Check if dependency is declared
   ```
   Use Grep(pattern="<module_name>", path="pyproject.toml|package.json|dependencies")
   ```

2. Verify environment setup
   ```
   Use Read(.env.example) to check required env vars
   ```

3. Check service dependencies (Docker, databases, etc.)
   ```
   Use Bash(command="docker ps") to verify services running
   ```

**Recommended actions**:
- Update dependency declarations
- Add missing environment variables to `.env.example`
- Create startup validation script
- **Create Linear issue**: "Add [dependency] to project setup"

### Phase 3: Solution Proposal

Based on root cause analysis, generate a comprehensive report with:

#### 1. Immediate Fix (if applicable)

**For simple errors**, provide code changes or commands to fix immediately:

```markdown
## Immediate Fix

**Error**: ModuleNotFoundError: No module named 'fastmcp'

**Solution**: Add dependency to UV script
\`\`\`python
# In error_analysis_mcp.py, add to dependencies:
# dependencies = [
#     "fastmcp>=2.0",  # <- Add this
#     ...
# ]
\`\`\`

**Command to apply**:
Edit(file_path="...", old_string="...", new_string="...")
```

#### 2. Systemic Improvement

**For preventing future occurrences**, create actionable Linear issues:

```python
# Create Linear issue for tracking
mcp__linear__create_issue(
    team="DEV",
    title="Add [missing piece] to prevent [error type]",
    description="""
## Problem
Error occurred: {error_message}

Root cause: {root_cause_category}

## Proposed Solution
{detailed_solution}

## Acceptance Criteria
- [ ] Documentation/example added
- [ ] Tested with similar use case
- [ ] Knowledge base updated
- [ ] No recurrence in next 30 days

## Related Errors
- {trace_id_1}
- {trace_id_2}
""",
    priority=2,  # High if recurring, Normal otherwise
    labels=["error-prevention", "systemic-improvement", <root_cause_category>]
)
```

#### 3. Knowledge Base Update

**Always** add learnings to knowledge base for future reference:

```python
mcp__qdrant-vectors__qdrant-store(
    information=f"""
Error Signature: {error_type} - {error_message}

Root Cause: {root_cause_category}
Service: {service_name}
Occurrences: {count}

Solution:
{solution_description}

Prevention:
{prevention_steps}

Code Example:
{working_code_example}

Last Updated: {timestamp}
""",
    metadata={
        "type": "error_analysis",
        "error_type": error_type,
        "root_cause": root_cause_category,
        "service": service_name,
        "severity": severity,
        "auto_fixable": True/False
    }
)
```

### Phase 4: Trend Analysis & Reporting

For **automatic monitoring mode**, analyze trends over time:

```python
# Get error trends
trend_data = mcp__error-analysis__analyze_error_trend(
    service=service_name,
    time_range="7d",
    interval="1h"
)

# Get error patterns
patterns = mcp__error-analysis__get_error_patterns(
    time_range="7d",
    service=service_name,
    min_occurrences=3
)
```

**Generate weekly report** (if multiple errors analyzed):

```markdown
# Error Analysis Report - Week of {week_start}

## Summary
- Total errors: {total_count}
- Unique patterns: {pattern_count}
- Services affected: {affected_services}

## Top Error Patterns
1. **{pattern_1_message}** ({count} occurrences)
   - Root cause: {category}
   - Status: {Linear issue created/Fixed}

2. **{pattern_2_message}** ({count} occurrences)
   - Root cause: {category}
   - Status: {Linear issue created/Fixed}

## Root Cause Distribution
- Documentation gaps: {percentage}%
- Missing examples: {percentage}%
- Agent scope issues: {percentage}%
- Config/dependencies: {percentage}%

## Systemic Improvements Implemented
- {improvement_1} (Linear issue DEV-XXX)
- {improvement_2} (Linear issue DEV-YYY)

## Recommendations
1. {high_impact_recommendation}
2. {medium_impact_recommendation}

## Next Week Focus
- Address top 3 recurring patterns
- Review agent architecture for {service_name}
```

## Output Format

The skill should always output:

### 1. Analysis Report (Markdown)

```markdown
# Error Analysis Report

**Error**: {error_message}
**Service**: {service_name}
**Timestamp**: {timestamp}
**Trace ID**: {trace_id} (if available)

## Context
{description of what was happening}

## Root Cause
**Category**: {Documentation Gap | Missing Examples | Agent Scope | Configuration}

{detailed analysis}

## Occurrences
- **Total**: {count} times in past {time_range}
- **Trend**: {increasing | stable | decreasing}
- **Similar errors**: {count} related patterns found

## Previous Solutions
{If found in knowledge base, show previous solution}

## Recommended Actions

### Immediate
{code changes or commands to fix now}

### Systemic
- Linear issue created: DEV-XXX - {title}
- Knowledge base updated with solution
- Documentation {created | updated}: {path}

## Prevention Strategy
{How to prevent this error class in the future}
```

### 2. Linear Issue (created automatically)

With labels:
- `error-prevention`
- `systemic-improvement`
- Root cause category tag
- Service tag

### 3. Knowledge Base Entry (created automatically)

Searchable by:
- Error message
- Error type
- Service name
- Root cause category

### 4. Follow-up Actions (if applicable)

- GitHub PR for documentation updates
- Skill creation for reusable patterns
- Agent refactoring proposal

## Example Usage

### Manual Trigger (via slash command)

```
User: /analyze-error
Error: ModuleNotFoundError: No module named 'typing_extensions'
Service: resume-agent
Context: Running job analysis workflow with LangGraph

Skill execution:
1. Query ELK for similar errors → Found 3 occurrences in past week
2. Search knowledge base → No previous solution found
3. Classify root cause → Configuration/Dependency issue
4. Search codebase → Found usage but no dependency declaration
5. Generate solution:
   - Immediate: Add to UV script dependencies
   - Systemic: Create Linear issue for dependency audit
   - Knowledge base: Store solution for future
6. Output report with all recommendations
```

### Automatic Trigger (via Kibana alert)

```
Kibana alert: High error rate detected
Service: agent-chat-ui
Error rate: 15 errors/min (threshold: 10)

Skill execution:
1. Query ELK for error patterns → 90% are same error
2. Analyze trend → Started 15 minutes ago (sudden spike)
3. Get error context → All errors have same stack trace
4. Classify → Missing code example (using wrong API method)
5. Search for solution → Found working pattern in resume-agent
6. Generate report + Create Linear issue
7. Notify user via observability dashboard
```

## Integration Points

### With Observability Server

The skill integrates with `apps/observability-server/` via:
- Kibana alert webhook → `/alerts/trigger`
- Trigger error analysis for high error rates
- Store analysis results in events.db

### With Linear

Auto-create issues with:
- Clear title and description
- Acceptance criteria
- Priority based on severity/frequency
- Labels for categorization

### With Knowledge Base (Qdrant)

Store learnings for:
- Error patterns and solutions
- Code examples (working vs broken)
- Prevention strategies
- Service-specific gotchas

### With GitHub (optional)

Propose fixes via:
- Create branch for documentation updates
- Submit PR with example code
- Link PR to Linear issue

## Success Metrics

Track effectiveness of error analysis:

- **Error recurrence rate**: % of errors that happen again after fix
- **Time to resolution**: How quickly errors are understood and fixed
- **Knowledge base coverage**: % of errors with documented solutions
- **Systemic improvements**: Count of Linear issues created and completed
- **Error prevention**: Reduction in total error count over time

## Advanced: Pattern Recognition

Over time, the skill learns to recognize:

1. **Service-specific patterns**
   - resume-agent: Browser automation errors
   - agent-chat-ui: API integration errors

2. **Technology patterns**
   - LangGraph: State management, tool binding
   - FastMCP: Server initialization, tool registration
   - Elasticsearch: Query syntax, index patterns

3. **Temporal patterns**
   - Errors after dependency updates
   - Errors during deployment
   - Errors under high load

This allows the skill to become more accurate and faster over time.

## Notes

- Always search knowledge base FIRST before deep analysis
- Prioritize fixes that prevent entire categories of errors
- Balance immediate fixes vs long-term improvements
- Use Linear issues to track systemic changes
- Update knowledge base even for one-off errors (might recur)

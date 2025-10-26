# Quickstart: LangGraph Resume Agent

**Date**: 2025-10-23
**Feature**: LangGraph Resume Agent (006)
**Purpose**: Get started with the LangGraph implementation in 5 minutes

## Prerequisites

- Python 3.10+
- UV package manager installed
- Anthropic API key (for Claude)
- Existing resume agent data (`data/resume_agent.db`, `resumes/`)

## Installation

```bash
# Navigate to LangGraph implementation directory
cd apps/resume-agent-langgraph

# Install dependencies via UV
uv sync

# Copy environment template
cp .env.example .env

# Add your Anthropic API key to .env
# ANTHROPIC_API_KEY=your_key_here
```

## Quick Start

### Option 1: Use with Claude Desktop (Recommended)

1. **Start the MCP server**:
   ```bash
   uv run resume_agent_langgraph.py
   ```

2. **Configure Claude Desktop** (add to `claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "resume-agent-langgraph": {
         "command": "uv",
         "args": [
           "run",
           "D:\\source\\Cernji-Agents\\apps\\resume-agent-langgraph\\resume_agent_langgraph.py"
         ],
         "env": {
           "ANTHROPIC_API_KEY": "your_key_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and verify MCP server connection.

4. **Test with a job application**:
   ```
   User: Analyze this job posting: https://example.com/job
   Claude: [Uses analyze_job_posting tool from LangGraph implementation]
   ```

### Option 2: Direct Python Usage

```python
from resume_agent_langgraph import complete_application_workflow

# Execute complete workflow
result = complete_application_workflow(
    job_url="https://example.com/job-posting"
)

print(f"Job Analysis: {result['job_analysis']}")
print(f"Tailored Resume: {result['tailored_resume']}")
print(f"Cover Letter: {result['cover_letter']}")
print(f"Portfolio Examples: {result['portfolio_examples']}")
print(f"Errors: {result['errors']}")
```

## Key Differences from Original Implementation

| Aspect | Original (Claude Agent SDK) | LangGraph Version |
|--------|----------------------------|-------------------|
| **Orchestration** | Manual sequencing in agent loops | StateGraph with nodes and edges |
| **State Management** | In-memory variables | Persistent checkpoints (SqliteSaver) |
| **Error Handling** | Try-catch with early exit | Conditional edges with error accumulation |
| **Resumption** | Not supported | Resume from last checkpoint via thread_id |
| **Visualization** | No built-in visualization | LangGraph Studio support |
| **Caching** | At DAL level only | DAL + workflow-level cache nodes |

## Workflow State Recovery Example

```python
from langgraph.graph import StateGraph
from resume_agent_langgraph import application_workflow

# Start workflow
workflow_id = "unique-workflow-123"
result = application_workflow.invoke(
    {"job_url": "https://example.com/job"},
    config={"configurable": {"thread_id": workflow_id}}
)

# If interrupted, resume from last checkpoint
resumed_result = application_workflow.invoke(
    None,  # No new input needed
    config={"configurable": {"thread_id": workflow_id}}
)
```

## Performance Benchmarks

Expected performance (must match original implementation per SC-003):

| Operation | Target | Typical |
|-----------|--------|---------|
| Job analysis (new) | <15s | 10-12s |
| Job analysis (cached) | <3s | <1s |
| Resume tailoring | <20s | 15-18s |
| Cover letter generation | <25s | 20-23s |
| Complete workflow | <60s | 45-55s |

**Performance Monitoring**: Each workflow execution logs node-level durations to observability server.

## Observability Integration

LangGraph implementation maintains existing observability hooks:

```python
# Observability events emitted at:
# - Workflow start (SessionStart)
# - Each node entry (PreToolUse)
# - Each node exit (PostToolUse)
# - Workflow completion (SessionEnd)

# View real-time events in observability dashboard:
# http://localhost:3000
```

## Troubleshooting

### Issue: "Module 'langgraph' not found"

**Solution**: Install dependencies via UV:
```bash
cd apps/resume-agent-langgraph
uv sync
```

### Issue: "Checkpoint database locked"

**Solution**: Ensure no other workflow executions are running with the same `thread_id`. Each concurrent workflow needs a unique ID.

### Issue: "Performance slower than original"

**Solution**:
1. Check if caching is enabled (should see `cached: true` in responses)
2. Verify network latency (Claude API calls)
3. Check observability logs for slow nodes

### Issue: "State recovery not working"

**Solution**:
1. Verify `data/workflow_checkpoints.db` exists and is writable
2. Ensure using same `thread_id` for resumption
3. Check checkpoint retention policy (default: 7 days)

## Testing

Run contract tests to verify backward compatibility:

```bash
cd apps/resume-agent-langgraph

# Run all tests
uv run pytest tests/

# Run contract tests only
uv run pytest tests/contract/

# Run with coverage
uv run pytest --cov=resume_agent_langgraph tests/
```

Expected test results:
- ✅ All 22 MCP tool signatures match original
- ✅ Return schemas match original
- ✅ Performance targets met
- ✅ Error handling matches original behavior

## Next Steps

1. **Compare with original**: Run side-by-side comparison with `apps/resume-agent/`
2. **Evaluate developer experience**: Note workflow changes, state management, error handling
3. **Performance testing**: Run benchmarks with identical inputs
4. **Decision**: Keep LangGraph implementation or revert to Claude Agent SDK

## Resources

- **LangGraph Documentation**: https://python.langchain.com/docs/langgraph
- **Feature Spec**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **MCP Tool Contracts**: [contracts/mcp-tools.md](./contracts/mcp-tools.md)

## Feedback

This is an experimental implementation. Please document:
- Developer experience (easier/harder than original?)
- State management clarity (better/worse?)
- Debugging experience (LangGraph Studio, logs)
- Performance observations
- Workflow visualization utility

**Evaluation Criteria**: See Success Criteria (SC-001 to SC-010) in [spec.md](./spec.md)

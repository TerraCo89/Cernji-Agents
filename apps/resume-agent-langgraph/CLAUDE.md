# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

LangGraph-based conversational agent for resume tailoring and career assistance. This is an experimental implementation exploring LangGraph's workflow orchestration capabilities compared to the MCP server implementation in `apps/resume-agent/`.

**Tech Stack**: Python 3.11+, LangGraph, LangChain, Anthropic/OpenAI SDK, FastMCP, SQLite

## Quick Start Commands

### Development Server

```bash
# Start LangGraph dev server with Studio UI (port 2024)
langgraph dev

# Alternative: Start FastAPI server (if implemented)
python scripts/start_fastapi.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=resume_agent --cov-report=term-missing

# Run specific test files
pytest tests/test_graph_invoke.py
pytest tests/integration/test_job_analysis_workflow.py
pytest tests/contract/test_mcp_tools.py

# Test collection only (verify imports)
pytest --collect-only -q
```

### Installation

```bash
# Install package and dependencies
pip install -e .

# Install with LangGraph CLI for local development
pip install -e . "langgraph-cli[inmem]"

# Setup environment
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY or OPENAI_API_KEY)
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Validate syntax and imports
python -m compileall -q . && pytest --collect-only -q
```

## Architecture

### Core Graph Pattern

The main graph (`src/resume_agent/graph.py`) follows LangGraph's tool-calling chatbot pattern:

```
START → chatbot → tools (if tool calls) → chatbot → END
              ↓
            (END if no tool calls)
```

**Key Components**:
- **State**: `ResumeAgentState` TypedDict with custom reducers (imported from `state.schemas`)
- **Node**: `chatbot()` function that invokes LLM with tools bound
- **Tools**: List of LangChain tools (`@tool` decorated functions)
- **Checkpointing**: Automatic via LangGraph server (no manual checkpointer needed)

### State Schema Design

State is defined using TypedDict (not Pydantic) for msgpack serialization compatibility:

**Location**: `src/resume_agent/state/schemas.py`

**Key State Fields**:
- `messages` - Conversation history (uses `add_messages` reducer)
- `job_analysis` - Current job analysis data
- `master_resume` - User's master resume
- `tailored_resume` - Job-specific tailored resume
- `portfolio_examples` - Relevant code examples (uses `append_unique_examples` reducer)
- `workflow_progress` - Multi-step workflow tracking
- `error_message` - Latest error for resilient error handling

**Custom Reducers**:
- `append_unique_examples()` - Deduplicate portfolio entries by id/title
- `replace_with_latest()` - Always use new value (default replacement behavior)

### Tool Organization

Tools are organized by function in `src/resume_agent/tools/`:

- **`job_analyzer.py`** - Job posting analysis
- **`ats_scorer.py`** - ATS compatibility scoring
- **`resume_parser.py`** - Resume data loading and parsing

All tools are LangChain `@tool` decorated functions that can be bound to the LLM.

### Data Access Pattern

**Design Decision**: Reuse data access functions from the original MCP server (`apps/resume-agent/resume_agent.py`) rather than duplicating code.

**Import Pattern**:
```python
import sys
sys.path.append("apps/resume-agent")
from resume_agent import (
    data_read_master_resume,
    data_write_job_analysis,
    # ... other DAL functions
)
```

This maintains a single source of truth for database operations across both implementations.

## LangGraph Development Patterns

### Error Handling

**Never raise exceptions in nodes** - accumulate errors in state instead:

```python
def analyze_job_node(state: ResumeAgentState) -> dict:
    try:
        analysis = perform_analysis(state["job_url"])
        return {"job_analysis": analysis}
    except Exception as e:
        # Accumulate error, don't raise
        return {
            "error_message": f"Analysis failed: {str(e)}",
            "messages": [AIMessage(content="Could not analyze job posting.")]
        }
```

This enables partial success and workflow resumability.

### State Updates

**Always return partial state updates**, never mutate state directly:

```python
# ✅ Correct
def node(state: ResumeAgentState) -> dict:
    return {"new_field": "value"}  # Returns update dict

# ❌ Wrong
def node(state: ResumeAgentState) -> dict:
    state["new_field"] = "value"  # Don't mutate!
    return state
```

### TypedDict vs Pydantic

**Use TypedDict for state schemas** (msgpack serialization requirement):

```python
# State schema - TypedDict
class MyState(TypedDict):
    field: str

# Validation at MCP tool boundary - Pydantic
class MyStateModel(BaseModel):
    field: str

validated = MyStateModel(field="value")
initial_state = validated.model_dump(mode='json')  # Convert to dict
graph.invoke(initial_state)  # Pass dict, not Pydantic model
```

### Thread Management

**Always provide thread_id** for conversation persistence:

```python
result = graph.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config={"configurable": {"thread_id": "unique-conversation-id"}}
)
```

When running via `langgraph dev`, checkpointing is automatic.

## Project Structure

```
apps/resume-agent-langgraph/
├── src/resume_agent/
│   ├── graph.py              # Main graph definition
│   ├── state/
│   │   └── schemas.py        # State TypedDict + reducers
│   ├── tools/
│   │   ├── job_analyzer.py   # Job analysis tools
│   │   ├── ats_scorer.py     # ATS scoring tools
│   │   └── resume_parser.py  # Resume parsing tools
│   ├── nodes/                # Node functions (if separated)
│   └── prompts/              # Prompt templates
├── tests/
│   ├── unit/                 # Unit tests for individual functions
│   ├── integration/          # Integration tests for workflows
│   └── contract/             # Contract tests vs MCP server
├── examples/                 # Example usage and tutorials
├── docs/                     # Architecture and design docs
├── scripts/                  # Dev/deployment scripts
├── langgraph.json            # LangGraph server configuration
├── pyproject.toml            # Dependencies and metadata
└── .env.example              # Environment template
```

## Configuration

### Environment Variables

Required variables (choose one LLM provider):

```bash
# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...

# Optional: Provider/model selection (defaults shown)
LLM_PROVIDER=openai          # or "anthropic"
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-sonnet-4-5
```

### LangGraph Configuration

`langgraph.json` defines available graphs:

```json
{
  "graphs": {
    "resume_agent_advanced": "./src/resume_agent/graph.py:graph",
    "resume_agent_basic": "./resume_agent_langgraph.py:resume_agent_langgraph"
  },
  "env": ".env"
}
```

## Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/unit/`) - Individual tool/node functions
2. **Integration Tests** (`tests/integration/`) - Full workflow execution
3. **Contract Tests** (`tests/contract/`) - Verify compatibility with MCP server DAL

### Running Tests After Changes

After refactoring or moving modules, validate immediately:

```bash
# Quick validation (< 30 seconds)
python -m compileall -q . && pytest --collect-only -q

# Full test suite
pytest

# Or use validation script (if available)
.\scripts\validate-changes.ps1  # Windows
./scripts/validate-changes.sh   # Linux/macOS
```

## Key Architectural Decisions

**Documented in**: `docs/architecture-decisions.md`

1. **Hybrid Tool Approach** - Reimplement workflows as nodes, reuse data access directly
2. **StateGraph with TypedDict** - Automatic checkpointing, custom reducers
3. **Direct DAL Reuse** - Import functions from MCP server (single source of truth)
4. **Error Accumulation** - Never raise in nodes, accumulate errors in state for partial success
5. **Node-by-Node Streaming** - SSE for real-time progress updates (future)

## Common Operations

### Adding a New Tool

1. Create tool function in appropriate module:
```python
# src/resume_agent/tools/my_tool.py
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> dict:
    """Tool description for LLM."""
    # Implementation
    return {"result": "value"}
```

2. Export from `tools/__init__.py`:
```python
from .my_tool import my_new_tool
__all__ = [..., "my_new_tool"]
```

3. Add to tools list in `graph.py`:
```python
from resume_agent.tools import my_new_tool
tools = [..., my_new_tool]
```

The graph automatically handles tool routing - no manual edge configuration needed.

### Adding State Fields

Extend `ResumeAgentState` in `state/schemas.py`:

```python
class ResumeAgentState(TypedDict, total=False):
    # Existing fields...
    my_new_field: Annotated[Optional[str], replace_with_latest]
```

### Debugging with LangGraph Studio

1. Start dev server: `langgraph dev`
2. Studio opens in browser automatically
3. Create new thread, send messages
4. View graph execution, state transitions, tool calls
5. Edit past state and rerun from specific nodes

## Resources

- **README.md** - Project overview and quick start
- **docs/architecture-decisions.md** - Key design decisions and rationale
- **docs/WORKING_PATTERN.md** - LangGraph development patterns
- **docs/state-schema.md** - Complete state schema documentation
- **docs/workflow-mapping.md** - MCP tool → LangGraph node mapping
- **examples/basic_usage.py** - Programmatic graph invocation example
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Original MCP Server**: `apps/resume-agent/resume_agent.py`

## Integration with Parent Repository

This is one app in a multi-app monorepo. See parent `CLAUDE.md` for:
- Overall project structure
- Other applications (MCP server, Agent Chat UI, Observability)
- Shared development practices
- Deployment guides

# Resume Agent - LangGraph Conversational Agent

A real-time conversational agent powered by LangGraph and Claude, designed to assist with job applications and resume management.

> **🆕 Latest Update**: Rebuilt with clean LangGraph patterns following the official tutorial. The new `src/resume_agent/graph.py` provides a minimal foundation ready for incremental feature additions. Use `langgraph dev` to run with Studio UI for visual debugging.

## Current Status: v0.3.0 - Clean Foundation

This is a clean foundation following LangGraph best practices:

- ✅ Minimal graph structure ready for incremental additions
- ✅ Multi-provider LLM support (OpenAI + Anthropic via init_chat_model)
- ✅ Tool-ready architecture (add tools to the `tools` list)
- ✅ LangGraph Studio integration for visual debugging
- ✅ Professional package structure
- ✅ Type-safe with TypedDict and add_messages reducer

## Purpose

This implementation explores LangGraph for building conversational agents, starting simple and adding features incrementally. Key capabilities being demonstrated:

- **Conversational Flow**: Natural language interaction with context retention
- **State Management**: Explicit conversation state with message history
- **Workflow Orchestration**: Multi-step agent loops with conditional routing
- **Extensibility**: Clean patterns for adding specialized functions

## Next Steps

The following features will be added incrementally (from original MCP server):

1. Job analysis with structured data extraction
2. ATS-optimized resume tailoring
3. Personalized cover letter generation
4. GitHub portfolio code example search
5. RAG pipeline for company website context
6. Career history management

## Quick Start

### Prerequisites

- Python 3.10+
- UV package manager
- Anthropic API key (for Claude) or OpenAI API key (for GPT models)

### Installation

```bash
# Navigate to project directory
cd apps/resume-agent-langgraph

# Install dependencies including LangGraph CLI
pip install -e . "langgraph-cli[inmem]"

# Install Playwright browsers (required for web scraping)
playwright install chromium

# Copy environment template
cp .env.example .env

# Configure your API keys in .env (see next section)
```

### LLM Provider Configuration

Add your API keys to `.env`:

```bash
# .env
# Required: Choose one LLM provider
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Customize models (defaults shown)
LLM_PROVIDER=openai  # or "anthropic"
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-sonnet-4-5
```

The `init_chat_model()` function will automatically select the right provider based on your configuration.

### Running the Agent

Start the LangGraph development server with Studio UI:

```bash
langgraph dev
```

This will:
- Start the LangGraph server on port 2024
- Open LangGraph Studio in your browser for visual debugging
- Enable hot reload for code changes

**Using LangGraph Studio:**
1. Click the `+` button to start a new conversation thread
2. Type messages in the input field
3. View the graph execution in real-time
4. Edit past state and rerun from specific nodes for debugging
5. Monitor message flow and state changes visually

**Example interaction:**
```
You: Hello! I need help tailoring my resume.
Assistant: Hello! I'd be happy to help you tailor your resume. Could you tell me more about...
```

**For programmatic access**, see the `examples/basic_usage.py` file for how to invoke the graph directly from Python code.

## Architecture

The graph follows LangGraph's standard single-node chatbot pattern (ready to extend with tools):

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       v
┌─────────────┐
│  chatbot    │  ← Process messages with LLM
└──────┬──────┘
       │
       v
    (END when no tool calls)
    (tools node when tool calls present - currently no tools)
```

### Key Components

**Defined in `src/resume_agent/graph.py`:**

1. **State**: TypedDict with message history
   - `messages: Annotated[list, add_messages]` - Standard LangGraph message reducer
   - Automatically appends messages rather than overwriting

2. **chatbot node**: Main processing node
   - Invokes LLM (OpenAI or Anthropic via `init_chat_model`)
   - If tools are present, binds them to LLM and handles tool calls
   - Returns assistant response to append to message history

3. **tools list**: Currently empty, ready for additions
   - Add tools here (e.g., job analyzer, resume parser)
   - When tools are added, ToolNode and tools_condition are automatically configured

4. **LLM Configuration**: Multi-provider support
   - Configured via environment variables (`LLM_PROVIDER`, `OPENAI_MODEL`, `ANTHROPIC_MODEL`)
   - Uses LangChain's `init_chat_model()` for unified interface

5. **Checkpointing**: Handled by LangGraph Server
   - When running via `langgraph dev`, persistence is automatic
   - Thread-based conversation history maintained by the server

## Development

### Project Structure

```
apps/resume-agent-langgraph/
├── src/resume_agent/
│   ├── graph.py                # Main graph definition (NEW)
│   ├── state/                  # State schemas (existing modular code)
│   ├── tools/                  # Tool definitions (existing modular code)
│   ├── nodes/                  # Node functions (existing modular code)
│   └── prompts/                # Prompt templates (existing modular code)
├── examples/                    # Example usage patterns
│   └── basic_usage.py          # Programmatic graph invocation
├── docs/                        # Documentation
├── tests/                       # Test suite
├── langgraph.json              # LangGraph server config
├── pyproject.toml              # Dependencies
├── .env.example                # Environment template
└── README.md                    # This file
```

### Adding New Capabilities

The graph is designed for incremental additions. Start simple and add features one at a time:

#### 1. Adding Tools

Add tools to the `tools` list in `graph.py`:

```python
from langchain_core.tools import tool

@tool
def analyze_job(url: str) -> dict:
    """Analyze a job posting from a URL."""
    # Implementation here
    return {"title": "...", "requirements": [...]}

# Add to tools list
tools = [analyze_job]
```

The graph automatically detects tools and adds routing! No manual edge configuration needed.

#### 2. Extending State

Add fields to track additional data:

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    job_url: str  # Track current job being analyzed
    resume_data: dict  # Cache parsed resume
```

#### 3. Adding Human-in-the-Loop

Use `interrupt()` for human verification:

```python
from langgraph.types import Command, interrupt
from langchain_core.tools import tool, InjectedToolCallId

@tool
def verify_resume_changes(
    changes: dict,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Request human approval for resume changes."""
    human_response = interrupt({
        "question": "Apply these changes?",
        "changes": changes
    })

    if human_response.lower().startswith("y"):
        return Command(update={"resume_data": changes})
    else:
        return "Changes rejected"
```

See the basic-langgraph-agent example for a complete working implementation of human-in-the-loop.

### Testing

Test the graph using LangGraph Studio or programmatically:

```python
from src.resume_agent.graph import graph
from langchain_core.messages import HumanMessage

# Invoke the graph
result = graph.invoke({
    "messages": [HumanMessage(content="Hello!")]
})

print(result["messages"][-1].content)
```

Run the test suite:

```bash
pytest tests/
```

## Resources

- **LangGraph Documentation**: https://python.langchain.com/docs/langgraph
- **Crash Course Notebook**: [langgraph_crash_course.ipynb](examples/langgraph_crash_course.ipynb)
- **LLM Provider Comparison**: [PROVIDERS.md](docs/PROVIDERS.md) - Claude vs OpenAI comparison
- **Original MCP Server**: `/apps/resume-agent/resume_agent.py`
- **Feature Spec**: `/specs/006-langgraph-resume-agent/spec.md`

## What's Next?

Once the foundational conversational pattern is working well, we'll add specialized functions:

1. **Job Analysis** - Parse job postings and extract requirements
2. **Resume Tailoring** - Match your experience to job requirements
3. **Cover Letter Generation** - Write personalized cover letters
4. **Portfolio Search** - Find relevant code examples from GitHub

Each function will be tested individually before integration into the conversational flow.

## License

Experimental

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangGraph chatbot application based on the official LangGraph tutorial. It demonstrates an interactive agent with tools, human-in-the-loop feedback, and multi-node graph orchestration that can be visualized and debugged using LangGraph Studio.

**Features**:
- **Tool Integration**: Web search via TavilySearch and custom human assistance tool
- **Human-in-the-Loop**: Interactive verification using interrupt() with dual format support (Studio UI string responses and programmatic dict responses)
- **State Management**: Extended state schema with message history, name, and birthday fields
- **Conditional Routing**: Dynamic tool execution with automatic routing back to chatbot

**Tech Stack**: Python 3.10+, LangGraph, LangChain, LangGraph CLI, Tavily API

## Essential Commands

**Install dependencies**:
```bash
pip install -e . "langgraph-cli[inmem]"
```

**Start LangGraph development server** (includes Studio UI):
```bash
langgraph dev
```

**Run unit tests**:
```bash
make test
# Or specific file:
make test TEST_FILE=tests/unit_tests/test_configuration.py
```

**Run integration tests**:
```bash
make integration_tests
```

**Lint code**:
```bash
make lint
```

**Format code**:
```bash
make format
```

## Architecture

The application follows LangGraph's standard structure:

- **Graph definition**: `src/agent/graph.py` - Core chatbot logic using StateGraph
- **State schema**: TypedDict-based `State` class with:
  - `messages`: Message history using `add_messages` reducer
  - `name`: User's name (populated by human_assistance tool)
  - `birthday`: User's birthday (populated by human_assistance tool)
- **Graph flow**: Cyclic flow with conditional routing:
  - START → chatbot node
  - chatbot → tools node (if tool calls present) OR END (if no tool calls)
  - tools → chatbot (after tool execution)
- **Tools**:
  - `TavilySearch`: Web search tool with max 2 results
  - `human_assistance`: Custom tool using interrupt() for human-in-the-loop verification
- **LLM**: Configured via `init_chat_model()` - currently uses OpenAI GPT-4.1-mini but supports any LangChain-compatible model

The chatbot node invokes the LLM with tools bound, receiving either a message response or tool calls. Tool execution happens in the tools node via ToolNode, with the human_assistance tool pausing execution for human input via interrupt(). Tool results flow back to the chatbot for continued processing. Parallel tool calling is disabled to prevent duplicate invocations during interrupts.

## Configuration

**Environment setup**:
1. Copy `.env.example` to `.env`
2. Add required API keys:
   - LLM provider (OpenAI, Anthropic, etc.)
   - `TAVILY_API_KEY` for web search functionality
3. Optionally add `LANGSMITH_API_KEY` for tracing

**LangGraph server config**: `langgraph.json` defines:
- Graph entrypoint: `./src/agent/graph.py:graph`
- Environment file: `.env`
- Dependencies: Current directory (`.`)

## Development Workflow

1. Edit `src/agent/graph.py` to modify graph logic
2. Changes auto-reload in LangGraph Studio via hot reload
3. Use Studio UI to debug by editing past state and rerunning from specific nodes
4. Run tests to validate changes
5. Use `+` button in Studio to create new conversation threads

## Testing

- **Unit tests**: `tests/unit_tests/` - Test graph configuration and structure
- **Integration tests**: `tests/integration_tests/` - Test full graph execution with real LLM calls
- Integration tests use `@pytest.mark.anyio` for async support

## Package Structure

The package is configured with dual naming in `pyproject.toml`:
- `langgraph.templates.agent` - LangGraph template namespace
- `agent` - Local package name

Both point to `src/agent/` directory.

## Code Quality

**Linting**: Ruff with strict settings including:
- pycodestyle (E), pyflakes (F), isort (I), pydocstyle (D)
- Google-style docstrings required
- Type checking with mypy in strict mode

**Formatting**: Ruff format with import sorting

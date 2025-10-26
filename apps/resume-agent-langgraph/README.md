# Resume Agent - LangGraph Conversational Agent

A real-time conversational agent powered by LangGraph and Claude, designed to assist with job applications and resume management.

## Current Status: v0.3.0 - Professional Modular Architecture

This is a production-ready implementation with professional folder structure. The agent features:

- ✅ Modular architecture with clear separation of concerns
- ✅ Multi-provider support (Claude + OpenAI)
- ✅ Professional package structure following best practices
- ✅ Comprehensive test suite and examples
- ✅ Easy to extend with new features
- ✅ Type-safe with TypedDict and Pydantic

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

# Install dependencies via UV
uv sync

# Copy environment template
cp .env.example .env

# Configure your LLM provider in .env
# LLM_PROVIDER=openai  # or "claude" (default: claude)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
```

### LLM Provider Configuration

The agent supports both **Claude (Anthropic)** and **OpenAI** as LLM providers:

**OpenAI (Recommended for testing - cheaper):**
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
# Optional: OPENAI_MODEL=gpt-4o-mini (default)
```

**Claude (Anthropic):**
```bash
# .env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_key_here
# Optional: CLAUDE_MODEL=claude-sonnet-4-5 (default)
```

The agent will automatically show which provider and model it's using when it starts.

**💡 Tip**: OpenAI is ~20x cheaper than Claude, making it ideal for testing. See [PROVIDERS.md](docs/PROVIDERS.md) for detailed comparison.

### Running the Agent

#### Interactive Mode

Run the agent in your terminal for a real-time conversation:

```bash
# Start the conversational agent
uv run apps/resume-agent-langgraph/resume_agent_langgraph.py
```

**Example session:**
```
============================================================
🚀 Resume Agent - LangGraph Conversational Agent
============================================================

💡 LLM Provider: OpenAI
💡 Model: gpt-4o-mini

Welcome! I'm your Resume Agent assistant.
I'm currently in development mode, learning to chat with you.

Type 'exit', 'quit', or 'bye' to end the conversation.
============================================================

============================================================
👤 You (type 'exit' or 'quit' to end): Hello!

🤖 Thinking... (OpenAI/gpt-4o-mini)

🤖 Assistant: Hello! How can I assist you today?

============================================================
👤 You (type 'exit' or 'quit' to end): exit

👋 Goodbye! Thanks for chatting!
```

#### Test Mode

Run automated tests without interactive input:

```bash
uv run apps/resume-agent-langgraph/test_agent.py
```

This will test the agent with 3 predefined messages and verify the conversation flow.

## Architecture

Based on patterns from the [LangGraph Crash Course](langgraph_crash_course.ipynb):

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       v
┌─────────────┐
│ get_input   │  ← Get user message from CLI
└──────┬──────┘
       │
       v (conditional: continue or exit)
┌─────────────┐
│    chat     │  ← Process with Claude API
└──────┬──────┘
       │
       v (loop back)
```

### Key Components

1. **ConversationState**: TypedDict with append-only messages list
   - Uses `Annotated[list, add]` for message appending (standard LangGraph pattern)
   - Tracks conversation history across turns
   - `should_continue` flag for exit handling

2. **chat_node**: Processes messages with Claude API
   - Takes full conversation history
   - Sends to Claude with system prompt
   - Returns assistant response

3. **get_user_input_node**: Handles CLI input and exit commands
   - Displays last assistant message
   - Gets user input from terminal
   - Checks for exit commands (exit/quit/bye)

4. **should_continue**: Conditional edge for conversation flow
   - Routes to "chat" if user wants to continue
   - Routes to END if user wants to exit

5. **MemorySaver**: Checkpointer for conversation history
   - Maintains conversation context across turns
   - Thread-based session management

## Development

### Project Structure

```
apps/resume-agent-langgraph/
├── resume_agent_langgraph.py   # Conversational agent
├── test_agent.py                # Automated test script
├── examples/                    # Example code and tutorials
│   └── langgraph_crash_course.ipynb
├── docs/                        # Documentation
│   └── CLAUDE.md               # Development guidance
├── pyproject.toml               # UV dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

### Adding New Capabilities

Follow this pattern for adding functions to the agent:

#### 1. Define a new node function

```python
def analyze_job_node(state: ConversationState) -> dict:
    """Analyze a job posting from URL in user message."""
    # Extract job URL from user message
    last_msg = state["messages"][-1]["content"]

    # Call analysis logic (can reuse from original MCP server)
    analysis = perform_job_analysis(extract_url(last_msg))

    # Format response
    response = format_analysis_response(analysis)

    # Return assistant message
    return {
        "messages": [{
            "role": "assistant",
            "content": response
        }]
    }
```

#### 2. Add the node to the graph

```python
graph.add_node("analyze_job", analyze_job_node)
```

#### 3. Add routing logic

```python
def route_intent(state: ConversationState) -> str:
    """Route to specialized nodes based on user intent."""
    last_message = state["messages"][-1]["content"].lower()

    if "analyze" in last_message and "job" in last_message:
        return "analyze_job"

    return "chat"  # Default to general chat
```

#### 4. Update conditional edges

```python
graph.add_conditional_edges(
    "get_input",
    route_intent,
    {
        "chat": "chat",
        "analyze_job": "analyze_job",
        END: END
    }
)
```

### Testing New Nodes

Always test nodes in isolation first:

```python
# Test the node directly
test_state = {
    "messages": [
        {"role": "user", "content": "Analyze this job: https://example.com/job"}
    ],
    "should_continue": True
}

result = analyze_job_node(test_state)
print(result)  # Should return formatted analysis
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

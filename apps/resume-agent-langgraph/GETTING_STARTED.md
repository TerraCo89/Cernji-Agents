# Getting Started with Resume Agent

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd apps/resume-agent-langgraph
pip install -e . "langgraph-cli[inmem]"
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Add your API key to .env
# For OpenAI:
OPENAI_API_KEY=sk-...

# Or for Anthropic:
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start the Server

```bash
langgraph dev
```

This opens LangGraph Studio in your browser where you can:
- Chat with the agent in real-time
- Visualize the graph execution
- Debug by editing past states
- See message flow and state changes

### 4. Test It Out

In the Studio UI:
1. Click the `+` button to start a new thread
2. Type: "Hello! I need help with my resume."
3. Watch the graph execute and see the response

## What's Been Built

### Current State

A minimal but complete LangGraph chatbot foundation:

```
src/resume_agent/graph.py
├── State: TypedDict with message history
├── chatbot node: LLM processing
├── tools list: Empty, ready for additions
└── graph: Compiled StateGraph
```

### Architecture Highlights

**State Management**:
- Uses `Annotated[list, add_messages]` for automatic message appending
- TypedDict provides type safety without Pydantic overhead

**LLM Configuration**:
- Multi-provider support (OpenAI/Anthropic)
- Unified interface via `init_chat_model()`
- Environment variable configuration

**Tool Infrastructure**:
- Conditional routing automatically enabled when tools are added
- ToolNode and tools_condition configured dynamically

**Deployment**:
- LangGraph Server handles checkpointing automatically
- Hot reload for rapid development
- Studio UI for visual debugging

## Next Steps

### Adding Your First Tool

1. Edit `src/resume_agent/graph.py`
2. Add a tool function:

```python
from langchain_core.tools import tool

@tool
def get_resume_tips(topic: str) -> str:
    """Get resume writing tips for a specific topic."""
    tips = {
        "formatting": "Use clean, ATS-friendly formatting...",
        "keywords": "Include relevant keywords from the job description...",
        "achievements": "Use the STAR method to describe achievements..."
    }
    return tips.get(topic, "Ask about: formatting, keywords, or achievements")

# Add to tools list
tools = [get_resume_tips]
```

3. Save the file (hot reload applies changes)
4. Test in Studio: "Give me resume tips about formatting"

### Extending State

Track additional data across conversations:

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    resume_url: str  # Track user's resume
    job_requirements: list[str]  # Extracted from job posting
```

### Adding Human-in-the-Loop

Create tools that pause for human input:

```python
from langgraph.types import interrupt, Command
from langchain_core.tools import tool, InjectedToolCallId
from typing import Annotated

@tool
def confirm_changes(
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Request human confirmation before making changes."""
    response = interrupt({
        "question": "Proceed with these changes?",
        "summary": summary
    })

    if response.lower().startswith("y"):
        return Command(update={"confirmed": True})
    return "Changes cancelled"
```

## Learning Resources

- **Basic Example**: `../basic-langgraph-agent/src/agent/graph.py` - Full tool + human-in-loop example
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Tutorial Source**: https://langchain-ai.github.io/langgraph/concepts/why-langgraph/

## Development Workflow

1. Edit code in `src/resume_agent/graph.py`
2. Save (hot reload applies changes)
3. Test in Studio UI
4. Use Studio's "edit state" feature to debug specific scenarios
5. When satisfied, write tests in `tests/`

## Troubleshooting

**Studio won't connect:**
- Check port 2024 is available
- Verify langgraph.json points to correct graph path
- Check console for startup errors

**LLM not responding:**
- Verify API key in .env
- Check LLM_PROVIDER matches your key (openai or anthropic)
- Look for errors in langgraph dev output

**Import errors:**
- Run `pip install -e . "langgraph-cli[inmem]"` again
- Check pyproject.toml dependencies
- Verify Python >= 3.11

## Ready to Build!

You now have a solid foundation. The existing modular code in `src/resume_agent/` (tools/, nodes/, state/) can be integrated incrementally as needed.

Start simple, test often, and add features one at a time. The LangGraph Studio UI makes debugging a breeze!

# LLM Provider Integration Patterns for LangGraph

## Solution Description

LangGraph nodes are standard Python functions that receive state and return state updates. This design allows direct integration with any LLM SDK without requiring LangChain wrappers. There are two primary approaches:

### Approach 1: Direct SDK Integration (Used in this project)
Call Anthropic and OpenAI SDKs directly within LangGraph nodes, managing message format conversion manually. This provides full control over API parameters and avoids LangChain dependencies.

### Approach 2: LangChain Wrapper Integration (Standard pattern)
Use `ChatAnthropic` and `ChatOpenAI` from LangChain, which handle message conversion automatically but add dependencies.

**This project uses Approach 1** for maximum flexibility and minimal dependencies.

## Key Differences Between Anthropic and OpenAI APIs

### Message Format
- **Anthropic**: Uses separate `system` parameter for system prompts
  ```python
  client.messages.create(
      model="claude-sonnet-4-5",
      system="You are a helpful assistant",  # System prompt separate
      messages=[{"role": "user", "content": "Hello"}]
  )
  ```

- **OpenAI**: Includes system message in `messages` array
  ```python
  client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
          {"role": "system", "content": "You are a helpful assistant"},
          {"role": "user", "content": "Hello"}
      ]
  )
  ```

### Response Format
- **Anthropic**: `response.content[0].text`
- **OpenAI**: `response.choices[0].message.content`

## Working Code Example

### 1. Multi-Provider LLM Function

```python
"""LLM provider abstraction for Claude and OpenAI."""

import anthropic
import openai
from typing import Literal


def call_llm(
    messages: list[dict],
    system_prompt: str,
    provider: Literal["claude", "openai"] = "claude",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> str:
    """
    Call the configured LLM provider (Claude or OpenAI).

    Args:
        messages: List of message dicts with role and content
        system_prompt: System prompt to guide the LLM
        provider: Which provider to use ("claude" or "openai")
        model: Model name (uses defaults if not specified)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response

    Returns:
        Assistant's response text

    Raises:
        Exception: If LLM call fails
    """
    if provider == "openai":
        # OpenAI API
        client = openai.OpenAI()  # Uses OPENAI_API_KEY env var

        # OpenAI format includes system message in messages array
        api_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=api_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    else:
        # Claude API (default)
        client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

        # Claude uses separate system parameter
        response = client.messages.create(
            model=model or "claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature
        )

        return response.content[0].text
```

### 2. LangGraph Node Integration

```python
"""Conversation nodes for chat functionality."""

from typing import TypedDict
from langgraph.graph import StateGraph


class ConversationState(TypedDict):
    """State schema for conversation graph."""
    messages: list[dict]
    provider: str  # "claude" or "openai"
    should_continue: bool


def chat_node(state: ConversationState) -> dict:
    """
    Process user message with LLM and return response.

    Args:
        state: Current conversation state

    Returns:
        Partial state update with assistant message
    """
    # Get provider from state (defaults to claude)
    provider = state.get("provider", "claude")

    print(f"\n🤖 Thinking... ({provider})")

    try:
        # Extract messages (filtering out system messages for API format)
        api_messages = [
            msg for msg in state["messages"]
            if msg["role"] != "system"
        ]

        # Call LLM with provider selection
        assistant_message = call_llm(
            messages=api_messages,
            system_prompt="You are a helpful career assistant.",
            provider=provider
        )

        # Return assistant message (will be appended to state)
        return {
            "messages": [{
                "role": "assistant",
                "content": assistant_message
            }]
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {str(e)}"
            }]
        }
```

### 3. Message Format Conversion

When integrating with LangGraph SDK (which uses LangChain message formats), convert messages before calling LLM APIs:

```python
"""Message format conversion utilities for LangGraph SDK compatibility."""

from typing import Any, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def convert_langgraph_messages_to_api_format(
    messages: list[Union[BaseMessage, dict]]
) -> list[dict]:
    """
    Convert LangGraph SDK message format to LLM API format.

    LangGraph SDK uses LangChain message objects (BaseMessage subclasses):
    - HumanMessage, AIMessage, SystemMessage objects
    - OR dicts with 'type' field: "human", "ai", "system"

    LLM APIs (Claude/OpenAI) expect:
    - role: "user", "assistant", "system"
    - content: string

    Args:
        messages: List of messages in LangGraph SDK format

    Returns:
        List of messages in API format

    Examples:
        >>> from langchain_core.messages import HumanMessage
        >>> msgs = [HumanMessage(content="Hello")]
        >>> convert_langgraph_messages_to_api_format(msgs)
        [{"role": "user", "content": "Hello"}]
    """
    api_messages = []

    for msg in messages:
        # Handle BaseMessage objects (HumanMessage, AIMessage, etc.)
        if isinstance(msg, BaseMessage):
            role = _convert_message_type_to_role(msg)
            content = msg.content
        # Handle dict format
        elif isinstance(msg, dict):
            # Check if already in API format
            if "role" in msg:
                role = msg["role"]
            else:
                role = _convert_type_to_role(msg.get("type", "human"))
            content = msg.get("content", "")
        else:
            continue

        # Handle content that might be array format (multimodal)
        if isinstance(content, list):
            content = _extract_text_from_content_blocks(content)

        api_messages.append({
            "role": role,
            "content": content
        })

    return api_messages


def _convert_message_type_to_role(msg: BaseMessage) -> str:
    """Convert LangChain BaseMessage object to API role."""
    if isinstance(msg, HumanMessage):
        return "user"
    elif isinstance(msg, AIMessage):
        return "assistant"
    elif isinstance(msg, SystemMessage):
        return "system"
    else:
        return "user"


def _convert_type_to_role(msg_type: str) -> str:
    """Convert LangGraph SDK message types to API roles."""
    mapping = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "assistant",
    }
    return mapping.get(msg_type, "user")


def _extract_text_from_content_blocks(content_blocks: list[Any]) -> str:
    """Extract text from content block array (for multimodal messages)."""
    text_parts = []

    for block in content_blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif "text" in block:
                text_parts.append(block["text"])
        elif isinstance(block, str):
            text_parts.append(block)

    return " ".join(filter(None, text_parts))
```

### 4. Environment Configuration

```python
"""Configuration management with multi-provider support."""

import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # LLM Configuration
    llm_provider: Literal["claude", "openai"] = Field(
        default="claude",
        description="LLM provider to use"
    )

    # API Keys
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT models"
    )

    # Model Names
    claude_model: str = Field(
        default="claude-sonnet-4-5",
        description="Claude model name"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )

    # LLM Parameters
    temperature: float = Field(
        default=0.7,
        description="LLM temperature"
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens per response"
    )

    class Config:
        env_file = ".env"


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### 5. Complete LangGraph Integration Example

```python
"""Complete example of LangGraph with multi-provider LLM support."""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    """Graph state schema."""
    messages: list[dict]
    provider: Literal["claude", "openai"]
    should_continue: bool


def chat_node(state: State) -> dict:
    """LLM chat node with provider switching."""
    provider = state.get("provider", "claude")

    # Filter system messages for API format
    api_messages = [
        msg for msg in state["messages"]
        if msg["role"] != "system"
    ]

    # Call LLM
    response = call_llm(
        messages=api_messages,
        system_prompt="You are a helpful assistant.",
        provider=provider
    )

    return {
        "messages": [{
            "role": "assistant",
            "content": response
        }]
    }


def should_continue(state: State) -> str:
    """Conditional edge: continue conversation or end."""
    if state.get("should_continue", True):
        return "chat"
    return END


# Build graph
graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", should_continue)

app = graph.compile()


# Usage example
if __name__ == "__main__":
    # Test with Claude
    result_claude = app.invoke({
        "messages": [{"role": "user", "content": "Hello!"}],
        "provider": "claude",
        "should_continue": False
    })

    print("Claude response:", result_claude["messages"][-1]["content"])

    # Test with OpenAI
    result_openai = app.invoke({
        "messages": [{"role": "user", "content": "Hello!"}],
        "provider": "openai",
        "should_continue": False
    })

    print("OpenAI response:", result_openai["messages"][-1]["content"])
```

## Environment Variable Configuration

Create a `.env` file:

```bash
# Choose provider: "claude" or "openai"
LLM_PROVIDER=claude

# API Keys (set the one you're using)
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

# Model Selection
CLAUDE_MODEL=claude-sonnet-4-5
OPENAI_MODEL=gpt-4o-mini

# LLM Parameters
TEMPERATURE=0.7
MAX_TOKENS=2048
```

## Switching Providers at Runtime

### Option 1: Environment Variable
```bash
# Use Claude
export LLM_PROVIDER=claude

# Use OpenAI
export LLM_PROVIDER=openai
```

### Option 2: State-Based Switching
```python
# Pass provider in state
result = app.invoke({
    "messages": [{"role": "user", "content": "Hello"}],
    "provider": "openai",  # Switch to OpenAI for this request
    "should_continue": False
})
```

### Option 3: Configuration Override
```python
from config import Settings

# Override default provider
settings = Settings(llm_provider="openai")
```

## Sources

### Official Documentation
- **Anthropic Python SDK**: GitHub repository with examples of `client.messages.create()` usage
  - Basic usage: `client.messages.create(model, max_tokens, messages)`
  - System prompts: Separate `system` parameter
  - Response format: `response.content[0].text`

- **OpenAI Python SDK**: Platform documentation and examples
  - Basic usage: `client.chat.completions.create(model, messages)`
  - System prompts: Included in `messages` array as `{"role": "system"}`
  - Response format: `response.choices[0].message.content`

### LangGraph Integration Patterns
- **LangGraph Documentation**: Nodes are Python functions that read/update state
  - Direct SDK integration: Call any Python library within node functions
  - No requirement to use LangChain wrappers
  - Message conversion handled manually or via utility functions

- **LangChain Integration**: Optional ChatAnthropic/ChatOpenAI wrappers
  - Automatic message format conversion
  - Tool calling abstractions
  - Adds LangChain dependencies

### Multi-Provider Patterns
- **Provider Switching**: Runtime context-based model selection
  - Initialize both providers
  - Select based on state/config
  - Environment variable configuration

- **Message Format Conversion**: LangGraph SDK to API format
  - LangGraph uses LangChain message objects (HumanMessage, AIMessage)
  - APIs expect dicts with "role" and "content"
  - Conversion utilities handle both formats

### Project Implementation
- **Current codebase**: `apps/resume-agent-langgraph/src/resume_agent/llm/`
  - `providers.py`: Multi-provider LLM abstraction
  - `messages.py`: Message format conversion utilities
  - `nodes/conversation.py`: Example node using provider abstraction
  - `config.py`: Environment-based configuration with Pydantic

## Key Insights

1. **LangGraph is SDK-agnostic**: Nodes are plain Python functions, allowing direct SDK usage

2. **Message format is critical**: Anthropic and OpenAI have different expectations for system prompts and response structures

3. **Provider switching patterns**:
   - Environment variables (deployment-level)
   - State-based (request-level)
   - Configuration objects (application-level)

4. **No LangChain requirement**: While LangChain provides convenient wrappers, direct SDK usage offers more control and fewer dependencies

5. **LangGraph SDK compatibility**: When using LangGraph's Agent Chat UI or SDK features, message conversion from LangChain format is necessary

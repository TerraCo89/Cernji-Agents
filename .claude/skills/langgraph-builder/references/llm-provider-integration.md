# LLM Provider Integration Guide

Complete guide for integrating Anthropic Claude and OpenAI GPT models within LangGraph nodes.

## Table of Contents

- [Direct SDK Integration](#direct-sdk-integration)
- [Multi-Provider Support](#multi-provider-support)
- [Message Format Conversion](#message-format-conversion)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Direct SDK Integration

### Anthropic Claude Integration

**Package:** `anthropic ^0.39.0`

```python
import anthropic
from langchain_core.messages import AIMessage, HumanMessage
import os

def call_claude(messages: list[dict], system_prompt: str) -> str:
    """Call Claude API with message history"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,  # Required for Anthropic
        system=system_prompt,  # Separate system parameter
        messages=messages  # [{"role": "user", "content": "..."}]
    )

    return response.content[0].text


def chat_node_claude(state: ConversationState) -> dict:
    """LangGraph node using Claude"""
    # Convert LangGraph messages to API format
    api_messages = [
        {"role": "user" if isinstance(msg, HumanMessage) else "assistant",
         "content": msg.content}
        for msg in state["messages"]
    ]

    # Call Claude
    response_text = call_claude(
        messages=api_messages,
        system_prompt="You are a helpful assistant."
    )

    # Return as AIMessage
    return {"messages": [AIMessage(content=response_text)]}
```

**Key Points:**
- `max_tokens` is **required**
- System prompt goes in separate `system` parameter
- Response accessed via `response.content[0].text`

### OpenAI GPT Integration

**Package:** `openai ^1.0.0`

```python
import openai
from langchain_core.messages import AIMessage, HumanMessage
import os

def call_openai(messages: list[dict], system_prompt: str) -> str:
    """Call OpenAI API with message history"""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # System message goes in messages array
    api_messages = [
        {"role": "system", "content": system_prompt}
    ] + messages

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,  # System message included
        max_tokens=2048  # Optional for OpenAI
    )

    return response.choices[0].message.content


def chat_node_openai(state: ConversationState) -> dict:
    """LangGraph node using OpenAI"""
    # Convert LangGraph messages to API format
    api_messages = [
        {"role": "user" if isinstance(msg, HumanMessage) else "assistant",
         "content": msg.content}
        for msg in state["messages"]
    ]

    # Call OpenAI
    response_text = call_openai(
        messages=api_messages,
        system_prompt="You are a helpful assistant."
    )

    # Return as AIMessage
    return {"messages": [AIMessage(content=response_text)]}
```

**Key Points:**
- `max_tokens` is **optional**
- System prompt goes in `messages` array as first message
- Response accessed via `response.choices[0].message.content`

---

## Multi-Provider Support

### Pattern 1: Environment Variable Switching

```python
from typing import Literal
import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()

def call_llm(messages: list[dict], system_prompt: str) -> str:
    """Unified LLM interface - switches based on env var"""
    if LLM_PROVIDER == "openai":
        return call_openai(messages, system_prompt)
    else:
        return call_claude(messages, system_prompt)


def chat_node(state: ConversationState) -> dict:
    """Provider-agnostic chat node"""
    api_messages = convert_to_api_format(state["messages"])

    response_text = call_llm(
        messages=api_messages,
        system_prompt="You are a helpful assistant."
    )

    return {"messages": [AIMessage(content=response_text)]}
```

**.env:**
```bash
LLM_PROVIDER=claude  # or "openai"
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Pattern 2: Runtime Provider Selection

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    provider: Literal["claude", "openai"]  # Provider in state


def chat_node(state: ConversationState) -> dict:
    """Chat node with runtime provider selection"""
    provider = state.get("provider", "claude")
    api_messages = convert_to_api_format(state["messages"])

    if provider == "openai":
        response_text = call_openai(api_messages, "You are a helpful assistant.")
    else:
        response_text = call_claude(api_messages, "You are a helpful assistant.")

    return {"messages": [AIMessage(content=response_text)]}
```

**Usage:**
```python
# Use Claude
result = graph.invoke({
    "messages": [HumanMessage("Hello")],
    "provider": "claude"
})

# Use OpenAI
result = graph.invoke({
    "messages": [HumanMessage("Hello")],
    "provider": "openai"
})
```

### Pattern 3: Pydantic Settings

```python
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    llm_provider: Literal["claude", "openai"] = "claude"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def call_llm(messages: list[dict], system_prompt: str) -> str:
    """Settings-based provider selection"""
    if settings.llm_provider == "openai":
        client = openai.OpenAI(api_key=settings.openai_api_key)
        api_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=api_messages,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature
        )
        return response.choices[0].message.content
    else:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
```

---

## Message Format Conversion

### LangGraph Messages → API Format

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

def convert_to_api_format(messages: list[BaseMessage]) -> list[dict]:
    """
    Convert LangGraph BaseMessage objects to API format.

    LangGraph: HumanMessage(content="Hello")
    API: {"role": "user", "content": "Hello"}
    """
    api_messages = []

    for msg in messages:
        # Determine role
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            role = "user"  # Default

        # Extract content
        content = msg.content

        # Handle array content (multimodal)
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = [
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ]
            content = " ".join(filter(None, text_parts))

        api_messages.append({
            "role": role,
            "content": content
        })

    return api_messages
```

### API Format → LangGraph Messages

```python
def convert_from_api_format(messages: list[dict]) -> list[BaseMessage]:
    """
    Convert API format to LangGraph BaseMessage objects.

    API: {"role": "user", "content": "Hello"}
    LangGraph: HumanMessage(content="Hello")
    """
    langgraph_messages = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "user":
            langgraph_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langgraph_messages.append(AIMessage(content=content))
        elif role == "system":
            langgraph_messages.append(SystemMessage(content=content))
        else:
            # Default to HumanMessage
            langgraph_messages.append(HumanMessage(content=content))

    return langgraph_messages
```

---

## Error Handling

### Pattern 1: Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential
import anthropic

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_claude_with_retry(messages: list[dict], system_prompt: str) -> str:
    """Call Claude with automatic retry on failure"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )

    return response.content[0].text
```

### Pattern 2: Fallback Provider

```python
def call_llm_with_fallback(messages: list[dict], system_prompt: str) -> str:
    """Try Claude first, fallback to OpenAI on error"""
    try:
        return call_claude(messages, system_prompt)
    except Exception as e:
        print(f"Claude failed: {e}, falling back to OpenAI")
        return call_openai(messages, system_prompt)
```

### Pattern 3: Error Response to User

```python
def safe_chat_node(state: ConversationState) -> dict:
    """Chat node with graceful error handling"""
    api_messages = convert_to_api_format(state["messages"])

    try:
        response_text = call_llm(api_messages, "You are a helpful assistant.")
        return {"messages": [AIMessage(content=response_text)]}

    except anthropic.RateLimitError as e:
        error_msg = "I'm experiencing high demand. Please try again in a moment."
        return {"messages": [AIMessage(content=error_msg)]}

    except anthropic.APIConnectionError as e:
        error_msg = "I'm having trouble connecting. Please check your internet connection."
        return {"messages": [AIMessage(content=error_msg)]}

    except Exception as e:
        print(f"Unexpected error in chat node: {e}")
        error_msg = f"I encountered an error: {str(e)}"
        return {"messages": [AIMessage(content=error_msg)]}
```

---

## Environment Variable Loading (CRITICAL)

### The Authentication Error

**Symptom:**
```python
TypeError: "Could not resolve authentication method. Expected either api_key or auth_token to be set. Or for one of the `X-Api-Key` or `Authorization` headers to be explicitly omitted"
```

**Root Cause:** The `.env` file exists but environment variables are not loaded into the Python process.

**Why This Happens:**
- `.env` files are NOT automatically loaded by Python
- Even if you have a `.env` file with `ANTHROPIC_API_KEY=...`, `os.getenv("ANTHROPIC_API_KEY")` returns `None`
- `ChatAnthropic` and other LangChain integrations require the env var to be available in the process
- This is especially common in async browser automation and LangGraph contexts

### Solution 1: Explicit dotenv Loading (Recommended)

**Install:**
```bash
pip install python-dotenv
# or
uv add python-dotenv
```

**Code Pattern:**
```python
from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic

# CRITICAL: Load .env file BEFORE initializing any clients
load_dotenv()

# Now environment variables are available
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment")

# Initialize ChatAnthropic (will use env var automatically)
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    temperature=0,
    api_key=api_key  # Explicit is better than implicit
)
```

**When to call `load_dotenv()`:**
- ✅ At the top of your main module (before any imports that use env vars)
- ✅ In async context managers for browser automation
- ✅ Before creating LangGraph agents that use LLM providers
- ❌ NOT in every function (call once at startup)

### Solution 2: Explicit API Key Passing

```python
import os
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

# Pass API key explicitly (safer)
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0
)
```

### Solution 3: Pydantic Settings (Production)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    llm_provider: str = "claude"
    claude_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"  # Pydantic automatically loads this

settings = Settings()

# Use settings object
llm = ChatAnthropic(
    model=settings.claude_model,
    api_key=settings.anthropic_api_key
)
```

### Browser Automation Context

**Special Case:** Async browser automation requires dotenv loading BEFORE browser context creation.

```python
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from contextlib import asynccontextmanager

# Load FIRST, before any async operations
load_dotenv()

@asynccontextmanager
async def create_browser_context(headless: bool = True):
    """Browser context with proper env var loading"""
    from playwright.async_api import async_playwright

    playwright = None
    browser = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        yield browser
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def create_scraper_agent(browser):
    """Create agent - env vars already loaded"""
    from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
    from langgraph.prebuilt import create_react_agent

    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    tools = toolkit.get_tools()

    # ChatAnthropic will find ANTHROPIC_API_KEY from environment
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0
    )

    agent = create_react_agent(model=llm, tools=tools)
    return agent
```

### Verification Steps

**1. Check if dotenv is needed:**
```python
import os
print(os.getenv("ANTHROPIC_API_KEY"))  # None = need load_dotenv()
```

**2. After loading dotenv:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("ANTHROPIC_API_KEY"))  # Should print key
```

**3. Verify ChatAnthropic works:**
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5")
result = llm.invoke("Hello")
print(result.content)  # Should print response
```

### Common Mistakes

❌ **Mistake 1: Assuming .env auto-loads**
```python
# This FAILS - .env file exists but not loaded
llm = ChatAnthropic(model="claude-sonnet-4-5")
```

❌ **Mistake 2: Loading dotenv in the wrong place**
```python
async def create_agent():
    load_dotenv()  # TOO LATE - load at module level
    llm = ChatAnthropic(...)
```

❌ **Mistake 3: Not checking if env var is set**
```python
api_key = os.getenv("ANTHROPIC_API_KEY")  # Could be None!
llm = ChatAnthropic(api_key=api_key)  # TypeError
```

✅ **Correct Pattern:**
```python
from dotenv import load_dotenv
import os

# Load at module level (top of file)
load_dotenv()

# Validate
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

# Use
llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key)
```

---

## Best Practices

### 1. Environment Variable Management

```python
# .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LLM_PROVIDER=claude
CLAUDE_MODEL=claude-sonnet-4-5
OPENAI_MODEL=gpt-4o-mini
```

```python
# config.py
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env BEFORE Settings initialization
load_dotenv()

class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    llm_provider: str = "claude"
    claude_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Client Initialization

```python
# Initialize clients once (not per-request)
claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
openai_client = openai.OpenAI(api_key=settings.openai_api_key)

def call_claude(messages: list[dict], system_prompt: str) -> str:
    # Reuse existing client
    response = claude_client.messages.create(...)
    return response.content[0].text
```

### 3. Cost Tracking

```python
from collections import defaultdict

# Track usage
usage_stats = defaultdict(lambda: {"requests": 0, "tokens": 0})

def call_claude_tracked(messages: list[dict], system_prompt: str) -> str:
    """Call Claude with usage tracking"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )

    # Track usage
    usage_stats["claude"]["requests"] += 1
    usage_stats["claude"]["tokens"] += response.usage.input_tokens + response.usage.output_tokens

    return response.content[0].text
```

### 4. Prompt Management

```python
# prompts.py
SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "resume_agent": "You are a career advisor helping with resumes and job applications.",
    "code_reviewer": "You are an expert code reviewer providing constructive feedback."
}

def call_llm(messages: list[dict], prompt_key: str = "default") -> str:
    """Call LLM with named system prompt"""
    system_prompt = SYSTEM_PROMPTS[prompt_key]
    # ... rest of implementation
```

### 5. Model Selection

```python
# Model costs and capabilities
MODELS = {
    "claude-sonnet-4-5": {
        "provider": "anthropic",
        "input_cost": 3.00,  # per million tokens
        "output_cost": 15.00,
        "context_window": 200000,
        "best_for": ["reasoning", "code", "long-context"]
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "input_cost": 0.15,
        "output_cost": 0.60,
        "context_window": 128000,
        "best_for": ["speed", "cost", "simple-tasks"]
    }
}

def select_model(task_type: str) -> str:
    """Select optimal model for task"""
    if task_type in ["complex-reasoning", "code-generation"]:
        return "claude-sonnet-4-5"
    else:
        return "gpt-4o-mini"
```

---

## API Comparison Table

| Feature | Anthropic Claude | OpenAI GPT |
|---------|-----------------|------------|
| **System Prompt** | Separate `system` parameter | First message in `messages` array |
| **max_tokens** | Required | Optional |
| **Response Access** | `response.content[0].text` | `response.choices[0].message.content` |
| **Streaming** | `client.messages.stream()` | `stream=True` parameter |
| **Tool Calling** | `tools` parameter | `tools` parameter |
| **Image Support** | Content blocks | Content array |
| **Context Window** | Up to 200K tokens | Up to 128K tokens |

---

## Quick Reference

### Anthropic
```python
client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=2048,  # Required
    system="You are...",  # Separate parameter
    messages=[{"role": "user", "content": "..."}]
)
# Access: response.content[0].text
```

### OpenAI
```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are..."},  # In array
        {"role": "user", "content": "..."}
    ]
)
# Access: response.choices[0].message.content
```

---

## See Also

- **StateGraph Guide**: Message handling in nodes
- **Error Handling**: Robust error patterns
- **Production Deployment**: Environment configuration

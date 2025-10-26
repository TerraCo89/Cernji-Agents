# LangGraph Research Examples

This directory contains comprehensive research and working examples for LangGraph development, including LLM provider integration and LangGraph dev server deployment.

## Contents

### LangGraph Dev Server Research (NEW!)

#### 1. **langgraph_dev_server_guide.md**
Complete guide for serving LangGraph agents with `langgraph dev`:
- langgraph.json configuration structure
- Graph builder function patterns
- REST API endpoint documentation with curl examples
- Thread ID and config patterns
- Agent Chat UI integration
- Troubleshooting and best practices

**Read this first** for complete LangGraph dev server understanding.

#### 2. **langgraph_dev_quickstart.md**
Quick reference card for common tasks:
- Minimal 3-file setup
- Essential curl commands
- Common issues and fixes
- Python SDK examples

**Use this** for quick lookups during development.

#### 3. **test_langgraph_api.sh** (Linux/macOS)
Complete API test suite:
- Tests threads, runs, streaming, and state
- Validates server health and memory persistence
- Colorized output

**Run this** to verify your LangGraph dev server setup.

#### 4. **test_langgraph_api.ps1** (Windows)
PowerShell version of the test suite with same coverage.

---

### LLM Provider Integration Research

#### 5. **llm_provider_integration_patterns.md**
Complete guide to integration patterns including:
- Solution description and approaches
- Key differences between Anthropic and OpenAI APIs
- Message format conversion for LangGraph SDK
- Environment configuration
- Multi-provider switching strategies

**Read this first** for conceptual understanding.

#### 6. **working_code_examples.py**
Fully functional Python code demonstrating:
- Multi-provider LLM abstraction (`call_llm()`)
- Direct SDK calls (`call_anthropic()`, `call_openai()`)
- Message format conversion utilities
- LangGraph node functions
- Streaming support
- Configuration management

**Run this** to see examples in action:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxxxx
export OPENAI_API_KEY=sk-xxxxx
python working_code_examples.py
```

#### 7. **provider_comparison.md**
Side-by-side comparison of Anthropic vs OpenAI:
- Quick reference table
- API differences in detail
- System prompt handling
- Response format structures
- Streaming approaches
- Tool calling patterns
- Error handling
- Cost and performance characteristics

**Use this** as a quick reference guide.

## Quick Start

### Installation
```bash
pip install anthropic openai langchain-core
```

### Environment Setup
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
LLM_PROVIDER=claude  # or openai
```

### Basic Usage

#### Call Claude
```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are helpful.",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content[0].text)
```

#### Call OpenAI
```python
import openai

client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

#### Unified Interface
```python
def call_llm(messages, system, provider="claude"):
    if provider == "openai":
        client = openai.OpenAI()
        api_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )
        return response.choices[0].message.content
    else:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=system,
            messages=messages
        )
        return response.content[0].text

# Use in LangGraph node
def chat_node(state):
    response = call_llm(
        messages=state["messages"],
        system="You are helpful.",
        provider=state.get("provider", "claude")
    )
    return {"messages": [{"role": "assistant", "content": response}]}
```

## Key Findings

### 1. Direct SDK Integration is Preferred
LangGraph nodes are plain Python functions. Direct SDK usage provides:
- Full control over API parameters
- No LangChain dependencies
- Clearer error handling
- Easier debugging

### 2. Critical API Differences

| Feature | Anthropic | OpenAI |
|---------|-----------|--------|
| System prompt | Separate parameter | In messages array |
| Response path | `response.content[0].text` | `response.choices[0].message.content` |
| Required params | `max_tokens` required | `max_tokens` optional |

### 3. Message Format Conversion
When using LangGraph SDK (Agent Chat UI), convert LangChain message objects:
```python
# LangGraph SDK format
HumanMessage(content="Hello")

# API format
{"role": "user", "content": "Hello"}
```

### 4. Multi-Provider Switching Strategies

**Strategy 1: Environment Variable** (Deployment-level)
```bash
export LLM_PROVIDER=claude
```

**Strategy 2: State-Based** (Request-level)
```python
app.invoke({
    "messages": [...],
    "provider": "openai"  # Switch per request
})
```

**Strategy 3: Configuration Object** (Application-level)
```python
config = Settings(llm_provider="claude")
```

## Project Integration

### Current Implementation
The `apps/resume-agent-langgraph/` project uses:
- **Provider abstraction**: `src/resume_agent/llm/providers.py`
- **Message conversion**: `src/resume_agent/llm/messages.py`
- **Configuration**: `src/resume_agent/config.py` (Pydantic)
- **Node examples**: `src/resume_agent/nodes/conversation.py`

### File Locations
```
apps/resume-agent-langgraph/
├── src/resume_agent/
│   ├── llm/
│   │   ├── providers.py          # Multi-provider abstraction
│   │   └── messages.py           # Message format conversion
│   ├── config.py                 # Environment configuration
│   └── nodes/
│       └── conversation.py       # Example node usage
```

## Common Patterns

### Pattern 1: Simple Node
```python
def chat_node(state):
    """Call LLM and return response."""
    response = call_llm(
        messages=state["messages"],
        system_prompt="You are helpful.",
        provider="claude"
    )
    return {"messages": [{"role": "assistant", "content": response}]}
```

### Pattern 2: Provider Switching
```python
def chat_node(state):
    """Switch provider based on state."""
    provider = state.get("provider", "claude")
    response = call_llm(
        messages=state["messages"],
        system_prompt="You are helpful.",
        provider=provider
    )
    return {"messages": [{"role": "assistant", "content": response}]}
```

### Pattern 3: With Message Conversion
```python
def chat_node(state):
    """Convert LangGraph SDK messages before calling API."""
    api_messages = convert_langgraph_messages_to_api_format(
        state["messages"]
    )
    response = call_llm(
        messages=api_messages,
        system_prompt="You are helpful.",
        provider="claude"
    )
    return {"messages": [{"role": "assistant", "content": response}]}
```

## Testing

### Test Both Providers
```python
# Test Claude
result = app.invoke({
    "messages": [{"role": "user", "content": "Hello"}],
    "provider": "claude"
})

# Test OpenAI
result = app.invoke({
    "messages": [{"role": "user", "content": "Hello"}],
    "provider": "openai"
})
```

### Test Message Conversion
```python
from langchain_core.messages import HumanMessage

msgs = [HumanMessage(content="Hello")]
api_msgs = convert_langgraph_messages_to_api_format(msgs)
assert api_msgs == [{"role": "user", "content": "Hello"}]
```

## Resources

### Official Documentation
- **Anthropic**: https://docs.anthropic.com/en/api/messages
- **OpenAI**: https://platform.openai.com/docs/guides/text-generation
- **LangGraph**: https://langchain-ai.github.io/langgraph/

### SDK Repositories
- **Anthropic SDK**: https://github.com/anthropics/anthropic-sdk-python
- **OpenAI SDK**: https://github.com/openai/openai-python
- **LangGraph**: https://github.com/langchain-ai/langgraph

### Related Research
- Message format conversion patterns
- Multi-provider orchestration
- LangGraph without LangChain examples
- Token usage and cost optimization

## Next Steps

1. **Review working_code_examples.py** - Run examples with your API keys
2. **Read provider_comparison.md** - Understand API differences
3. **Study llm_provider_integration_patterns.md** - Learn integration patterns
4. **Check current implementation** - See how it's used in the project
5. **Test with both providers** - Verify switching works correctly

## Questions & Answers

### Q: Can I use LangGraph without LangChain?
**A:** Yes! LangGraph nodes are plain Python functions. Direct SDK usage is fully supported.

### Q: Which provider should I use?
**A:**
- **Claude Sonnet**: Best quality, large context (200K)
- **GPT-4o-mini**: Fastest, cheapest
- **Multi-provider**: Best of both worlds

### Q: How do I handle message format conversion?
**A:** Use the `convert_langgraph_messages_to_api_format()` utility when working with LangGraph SDK (Agent Chat UI).

### Q: What about streaming?
**A:** Both providers support streaming:
- Claude: `client.messages.stream()`
- OpenAI: `stream=True` parameter

### Q: How do I switch providers at runtime?
**A:** Pass provider in state, use environment variables, or configuration objects.

## License

This research is part of the Cernji-Agents project.

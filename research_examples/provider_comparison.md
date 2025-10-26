# Anthropic vs OpenAI API Comparison for LangGraph Integration

## Quick Reference Table

| Feature | Anthropic (Claude) | OpenAI (GPT) |
|---------|-------------------|--------------|
| **SDK Package** | `anthropic` | `openai` |
| **Version** | ^0.39.0 | ^1.0.0 |
| **Client Init** | `anthropic.Anthropic()` | `openai.OpenAI()` |
| **API Key Env Var** | `ANTHROPIC_API_KEY` | `OPENAI_API_KEY` |
| **Main Method** | `client.messages.create()` | `client.chat.completions.create()` |
| **System Prompt** | Separate `system` parameter | Part of `messages` array |
| **Message Format** | `[{"role": "user", "content": "..."}]` | Same |
| **Response Access** | `response.content[0].text` | `response.choices[0].message.content` |
| **Streaming** | `client.messages.stream()` | `stream=True` parameter |
| **Default Models** | `claude-sonnet-4-5`, `claude-opus-4` | `gpt-4o`, `gpt-4o-mini` |

## API Differences in Detail

### 1. System Prompt Handling

**Anthropic (Claude)**
```python
client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are a helpful assistant.",  # Separate parameter
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
```

**OpenAI (GPT)**
```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},  # In array
        {"role": "user", "content": "Hello"}
    ]
)
```

**Key Difference**:
- Claude: System prompt is a separate parameter
- OpenAI: System message is first element in messages array

### 2. Response Format

**Anthropic (Claude)**
```python
response = client.messages.create(...)

# Response structure
{
    "id": "msg_xxx",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "Hello! How can I help you?"
        }
    ],
    "model": "claude-sonnet-4-5",
    "stop_reason": "end_turn"
}

# Access text
text = response.content[0].text
```

**OpenAI (GPT)**
```python
response = client.chat.completions.create(...)

# Response structure
{
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "finish_reason": "stop"
        }
    ],
    "model": "gpt-4o-mini"
}

# Access text
text = response.choices[0].message.content
```

**Key Difference**:
- Claude: `response.content[0].text`
- OpenAI: `response.choices[0].message.content`

### 3. Streaming Responses

**Anthropic (Claude)**
```python
# Context manager approach
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are helpful.",
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Or event-based
stream = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)

for event in stream:
    if event.type == "content_block_delta":
        print(event.delta.text, end="", flush=True)
```

**OpenAI (GPT)**
```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**Key Difference**:
- Claude: Dedicated `messages.stream()` method or context manager
- OpenAI: `stream=True` parameter in main method

### 4. Required Parameters

**Anthropic (Claude)**
```python
# Required parameters
client.messages.create(
    model="claude-sonnet-4-5",      # Required
    max_tokens=1024,                # Required
    messages=[...]                  # Required
)

# Optional parameters
system="..."                        # Optional
temperature=0.7                     # Optional (default: 1.0)
top_p=1.0                          # Optional
```

**OpenAI (GPT)**
```python
# Required parameters
client.chat.completions.create(
    model="gpt-4o-mini",            # Required
    messages=[...]                  # Required
)

# Optional parameters
max_tokens=1024                     # Optional (defaults to model max)
temperature=0.7                     # Optional (default: 1.0)
top_p=1.0                          # Optional
```

**Key Difference**:
- Claude: `max_tokens` is required
- OpenAI: `max_tokens` is optional

### 5. Tool Calling (Function Calling)

**Anthropic (Claude)**
```python
tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
)

# Tool use is in response.content
for block in response.content:
    if block.type == "tool_use":
        tool_name = block.name
        tool_input = block.input
```

**OpenAI (GPT)**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o-mini",
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
)

# Tool calls in message
tool_calls = response.choices[0].message.tool_calls
if tool_calls:
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
```

**Key Difference**:
- Claude: Tools defined with `input_schema`, results in `content` blocks
- OpenAI: Tools wrapped in `function` object, results in `tool_calls`

## LangGraph Integration Patterns

### Pattern 1: Unified Interface

```python
def call_llm(messages: list[dict], system: str, provider: str) -> str:
    """Unified LLM interface."""
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
```

### Pattern 2: Provider Classes

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def call(self, messages: list[dict], system: str) -> str:
        pass

class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.client = anthropic.Anthropic()

    def call(self, messages: list[dict], system: str) -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=system,
            messages=messages
        )
        return response.content[0].text

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = openai.OpenAI()

    def call(self, messages: list[dict], system: str) -> str:
        api_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )
        return response.choices[0].message.content

# Usage in LangGraph node
def chat_node(state):
    provider = get_provider(state["provider_name"])
    response = provider.call(state["messages"], "You are helpful.")
    return {"messages": [{"role": "assistant", "content": response}]}
```

### Pattern 3: Configuration-Based

```python
from pydantic import BaseModel

class ProviderConfig(BaseModel):
    provider: Literal["claude", "openai"]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048

def call_with_config(
    messages: list[dict],
    system: str,
    config: ProviderConfig
) -> str:
    if config.provider == "openai":
        client = openai.OpenAI()
        api_messages = [{"role": "system", "content": system}] + messages
        return client.chat.completions.create(
            model=config.model,
            messages=api_messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        ).choices[0].message.content
    else:
        client = anthropic.Anthropic()
        return client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            system=system,
            messages=messages,
            temperature=config.temperature
        ).content[0].text
```

## Error Handling Differences

### Anthropic Errors
```python
from anthropic import APIError, RateLimitError, APIConnectionError

try:
    response = client.messages.create(...)
except RateLimitError:
    # Handle rate limit (429)
    pass
except APIConnectionError:
    # Handle connection error
    pass
except APIError as e:
    # Handle other API errors
    print(f"Status: {e.status_code}")
    print(f"Message: {e.message}")
```

### OpenAI Errors
```python
from openai import APIError, RateLimitError, APIConnectionError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    # Handle rate limit (429)
    pass
except APIConnectionError:
    # Handle connection error
    pass
except APIError as e:
    # Handle other API errors
    print(f"Status: {e.status_code}")
    print(f"Message: {e.message}")
```

**Key Difference**: Error classes are similar but from different packages

## Cost Considerations

### Anthropic Pricing (as of 2024)
- Claude Sonnet 4.5: $3/M input tokens, $15/M output tokens
- Claude Opus 4: $15/M input tokens, $75/M output tokens

### OpenAI Pricing (as of 2024)
- GPT-4o: $5/M input tokens, $15/M output tokens
- GPT-4o-mini: $0.15/M input tokens, $0.60/M output tokens

### Token Counting

**Anthropic**
```python
# Token usage in response
response = client.messages.create(...)
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
```

**OpenAI**
```python
# Token usage in response
response = client.chat.completions.create(...)
print(f"Input tokens: {response.usage.prompt_tokens}")
print(f"Output tokens: {response.usage.completion_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")
```

## Performance Characteristics

### Latency
- **Claude**: Generally 1-3s for first token
- **GPT-4o**: Generally 0.5-2s for first token
- **GPT-4o-mini**: Fastest, 0.3-1s for first token

### Context Windows
- **Claude Sonnet 4.5**: 200K tokens
- **Claude Opus 4**: 200K tokens
- **GPT-4o**: 128K tokens
- **GPT-4o-mini**: 128K tokens

### Rate Limits (Tier 1)
- **Anthropic**: 50 requests/min, 40K tokens/min
- **OpenAI**: 500 requests/min, 30K tokens/min

## Recommendations for LangGraph Projects

### Use Claude When:
- Need large context windows (200K tokens)
- Building complex reasoning tasks
- Want strong refusal training (safety)
- Working with multimodal inputs (vision)

### Use OpenAI When:
- Need faster response times (gpt-4o-mini)
- Building cost-sensitive applications (gpt-4o-mini is cheaper)
- Need function calling with complex schemas
- Want better JSON mode reliability

### Multi-Provider Strategy:
1. **Development**: Use gpt-4o-mini for speed and cost
2. **Production**: Use Claude Sonnet for quality
3. **Fallback**: Implement provider switching for redundancy
4. **Cost Optimization**: Route simple queries to gpt-4o-mini, complex to Claude

## Implementation Checklist

- [ ] Install both SDKs: `pip install anthropic openai`
- [ ] Set API keys in environment
- [ ] Create unified LLM interface
- [ ] Handle system prompt differences
- [ ] Normalize response extraction
- [ ] Implement error handling for both
- [ ] Add provider switching logic
- [ ] Test with both providers
- [ ] Monitor costs and latency
- [ ] Implement fallback mechanism

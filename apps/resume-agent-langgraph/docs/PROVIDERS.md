# LLM Provider Comparison

The Resume Agent supports both Claude and OpenAI as LLM providers. This document compares the two options.

## Quick Comparison

| Feature | OpenAI (gpt-4o-mini) | Claude (claude-sonnet-4-5) |
|---------|----------------------|----------------------------|
| **Cost** | ~$0.15/1M input tokens | ~$3.00/1M input tokens |
| **Speed** | Fast | Very Fast |
| **Quality** | Excellent for general chat | Exceptional reasoning |
| **Best For** | Testing, development | Production, complex tasks |

## Configuration

Switch providers by setting `LLM_PROVIDER` in `.env`:

### OpenAI (Recommended for Testing)

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

Default model: `gpt-4o-mini` (override with `OPENAI_MODEL` env var)

**Pricing (as of 2024):**
- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens
- Roughly **20x cheaper** than Claude for testing

### Claude (Recommended for Production)

```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_key_here
```

Default model: `claude-sonnet-4-5` (override with `CLAUDE_MODEL` env var)

**Pricing (as of 2024):**
- Input: ~$3.00 per 1M tokens
- Output: ~$15.00 per 1M tokens
- Superior reasoning and code understanding

## Testing Both Providers

### Test with OpenAI:
```bash
# Set in .env
LLM_PROVIDER=openai

# Run test
cd apps/resume-agent-langgraph
uv run test_agent.py
```

### Test with Claude:
```bash
# Set in .env
LLM_PROVIDER=claude

# Run test
cd apps/resume-agent-langgraph
uv run test_agent.py
```

## When to Use Each

### Use OpenAI (gpt-4o-mini) for:
- **Development & Testing**: Much cheaper for rapid iteration
- **Simple Conversations**: Good enough for basic chat
- **High Volume**: When cost is a primary concern
- **Learning LangGraph**: Cheaper while building features

### Use Claude (claude-sonnet-4-5) for:
- **Production**: When quality matters most
- **Complex Reasoning**: Job analysis, resume tailoring
- **Code Understanding**: Portfolio search and analysis
- **Professional Output**: Cover letter generation

## Implementation Details

The agent uses a unified interface (`call_llm()`) that handles both providers:

```python
def call_llm(messages: list, system_prompt: str) -> str:
    """Call the configured LLM provider (Claude or OpenAI)."""
    if LLM_PROVIDER == "openai":
        # OpenAI format: system message in messages array
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=api_messages,
            max_tokens=2048
        )
        return response.choices[0].message.content
    else:
        # Claude format: separate system parameter
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
```

## Recommendation

**Start with OpenAI** for development, then **switch to Claude** when you're ready to deploy or need higher quality outputs.

The cost difference is significant:
- 100K test messages with OpenAI: ~$15
- 100K test messages with Claude: ~$300

Once your features are working, evaluate which provider gives better results for your specific use case.

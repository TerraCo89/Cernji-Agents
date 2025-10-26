"""
Working code examples for LLM provider integration in LangGraph.

This module demonstrates three complete patterns:
1. Direct SDK integration without LangChain
2. Multi-provider support with environment configuration
3. Message format conversion for LangGraph SDK compatibility

Usage:
    # Set environment variables
    export ANTHROPIC_API_KEY=sk-ant-xxxxx
    export OPENAI_API_KEY=sk-xxxxx
    export LLM_PROVIDER=claude  # or openai

    # Run examples
    python working_code_examples.py
"""

import os
from typing import TypedDict, Literal, Union, Any
import anthropic
import openai
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


# =============================================================================
# EXAMPLE 1: Multi-Provider LLM Abstraction
# =============================================================================


def call_anthropic(
    messages: list[dict],
    system_prompt: str,
    model: str = "claude-sonnet-4-5",
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> str:
    """
    Call Anthropic's Claude API.

    Args:
        messages: List of message dicts with role/content
        system_prompt: System instruction for the model
        model: Claude model name
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Assistant's response text
    """
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Anthropic uses separate system parameter
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
        temperature=temperature
    )

    # Extract text from response
    return response.content[0].text


def call_openai(
    messages: list[dict],
    system_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> str:
    """
    Call OpenAI's GPT API.

    Args:
        messages: List of message dicts with role/content
        system_prompt: System instruction for the model
        model: OpenAI model name
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Assistant's response text
    """
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # OpenAI includes system message in messages array
    api_messages = [
        {"role": "system", "content": system_prompt}
    ] + messages

    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Extract text from response
    return response.choices[0].message.content


def call_llm(
    messages: list[dict],
    system_prompt: str,
    provider: Literal["claude", "openai"] = "claude",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> str:
    """
    Unified LLM call interface supporting multiple providers.

    Args:
        messages: List of message dicts with role/content
        system_prompt: System instruction for the model
        provider: Which provider to use
        model: Model name (uses defaults if None)
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Assistant's response text

    Example:
        >>> messages = [{"role": "user", "content": "Hello!"}]
        >>> response = call_llm(messages, "You are helpful.", provider="claude")
        >>> print(response)
        "Hello! How can I help you today?"
    """
    if provider == "openai":
        return call_openai(
            messages=messages,
            system_prompt=system_prompt,
            model=model or "gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens
        )
    else:
        return call_anthropic(
            messages=messages,
            system_prompt=system_prompt,
            model=model or "claude-sonnet-4-5",
            temperature=temperature,
            max_tokens=max_tokens
        )


# =============================================================================
# EXAMPLE 2: Message Format Conversion for LangGraph SDK
# =============================================================================


def convert_langgraph_messages_to_api_format(
    messages: list[Union[BaseMessage, dict]]
) -> list[dict]:
    """
    Convert LangGraph SDK message format to LLM API format.

    LangGraph SDK uses LangChain message objects:
    - HumanMessage, AIMessage, SystemMessage objects
    - OR dicts with 'type' field: "human", "ai", "system"

    LLM APIs expect:
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

        >>> msgs = [{"type": "human", "content": "Hello"}]
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
            "content": str(content)
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


# =============================================================================
# EXAMPLE 3: LangGraph Node Functions
# =============================================================================


class ConversationState(TypedDict):
    """State schema for conversation graph."""
    messages: list[dict]
    provider: str
    should_continue: bool


def chat_node(state: ConversationState) -> dict:
    """
    LangGraph node that processes messages with LLM.

    This demonstrates:
    - Extracting state
    - Calling LLM with provider selection
    - Returning partial state update

    Args:
        state: Current conversation state

    Returns:
        Partial state update with assistant message
    """
    provider = state.get("provider", "claude")

    print(f"\n🤖 Calling {provider}...")

    try:
        # Filter system messages (they'll be in system_prompt)
        api_messages = [
            msg for msg in state["messages"]
            if msg["role"] != "system"
        ]

        # Call LLM
        response = call_llm(
            messages=api_messages,
            system_prompt="You are a helpful career assistant.",
            provider=provider
        )

        # Return assistant message (will be appended to state)
        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }]
        }


def chat_node_with_langgraph_sdk(state: ConversationState) -> dict:
    """
    LangGraph node with SDK message format conversion.

    This demonstrates:
    - Converting LangGraph SDK messages to API format
    - Handling both BaseMessage objects and dicts

    Args:
        state: Current conversation state

    Returns:
        Partial state update with assistant message
    """
    provider = state.get("provider", "claude")

    print(f"\n🤖 Calling {provider} (with SDK conversion)...")

    try:
        # Convert LangGraph SDK format to API format
        api_messages = convert_langgraph_messages_to_api_format(
            state["messages"]
        )

        # Filter system messages
        api_messages = [
            msg for msg in api_messages
            if msg["role"] != "system"
        ]

        # Call LLM
        response = call_llm(
            messages=api_messages,
            system_prompt="You are a helpful career assistant.",
            provider=provider
        )

        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }]
        }


# =============================================================================
# EXAMPLE 4: Streaming Support
# =============================================================================


def call_llm_streaming(
    messages: list[dict],
    system_prompt: str,
    provider: Literal["claude", "openai"] = "claude",
    model: str | None = None
):
    """
    Stream LLM responses for real-time updates.

    Args:
        messages: List of message dicts
        system_prompt: System instruction
        provider: Which provider to use
        model: Model name

    Yields:
        Text chunks from the streaming response

    Example:
        >>> messages = [{"role": "user", "content": "Count to 10"}]
        >>> for chunk in call_llm_streaming(messages, "You are helpful."):
        ...     print(chunk, end="", flush=True)
    """
    if provider == "openai":
        client = openai.OpenAI()
        api_messages = [{"role": "system", "content": system_prompt}] + messages

        stream = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=api_messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    else:
        client = anthropic.Anthropic()

        with client.messages.stream(
            model=model or "claude-sonnet-4-5",
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text


# =============================================================================
# EXAMPLE 5: Provider Configuration
# =============================================================================


class LLMConfig:
    """Configuration for LLM providers."""

    def __init__(
        self,
        provider: Literal["claude", "openai"] = "claude",
        claude_model: str = "claude-sonnet-4-5",
        openai_model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.provider = provider
        self.claude_model = claude_model
        self.openai_model = openai_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "claude"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2048"))
        )

    def get_model(self) -> str:
        """Get the model name for current provider."""
        return self.claude_model if self.provider == "claude" else self.openai_model


# =============================================================================
# USAGE EXAMPLES
# =============================================================================


def example_basic_usage():
    """Example 1: Basic LLM call with provider selection."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic LLM Call")
    print("="*60)

    messages = [
        {"role": "user", "content": "What is LangGraph?"}
    ]

    # Call Claude
    print("\n📞 Calling Claude...")
    response = call_llm(
        messages=messages,
        system_prompt="You are a helpful AI assistant.",
        provider="claude"
    )
    print(f"Claude: {response[:100]}...")

    # Call OpenAI
    print("\n📞 Calling OpenAI...")
    response = call_llm(
        messages=messages,
        system_prompt="You are a helpful AI assistant.",
        provider="openai"
    )
    print(f"OpenAI: {response[:100]}...")


def example_message_conversion():
    """Example 2: Message format conversion."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Message Format Conversion")
    print("="*60)

    # LangGraph SDK format (LangChain objects)
    from langchain_core.messages import HumanMessage, AIMessage

    langgraph_messages = [
        HumanMessage(content="Hello!"),
        AIMessage(content="Hi! How can I help?"),
        HumanMessage(content="Tell me about Python.")
    ]

    # Convert to API format
    api_messages = convert_langgraph_messages_to_api_format(langgraph_messages)

    print("\nOriginal (LangGraph SDK):")
    for msg in langgraph_messages:
        print(f"  {type(msg).__name__}: {msg.content}")

    print("\nConverted (API format):")
    for msg in api_messages:
        print(f"  {msg['role']}: {msg['content']}")


def example_streaming():
    """Example 3: Streaming responses."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Streaming Responses")
    print("="*60)

    messages = [
        {"role": "user", "content": "Count from 1 to 5 slowly."}
    ]

    print("\n📡 Streaming from Claude:")
    for chunk in call_llm_streaming(
        messages=messages,
        system_prompt="You are helpful.",
        provider="claude"
    ):
        print(chunk, end="", flush=True)

    print("\n\n📡 Streaming from OpenAI:")
    for chunk in call_llm_streaming(
        messages=messages,
        system_prompt="You are helpful.",
        provider="openai"
    ):
        print(chunk, end="", flush=True)

    print()


def example_config_based():
    """Example 4: Configuration-based provider selection."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Configuration-Based Selection")
    print("="*60)

    # Load config from environment
    config = LLMConfig.from_env()

    print(f"\nLoaded config:")
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.get_model()}")
    print(f"  Temperature: {config.temperature}")

    messages = [
        {"role": "user", "content": "What's 2+2?"}
    ]

    response = call_llm(
        messages=messages,
        system_prompt="You are a math tutor.",
        provider=config.provider,
        model=config.get_model(),
        temperature=config.temperature,
        max_tokens=config.max_tokens
    )

    print(f"\nResponse: {response}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LLM Provider Integration Examples for LangGraph")
    print("="*60)

    # Check for API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    print(f"\n✓ Anthropic API Key: {'Set' if has_anthropic else 'Not set'}")
    print(f"✓ OpenAI API Key: {'Set' if has_openai else 'Not set'}")

    if not (has_anthropic or has_openai):
        print("\n⚠️  No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        print("Example:")
        print("  export ANTHROPIC_API_KEY=sk-ant-xxxxx")
        print("  export OPENAI_API_KEY=sk-xxxxx")
        exit(1)

    # Run examples
    # Uncomment the examples you want to run

    # example_basic_usage()
    example_message_conversion()
    # example_streaming()
    # example_config_based()

    print("\n" + "="*60)
    print("✅ Examples complete!")
    print("="*60)

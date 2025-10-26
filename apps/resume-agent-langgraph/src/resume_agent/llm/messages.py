"""Message format conversion utilities for LangGraph SDK compatibility."""

from typing import Any, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def convert_langgraph_messages_to_api_format(messages: list[Union[BaseMessage, dict]]) -> list[dict]:
    """
    Convert LangGraph SDK message format to LLM API format.

    LangGraph SDK uses LangChain message objects (BaseMessage subclasses):
    - HumanMessage, AIMessage, SystemMessage objects
    - OR dicts with 'type' field: "human", "ai", "system"
    - content: string or array of content blocks

    LLM APIs (Claude/OpenAI) expect:
    - role: "user", "assistant", "system"
    - content: string

    Args:
        messages: List of messages in LangGraph SDK format (BaseMessage objects or dicts)

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
            role = msg.get("role") or _convert_type_to_role(msg.get("type", "human"))
            content = msg.get("content", "")
        else:
            # Skip unknown message types
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
    """
    Convert LangChain BaseMessage object to API role.

    Args:
        msg: BaseMessage object (HumanMessage, AIMessage, etc.)

    Returns:
        API role string
    """
    if isinstance(msg, HumanMessage):
        return "user"
    elif isinstance(msg, AIMessage):
        return "assistant"
    elif isinstance(msg, SystemMessage):
        return "system"
    else:
        # Default to user for unknown types
        return "user"


def _convert_type_to_role(msg_type: str) -> str:
    """
    Convert LangGraph SDK message types to API roles.

    Args:
        msg_type: Message type from LangGraph SDK

    Returns:
        API role string
    """
    mapping = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "assistant",  # Tool messages treated as assistant messages
    }
    return mapping.get(msg_type, "user")


def _extract_text_from_content_blocks(content_blocks: list[Any]) -> str:
    """
    Extract text from content block array.

    Content blocks can include text, images, files, etc.
    This extracts only the text portions.

    Args:
        content_blocks: List of content blocks

    Returns:
        Concatenated text content
    """
    text_parts = []

    for block in content_blocks:
        if isinstance(block, dict):
            # Handle {"type": "text", "text": "..."} format
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            # Handle other text-like blocks
            elif "text" in block:
                text_parts.append(block["text"])
        elif isinstance(block, str):
            # Handle plain string blocks
            text_parts.append(block)

    return " ".join(filter(None, text_parts))

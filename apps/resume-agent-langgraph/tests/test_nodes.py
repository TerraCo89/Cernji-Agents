"""Unit tests for conversation nodes."""

import pytest
from src.resume_agent.nodes.conversation import chat_node, get_user_input_node
from src.resume_agent.state import ConversationState


def test_chat_node_basic():
    """Test chat node with simple message and verify response has messages list."""
    # Setup initial state with a user message
    state: ConversationState = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "should_continue": True
    }

    # Execute chat node
    result = chat_node(state)

    # Verify result structure
    assert "messages" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0

    # Verify message format
    message = result["messages"][0]
    assert "role" in message
    assert "content" in message
    assert message["role"] == "assistant"
    assert isinstance(message["content"], str)
    assert len(message["content"]) > 0


def test_conversation_state_structure():
    """Verify state has required keys."""
    # Create a conversation state
    state: ConversationState = {
        "messages": [],
        "should_continue": True
    }

    # Verify required keys
    assert "messages" in state
    assert "should_continue" in state

    # Verify types
    assert isinstance(state["messages"], list)
    assert isinstance(state["should_continue"], bool)

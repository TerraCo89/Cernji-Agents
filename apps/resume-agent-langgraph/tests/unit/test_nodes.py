"""Unit tests for conversation nodes."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from src.resume_agent.nodes.conversation import chat_node, get_user_input_node
from src.resume_agent.state import ResumeAgentState, create_initial_state


def test_chat_node_basic():
    """Test chat node with simple message and verify response has messages list."""
    # Setup initial state with a user message using LangChain message format
    state: ResumeAgentState = create_initial_state()
    state["messages"] = [
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ]

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


def test_resume_agent_state_structure():
    """Verify state has required keys from ResumeAgentState schema."""
    # Create initial state using helper function
    state = create_initial_state()

    # Verify required keys
    assert "messages" in state
    assert "user_id" in state

    # Verify optional application data keys exist (with None/empty defaults)
    assert "job_url" in state
    assert "job_analysis" in state
    assert "master_resume" in state
    assert "tailored_resume" in state
    assert "cover_letter" in state
    assert "portfolio_examples" in state

    # Verify types
    assert isinstance(state["messages"], list)
    assert isinstance(state["portfolio_examples"], list)
    assert isinstance(state["user_id"], str)

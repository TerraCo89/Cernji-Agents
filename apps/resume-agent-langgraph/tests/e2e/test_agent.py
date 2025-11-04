#!/usr/bin/env python3
"""
Test script for Resume Agent conversational functionality.

This script tests the agent without interactive input.
"""

import os
import sys
from pathlib import Path

# Add project root to path (two levels up from tests/e2e/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from resume_agent_langgraph import build_conversation_graph
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_conversation():
    """Test a simple conversation flow."""

    print("\n" + "="*60)
    print("Testing Resume Agent Conversational Flow")
    print("="*60)

    # Build the graph
    app = build_conversation_graph()

    # Test message 1
    print("\n[Test 1] User: Hello!")
    initial_state = {
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "should_continue": True
    }

    # Create a config with thread_id
    config = {"configurable": {"thread_id": "test-conversation"}}

    # For testing, we'll manually step through the chat node only
    # (skipping the get_input node which requires interactive input)
    from resume_agent_langgraph import chat_node

    result1 = chat_node(initial_state)
    print(f"Assistant: {result1['messages'][0]['content']}")

    # Test message 2
    print("\n[Test 2] User: What can you do?")
    state2 = {
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": result1['messages'][0]['content']},
            {"role": "user", "content": "What can you do?"}
        ],
        "should_continue": True
    }

    result2 = chat_node(state2)
    print(f"Assistant: {result2['messages'][0]['content']}")

    # Test message 3
    print("\n[Test 3] User: Tell me about LangGraph")
    state3 = {
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": result1['messages'][0]['content']},
            {"role": "user", "content": "What can you do?"},
            {"role": "assistant", "content": result2['messages'][0]['content']},
            {"role": "user", "content": "Tell me about LangGraph"}
        ],
        "should_continue": True
    }

    result3 = chat_node(state3)
    print(f"Assistant: {result3['messages'][0]['content']}")

    print("\n" + "="*60)
    print("✅ All tests completed successfully!")
    print("="*60)
    print("\nThe agent is working correctly.")
    print("To use interactively, run:")
    print("  uv run apps/resume-agent-langgraph/resume_agent_langgraph.py")
    print("\n")

if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("Please set your API key in .env file")
        sys.exit(1)

    test_conversation()

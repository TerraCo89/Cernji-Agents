"""Conversation nodes for chat functionality."""

from ..state import ConversationState
from ..llm import call_llm, get_provider_info
from ..prompts import CONVERSATION_SYSTEM


def chat_node(state: ConversationState) -> dict:
    """
    Process user message with LLM and return response.

    Args:
        state: Current conversation state

    Returns:
        Partial state update with assistant message
    """
    provider_name, model_name = get_provider_info()
    print(f"\n🤖 Thinking... ({provider_name}/{model_name})")

    try:
        # Build messages list for API
        api_messages = []
        for msg in state["messages"]:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Call LLM
        assistant_message = call_llm(api_messages, CONVERSATION_SYSTEM)

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


def get_user_input_node(state: ConversationState) -> dict:
    """
    Get input from user via CLI.

    Args:
        state: Current conversation state

    Returns:
        Partial state update with user message and continue flag
    """
    # Display last assistant message
    if state["messages"]:
        last_msg = state["messages"][-1]
        if last_msg["role"] == "assistant":
            print(f"\n🤖 Assistant: {last_msg['content']}")

    # Get user input
    print("\n" + "="*60)
    user_input = input("👤 You (type 'exit' or 'quit' to end): ").strip()

    # Check for exit command
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("\n👋 Goodbye! Thanks for chatting!\n")
        return {
            "should_continue": False,
            "messages": [{
                "role": "user",
                "content": user_input
            }]
        }

    # Return user message
    return {
        "should_continue": True,
        "messages": [{
            "role": "user",
            "content": user_input
        }]
    }

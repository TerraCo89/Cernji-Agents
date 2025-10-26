"""
Basic usage example for the Resume Agent conversation graph.

This example demonstrates how to:
1. Build the conversation graph
2. Initialize the state
3. Invoke the graph with a thread_id for persistence
4. Process the conversation
"""

from src.resume_agent.graphs.conversation import build_conversation_graph


def main():
    """
    Run a simple conversation with the Resume Agent.

    This example shows the basic workflow:
    - Build the conversation graph
    - Initialize with empty state
    - Run conversation loop with checkpointing
    """
    # Step 1: Build the conversation graph
    # This creates a StateGraph with nodes for getting user input and chatting
    # The graph is compiled with a MemorySaver checkpointer for persistence
    print("Building conversation graph...")
    app = build_conversation_graph()

    # Step 2: Initialize the conversation state
    # The state tracks messages and whether to continue the conversation
    initial_state = {
        "messages": [],
        "should_continue": True
    }

    # Step 3: Configure the graph with a thread_id
    # The thread_id enables conversation persistence and resumption
    # Using the same thread_id will resume a previous conversation
    config = {
        "configurable": {
            "thread_id": "example-conversation-001"
        }
    }

    # Step 4: Run the conversation
    # The graph will loop:
    # 1. Get user input
    # 2. Check if should continue
    # 3. Process with LLM if continuing
    # 4. Loop back to get input
    print("\nStarting conversation...")
    print("=" * 60)
    print("Resume Agent - Basic Usage Example")
    print("=" * 60)
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print()

    # Invoke the graph with initial state and config
    # The graph will handle the conversation loop internally
    final_state = app.invoke(initial_state, config=config)

    # Step 5: View final state (optional)
    print("\n" + "=" * 60)
    print("Conversation ended.")
    print(f"Total messages: {len(final_state['messages'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()

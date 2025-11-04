"""
Basic chat example with the Japanese Learning Agent.

This demonstrates how to programmatically invoke the agent and maintain
conversation state across multiple turns.
"""

from japanese_agent.graph import graph
from langchain_core.messages import HumanMessage


def main():
    """Run a basic chat session with the agent."""

    # Create a thread ID for persistent conversation
    thread_id = "example-session-001"

    # Example conversation
    messages = [
        "Hello! I'd like to learn Japanese.",
        "Can you show me my vocabulary statistics?",
        "What flashcards are due for review?",
    ]

    print("=" * 60)
    print("Japanese Learning Agent - Basic Chat Example")
    print("=" * 60)

    for user_message in messages:
        print(f"\n👤 User: {user_message}")

        # Invoke the graph with the user message
        result = graph.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Get the agent's response
        agent_response = result["messages"][-1].content
        print(f"🤖 Agent: {agent_response}")

    print("\n" + "=" * 60)
    print("Conversation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

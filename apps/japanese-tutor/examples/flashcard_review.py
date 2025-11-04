"""
Flashcard review session example.

Demonstrates how to conduct a spaced repetition review session.
"""

from japanese_agent.graph import graph
from langchain_core.messages import HumanMessage


def review_session(num_cards: int = 5, thread_id: str = "review-session"):
    """
    Conduct a flashcard review session.

    Args:
        num_cards: Number of flashcards to review
        thread_id: Conversation thread ID
    """

    print("=" * 60)
    print("Flashcard Review Session")
    print("=" * 60)

    # Start review session
    print(f"\n🎴 Starting review of {num_cards} flashcards...\n")

    message = f"Let's review {num_cards} flashcards."

    result = graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    agent_response = result["messages"][-1].content
    print(f"🤖 Agent: {agent_response}\n")

    # Simulate user reviewing cards
    # In a real application, this would be interactive
    ratings = [3, 2, 3, 1, 3]  # easy, medium, easy, hard, easy

    for i, rating in enumerate(ratings[:num_cards], 1):
        rating_text = ["again", "hard", "medium", "easy"][rating]
        message = f"Card {i}: {rating_text}"

        print(f"👤 User: {message}")

        result = graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        agent_response = result["messages"][-1].content
        print(f"🤖 Agent: {agent_response}\n")

    # Get review statistics
    print("📊 Getting review statistics...")
    message = "What are my review statistics?"

    result = graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    agent_response = result["messages"][-1].content
    print(f"🤖 Agent: {agent_response}\n")

    print("=" * 60)
    print("Review session complete! 🎉")
    print("=" * 60)


if __name__ == "__main__":
    review_session(num_cards=5)

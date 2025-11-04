"""
Screenshot analysis example with the Japanese Learning Agent.

Demonstrates how to analyze a game screenshot and extract vocabulary.
"""

from japanese_agent.graph import graph
from langchain_core.messages import HumanMessage


def analyze_screenshot(image_path: str, thread_id: str = "screenshot-session"):
    """
    Analyze a screenshot and extract Japanese text.

    Args:
        image_path: Path to the screenshot image
        thread_id: Conversation thread ID for state persistence
    """

    print("=" * 60)
    print("Screenshot Analysis Example")
    print("=" * 60)
    print(f"\n📸 Analyzing: {image_path}\n")

    # Create message requesting screenshot analysis
    message = f"Please analyze this screenshot: {image_path}"

    # Invoke the graph
    result = graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    # Display response
    agent_response = result["messages"][-1].content
    print(f"🤖 Agent Response:\n{agent_response}\n")

    # Check if vocabulary was extracted (in state)
    vocabulary = result.get("vocabulary", [])
    if vocabulary:
        print(f"\n📚 Extracted {len(vocabulary)} vocabulary words:")
        for vocab in vocabulary[:5]:  # Show first 5
            print(f"  • {vocab.get('word')} ({vocab.get('reading')}) - {vocab.get('meaning')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Example usage
    # Replace with actual screenshot path
    screenshot_path = "path/to/your/screenshot.png"

    analyze_screenshot(screenshot_path)

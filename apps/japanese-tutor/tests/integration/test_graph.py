"""Integration tests for the Japanese Learning Agent graph."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from japanese_agent.graph import graph
from japanese_agent.state.schemas import create_initial_state


class TestGraphBasics:
    """Test basic graph functionality."""

    def test_graph_compiles(self):
        """Test that the graph compiles without errors."""
        assert graph is not None

    def test_graph_simple_message(self):
        """Test graph with a simple message."""
        result = graph.invoke(
            {"messages": [HumanMessage(content="Hello")]},
            config={"configurable": {"thread_id": "test-1"}}
        )

        # Should have at least 2 messages (user + AI)
        assert len(result["messages"]) >= 2

        # Last message should be from AI
        assert isinstance(result["messages"][-1], AIMessage)

    def test_graph_preserves_state_structure(self):
        """Test that graph returns complete state structure."""
        initial_state = create_initial_state()
        initial_state["messages"] = [HumanMessage(content="Test")]

        result = graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": "test-2"}}
        )

        # Check that key state fields exist
        assert "messages" in result
        assert "vocabulary" in result
        assert "flashcards" in result
        assert "user_id" in result


class TestGraphWithTools:
    """Test graph with tool invocations."""

    def test_vocabulary_statistics_tool(self):
        """Test that vocabulary statistics tool can be called."""
        result = graph.invoke(
            {"messages": [HumanMessage(content="What are my vocabulary statistics?")]},
            config={"configurable": {"thread_id": "test-vocab-stats"}}
        )

        # Check that we got a response
        assert len(result["messages"]) >= 2

        # Response should mention vocabulary or statistics
        response = result["messages"][-1].content.lower()
        # Note: Tool is a stub, so we just check it doesn't error

    def test_flashcard_review_tool(self):
        """Test that flashcard review tool can be called."""
        result = graph.invoke(
            {"messages": [HumanMessage(content="Show me flashcards due for review")]},
            config={"configurable": {"thread_id": "test-flashcards"}}
        )

        # Check that we got a response
        assert len(result["messages"]) >= 2


@pytest.mark.skip(reason="Requires actual screenshot file")
class TestScreenshotAnalysis:
    """Test screenshot analysis workflow (requires actual files)."""

    def test_screenshot_analysis_claude(self):
        """Test Claude Vision screenshot analysis."""
        # This test requires an actual screenshot file
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="Analyze screenshot: test.png")
                ]
            },
            config={"configurable": {"thread_id": "test-screenshot"}}
        )

        assert len(result["messages"]) >= 2

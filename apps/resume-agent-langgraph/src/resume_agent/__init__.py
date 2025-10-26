"""Resume Agent - LangGraph Conversational Agent."""

# Main graph is exported from graph.py
# Legacy modular components are available but not imported by default
# to avoid import errors when only using the main graph

__version__ = "0.3.0"

__all__ = [
    # Main graph is in graph.py and loaded directly by langgraph.json
    # Legacy components can be imported explicitly if needed:
    # from resume_agent.config import get_settings
    # from resume_agent.state import schemas
    # from resume_agent.llm import providers
]

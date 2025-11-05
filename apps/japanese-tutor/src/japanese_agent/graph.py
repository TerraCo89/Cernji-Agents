"""LangGraph Japanese Learning Agent - Main Graph.

A conversational agent for learning Japanese through game screenshots.
Implements OCR, vocabulary tracking, and flashcard review workflows.
"""
from __future__ import annotations

import os
import base64
import tempfile
import atexit
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from dotenv import load_dotenv

# Import state schema
from japanese_agent.state.schemas import JapaneseAgentState

# Import nodes
from japanese_agent.nodes import emit_screenshot_ui

# Import tools
from japanese_agent.tools import (
    # Screenshot analysis
    analyze_screenshot_claude,
    analyze_screenshot_manga_ocr,
    hybrid_screenshot_analysis,

    # Vocabulary management
    search_vocabulary,
    list_vocabulary_by_status,
    update_vocabulary_status,
    get_vocabulary_statistics,

    # Flashcard management
    get_due_flashcards,
    record_flashcard_review,
    create_flashcard,
    get_review_statistics,
)

# Load environment variables
load_dotenv()


# ==============================================================================
# Temporary File Management
# ==============================================================================

# Track temporary files for cleanup
_temp_files: List[str] = []


def cleanup_temp_files():
    """Clean up temporary image files on exit."""
    for file_path in _temp_files:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            # Log but don't fail - temp files will be cleaned by OS eventually
            print(f"Warning: Could not delete temp file {file_path}: {e}")


# Register cleanup handler
atexit.register(cleanup_temp_files)


# ==============================================================================
# Image Preprocessing Helpers
# ==============================================================================

def extract_base64_from_data_url(data_url: str) -> tuple[str, str]:
    """
    Extract base64 data and mime type from a data URL.

    Args:
        data_url: Data URL in format "data:image/jpeg;base64,{base64_data}"

    Returns:
        Tuple of (base64_data, mime_type)

    Raises:
        ValueError: If data URL format is invalid
    """
    if not data_url.startswith("data:"):
        raise ValueError(f"Invalid data URL format: must start with 'data:'")

    try:
        # Split "data:image/jpeg;base64,{data}" into parts
        header, base64_data = data_url.split(",", 1)

        # Extract mime type from header
        # header format: "data:image/jpeg;base64"
        mime_part = header.split(";")[0]  # "data:image/jpeg"
        mime_type = mime_part.split(":", 1)[1]  # "image/jpeg"

        return base64_data, mime_type

    except (ValueError, IndexError) as e:
        raise ValueError(f"Failed to parse data URL: {e}")


def determine_file_extension(mime_type: str) -> str:
    """
    Determine file extension from MIME type.

    Args:
        mime_type: MIME type string (e.g., "image/jpeg")

    Returns:
        File extension with dot (e.g., ".jpg")
    """
    mime_to_ext = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }

    return mime_to_ext.get(mime_type.lower(), ".png")  # Default to .png


def save_image_to_temp_file(base64_data: str, mime_type: str) -> str:
    """
    Save base64-encoded image data to a temporary file.

    Args:
        base64_data: Base64-encoded image data
        mime_type: MIME type of the image

    Returns:
        Absolute path to the created temporary file

    Raises:
        ValueError: If base64 data is invalid
    """
    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_data)

        # Determine file extension
        extension = determine_file_extension(mime_type)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
            prefix="japanese_agent_screenshot_"
        )

        try:
            # Write image bytes
            temp_file.write(image_bytes)
            temp_file.flush()

            # Get absolute path
            temp_path = os.path.abspath(temp_file.name)

            # Track for cleanup
            _temp_files.append(temp_path)

            return temp_path

        finally:
            temp_file.close()

    except Exception as e:
        raise ValueError(f"Failed to save image to temp file: {e}")


# ==============================================================================
# Tool Definitions
# ==============================================================================

# List of tools available to the LLM
tools = [
    # Screenshot Analysis Tools
    analyze_screenshot_claude,
    analyze_screenshot_manga_ocr,
    hybrid_screenshot_analysis,

    # Vocabulary Tools
    search_vocabulary,
    list_vocabulary_by_status,
    update_vocabulary_status,
    get_vocabulary_statistics,

    # Flashcard Tools
    get_due_flashcards,
    record_flashcard_review,
    create_flashcard,
    get_review_statistics,
]


# ==============================================================================
# LLM Configuration
# ==============================================================================

# Initialize the chat model - configured via environment variables
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# Select model based on provider
if LLM_PROVIDER.lower() == "anthropic":
    model_string = f"anthropic:{ANTHROPIC_MODEL}"
else:
    model_string = f"openai:{OPENAI_MODEL}"

llm = init_chat_model(model_string)


# ==============================================================================
# Node Functions
# ==============================================================================

def preprocess_images(state: JapaneseAgentState) -> Dict[str, Any]:
    """
    Extract images from message content and save as temporary files.

    When users attach images in LangGraph Studio, they come as base64-encoded
    content blocks in HumanMessage objects. This node extracts them and saves
    to temp files so screenshot analysis tools can access them via file paths.

    Args:
        state: Current graph state

    Returns:
        State update dict with file path in current_screenshot, or empty dict if no images
    """
    # Get the last message
    if not state.get("messages"):
        return {}

    last_message = state["messages"][-1]

    # Only process HumanMessage (user messages)
    if not isinstance(last_message, HumanMessage):
        return {}

    # Check if content is a list (multimodal format)
    content = last_message.content
    if not isinstance(content, list):
        return {}

    # Look for image content blocks
    for block in content:
        if not isinstance(block, dict):
            continue

        # Handle "image_url" format (LangGraph Studio / OpenAI format)
        if block.get("type") == "image_url":
            try:
                image_url_data = block.get("image_url", {})
                url = image_url_data.get("url", "")

                if url.startswith("data:"):
                    # Extract base64 data from data URL
                    base64_data, mime_type = extract_base64_from_data_url(url)

                    # Save to temp file
                    temp_file_path = save_image_to_temp_file(base64_data, mime_type)

                    # Update state with file path AND add AI message with path
                    return {
                        "current_screenshot": {
                            "file_path": temp_file_path,
                            "processed_at": datetime.now(timezone.utc).isoformat(),
                            "ocr_method": "pending",
                        },
                        "messages": [
                            AIMessage(
                                content=f"I've received the image and saved it for analysis. The file is ready at: {temp_file_path}"
                            )
                        ]
                    }
                # Could also handle http/https URLs here if needed

            except Exception as e:
                # Log error but don't fail the whole graph
                print(f"Error processing image_url block: {e}")
                continue

        # Handle "image" format (direct base64)
        elif block.get("type") == "image":
            try:
                base64_data = block.get("base64", "")
                mime_type = block.get("mime_type", "image/png")

                if base64_data:
                    # Save to temp file
                    temp_file_path = save_image_to_temp_file(base64_data, mime_type)

                    # Update state with file path AND add AI message with path
                    return {
                        "current_screenshot": {
                            "file_path": temp_file_path,
                            "processed_at": datetime.now(timezone.utc).isoformat(),
                            "ocr_method": "pending",
                        },
                        "messages": [
                            AIMessage(
                                content=f"I've received the image and saved it for analysis. The file is ready at: {temp_file_path}"
                            )
                        ]
                    }

            except Exception as e:
                # Log error but don't fail the whole graph
                print(f"Error processing image block: {e}")
                continue

    # No images found, return empty dict (no state update)
    return {}


def chatbot(state: JapaneseAgentState) -> Dict[str, Any]:
    """Main chatbot node that processes messages and generates responses.

    This is the core conversation node that:
    1. Receives user messages from state
    2. Invokes LLM with tools bound
    3. Returns AI response (may include tool calls)

    Args:
        state: Current graph state with full JapaneseAgentState schema

    Returns:
        Dictionary with new messages to add to state
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Invoke LLM with conversation history
    message = llm_with_tools.invoke(state["messages"])

    # Disable parallel tool calling to avoid issues with interrupts
    # (if your LLM supports parallel tool calling, you may want to enable it)
    if hasattr(message, 'tool_calls') and len(message.tool_calls) > 1:
        # For now, only take the first tool call
        message.tool_calls = [message.tool_calls[0]]

    return {"messages": [message]}


def route_after_chatbot(state: JapaneseAgentState) -> str:
    """Route after chatbot based on tool calls.

    If the last message contains tool calls, route to the tool node.
    Otherwise, end the conversation.

    Args:
        state: Current graph state

    Returns:
        Next node name or END
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


# ==============================================================================
# Build Graph
# ==============================================================================

# Initialize graph builder with JapaneseAgentState schema
graph_builder = StateGraph(JapaneseAgentState)

# Add preprocessing node for image extraction
graph_builder.add_node("preprocess_images", preprocess_images)

# Add chatbot node
graph_builder.add_node("chatbot", chatbot)

# Add tool node for all tools
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Add screenshot UI emission node
graph_builder.add_node("emit_screenshot_ui", emit_screenshot_ui)

# Define entry point: START -> preprocess_images -> chatbot
graph_builder.add_edge(START, "preprocess_images")
graph_builder.add_edge("preprocess_images", "chatbot")

# Route from chatbot: either to tools or END
graph_builder.add_conditional_edges(
    "chatbot",
    route_after_chatbot,
    {
        "tools": "tools",
        END: END,
    }
)

# Tools -> emit_screenshot_ui -> chatbot for next turn
graph_builder.add_edge("tools", "emit_screenshot_ui")
graph_builder.add_edge("emit_screenshot_ui", "chatbot")

# Compile the graph
# Note: When running via `langgraph dev`, checkpointing/persistence is handled
# automatically by the server - no need to pass a checkpointer here!
graph = graph_builder.compile()


# ==============================================================================
# Graph Export
# ==============================================================================

# This allows the graph to be loaded by LangGraph server
__all__ = ["graph"]

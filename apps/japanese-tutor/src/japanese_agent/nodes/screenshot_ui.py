"""Screenshot UI Node - Emits screenshot analysis results as UI components."""
from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message

from japanese_agent.state.schemas import JapaneseAgentState


def emit_screenshot_ui(state: JapaneseAgentState) -> Dict[str, Any]:
    """Emit screenshot UI messages after screenshot analysis tools are called.

    Checks if the last tool message contains screenshot analysis results and
    emits a screenshot_card UI component with the OCR results and base64-encoded image.

    Args:
        state: Current graph state

    Returns:
        Empty dict (no state updates, only UI emission)
    """
    messages = state["messages"]

    # Look for the most recent ToolMessage with screenshot analysis results
    for message in reversed(messages):
        if hasattr(message, "type") and message.type == "tool":
            # Check if this is a screenshot analysis tool
            tool_name = getattr(message, "name", "")
            if tool_name in ["analyze_screenshot_claude", "analyze_screenshot_manga_ocr", "hybrid_screenshot_analysis"]:
                try:
                    # Parse tool content (JSON string)
                    tool_result = json.loads(message.content) if isinstance(message.content, str) else message.content

                    # Skip if there was an error
                    if "error" in tool_result:
                        break

                    # Get the associated AI message (the one that requested this analysis)
                    ai_message = None
                    for msg in reversed(messages):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            # Check if this AI message made the screenshot analysis call
                            for tool_call in msg.tool_calls:
                                if tool_call.get("name") == tool_name:
                                    ai_message = msg
                                    break
                            if ai_message:
                                break

                    # If no AI message found, create one
                    if not ai_message:
                        ai_message = AIMessage(
                            id=str(uuid.uuid4()),
                            content="Screenshot analysis complete!"
                        )

                    # Get base64 image data from state if available
                    image_data = ""
                    media_type = "image/png"

                    # Try to get image from current_screenshot in state
                    if "current_screenshot" in state and state["current_screenshot"]:
                        screenshot_info = state["current_screenshot"]
                        if "file_path" in screenshot_info:
                            try:
                                # Read and encode the image file
                                with open(screenshot_info["file_path"], "rb") as f:
                                    image_bytes = f.read()
                                    image_data = base64.b64encode(image_bytes).decode("utf-8")

                                    # Determine media type from file extension
                                    file_ext = Path(screenshot_info["file_path"]).suffix.lower()
                                    media_type_map = {
                                        ".png": "image/png",
                                        ".jpg": "image/jpeg",
                                        ".jpeg": "image/jpeg",
                                        ".webp": "image/webp",
                                    }
                                    media_type = media_type_map.get(file_ext, "image/png")
                            except Exception as e:
                                print(f"Warning: Could not read screenshot file: {e}")

                    # Format extracted text for UI
                    extracted_text_formatted = []
                    if "extracted_text" in tool_result and tool_result["extracted_text"]:
                        for segment in tool_result["extracted_text"]:
                            if isinstance(segment, dict):
                                extracted_text_formatted.append({
                                    "text": segment.get("text", ""),
                                    "reading": segment.get("reading", ""),
                                    "confidence": segment.get("confidence", 1.0),
                                })
                            elif isinstance(segment, str):
                                # Fallback for string-only format
                                extracted_text_formatted.append({
                                    "text": segment,
                                    "reading": "",
                                    "confidence": 1.0,
                                })

                    # Emit screenshot card UI component
                    push_ui_message(
                        "screenshot_card",
                        {
                            "image_data": image_data,
                            "media_type": media_type,
                            "extracted_text": extracted_text_formatted,
                            "translation": tool_result.get("translation", ""),
                            "ocr_method": tool_result.get("ocr_method", "claude"),
                            "processed_at": tool_result.get("processed_at", datetime.now(timezone.utc).isoformat()),
                        },
                        message=ai_message
                    )

                    break  # Only emit for the most recent screenshot analysis

                except Exception as e:
                    print(f"Warning: Could not emit screenshot UI: {e}")
                    break

    return {}

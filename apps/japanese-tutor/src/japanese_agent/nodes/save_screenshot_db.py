"""Save Screenshot to Database Node - Persists screenshot analysis results."""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any

from japanese_agent.state.schemas import JapaneseAgentState
from japanese_agent.database.connection import execute_insert, get_connection


async def save_screenshot_to_db(state: JapaneseAgentState) -> Dict[str, Any]:
    """Save screenshot analysis results to database.

    This node runs after screenshot analysis tools complete and persists:
    - Base64 image data for reliable retrieval
    - OCR extracted text (JSON array)
    - Metadata (confidence, method, timestamps)

    Args:
        state: Current graph state

    Returns:
        State update dict with screenshot_id, or empty dict if nothing to save
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
                        print(f"[INFO] Skipping screenshot save - analysis had errors")
                        break

                    # Get screenshot data from state
                    if "current_screenshot" not in state or not state["current_screenshot"]:
                        print(f"[WARN] No current_screenshot in state to save")
                        break

                    screenshot_info = state["current_screenshot"]

                    # Get required fields
                    base64_data = screenshot_info.get("base64_data")
                    mime_type = screenshot_info.get("mime_type", "image/png")
                    file_path = screenshot_info.get("file_path")  # Optional

                    if not base64_data:
                        print(f"[WARN] No base64_data in screenshot_info, cannot save to database")
                        break

                    # Calculate checksum for duplicate detection
                    checksum = hashlib.sha256(base64_data.encode()).hexdigest()

                    # Extract OCR data
                    extracted_text = tool_result.get("extracted_text", [])
                    extracted_text_json = json.dumps(extracted_text)
                    ocr_method = tool_result.get("ocr_method", "unknown")

                    # Calculate average confidence
                    if extracted_text:
                        confidences = [seg.get("confidence", 1.0) for seg in extracted_text if isinstance(seg, dict)]
                        ocr_confidence = sum(confidences) / len(confidences) if confidences else 0.95
                    else:
                        ocr_confidence = 0.95  # Default

                    # Check if already saved (by checksum)
                    conn = await get_connection()
                    async with conn.execute(
                        "SELECT id FROM screenshots WHERE checksum = ?",
                        (checksum,)
                    ) as cursor:
                        existing = await cursor.fetchone()

                    if existing:
                        screenshot_id = existing["id"]
                        print(f"[INFO] Screenshot already in database (ID: {screenshot_id})")
                    else:
                        # Save to database
                        screenshot_id = await execute_insert(
                            """
                            INSERT INTO screenshots (
                                file_path, base64_data, mime_type, processed_at,
                                ocr_confidence, extracted_text_json, checksum,
                                language_detected, has_furigana
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                file_path,
                                base64_data,
                                mime_type,
                                datetime.now(timezone.utc).isoformat(),
                                ocr_confidence,
                                extracted_text_json,
                                checksum,
                                "ja",  # Japanese
                                any(seg.get("reading") for seg in extracted_text if isinstance(seg, dict))
                            )
                        )

                        print(f"[SUCCESS] Screenshot saved to database (ID: {screenshot_id})")

                    # Update state with database ID
                    return {
                        "current_screenshot": {
                            **screenshot_info,
                            "id": screenshot_id,
                            "screenshot_id": screenshot_id,
                        }
                    }

                except Exception as e:
                    print(f"[ERROR] Failed to save screenshot to database: {e}")
                    import traceback
                    traceback.print_exc()
                    break

    return {}

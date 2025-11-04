"""
Unit tests for image preprocessing functionality.

Tests the image extraction and temporary file handling for LangGraph Studio images.
"""

import pytest
import os
import base64
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

from japanese_agent.graph import (
    extract_base64_from_data_url,
    determine_file_extension,
    save_image_to_temp_file,
    preprocess_images,
    _temp_files,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_image_base64():
    """Create a simple base64-encoded PNG image."""
    from PIL import Image
    import io

    # Create a tiny test image
    img = Image.new('RGB', (10, 10), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()

    return base64.b64encode(image_bytes).decode('utf-8')


@pytest.fixture
def sample_data_url(sample_image_base64):
    """Create a data URL with base64 image."""
    return f"data:image/png;base64,{sample_image_base64}"


@pytest.fixture
def cleanup_temp_files():
    """Fixture to clean up temp files after tests."""
    yield
    # Clean up any temp files created during tests
    for file_path in _temp_files[:]:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            _temp_files.remove(file_path)
        except:
            pass


# ==============================================================================
# Helper Function Tests
# ==============================================================================

class TestExtractBase64FromDataUrl:
    """Tests for extract_base64_from_data_url helper function."""

    def test_extract_png_data_url(self, sample_data_url, sample_image_base64):
        """Test extracting base64 data from PNG data URL."""
        base64_data, mime_type = extract_base64_from_data_url(sample_data_url)

        assert base64_data == sample_image_base64
        assert mime_type == "image/png"

    def test_extract_jpeg_data_url(self):
        """Test extracting base64 data from JPEG data URL."""
        test_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"
        base64_data, mime_type = extract_base64_from_data_url(test_data)

        assert base64_data == "/9j/4AAQSkZJRgABAQAAAQABAAD"
        assert mime_type == "image/jpeg"

    def test_invalid_data_url_no_prefix(self):
        """Test handling of URL without 'data:' prefix."""
        with pytest.raises(ValueError, match="must start with 'data:'"):
            extract_base64_from_data_url("http://example.com/image.png")

    def test_invalid_data_url_malformed(self):
        """Test handling of malformed data URL."""
        with pytest.raises(ValueError, match="Failed to parse data URL"):
            extract_base64_from_data_url("data:image/png")


class TestDetermineFileExtension:
    """Tests for determine_file_extension helper function."""

    def test_png_extension(self):
        """Test PNG mime type returns .png extension."""
        assert determine_file_extension("image/png") == ".png"

    def test_jpeg_extension(self):
        """Test JPEG mime type returns .jpg extension."""
        assert determine_file_extension("image/jpeg") == ".jpg"

    def test_jpg_extension(self):
        """Test JPG mime type returns .jpg extension."""
        assert determine_file_extension("image/jpg") == ".jpg"

    def test_gif_extension(self):
        """Test GIF mime type returns .gif extension."""
        assert determine_file_extension("image/gif") == ".gif"

    def test_webp_extension(self):
        """Test WebP mime type returns .webp extension."""
        assert determine_file_extension("image/webp") == ".webp"

    def test_case_insensitive(self):
        """Test mime type matching is case-insensitive."""
        assert determine_file_extension("IMAGE/PNG") == ".png"
        assert determine_file_extension("Image/Jpeg") == ".jpg"

    def test_unknown_mime_type(self):
        """Test unknown mime type defaults to .png."""
        assert determine_file_extension("image/unknown") == ".png"
        assert determine_file_extension("application/octet-stream") == ".png"


class TestSaveImageToTempFile:
    """Tests for save_image_to_temp_file helper function."""

    def test_save_png_image(self, sample_image_base64, cleanup_temp_files):
        """Test saving PNG image to temp file."""
        file_path = save_image_to_temp_file(sample_image_base64, "image/png")

        # Verify file exists
        assert os.path.exists(file_path)

        # Verify it's an absolute path
        assert os.path.isabs(file_path)

        # Verify extension
        assert file_path.endswith(".png")

        # Verify prefix
        assert "japanese_agent_screenshot_" in os.path.basename(file_path)

        # Verify file is tracked for cleanup
        assert file_path in _temp_files

    def test_save_jpeg_image(self, cleanup_temp_files):
        """Test saving JPEG image to temp file."""
        # Create a simple base64 JPEG (minimal valid JPEG header)
        jpeg_base64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/AKp/2Q=="

        file_path = save_image_to_temp_file(jpeg_base64, "image/jpeg")

        assert os.path.exists(file_path)
        assert file_path.endswith(".jpg")

    def test_invalid_base64_data(self):
        """Test handling of invalid base64 data."""
        with pytest.raises(ValueError, match="Failed to save image"):
            save_image_to_temp_file("not-valid-base64!!!", "image/png")

    def test_file_contains_correct_data(self, sample_image_base64, cleanup_temp_files):
        """Test that saved file contains correct image data."""
        file_path = save_image_to_temp_file(sample_image_base64, "image/png")

        # Read the file and verify it matches original data
        with open(file_path, 'rb') as f:
            saved_data = base64.b64encode(f.read()).decode('utf-8')

        assert saved_data == sample_image_base64


# ==============================================================================
# Preprocessing Node Tests
# ==============================================================================

class TestPreprocessImages:
    """Tests for preprocess_images node function."""

    def test_extract_image_from_image_url_format(self, sample_data_url, cleanup_temp_files):
        """Test extracting image from image_url format message."""
        # Create a HumanMessage with image_url content
        message = HumanMessage(
            content=[
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url}
                }
            ]
        )

        state = {"messages": [message]}

        # Call preprocessing
        result = preprocess_images(state)

        # Verify state update
        assert "current_screenshot" in result
        assert "file_path" in result["current_screenshot"]
        assert os.path.exists(result["current_screenshot"]["file_path"])
        assert result["current_screenshot"]["file_path"].endswith(".png")
        assert "processed_at" in result["current_screenshot"]
        assert result["current_screenshot"]["ocr_method"] == "pending"

        # Verify AIMessage with file path is added
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert result["current_screenshot"]["file_path"] in result["messages"][0].content

    def test_extract_image_from_direct_base64_format(self, sample_image_base64, cleanup_temp_files):
        """Test extracting image from direct base64 format message."""
        # Create a HumanMessage with direct base64 content
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Analyze this screenshot"},
                {
                    "type": "image",
                    "base64": sample_image_base64,
                    "mime_type": "image/png"
                }
            ]
        )

        state = {"messages": [message]}

        # Call preprocessing
        result = preprocess_images(state)

        # Verify state update
        assert "current_screenshot" in result
        assert "file_path" in result["current_screenshot"]
        assert os.path.exists(result["current_screenshot"]["file_path"])

        # Verify AIMessage with file path is added
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert result["current_screenshot"]["file_path"] in result["messages"][0].content

    def test_no_images_returns_empty_dict(self):
        """Test that messages without images return empty dict."""
        message = HumanMessage(content="Hello, how are you?")
        state = {"messages": [message]}

        result = preprocess_images(state)

        assert result == {}

    def test_text_only_content_list_returns_empty_dict(self):
        """Test that content list with only text returns empty dict."""
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"}
            ]
        )
        state = {"messages": [message]}

        result = preprocess_images(state)

        assert result == {}

    def test_ai_message_not_processed(self, sample_data_url):
        """Test that AIMessage is not processed."""
        message = AIMessage(
            content=[
                {"type": "text", "text": "Here's an image"},
                {"type": "image_url", "image_url": {"url": sample_data_url}}
            ]
        )
        state = {"messages": [message]}

        result = preprocess_images(state)

        assert result == {}

    def test_empty_messages_returns_empty_dict(self):
        """Test that empty messages list returns empty dict."""
        state = {"messages": []}

        result = preprocess_images(state)

        assert result == {}

    def test_no_messages_key_returns_empty_dict(self):
        """Test that state without messages key returns empty dict."""
        state = {}

        result = preprocess_images(state)

        assert result == {}

    def test_multiple_images_uses_first_one(self, sample_data_url, cleanup_temp_files):
        """Test that when multiple images exist, first one is used."""
        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url.replace("png", "jpeg")}
                }
            ]
        )
        state = {"messages": [message]}

        result = preprocess_images(state)

        # Should have processed the first image
        assert "current_screenshot" in result
        assert result["current_screenshot"]["file_path"].endswith(".png")

        # Should have AIMessage
        assert "messages" in result
        assert len(result["messages"]) == 1

    def test_invalid_base64_logs_error_and_continues(self, capfd):
        """Test that invalid base64 logs error but doesn't crash."""
        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,INVALID!!!"}
                }
            ]
        )
        state = {"messages": [message]}

        result = preprocess_images(state)

        # Should return empty dict and print error
        assert result == {}

        # Check that error was printed
        captured = capfd.readouterr()
        assert "Error processing image_url block" in captured.out

    def test_http_url_not_processed(self):
        """Test that HTTP URLs are not processed (only data URLs)."""
        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.png"}
                }
            ]
        )
        state = {"messages": [message]}

        result = preprocess_images(state)

        # HTTP URLs are not handled yet
        assert result == {}

    def test_processes_last_message_only(self, sample_data_url, cleanup_temp_files):
        """Test that only the last message is processed."""
        old_message = HumanMessage(content="Old message")
        new_message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url}
                }
            ]
        )
        state = {"messages": [old_message, new_message]}

        result = preprocess_images(state)

        # Should process the new message with image
        assert "current_screenshot" in result
        assert "messages" in result
        assert len(result["messages"]) == 1


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestImagePreprocessingIntegration:
    """Integration tests for complete image preprocessing workflow."""

    def test_full_workflow_with_state_update(self, sample_data_url, cleanup_temp_files):
        """Test complete workflow from message to state update."""
        # Simulate user attaching image in LangGraph Studio
        user_message = HumanMessage(
            content=[
                {"type": "text", "text": "Please analyze this Japanese screenshot"},
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url}
                }
            ]
        )

        initial_state = {
            "messages": [user_message],
            "current_screenshot": None,
            "vocabulary": [],
            "flashcards": [],
        }

        # Run preprocessing
        state_update = preprocess_images(initial_state)

        # Verify complete state update structure
        assert "current_screenshot" in state_update
        screenshot = state_update["current_screenshot"]

        assert "file_path" in screenshot
        assert "processed_at" in screenshot
        assert "ocr_method" in screenshot

        # Verify file was created and is valid
        file_path = screenshot["file_path"]
        assert os.path.exists(file_path)
        assert os.path.isfile(file_path)
        assert os.path.getsize(file_path) > 0

        # Verify file can be opened as image
        from PIL import Image
        img = Image.open(file_path)
        assert img.size == (10, 10)  # Our test image size
        assert img.mode == "RGB"

        # Verify AIMessage was added with file path
        assert "messages" in state_update
        assert len(state_update["messages"]) == 1
        assert isinstance(state_update["messages"][0], AIMessage)
        assert file_path in state_update["messages"][0].content

    def test_workflow_with_mixed_content(self, sample_data_url, cleanup_temp_files):
        """Test workflow with text and image mixed content."""
        message = HumanMessage(
            content=[
                {"type": "text", "text": "I have a question about this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": sample_data_url}
                },
                {"type": "text", "text": "What does the Japanese text say?"}
            ]
        )

        state = {"messages": [message]}
        result = preprocess_images(state)

        # Should successfully extract image despite mixed content
        assert "current_screenshot" in result
        assert os.path.exists(result["current_screenshot"]["file_path"])

        # Verify AIMessage was added
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)

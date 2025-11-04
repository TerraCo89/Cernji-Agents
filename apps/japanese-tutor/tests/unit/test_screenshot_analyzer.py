"""
Unit tests for screenshot analyzer tools.

Tests the Claude Vision API integration and helper functions.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from japanese_agent.tools.screenshot_analyzer import (
    encode_image_to_base64,
    create_vision_prompt,
    parse_claude_response,
    analyze_screenshot_claude,
    preprocess_image_for_ocr,
    get_manga_ocr_model,
    analyze_screenshot_manga_ocr,
    hybrid_screenshot_analysis,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_image_path(tmp_path):
    """Create a temporary test image file."""
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    img_path = tmp_path / "test_screenshot.png"
    img.save(img_path)

    return str(img_path)


@pytest.fixture
def sample_claude_response():
    """Sample Claude Vision API response in JSON format."""
    return {
        "extracted_text": [
            {
                "text": "こんにちは",
                "reading": "konnichiwa",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 100, "height": 30}
            },
            {
                "text": "世界",
                "reading": "sekai",
                "confidence": 0.92,
                "position": {"x": 10, "y": 60, "width": 80, "height": 30}
            }
        ],
        "translation": "Hello, world",
        "context": "A greeting message appears on the screen",
        "vocabulary": [
            {
                "word": "こんにちは",
                "reading": "konnichiwa",
                "meaning": "hello, good afternoon",
                "part_of_speech": "interjection",
                "jlpt_level": "N5"
            },
            {
                "word": "世界",
                "reading": "sekai",
                "meaning": "world",
                "part_of_speech": "noun",
                "jlpt_level": "N5"
            }
        ]
    }


# ==============================================================================
# Helper Function Tests
# ==============================================================================

class TestEncodeImageToBase64:
    """Tests for encode_image_to_base64 helper function."""

    def test_encode_png_image(self, sample_image_path):
        """Test encoding a PNG image to base64."""
        base64_str, media_type = encode_image_to_base64(sample_image_path)

        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        assert media_type == "image/png"

    def test_encode_jpeg_image(self, tmp_path):
        """Test encoding a JPEG image to base64."""
        from PIL import Image

        # Create JPEG test image
        img = Image.new('RGB', (100, 100), color='blue')
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        base64_str, media_type = encode_image_to_base64(str(img_path))

        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        assert media_type == "image/jpeg"

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64("/nonexistent/image.png")

    def test_unsupported_format(self, tmp_path):
        """Test handling of unsupported image format."""
        # Create a file with unsupported extension
        unsupported_file = tmp_path / "test.bmp"
        unsupported_file.write_text("fake image data")

        with pytest.raises(ValueError, match="Unsupported image format"):
            encode_image_to_base64(str(unsupported_file))


class TestCreateVisionPrompt:
    """Tests for create_vision_prompt helper function."""

    def test_prompt_contains_json_structure(self):
        """Test that prompt contains expected JSON structure."""
        prompt = create_vision_prompt()

        assert "extracted_text" in prompt
        assert "translation" in prompt
        assert "context" in prompt
        assert "vocabulary" in prompt
        assert "confidence" in prompt

    def test_prompt_contains_guidelines(self):
        """Test that prompt contains analysis guidelines."""
        prompt = create_vision_prompt()

        assert "hiragana" in prompt or "readings" in prompt
        assert "JLPT" in prompt
        assert "JSON" in prompt


class TestParseClaudeResponse:
    """Tests for parse_claude_response helper function."""

    def test_parse_json_response(self, sample_claude_response):
        """Test parsing a valid JSON response."""
        json_str = json.dumps(sample_claude_response)
        result = parse_claude_response(json_str, "/test/image.png")

        assert result["file_path"] == "/test/image.png"
        assert "processed_at" in result
        assert result["ocr_method"] == "claude"
        assert len(result["extracted_text"]) == 2
        assert result["translation"] == "Hello, world"
        assert len(result["vocabulary"]) == 2

    def test_parse_json_in_markdown_block(self, sample_claude_response):
        """Test parsing JSON wrapped in markdown code block."""
        json_str = f"```json\n{json.dumps(sample_claude_response)}\n```"
        result = parse_claude_response(json_str, "/test/image.png")

        assert result["ocr_method"] == "claude"
        assert len(result["extracted_text"]) == 2

    def test_parse_invalid_json(self):
        """Test handling of invalid JSON response."""
        invalid_json = "This is not JSON"
        result = parse_claude_response(invalid_json, "/test/image.png")

        assert "error" in result
        assert "Failed to parse" in result["error"]
        assert result["ocr_method"] == "claude"
        assert result["extracted_text"] == []

    def test_parse_empty_fields(self):
        """Test parsing response with missing optional fields."""
        minimal_response = {"extracted_text": [], "translation": "Test"}
        json_str = json.dumps(minimal_response)
        result = parse_claude_response(json_str, "/test/image.png")

        assert result["extracted_text"] == []
        assert result["translation"] == "Test"
        assert result["context"] == ""
        assert result.get("vocabulary", []) == []


# ==============================================================================
# Tool Integration Tests
# ==============================================================================

class TestAnalyzeScreenshotClaude:
    """Tests for analyze_screenshot_claude tool function."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"})
    @patch('japanese_agent.tools.screenshot_analyzer.Anthropic')
    def test_successful_analysis(self, mock_anthropic_class, sample_image_path, sample_claude_response):
        """Test successful screenshot analysis with mocked API."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock the API response
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = json.dumps(sample_claude_response)
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        # Call the function
        result = analyze_screenshot_claude.func(sample_image_path)

        # Assertions
        assert "error" not in result
        assert result["ocr_method"] == "claude"
        assert len(result["extracted_text"]) == 2
        assert result["translation"] == "Hello, world"
        assert len(result["vocabulary"]) == 2

        # Verify API was called
        mock_client.messages.create.assert_called_once()

    def test_missing_api_key(self, sample_image_path):
        """Test handling of missing ANTHROPIC_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            result = analyze_screenshot_claude.func(sample_image_path)

            assert "error" in result
            assert "ANTHROPIC_API_KEY" in result["error"]
            assert result["ocr_method"] == "claude"

    def test_image_not_found(self):
        """Test handling of non-existent image file."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = analyze_screenshot_claude.func("/nonexistent/image.png")

            assert "error" in result
            assert "not found" in result["error"].lower()
            assert result["ocr_method"] == "claude"

    def test_unsupported_image_format(self, tmp_path):
        """Test handling of unsupported image format."""
        unsupported_file = tmp_path / "test.bmp"
        unsupported_file.write_text("fake data")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = analyze_screenshot_claude.func(str(unsupported_file))

            assert "error" in result
            assert "Unsupported" in result["error"]

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"})
    @patch('japanese_agent.tools.screenshot_analyzer.Anthropic')
    def test_api_exception_handling(self, mock_anthropic_class, sample_image_path):
        """Test handling of API exceptions."""
        # Mock the client to raise an exception
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        result = analyze_screenshot_claude.func(sample_image_path)

        assert "error" in result
        assert "Unexpected error" in result["error"]
        assert result["ocr_method"] == "claude"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "claude-3-5-sonnet-20241022"})
    @patch('japanese_agent.tools.screenshot_analyzer.Anthropic')
    def test_custom_model_from_env(self, mock_anthropic_class, sample_image_path, sample_claude_response):
        """Test that custom model from environment is used."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = json.dumps(sample_claude_response)
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        result = analyze_screenshot_claude.func(sample_image_path)

        # Verify the model parameter in the API call
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-5-sonnet-20241022"


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"})
    @patch('japanese_agent.tools.screenshot_analyzer.Anthropic')
    def test_full_workflow(self, mock_anthropic_class, sample_image_path):
        """Test the complete workflow from image to structured result."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Create realistic response
        realistic_response = {
            "extracted_text": [
                {
                    "text": "始まり",
                    "reading": "hajimari",
                    "confidence": 0.93,
                    "position": {"x": 50, "y": 100, "width": 120, "height": 40}
                }
            ],
            "translation": "Beginning",
            "context": "Game title screen showing the start menu",
            "vocabulary": [
                {
                    "word": "始まり",
                    "reading": "hajimari",
                    "meaning": "beginning, start",
                    "part_of_speech": "noun",
                    "jlpt_level": "N3"
                }
            ]
        }

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = json.dumps(realistic_response)
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        # Execute
        result = analyze_screenshot_claude.func(sample_image_path)

        # Validate structure
        assert result["file_path"] == sample_image_path
        assert result["ocr_method"] == "claude"
        assert "processed_at" in result
        assert "error" not in result

        # Validate data
        assert len(result["extracted_text"]) == 1
        assert result["extracted_text"][0]["text"] == "始まり"
        assert result["extracted_text"][0]["confidence"] == 0.93

        assert result["translation"] == "Beginning"
        assert "start menu" in result["context"]

        assert len(result["vocabulary"]) == 1
        assert result["vocabulary"][0]["word"] == "始まり"
        assert result["vocabulary"][0]["jlpt_level"] == "N3"


# ==============================================================================
# manga-ocr Integration Tests
# ==============================================================================

class TestPreprocessImageForOcr:
    """Tests for preprocess_image_for_ocr helper function."""

    def test_preprocess_valid_image(self, sample_image_path):
        """Test preprocessing a valid image."""
        result = preprocess_image_for_ocr(sample_image_path)

        # Should return a PIL Image
        from PIL import Image
        assert isinstance(result, Image.Image)

        # Image should be grayscale (mode 'L')
        assert result.mode == "L"

        # Image should be upscaled 2x
        original = Image.open(sample_image_path)
        assert result.size[0] == original.size[0] * 2
        assert result.size[1] == original.size[1] * 2

    def test_preprocess_color_image(self, tmp_path):
        """Test preprocessing a color image."""
        from PIL import Image

        # Create a color test image
        img = Image.new('RGB', (50, 50), color=(255, 0, 0))
        img_path = tmp_path / "color_test.png"
        img.save(img_path)

        result = preprocess_image_for_ocr(str(img_path))

        # Should convert to grayscale
        assert result.mode == "L"
        assert result.size == (100, 100)  # 2x upscaled

    def test_preprocess_grayscale_image(self, tmp_path):
        """Test preprocessing an already grayscale image."""
        from PIL import Image

        # Create a grayscale test image
        img = Image.new('L', (50, 50), color=128)
        img_path = tmp_path / "gray_test.png"
        img.save(img_path)

        result = preprocess_image_for_ocr(str(img_path))

        assert result.mode == "L"
        assert result.size == (100, 100)

    def test_preprocess_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            preprocess_image_for_ocr("/nonexistent/image.png")

    def test_preprocess_invalid_file(self, tmp_path):
        """Test handling of invalid image file."""
        invalid_file = tmp_path / "invalid.png"
        invalid_file.write_text("Not an image")

        with pytest.raises(ValueError, match="Failed to preprocess image"):
            preprocess_image_for_ocr(str(invalid_file))


class TestGetMangaOcrModel:
    """Tests for get_manga_ocr_model function."""

    @patch('japanese_agent.tools.screenshot_analyzer.MangaOcr')
    def test_model_initialization(self, mock_manga_ocr_class):
        """Test that model is initialized on first call."""
        # Reset the global model cache
        import japanese_agent.tools.screenshot_analyzer as sa
        sa._manga_ocr_model = None

        mock_model = MagicMock()
        mock_manga_ocr_class.return_value = mock_model

        # First call should initialize model
        result = get_manga_ocr_model()

        assert result == mock_model
        mock_manga_ocr_class.assert_called_once()

    @patch('japanese_agent.tools.screenshot_analyzer.MangaOcr')
    def test_model_caching(self, mock_manga_ocr_class):
        """Test that model is cached after first initialization."""
        # Reset the global model cache
        import japanese_agent.tools.screenshot_analyzer as sa
        sa._manga_ocr_model = None

        mock_model = MagicMock()
        mock_manga_ocr_class.return_value = mock_model

        # First call
        result1 = get_manga_ocr_model()
        # Second call
        result2 = get_manga_ocr_model()

        # Should return same instance
        assert result1 == result2
        # Should only initialize once
        mock_manga_ocr_class.assert_called_once()


class TestAnalyzeScreenshotMangaOcr:
    """Tests for analyze_screenshot_manga_ocr tool function."""

    @patch('japanese_agent.tools.screenshot_analyzer.get_manga_ocr_model')
    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_successful_text_extraction(self, mock_preprocess, mock_get_model, sample_image_path):
        """Test successful text extraction with mocked manga-ocr."""
        from PIL import Image

        # Mock preprocessing
        mock_preprocessed = Image.new('L', (100, 100))
        mock_preprocess.return_value = mock_preprocessed

        # Mock manga-ocr model
        mock_model = MagicMock()
        mock_model.return_value = "こんにちは世界"
        mock_get_model.return_value = mock_model

        # Call the function
        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        # Assertions
        assert "error" not in result
        assert result["ocr_method"] == "manga-ocr"
        assert result["file_path"] == sample_image_path
        assert "processed_at" in result

        # Check extracted text
        assert len(result["extracted_text"]) == 1
        assert result["extracted_text"][0]["text"] == "こんにちは世界"
        assert result["extracted_text"][0]["confidence"] == 0.95
        assert result["extracted_text"][0]["reading"] is None
        assert result["extracted_text"][0]["position"] is None

        # Verify preprocessing was called
        mock_preprocess.assert_called_once_with(sample_image_path)

        # Verify model was called with preprocessed image
        mock_model.assert_called_once_with(mock_preprocessed)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = analyze_screenshot_manga_ocr.func("/nonexistent/image.png")

        assert "error" in result
        assert "not found" in result["error"].lower()
        assert result["ocr_method"] == "manga-ocr"
        assert result["extracted_text"] == []

    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_preprocessing_failure(self, mock_preprocess, sample_image_path):
        """Test handling of preprocessing failure."""
        mock_preprocess.side_effect = ValueError("Preprocessing failed")

        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        assert "error" in result
        assert "preprocessing failed" in result["error"].lower()
        assert result["ocr_method"] == "manga-ocr"

    @patch('japanese_agent.tools.screenshot_analyzer.get_manga_ocr_model')
    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_model_initialization_failure(self, mock_preprocess, mock_get_model, sample_image_path):
        """Test handling of model initialization failure."""
        from PIL import Image

        mock_preprocess.return_value = Image.new('L', (100, 100))
        mock_get_model.side_effect = Exception("Model loading failed")

        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        assert "error" in result
        assert "Failed to initialize" in result["error"]
        assert result["ocr_method"] == "manga-ocr"

    @patch('japanese_agent.tools.screenshot_analyzer.get_manga_ocr_model')
    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_ocr_extraction_failure(self, mock_preprocess, mock_get_model, sample_image_path):
        """Test handling of OCR extraction failure."""
        from PIL import Image

        mock_preprocess.return_value = Image.new('L', (100, 100))

        mock_model = MagicMock()
        mock_model.side_effect = Exception("OCR failed")
        mock_get_model.return_value = mock_model

        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        assert "error" in result
        assert "OCR extraction failed" in result["error"]
        assert result["ocr_method"] == "manga-ocr"

    @patch('japanese_agent.tools.screenshot_analyzer.get_manga_ocr_model')
    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_empty_text_extraction(self, mock_preprocess, mock_get_model, sample_image_path):
        """Test handling of image with no text."""
        from PIL import Image

        mock_preprocess.return_value = Image.new('L', (100, 100))

        mock_model = MagicMock()
        mock_model.return_value = ""  # No text found
        mock_get_model.return_value = mock_model

        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        assert "error" not in result
        assert result["ocr_method"] == "manga-ocr"
        assert result["extracted_text"] == []  # Empty list for no text

    @patch('japanese_agent.tools.screenshot_analyzer.get_manga_ocr_model')
    @patch('japanese_agent.tools.screenshot_analyzer.preprocess_image_for_ocr')
    def test_whitespace_only_text(self, mock_preprocess, mock_get_model, sample_image_path):
        """Test handling of whitespace-only extraction."""
        from PIL import Image

        mock_preprocess.return_value = Image.new('L', (100, 100))

        mock_model = MagicMock()
        mock_model.return_value = "   \n\t  "  # Only whitespace
        mock_get_model.return_value = mock_model

        result = analyze_screenshot_manga_ocr.func(sample_image_path)

        assert "error" not in result
        assert result["extracted_text"] == []  # Should be empty after strip


class TestHybridScreenshotAnalysis:
    """Tests for hybrid_screenshot_analysis function."""

    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_claude')
    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_manga_ocr')
    def test_successful_hybrid_analysis(self, mock_manga_tool, mock_claude_tool, sample_image_path):
        """Test successful hybrid analysis with both methods."""
        # Mock manga-ocr result
        mock_manga_tool.func.return_value = {
            "file_path": sample_image_path,
            "processed_at": "2024-01-01T00:00:00Z",
            "extracted_text": [
                {
                    "text": "こんにちは",
                    "reading": None,
                    "confidence": 0.95,
                    "position": None
                }
            ],
            "ocr_method": "manga-ocr"
        }

        # Mock Claude Vision result
        mock_claude_tool.func.return_value = {
            "file_path": sample_image_path,
            "processed_at": "2024-01-01T00:00:00Z",
            "extracted_text": [
                {
                    "text": "こんにちは",
                    "reading": "konnichiwa",
                    "confidence": 0.90,
                    "position": {"x": 10, "y": 20, "width": 100, "height": 30}
                }
            ],
            "translation": "Hello",
            "context": "A greeting message",
            "vocabulary": [
                {
                    "word": "こんにちは",
                    "reading": "konnichiwa",
                    "meaning": "hello",
                    "part_of_speech": "interjection",
                    "jlpt_level": "N5"
                }
            ],
            "ocr_method": "claude"
        }

        # Call hybrid analysis
        result = hybrid_screenshot_analysis.func(sample_image_path)

        # Assertions
        assert "error" not in result
        assert result["ocr_method"] == "hybrid"

        # Should use manga-ocr's extracted text (more accurate)
        assert len(result["extracted_text"]) == 1
        assert result["extracted_text"][0]["text"] == "こんにちは"

        # Should use Claude's translation and context
        assert result["translation"] == "Hello"
        assert result["context"] == "A greeting message"
        assert len(result["vocabulary"]) == 1

        # Should have processing notes
        assert "processing_notes" in result

    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_claude')
    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_manga_ocr')
    def test_manga_ocr_failure_fallback_to_claude(self, mock_manga_tool, mock_claude_tool, sample_image_path):
        """Test fallback to Claude when manga-ocr fails."""
        # Mock manga-ocr failure
        mock_manga_tool.func.return_value = {
            "error": "OCR failed",
            "file_path": sample_image_path,
            "extracted_text": [],
            "ocr_method": "manga-ocr"
        }

        # Mock Claude success
        mock_claude_tool.func.return_value = {
            "file_path": sample_image_path,
            "extracted_text": [{"text": "テスト", "confidence": 0.9}],
            "translation": "Test",
            "context": "Test context",
            "vocabulary": [],
            "ocr_method": "claude"
        }

        result = hybrid_screenshot_analysis.func(sample_image_path)

        # Should use Claude's extracted text as fallback
        assert result["extracted_text"][0]["text"] == "テスト"
        assert result["translation"] == "Test"

        # Should have partial errors
        assert "partial_errors" in result
        assert len(result["partial_errors"]) == 1

    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_claude')
    @patch('japanese_agent.tools.screenshot_analyzer.analyze_screenshot_manga_ocr')
    def test_both_methods_failure(self, mock_manga_tool, mock_claude_tool, sample_image_path):
        """Test handling when both OCR methods fail."""
        # Mock both failures
        mock_manga_tool.func.return_value = {
            "error": "manga-ocr failed",
            "file_path": sample_image_path,
            "extracted_text": [],
            "ocr_method": "manga-ocr"
        }

        mock_claude_tool.func.return_value = {
            "error": "Claude failed",
            "file_path": sample_image_path,
            "extracted_text": [],
            "ocr_method": "claude"
        }

        result = hybrid_screenshot_analysis.func(sample_image_path)

        # Should have error
        assert "error" in result
        assert "Both OCR methods failed" in result["error"]
        assert result["ocr_method"] == "hybrid"

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = hybrid_screenshot_analysis.func("/nonexistent/image.png")

        assert "error" in result
        assert "not found" in result["error"].lower()
        assert result["ocr_method"] == "hybrid"

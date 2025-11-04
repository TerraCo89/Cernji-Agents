"""
Screenshot analysis tools for Japanese Learning Agent.

Provides OCR and translation capabilities using Claude Vision API and manga-ocr.
"""

from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
import os
import base64
import json
from pathlib import Path
from datetime import datetime, timezone
from anthropic import Anthropic
from PIL import Image
import cv2
import numpy as np
from manga_ocr import MangaOcr


# ==============================================================================
# Module-level Model Cache
# ==============================================================================

# Global manga-ocr model instance (lazy loaded on first use)
_manga_ocr_model: Optional[MangaOcr] = None


def get_manga_ocr_model() -> MangaOcr:
    """
    Get or initialize the manga-ocr model.

    Uses lazy loading pattern - model is only loaded on first call.
    Subsequent calls return the cached instance.

    Returns:
        MangaOcr: Initialized manga-ocr model

    Note:
        First call downloads ~1GB PyTorch model (cached for subsequent runs).
    """
    global _manga_ocr_model

    if _manga_ocr_model is None:
        _manga_ocr_model = MangaOcr()

    return _manga_ocr_model


# ==============================================================================
# Helper Functions
# ==============================================================================

def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """
    Encode an image file to base64 for Claude Vision API.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_string, media_type)

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image format is not supported
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Determine media type from extension
    extension = path.suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }

    if extension not in media_type_map:
        raise ValueError(f"Unsupported image format: {extension}. Supported: PNG, JPG, JPEG")

    media_type = media_type_map[extension]

    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_string = base64.b64encode(image_data).decode("utf-8")

    return base64_string, media_type


def preprocess_image_for_ocr(image_path: str) -> Image.Image:
    """
    Preprocess an image to improve manga-ocr accuracy.

    Applies the following transformations:
    1. Convert to grayscale
    2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    3. Upscale 2x using bicubic interpolation for small text

    Args:
        image_path: Path to the image file

    Returns:
        Preprocessed PIL Image object

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image cannot be loaded
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        # Load image with PIL
        img = Image.open(image_path)

        # Convert to numpy array for OpenCV processing
        img_array = np.array(img)

        # Convert to grayscale if image is color
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply CLAHE for contrast enhancement
        # clipLimit: threshold for contrast limiting
        # tileGridSize: size of grid for histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Upscale 2x using bicubic interpolation for better small text recognition
        height, width = enhanced.shape
        upscaled = cv2.resize(
            enhanced,
            (width * 2, height * 2),
            interpolation=cv2.INTER_CUBIC
        )

        # Convert back to PIL Image
        processed_img = Image.fromarray(upscaled)

        return processed_img

    except Exception as e:
        raise ValueError(f"Failed to preprocess image {image_path}: {str(e)}")


def create_vision_prompt() -> str:
    """
    Create the structured prompt for Claude Vision API to analyze Japanese screenshots.

    Returns:
        Formatted prompt string requesting structured JSON output
    """
    return """Analyze this Japanese game screenshot and extract all Japanese text with detailed information.

Please provide a JSON response with the following structure:

{
  "extracted_text": [
    {
      "text": "Japanese text segment",
      "reading": "hiragana or romaji reading",
      "confidence": 0.95,
      "position": {"x": 0, "y": 0, "width": 100, "height": 50}
    }
  ],
  "translation": "Full English translation of all text",
  "context": "Description of the game scene, visual elements, and what's happening",
  "vocabulary": [
    {
      "word": "Japanese word",
      "reading": "hiragana reading",
      "meaning": "English meaning",
      "part_of_speech": "noun/verb/etc",
      "jlpt_level": "N5/N4/N3/N2/N1 or null"
    }
  ]
}

Guidelines:
1. Extract ALL visible Japanese text (hiragana, katakana, kanji)
2. Provide accurate hiragana readings (furigana) for each text segment
3. Estimate text position if visible (x, y, width, height in pixels from top-left)
4. Set confidence score (0.0-1.0) based on text clarity:
   - 0.95-1.0: Very clear, high-resolution text
   - 0.85-0.94: Clear text with minor artifacts
   - 0.70-0.84: Somewhat blurry or occluded text
   - Below 0.70: Very unclear or partially hidden text
5. Translate the complete meaning, preserving context
6. Describe the visual scene and game context
7. Extract key vocabulary words with their meanings and JLPT levels if known
8. Return ONLY the JSON object, no additional text

Please analyze this screenshot now."""


def parse_claude_response(response_text: str, image_path: str) -> Dict[str, Any]:
    """
    Parse Claude Vision API response and structure it to match ScreenshotDict schema.

    Args:
        response_text: Raw text response from Claude
        image_path: Original image path

    Returns:
        Dictionary matching ScreenshotDict schema

    Raises:
        json.JSONDecodeError: If response is not valid JSON
        KeyError: If required fields are missing
    """
    # Try to parse JSON response
    try:
        # Claude might wrap JSON in markdown code blocks
        if "```json" in response_text:
            # Extract JSON from markdown code block
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            # Generic code block
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        else:
            json_str = response_text.strip()

        data = json.loads(json_str)

        # Structure according to ScreenshotDict schema
        return {
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": data.get("extracted_text", []),
            "translation": data.get("translation", ""),
            "context": data.get("context", ""),
            "ocr_method": "claude",
            "vocabulary": data.get("vocabulary", []),
        }

    except json.JSONDecodeError as e:
        # If JSON parsing fails, return structured error
        return {
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "translation": "",
            "context": "",
            "ocr_method": "claude",
            "error": f"Failed to parse Claude response as JSON: {str(e)}",
            "raw_response": response_text[:500],  # Include first 500 chars for debugging
        }


# ==============================================================================
# Tool Implementations
# ==============================================================================

@tool
def analyze_screenshot_claude(image_path: str) -> Dict[str, Any]:
    """
    Analyze a screenshot using Claude Vision API for OCR and translation.

    This tool extracts Japanese text from game screenshots, provides readings,
    translations, and contextual information about the game scene.

    Args:
        image_path: Path to the screenshot image file

    Returns:
        Dictionary containing:
            - file_path: Original image path
            - processed_at: ISO timestamp of processing
            - extracted_text: List of Japanese text segments with readings and positions
            - translation: English translation
            - context: Game scene description
            - vocabulary: List of key words with meanings and JLPT levels
            - ocr_method: Always "claude" for this function
    """
    try:
        # Validate environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "error": "ANTHROPIC_API_KEY environment variable not set",
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "translation": "",
                "context": "",
                "ocr_method": "claude",
            }

        # Validate and encode image
        try:
            image_base64, media_type = encode_image_to_base64(image_path)
        except FileNotFoundError as e:
            return {
                "error": str(e),
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "translation": "",
                "context": "",
                "ocr_method": "claude",
            }
        except ValueError as e:
            return {
                "error": str(e),
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "translation": "",
                "context": "",
                "ocr_method": "claude",
            }

        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)

        # Get model from environment or use default
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        # Create vision prompt
        vision_prompt = create_vision_prompt()

        # Call Claude Vision API
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": vision_prompt,
                        },
                    ],
                }
            ],
        )

        # Extract response text
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        # Parse and structure response
        result = parse_claude_response(response_text, image_path)

        return result

    except Exception as e:
        # Catch-all error handling
        return {
            "error": f"Unexpected error during Claude Vision analysis: {str(e)}",
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "translation": "",
            "context": "",
            "ocr_method": "claude",
        }


@tool
def analyze_screenshot_manga_ocr(image_path: str) -> Dict[str, Any]:
    """
    Analyze a screenshot using manga-ocr for Japanese text extraction.

    This tool uses manga-ocr (specialized for Japanese game/manga text) to
    extract text with high accuracy. Best used in combination with Claude
    for translation and context understanding.

    Args:
        image_path: Path to the screenshot image file

    Returns:
        Dictionary containing:
            - extracted_text: Japanese text segments
            - confidence: OCR confidence scores
            - positions: Text bounding boxes
    """
    # Validate image path
    if not os.path.exists(image_path):
        return {
            "error": f"Image not found: {image_path}",
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "ocr_method": "manga-ocr",
        }

    try:
        # Preprocess image for better OCR accuracy
        try:
            preprocessed_img = preprocess_image_for_ocr(image_path)
        except FileNotFoundError as e:
            return {
                "error": str(e),
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "ocr_method": "manga-ocr",
            }
        except ValueError as e:
            return {
                "error": f"Image preprocessing failed: {str(e)}",
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "ocr_method": "manga-ocr",
            }

        # Initialize manga-ocr model (lazy loading)
        try:
            mocr = get_manga_ocr_model()
        except Exception as e:
            return {
                "error": f"Failed to initialize manga-ocr model: {str(e)}",
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "ocr_method": "manga-ocr",
            }

        # Extract text using manga-ocr
        try:
            extracted_text_raw = mocr(preprocessed_img)
        except Exception as e:
            return {
                "error": f"OCR extraction failed: {str(e)}",
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "ocr_method": "manga-ocr",
            }

        # Structure the output to match ExtractedTextDict schema
        # Note: manga-ocr returns a single string without bounding boxes
        # We'll create a single text segment with estimated high confidence
        extracted_text_segments = []

        if extracted_text_raw and extracted_text_raw.strip():
            segment = {
                "text": extracted_text_raw.strip(),
                "reading": None,  # manga-ocr doesn't provide readings
                "confidence": 0.95,  # manga-ocr is highly accurate for manga/game text
                "position": None,  # manga-ocr doesn't provide bounding boxes by default
            }
            extracted_text_segments.append(segment)

        # Return structured result
        return {
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": extracted_text_segments,
            "ocr_method": "manga-ocr",
        }

    except Exception as e:
        # Catch-all error handling
        return {
            "error": f"Unexpected error during manga-ocr analysis: {str(e)}",
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "ocr_method": "manga-ocr",
        }


@tool
def hybrid_screenshot_analysis(image_path: str) -> Dict[str, Any]:
    """
    Perform hybrid OCR analysis using both Claude Vision and manga-ocr.

    This combines the contextual understanding of Claude Vision with the
    specialized Japanese text extraction of manga-ocr for best results.

    Args:
        image_path: Path to the screenshot image file

    Returns:
        Dictionary combining results from both OCR methods with:
            - extracted_text: All Japanese text found
            - translation: English translation
            - vocabulary: Key vocabulary with readings and meanings
            - context: Game scene description
            - ocr_confidence: Confidence scores per text segment
    """
    # Validate image path
    if not os.path.exists(image_path):
        return {
            "error": f"Image not found: {image_path}",
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "translation": "",
            "context": "",
            "vocabulary": [],
            "ocr_method": "hybrid",
        }

    try:
        # Step 1: Use manga-ocr for accurate text extraction
        manga_result = analyze_screenshot_manga_ocr.func(image_path)

        # Step 2: Use Claude Vision for translation, context, and vocabulary
        claude_result = analyze_screenshot_claude.func(image_path)

        # Step 3: Merge results
        # Prefer manga-ocr for text extraction (more accurate for game text)
        # Use Claude for translation, context, and vocabulary (better contextual understanding)

        # Check if either method had errors
        manga_has_error = "error" in manga_result
        claude_has_error = "error" in claude_result

        # If both failed, return error
        if manga_has_error and claude_has_error:
            return {
                "error": f"Both OCR methods failed. manga-ocr: {manga_result.get('error', 'Unknown')}; Claude: {claude_result.get('error', 'Unknown')}",
                "file_path": image_path,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text": [],
                "translation": "",
                "context": "",
                "vocabulary": [],
                "ocr_method": "hybrid",
            }

        # Merge extracted text (prefer manga-ocr if available, fall back to Claude)
        extracted_text = []
        if not manga_has_error and manga_result.get("extracted_text"):
            extracted_text = manga_result["extracted_text"]
        elif not claude_has_error and claude_result.get("extracted_text"):
            extracted_text = claude_result["extracted_text"]

        # Use Claude's translation, context, and vocabulary (if available)
        translation = claude_result.get("translation", "") if not claude_has_error else ""
        context = claude_result.get("context", "") if not claude_has_error else ""
        vocabulary = claude_result.get("vocabulary", []) if not claude_has_error else []

        # Return merged result
        result = {
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": extracted_text,
            "translation": translation,
            "context": context,
            "vocabulary": vocabulary,
            "ocr_method": "hybrid",
        }

        # Add notes about which methods were used
        notes = []
        if not manga_has_error:
            notes.append("Text extraction: manga-ocr")
        if not claude_has_error:
            notes.append("Translation/Context: Claude Vision")

        if notes:
            result["processing_notes"] = ", ".join(notes)

        # Add partial error information if one method failed
        if manga_has_error or claude_has_error:
            errors = []
            if manga_has_error:
                errors.append(f"manga-ocr: {manga_result.get('error')}")
            if claude_has_error:
                errors.append(f"Claude Vision: {claude_result.get('error')}")
            result["partial_errors"] = errors

        return result

    except Exception as e:
        # Catch-all error handling
        return {
            "error": f"Unexpected error during hybrid analysis: {str(e)}",
            "file_path": image_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_text": [],
            "translation": "",
            "context": "",
            "vocabulary": [],
            "ocr_method": "hybrid",
        }


# Export all tools
__all__ = [
    "analyze_screenshot_claude",
    "analyze_screenshot_manga_ocr",
    "hybrid_screenshot_analysis",
]

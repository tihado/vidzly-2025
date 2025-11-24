"""
Unit tests for thumbnail_generator tool.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
from io import BytesIO

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.thumbnail_generator import thumbnail_generator


class TestThumbnailGenerator:
    """Test cases for thumbnail_generator function."""

    def test_thumbnail_generator_with_tuple_input(self, temp_image_file):
        """Test thumbnail_generator with tuple input (Gradio format)."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            mock_inline_data = Mock()
            mock_inline_data.data = b"fake generated image data"
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            image_input = (temp_image_file, "subtitle.srt")
            summary = "An exciting adventure"

            result = thumbnail_generator(image_input, summary)

            assert os.path.isabs(result)
            assert "thumbnail_" in result
            assert result.endswith(".png")

    def test_thumbnail_generator_without_output_path(self, temp_image_file):
        """Test thumbnail_generator generates output path when not provided."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            mock_inline_data = Mock()
            mock_inline_data.data = b"fake generated image data"
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            summary = "A dramatic moment"

            result = thumbnail_generator(temp_image_file, summary)

            assert os.path.isabs(result)
            assert "thumbnail_" in result
            assert result.endswith(".png")

    def test_thumbnail_generator_invalid_input_format(self):
        """Test thumbnail_generator with invalid input format."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with pytest.raises(Exception) as exc_info:
                thumbnail_generator(123, "summary")  # Invalid input type

            assert "Invalid image input format" in str(exc_info.value)

    def test_thumbnail_generator_file_not_found(self):
        """Test thumbnail_generator with non-existent file."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with pytest.raises(Exception) as exc_info:
                thumbnail_generator("/nonexistent/image.png", "summary")

            assert "Image file not found" in str(exc_info.value)

    def test_thumbnail_generator_without_api_key(self, temp_image_file):
        """Test thumbnail_generator raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                thumbnail_generator(temp_image_file, "summary")

            assert "GOOGLE_API_KEY" in str(exc_info.value)

    def test_thumbnail_generator_api_failure(self, temp_image_file):
        """Test thumbnail_generator handles API failures."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_genai_client.models.generate_content.side_effect = Exception(
                "API Error"
            )
            mock_client.return_value = mock_genai_client

            with pytest.raises(Exception) as exc_info:
                thumbnail_generator(temp_image_file, "summary")

            assert "Error generating thumbnail" in str(
                exc_info.value
            ) or "API Error" in str(exc_info.value)

    def test_thumbnail_generator_no_image_in_response(self, temp_image_file):
        """Test thumbnail_generator when API doesn't return image data."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.candidates = []  # No candidates
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with pytest.raises(Exception) as exc_info:
                thumbnail_generator(temp_image_file, "summary")

            assert "Failed to extract generated image" in str(
                exc_info.value
            ) or "Error generating thumbnail" in str(exc_info.value)

    def test_thumbnail_generator_creates_output_directory(
        self, temp_image_file, temp_output_dir
    ):
        """Test thumbnail_generator creates output directory if it doesn't exist."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            mock_inline_data = Mock()
            mock_inline_data.data = b"fake generated image data"
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            output_dir = os.path.join(temp_output_dir, "nested", "path")
            output_path = os.path.join(output_dir, "thumbnail.png")

            result = thumbnail_generator(temp_image_file, "summary", output_path)

            assert os.path.exists(output_dir)
            assert os.path.isabs(result)

    def test_thumbnail_generator_with_blob_format(self, temp_image_file):
        """Test thumbnail_generator handles blob format in response."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            # Test blob format instead of inline_data
            mock_blob = Mock()
            mock_blob.data = b"fake generated image data"
            mock_part.blob = mock_blob
            mock_part.inline_data = None
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            result = thumbnail_generator(temp_image_file, "summary")

            assert os.path.isabs(result)
            assert result.endswith(".png")

    def test_thumbnail_generator_api_fallback_without_response_modalities(
        self, temp_image_file
    ):
        """Test thumbnail_generator falls back when response_modalities fails."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            mock_guess_type.return_value = ("image/png", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            mock_inline_data = Mock()
            mock_inline_data.data = b"fake generated image data"
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]

            # First call fails, second succeeds
            mock_genai_client.models.generate_content.side_effect = [
                Exception("response_modalities not supported"),
                mock_response,
            ]
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            result = thumbnail_generator(temp_image_file, "summary")

            assert os.path.isabs(result)
            # Should have been called twice (first with response_modalities, second without)
            assert mock_genai_client.models.generate_content.call_count == 2

    def test_thumbnail_generator_mime_type_detection(self, temp_image_file):
        """Test thumbnail_generator handles different image MIME types."""
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}),
            patch("app.tools.thumbnail_generator.genai.Client") as mock_client,
            patch("app.tools.thumbnail_generator.Image.open") as mock_image_open,
            patch(
                "app.tools.thumbnail_generator.mimetypes.guess_type"
            ) as mock_guess_type,
            patch("builtins.open", mock_open(read_data=b"fake image data")),
        ):

            # Test with JPEG MIME type
            mock_guess_type.return_value = ("image/jpeg", None)

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_candidate = Mock()
            mock_content = Mock()
            mock_part = Mock()
            mock_inline_data = Mock()
            mock_inline_data.data = b"fake generated image data"
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            mock_image = Mock()
            mock_image.convert.return_value = mock_image
            mock_image_open.return_value = mock_image

            result = thumbnail_generator(temp_image_file, "summary")

            assert os.path.isabs(result)
            # Verify MIME type was used
            mock_guess_type.assert_called_once()

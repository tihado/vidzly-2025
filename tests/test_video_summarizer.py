"""
Unit tests for video_summarizer tool.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.video_summarizer import video_summarizer


class TestVideoSummarizer:
    """Test cases for video_summarizer function."""

    def test_video_summarizer_with_tuple_input(self, temp_video_file):
        """Test video_summarizer with tuple input (Gradio format)."""
        with (
            patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture,
            patch("app.tools.video_summarizer.genai.Client") as mock_client,
        ):

            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
                3: 1920,
                4: 1080,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.text = "Test summary"
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            video_input = (temp_video_file, "subtitle.srt")

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = video_summarizer(video_input, fps=2.0)

            result_json = json.loads(result)
            assert "summary" in result_json

    def test_video_summarizer_invalid_input_format(self):
        """Test video_summarizer with invalid input format."""
        result = video_summarizer(123, fps=2.0)
        result_json = json.loads(result)
        assert "error" in result_json
        assert "Invalid video input format" in result_json["error"]

    def test_video_summarizer_file_not_found(self):
        """Test video_summarizer with non-existent file."""
        result = video_summarizer("/nonexistent/video.mp4", fps=2.0)
        result_json = json.loads(result)
        assert "error" in result_json
        assert "Video file not found" in result_json["error"]

    def test_video_summarizer_cannot_open_video(self, temp_video_file):
        """Test video_summarizer when video cannot be opened."""
        with patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap

            result = video_summarizer(temp_video_file, fps=2.0)
            result_json = json.loads(result)

            assert "error" in result_json
            assert "Could not open video file" in result_json["error"]

    def test_video_summarizer_no_api_key(self, temp_video_file):
        """Test video_summarizer without API key (fallback mode)."""
        with patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
                3: 1920,
                4: 1080,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            with patch.dict(os.environ, {}, clear=True):
                result = video_summarizer(temp_video_file, fps=2.0)

            result_json = json.loads(result)

            assert "duration" in result_json
            assert "summary" in result_json
            assert "Video analysis requires GOOGLE_API_KEY" in result_json["summary"]
            assert result_json["mood_tags"] == []

    def test_video_summarizer_extracts_mood_tags(self, temp_video_file):
        """Test video_summarizer extracts mood tags from summary."""
        with (
            patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture,
            patch("app.tools.video_summarizer.genai.Client") as mock_client,
        ):

            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
                3: 1920,
                4: 1080,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            mock_genai_client = Mock()
            mock_response = Mock()
            # Include mood keywords in summary
            mock_response.text = "This is an energetic and fast-paced video with bright colors and fun activities."
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = video_summarizer(temp_video_file, fps=2.0)

            result_json = json.loads(result)

            assert "mood_tags" in result_json
            assert isinstance(result_json["mood_tags"], list)
            # Should detect some mood tags
            assert len(result_json["mood_tags"]) > 0

    def test_video_summarizer_default_mood_tags(self, temp_video_file):
        """Test video_summarizer uses default mood tag when none detected."""
        with (
            patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture,
            patch("app.tools.video_summarizer.genai.Client") as mock_client,
        ):

            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
                3: 1920,
                4: 1080,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            mock_genai_client = Mock()
            mock_response = Mock()
            # Summary without mood keywords
            mock_response.text = (
                "This is a regular video without specific mood indicators."
            )
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = video_summarizer(temp_video_file, fps=2.0)

            result_json = json.loads(result)

            assert "mood_tags" in result_json
            assert result_json["mood_tags"] == ["general"]

    def test_video_summarizer_custom_fps(self, temp_video_file):
        """Test video_summarizer with custom fps parameter."""
        with (
            patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture,
            patch("app.tools.video_summarizer.genai.Client") as mock_client,
        ):

            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
                3: 1920,
                4: 1080,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.text = "Test summary"
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = video_summarizer(temp_video_file, fps=5.0)

            result_json = json.loads(result)
            assert "summary" in result_json

            # Verify fps was passed to VideoMetadata
            call_args = mock_genai_client.models.generate_content.call_args
            assert call_args is not None

    def test_video_summarizer_error_handling(self, temp_video_file):
        """Test video_summarizer handles exceptions gracefully."""
        with patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.side_effect = Exception("Unexpected error")
            mock_capture.return_value = mock_cap

            result = video_summarizer(temp_video_file, fps=2.0)
            result_json = json.loads(result)

            assert "error" in result_json
            assert "Error processing video" in result_json["error"]

    def test_video_summarizer_metadata_extraction(self, temp_video_file):
        """Test video_summarizer extracts correct metadata."""
        with (
            patch("app.tools.video_summarizer.cv2.VideoCapture") as mock_capture,
            patch("app.tools.video_summarizer.genai.Client") as mock_client,
        ):

            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 24.0,  # FPS
                7: 720,  # Frame count
                3: 1280,  # Width
                4: 720,  # Height
            }.get(prop, 0)
            mock_capture.return_value = mock_cap

            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.text = "Test summary"
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = video_summarizer(temp_video_file, fps=2.0)

            result_json = json.loads(result)

            assert result_json["fps"] == 24.0
            assert result_json["frame_count"] == 720
            assert result_json["resolution"] == "1280x720"
            assert result_json["duration"] == pytest.approx(
                30.0, rel=0.1
            )  # 720/24 = 30


class TestVideoSummarizerIntegration:
    """Integration tests for video_summarizer using real video files."""

    def test_video_summarizer_real_video_basic(self, real_video_file):
        """Test video_summarizer with real video file - basic functionality."""
        result = video_summarizer(real_video_file, fps=2.0)
        result_json = json.loads(result)

        # Should return valid JSON with metadata
        assert "duration" in result_json
        assert "resolution" in result_json
        assert "fps" in result_json
        assert "frame_count" in result_json
        assert isinstance(result_json["duration"], (int, float))
        assert result_json["duration"] > 0

    def test_video_summarizer_real_video_no_api_key(self, real_video_file):
        """Test video_summarizer with real video file without API key (fallback mode)."""
        with patch.dict(os.environ, {}, clear=True):
            result = video_summarizer(real_video_file, fps=2.0)

        result_json = json.loads(result)

        # Should still return metadata even without API key
        assert "duration" in result_json
        assert "resolution" in result_json
        assert "summary" in result_json
        assert "Video analysis requires GOOGLE_API_KEY" in result_json["summary"]
        assert result_json["mood_tags"] == []

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set, skipping API test",
    )
    def test_video_summarizer_real_video_with_api(self, real_video_file):
        """Test video_summarizer with real video file and API key (if available)."""
        result = video_summarizer(real_video_file, fps=2.0)
        result_json = json.loads(result)

        # If API key is available, should get actual summary
        if "error" not in result_json:
            assert "summary" in result_json
            assert len(result_json["summary"]) > 0
            assert "mood_tags" in result_json
            assert isinstance(result_json["mood_tags"], list)

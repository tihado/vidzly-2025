"""
Unit tests for subtitle_creator tool.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.subtitle_creator import subtitle_creator


class TestSubtitleCreator:
    """Test cases for subtitle_creator function."""

    @pytest.fixture
    def simple_transcript(self):
        """Simple transcript JSON for testing."""
        return json.dumps({
            "subtitles": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello, welcome!",
                    "position": "bottom",
                    "fontsize": 48,
                    "color": "white"
                },
                {
                    "start": 2.5,
                    "end": 5.0,
                    "text": "This is a test.",
                    "position": "top",
                    "fontsize": 52,
                    "color": "yellow"
                }
            ],
            "default_style": {
                "font": "Arial",
                "fontsize": 48,
                "color": "white",
                "bg_color": "black"
            }
        })

    @pytest.fixture
    def minimal_transcript(self):
        """Minimal transcript with just required fields."""
        return json.dumps({
            "subtitles": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Test subtitle"
                }
            ]
        })

    def test_subtitle_creator_with_simple_transcript(self, temp_video_file, simple_transcript):
        """Test subtitle_creator with a simple transcript."""
        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            # Mock video
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            # Mock text clips
            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            # Mock composite
            mock_final = Mock()
            mock_composite.return_value = mock_final

            result = subtitle_creator(temp_video_file, simple_transcript)

            # Verify video was loaded
            mock_video_clip.assert_called_once_with(temp_video_file)

            # Verify text clips were created (2 subtitles)
            assert mock_text_clip.call_count == 2

            # Verify composite was created
            mock_composite.assert_called_once()

            # Verify video was written
            mock_final.write_videofile.assert_called_once()

            # Verify cleanup
            mock_video.close.assert_called_once()
            mock_final.close.assert_called_once()

            assert result.endswith(".mp4")
            assert os.path.exists(result) or result.startswith("/tmp/")

    def test_subtitle_creator_with_minimal_transcript(self, temp_video_file, minimal_transcript):
        """Test subtitle_creator with minimal transcript (no styling)."""
        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            result = subtitle_creator(temp_video_file, minimal_transcript)

            # Verify text clip was created with defaults
            mock_text_clip.assert_called_once()
            call_kwargs = mock_text_clip.call_args[1]
            assert call_kwargs["font"] == "Arial"
            assert call_kwargs["font_size"] == 48
            assert call_kwargs["color"] == "white"
            assert call_kwargs["bg_color"] == "black"

            assert result.endswith(".mp4")

    def test_subtitle_creator_with_tuple_input(self, temp_video_file, simple_transcript):
        """Test subtitle_creator with tuple input (Gradio format)."""
        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            video_input = (temp_video_file, "subtitle.srt")

            result = subtitle_creator(video_input, simple_transcript)

            mock_video_clip.assert_called_once_with(temp_video_file)
            assert result.endswith(".mp4")

    def test_subtitle_creator_with_custom_output_path(self, temp_video_file, minimal_transcript, tmp_path):
        """Test subtitle_creator with custom output path."""
        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            output_path = str(tmp_path / "custom_subtitled.mp4")

            result = subtitle_creator(temp_video_file, minimal_transcript, output_path)

            assert result == output_path
            mock_final.write_videofile.assert_called_once()

    def test_subtitle_creator_with_nonexistent_file(self, simple_transcript):
        """Test subtitle_creator with nonexistent video file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            subtitle_creator("/nonexistent/video.mp4", simple_transcript)
        assert "not found" in str(exc_info.value)

    def test_subtitle_creator_with_invalid_json(self, temp_video_file):
        """Test subtitle_creator with invalid JSON transcript."""
        invalid_json = "{ this is not valid json }"

        with pytest.raises(ValueError) as exc_info:
            subtitle_creator(temp_video_file, invalid_json)
        assert "Invalid JSON format" in str(exc_info.value)

    def test_subtitle_creator_with_missing_subtitles_array(self, temp_video_file):
        """Test subtitle_creator with missing subtitles array."""
        transcript = json.dumps({"default_style": {"font": "Arial"}})

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "must contain 'subtitles' array" in str(exc_info.value)

    def test_subtitle_creator_with_empty_subtitles(self, temp_video_file):
        """Test subtitle_creator with empty subtitles array."""
        transcript = json.dumps({"subtitles": []})

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "must contain 'subtitles' array" in str(exc_info.value)

    def test_subtitle_creator_with_missing_required_fields(self, temp_video_file):
        """Test subtitle_creator with subtitle missing required fields."""
        transcript = json.dumps({
            "subtitles": [
                {"start": 0.0, "text": "Missing end time"}
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "must have 'start', 'end', and 'text' fields" in str(exc_info.value)

    def test_subtitle_creator_with_negative_times(self, temp_video_file):
        """Test subtitle_creator with negative start/end times."""
        transcript = json.dumps({
            "subtitles": [
                {"start": -1.0, "end": 2.0, "text": "Negative start"}
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "must be >= 0" in str(exc_info.value)

    def test_subtitle_creator_with_invalid_time_range(self, temp_video_file):
        """Test subtitle_creator with end time before start time."""
        transcript = json.dumps({
            "subtitles": [
                {"start": 5.0, "end": 2.0, "text": "Invalid range"}
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "end time must be greater than start time" in str(exc_info.value)

    def test_subtitle_creator_with_time_exceeding_duration(self, temp_video_file):
        """Test subtitle_creator with start time exceeding video duration."""
        transcript = json.dumps({
            "subtitles": [
                {"start": 15.0, "end": 20.0, "text": "Beyond video"}
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video_clip.return_value = mock_video

            with pytest.raises(ValueError) as exc_info:
                subtitle_creator(temp_video_file, transcript)
            assert "exceeds video duration" in str(exc_info.value)

    def test_subtitle_creator_clamps_end_time(self, temp_video_file):
        """Test that end time is clamped to video duration."""
        transcript = json.dumps({
            "subtitles": [
                {"start": 8.0, "end": 15.0, "text": "End beyond duration"}
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            result = subtitle_creator(temp_video_file, transcript)

            # Verify end time was clamped by checking with_end was called with video duration
            mock_text.with_end.assert_called_with(10.0)

    def test_subtitle_creator_with_different_positions(self, temp_video_file):
        """Test subtitle_creator with different position options."""
        transcript = json.dumps({
            "subtitles": [
                {"start": 0.0, "end": 1.0, "text": "Bottom", "position": "bottom"},
                {"start": 1.0, "end": 2.0, "text": "Top", "position": "top"},
                {"start": 2.0, "end": 3.0, "text": "Center", "position": "center"},
                {"start": 3.0, "end": 4.0, "text": "Custom", "position": [100, 200]},
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            result = subtitle_creator(temp_video_file, transcript)

            # Verify 4 text clips were created
            assert mock_text_clip.call_count == 4

            # Verify with_position was called 4 times with different positions
            assert mock_text.with_position.call_count == 4

    def test_subtitle_creator_with_stroke_styling(self, temp_video_file):
        """Test subtitle_creator with stroke/outline styling."""
        transcript = json.dumps({
            "subtitles": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Outlined text",
                    "stroke_color": "black",
                    "stroke_width": 3
                }
            ]
        })

        with (
            patch("app.tools.subtitle_creator.VideoFileClip") as mock_video_clip,
            patch("app.tools.subtitle_creator.TextClip") as mock_text_clip,
            patch("app.tools.subtitle_creator.CompositeVideoClip") as mock_composite,
        ):
            mock_video = Mock()
            mock_video.duration = 10.0
            mock_video.size = (1920, 1080)
            mock_video.fps = 30.0
            mock_video_clip.return_value = mock_video

            mock_text = Mock()
            mock_text.with_start.return_value = mock_text
            mock_text.with_end.return_value = mock_text
            mock_text.with_position.return_value = mock_text
            mock_text_clip.return_value = mock_text

            mock_final = Mock()
            mock_composite.return_value = mock_final

            result = subtitle_creator(temp_video_file, transcript)

            # Verify stroke parameters were passed
            call_kwargs = mock_text_clip.call_args[1]
            assert call_kwargs["stroke_color"] == "black"
            assert call_kwargs["stroke_width"] == 3

    def test_subtitle_creator_with_invalid_video_input(self, simple_transcript):
        """Test subtitle_creator with invalid video input type."""
        with pytest.raises(ValueError) as exc_info:
            subtitle_creator(12345, simple_transcript)  # type: ignore
        assert "Invalid video input format" in str(exc_info.value)

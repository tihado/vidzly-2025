"""
Unit tests for video_clipper tool.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.video_clipper import video_clipper


class TestVideoClipper:
    """Test cases for video_clipper function."""

    def test_video_clipper_with_string_path(self, temp_video_file, mock_video_duration):
        """Test video_clipper with string path input."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            # Setup mock
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            start_time = 5.0
            end_time = 15.0
            output_path = tempfile.mktemp(suffix=".mp4")

            result = video_clipper(temp_video_file, start_time, end_time, output_path)

            # Assertions
            assert os.path.isabs(result)
            assert result == os.path.abspath(output_path)
            mock_video_clip.assert_called_once_with(temp_video_file)
            mock_video.subclipped.assert_called_once_with(start_time, end_time)
            mock_clipped.write_videofile.assert_called_once()
            mock_clipped.close.assert_called_once()
            mock_video.close.assert_called_once()

    def test_video_clipper_with_tuple_input(self, temp_video_file, mock_video_duration):
        """Test video_clipper with tuple input (Gradio format)."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            video_input = (temp_video_file, "subtitle.srt")
            start_time = 0.0
            end_time = 10.0
            output_path = tempfile.mktemp(suffix=".mp4")

            result = video_clipper(video_input, start_time, end_time, output_path)

            assert os.path.isabs(result)
            mock_video_clip.assert_called_once_with(temp_video_file)

    def test_video_clipper_without_output_path(
        self, temp_video_file, mock_video_duration
    ):
        """Test video_clipper generates output path when not provided."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            start_time = 2.5
            end_time = 7.5

            result = video_clipper(temp_video_file, start_time, end_time)

            assert os.path.isabs(result)
            assert "clipped" in result.lower() or os.path.basename(result).startswith(
                "clipped_"
            )
            mock_clipped.write_videofile.assert_called_once()

    def test_video_clipper_invalid_input_format(self):
        """Test video_clipper with invalid input format."""
        with pytest.raises(Exception) as exc_info:
            video_clipper(123, 0.0, 10.0)  # Invalid input type

        assert "Invalid video input format" in str(exc_info.value)

    def test_video_clipper_file_not_found(self):
        """Test video_clipper with non-existent file."""
        with pytest.raises(Exception) as exc_info:
            video_clipper("/nonexistent/video.mp4", 0.0, 10.0)

        assert "Video file not found" in str(exc_info.value)

    def test_video_clipper_negative_start_time(self, temp_video_file):
        """Test video_clipper with negative start time."""
        with pytest.raises(Exception) as exc_info:
            video_clipper(temp_video_file, -1.0, 10.0)

        assert "Start time must be >= 0" in str(exc_info.value)

    def test_video_clipper_end_time_less_than_start(self, temp_video_file):
        """Test video_clipper with end time less than start time."""
        with pytest.raises(Exception) as exc_info:
            video_clipper(temp_video_file, 10.0, 5.0)

        assert "End time must be greater than start time" in str(exc_info.value)

    def test_video_clipper_start_time_exceeds_duration(
        self, temp_video_file, mock_video_duration
    ):
        """Test video_clipper when start time exceeds video duration."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_video_clip.return_value = mock_video

            start_time = mock_video_duration + 10.0
            end_time = mock_video_duration + 20.0

            with pytest.raises(Exception) as exc_info:
                video_clipper(temp_video_file, start_time, end_time)

            assert "exceeds video duration" in str(exc_info.value)
            # close() may be called multiple times in error handling, so just check it was called
            assert mock_video.close.call_count >= 1

    def test_video_clipper_end_time_clamped_to_duration(
        self, temp_video_file, mock_video_duration
    ):
        """Test video_clipper clamps end_time to video duration."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            start_time = 5.0
            end_time = mock_video_duration + 10.0  # Exceeds duration
            output_path = tempfile.mktemp(suffix=".mp4")

            result = video_clipper(temp_video_file, start_time, end_time, output_path)

            # Should clamp end_time to duration
            mock_video.subclipped.assert_called_once_with(
                start_time, mock_video_duration
            )
            assert os.path.isabs(result)

    def test_video_clipper_creates_output_directory(
        self, temp_video_file, temp_output_dir, mock_video_duration
    ):
        """Test video_clipper creates output directory if it doesn't exist."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            output_dir = os.path.join(temp_output_dir, "nested", "path")
            output_path = os.path.join(output_dir, "output.mp4")

            result = video_clipper(temp_video_file, 0.0, 10.0, output_path)

            assert os.path.exists(output_dir)
            assert os.path.isabs(result)

    def test_video_clipper_cleanup_on_error(self, temp_video_file, mock_video_duration):
        """Test video_clipper properly cleans up resources on error."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_clipped.write_videofile.side_effect = Exception("Write error")
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            with pytest.raises(Exception) as exc_info:
                video_clipper(temp_video_file, 0.0, 10.0)

            assert "Error clipping video" in str(exc_info.value)
            # Verify cleanup was attempted
            mock_clipped.close.assert_called_once()
            mock_video.close.assert_called_once()

    def test_video_clipper_preserves_file_extension(
        self, temp_video_file, mock_video_duration
    ):
        """Test video_clipper preserves original file extension in output."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            # Test with .mp4 extension
            result = video_clipper(temp_video_file, 0.0, 10.0)
            assert result.endswith(".mp4") or ".mp4" in result

    def test_video_clipper_returns_absolute_path(
        self, temp_video_file, mock_video_duration
    ):
        """Test video_clipper always returns absolute path."""
        with patch("app.tools.video_clipper.VideoFileClip") as mock_video_clip:
            mock_video = Mock()
            mock_video.duration = mock_video_duration
            mock_clipped = Mock()
            mock_video.subclipped.return_value = mock_clipped
            mock_video_clip.return_value = mock_video

            # Test with relative path
            relative_output = "relative_output.mp4"
            result = video_clipper(temp_video_file, 0.0, 10.0, relative_output)

            assert os.path.isabs(result)


class TestVideoClipperIntegration:
    """Integration tests for video_clipper using real video files."""

    def test_video_clipper_real_video_basic_clip(
        self, real_video_file, temp_output_dir
    ):
        """Test video_clipper with real video file - basic clipping."""
        output_path = os.path.join(temp_output_dir, "clipped_output.mp4")
        start_time = 1.0
        end_time = 3.0

        result = video_clipper(real_video_file, start_time, end_time, output_path)

        # Assertions
        assert os.path.exists(result), f"Clipped video file should exist at {result}"
        assert os.path.isabs(result)
        assert result == os.path.abspath(output_path)
        assert os.path.getsize(result) > 0, "Clipped video should have content"

    def test_video_clipper_real_video_tuple_input(
        self, real_video_file, temp_output_dir
    ):
        """Test video_clipper with real video file using tuple input (Gradio format)."""
        output_path = os.path.join(temp_output_dir, "clipped_tuple.mp4")
        video_input = (real_video_file, "subtitle.srt")
        start_time = 0.5
        end_time = 2.5

        result = video_clipper(video_input, start_time, end_time, output_path)

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_video_clipper_real_video_auto_output_path(self, real_video_file):
        """Test video_clipper with real video file - auto-generated output path."""
        start_time = 2.0
        end_time = 4.0

        result = video_clipper(real_video_file, start_time, end_time)

        assert os.path.exists(result)
        assert os.path.isabs(result)
        assert os.path.getsize(result) > 0
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_video_clipper_real_video_short_clip(
        self, real_video_file, temp_output_dir
    ):
        """Test video_clipper with real video file - very short clip."""
        output_path = os.path.join(temp_output_dir, "short_clip.mp4")
        start_time = 0.0
        end_time = 0.5  # Half second clip

        result = video_clipper(real_video_file, start_time, end_time, output_path)

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_video_clipper_real_video_validation(self, real_video_file):
        """Test video_clipper validation with real video file."""
        from moviepy import VideoFileClip

        # Get actual video duration
        with VideoFileClip(real_video_file) as video:
            actual_duration = video.duration

        # Test with invalid start time (exceeds duration)
        with pytest.raises(Exception) as exc_info:
            video_clipper(real_video_file, actual_duration + 1.0, actual_duration + 2.0)

        assert "exceeds video duration" in str(exc_info.value)

    def test_video_clipper_real_video_end_time_clamping(
        self, real_video_file, temp_output_dir
    ):
        """Test video_clipper clamps end_time to video duration with real video."""
        from moviepy import VideoFileClip

        # Get actual video duration
        with VideoFileClip(real_video_file) as video:
            actual_duration = video.duration

        output_path = os.path.join(temp_output_dir, "clamped_output.mp4")
        start_time = max(0.0, actual_duration - 2.0)  # Start 2 seconds before end
        end_time = actual_duration + 10.0  # End time exceeds duration

        # Should not raise error, should clamp end_time
        result = video_clipper(real_video_file, start_time, end_time, output_path)

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

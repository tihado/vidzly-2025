"""
Unit tests for frame_extractor tool.
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch
import numpy as np
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.frame_extractor import frame_extractor


class TestFrameExtractor:
    """Test cases for frame_extractor main function."""

    def test_frame_extractor_with_api_key(self, temp_video_file, temp_output_dir):
        """Test frame_extractor with API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite, \
             patch("app.tools.frame_extractor.genai.Client") as mock_client, \
             patch("app.tools.frame_extractor.genai.types.Blob") as mock_blob, \
             patch("app.tools.frame_extractor.genai.types.VideoMetadata") as mock_video_metadata, \
             patch("app.tools.frame_extractor.genai.types.Part") as mock_part, \
             patch("app.tools.frame_extractor.mimetypes.guess_type") as mock_guess_type, \
             patch("builtins.open", create=True) as mock_open:
            
            # Setup video capture mock (called twice: once for metadata, once for frame extraction)
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,  # FPS
                7: 900,   # Frame count
            }.get(prop, 0)
            mock_cap.read.return_value = (True, np.ones((100, 100, 3), dtype=np.uint8) * 150)
            mock_cap.set.return_value = True
            mock_capture.return_value = mock_cap
            
            # Setup file open mock for reading video file
            mock_file = Mock()
            mock_file.read.return_value = b'video file data'
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            mock_open.return_value = mock_file
            
            # Setup genai types mocks
            mock_blob_instance = Mock()
            mock_video_metadata_instance = Mock()
            mock_part_instance = Mock()
            mock_blob.return_value = mock_blob_instance
            mock_video_metadata.return_value = mock_video_metadata_instance
            mock_part.return_value = mock_part_instance
            
            # Setup mimetypes mock
            mock_guess_type.return_value = ("video/mp4", None)
            
            # Setup Gemini API mock - returns timestamp
            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.text = "15.5"  # Return timestamp in seconds
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client
            
            result = frame_extractor(temp_video_file)
            
            assert isinstance(result, str)
            # VideoCapture should be called twice: once for metadata, once for frame extraction
            assert mock_capture.call_count == 2
            # imwrite is called once for the final output frame
            assert mock_imwrite.call_count == 1
            
            # Cleanup frames directory if it was created
            import shutil
            frames_dir = os.path.join(os.path.dirname(temp_video_file), "frames")
            if os.path.exists(frames_dir):
                shutil.rmtree(frames_dir)

    def test_frame_extractor_without_api_key(self, temp_video_file):
        """Test frame_extractor raises error without API key."""
        with patch.dict(os.environ, {}, clear=True), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            
            # Mock video capture to allow metadata extraction, so we reach the API key check
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,  # FPS
                7: 900,   # Frame count
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file)
            
            assert "GOOGLE_API_KEY" in str(exc_info.value)

    def test_frame_extractor_invalid_input_format(self):
        """Test frame_extractor with invalid input format."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with pytest.raises(Exception) as exc_info:
                frame_extractor(123)
            
            assert "Invalid video input format" in str(exc_info.value)

    def test_frame_extractor_file_not_found(self):
        """Test frame_extractor with non-existent file."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with pytest.raises(Exception) as exc_info:
                frame_extractor("/nonexistent/video.mp4")
            
            assert "Video file not found" in str(exc_info.value)

    def test_frame_extractor_cannot_open_video(self, temp_video_file):
        """Test frame_extractor when video cannot be opened."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file)
            
            assert "Could not open video file" in str(exc_info.value)

    def test_frame_extractor_zero_duration(self, temp_video_file):
        """Test frame_extractor with zero duration video."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 0.0,  # Zero FPS
                7: 0,    # Zero frames
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file)
            
            assert "zero duration" in str(exc_info.value).lower()
            mock_cap.release.assert_called_once()


class TestFrameExtractorIntegration:
    """Integration tests for frame_extractor using real video files."""

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set, skipping AI test"
    )
    def test_frame_extractor_real_video_ai(self, real_video_file):
        """Test frame_extractor with real video file using AI."""
        result = frame_extractor(real_video_file)
        
        assert os.path.exists(result)
        assert os.path.isabs(result)
        assert result.endswith(".png")
        assert os.path.getsize(result) > 0
        # Cleanup
        if os.path.exists(result):
            os.remove(result)
            frames_dir = os.path.dirname(result)
            if os.path.exists(frames_dir) and not os.listdir(frames_dir):
                os.rmdir(frames_dir)

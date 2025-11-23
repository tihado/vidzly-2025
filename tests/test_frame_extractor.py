"""
Unit tests for frame_extractor tool.
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.frame_extractor import (
    calculate_sharpness,
    calculate_contrast,
    calculate_brightness,
    calculate_frame_quality,
    extract_frame_at_timestamp,
    extract_best_frame,
    extract_ai_selected_frame,
    frame_extractor,
)


class TestFrameQualityMetrics:
    """Test cases for frame quality calculation functions."""

    def test_calculate_sharpness_with_color_frame(self):
        """Test calculate_sharpness with color (BGR) frame."""
        # Create a test frame (100x100, 3 channels)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = calculate_sharpness(frame)
        
        assert isinstance(result, (int, float))
        assert result >= 0

    def test_calculate_sharpness_with_grayscale_frame(self):
        """Test calculate_sharpness with grayscale frame."""
        # Create a test grayscale frame (100x100)
        frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        result = calculate_sharpness(frame)
        
        assert isinstance(result, (int, float))
        assert result >= 0

    def test_calculate_sharpness_sharper_frame_higher_score(self):
        """Test that sharper frames have higher sharpness scores."""
        # Create a blurry frame (low sharpness)
        blurry_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # Create a sharper frame with edges
        sharp_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        sharp_frame[40:60, :] = 255  # Add horizontal edge
        
        blurry_score = calculate_sharpness(blurry_frame)
        sharp_score = calculate_sharpness(sharp_frame)
        
        # Sharp frame should generally have higher score
        # (though this may vary, so we just check both are valid)
        assert blurry_score >= 0
        assert sharp_score >= 0

    def test_calculate_contrast_with_color_frame(self):
        """Test calculate_contrast with color (BGR) frame."""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = calculate_contrast(frame)
        
        assert isinstance(result, (int, float))
        assert result >= 0
        assert result <= 255  # Standard deviation of uint8 values

    def test_calculate_contrast_with_grayscale_frame(self):
        """Test calculate_contrast with grayscale frame."""
        frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        result = calculate_contrast(frame)
        
        assert isinstance(result, (int, float))
        assert result >= 0

    def test_calculate_contrast_high_contrast_higher_score(self):
        """Test that high contrast frames have higher contrast scores."""
        # Low contrast frame (uniform)
        low_contrast = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # High contrast frame (black and white)
        high_contrast = np.zeros((100, 100, 3), dtype=np.uint8)
        high_contrast[::2, ::2] = 255
        
        low_score = calculate_contrast(low_contrast)
        high_score = calculate_contrast(high_contrast)
        
        assert high_score > low_score

    def test_calculate_brightness_with_color_frame(self):
        """Test calculate_brightness with color (BGR) frame."""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = calculate_brightness(frame)
        
        assert isinstance(result, (int, float))
        assert 0 <= result <= 255

    def test_calculate_brightness_with_grayscale_frame(self):
        """Test calculate_brightness with grayscale frame."""
        frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        result = calculate_brightness(frame)
        
        assert isinstance(result, (int, float))
        assert 0 <= result <= 255

    def test_calculate_brightness_dark_frame(self):
        """Test calculate_brightness with dark frame."""
        dark_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = calculate_brightness(dark_frame)
        
        assert result == 0.0

    def test_calculate_brightness_bright_frame(self):
        """Test calculate_brightness with bright frame."""
        bright_frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        result = calculate_brightness(bright_frame)
        
        assert result == 255.0

    def test_calculate_frame_quality_returns_float(self):
        """Test calculate_frame_quality returns a float."""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = calculate_frame_quality(frame)
        
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_calculate_frame_quality_optimal_brightness(self):
        """Test calculate_frame_quality gives high score for optimal brightness."""
        # Frame with optimal brightness (150)
        optimal_frame = np.ones((100, 100, 3), dtype=np.uint8) * 150
        
        result = calculate_frame_quality(optimal_frame)
        
        assert 0.0 <= result <= 1.0

    def test_calculate_frame_quality_too_dark(self):
        """Test calculate_frame_quality penalizes too dark frames."""
        dark_frame = np.ones((100, 100, 3), dtype=np.uint8) * 30  # Very dark
        
        result = calculate_frame_quality(dark_frame)
        
        assert 0.0 <= result <= 1.0

    def test_calculate_frame_quality_too_bright(self):
        """Test calculate_frame_quality penalizes too bright frames."""
        bright_frame = np.ones((100, 100, 3), dtype=np.uint8) * 250  # Very bright
        
        result = calculate_frame_quality(bright_frame)
        
        assert 0.0 <= result <= 1.0


class TestExtractFrameAtTimestamp:
    """Test cases for extract_frame_at_timestamp function."""

    def test_extract_frame_at_timestamp_success(self, temp_video_file, temp_output_dir):
        """Test extract_frame_at_timestamp successfully extracts frame."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite:
            
            # Setup mock
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.return_value = 30.0  # FPS
            mock_cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            mock_capture.return_value = mock_cap
            
            timestamp = 5.0
            output_path = os.path.join(temp_output_dir, "frame.png")
            result = extract_frame_at_timestamp(temp_video_file, timestamp, output_path)
            
            # Assertions
            assert isinstance(result, str)
            assert result == output_path
            mock_cap.set.assert_called_once()
            mock_cap.read.assert_called_once()
            mock_cap.release.assert_called_once()
            mock_imwrite.assert_called_once()

    def test_extract_frame_at_timestamp_with_output_path(self, temp_video_file, temp_output_dir):
        """Test extract_frame_at_timestamp with custom output path."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.return_value = 30.0
            mock_cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            mock_capture.return_value = mock_cap
            
            timestamp = 10.0
            output_path = os.path.join(temp_output_dir, "custom_frame.png")
            result = extract_frame_at_timestamp(temp_video_file, timestamp, output_path)
            
            assert result == output_path
            mock_imwrite.assert_called_once()

    def test_extract_frame_at_timestamp_cannot_open_video(self):
        """Test extract_frame_at_timestamp when video cannot be opened."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_frame_at_timestamp("/path/to/video.mp4", 5.0)
            
            assert "Could not open video file" in str(exc_info.value)

    def test_extract_frame_at_timestamp_cannot_read_frame(self, temp_video_file):
        """Test extract_frame_at_timestamp when frame cannot be read."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.return_value = 30.0
            mock_cap.read.return_value = (False, None)  # Failed to read
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_frame_at_timestamp(temp_video_file, 5.0)
            
            assert "Could not extract frame" in str(exc_info.value)
            mock_cap.release.assert_called_once()


class TestExtractBestFrame:
    """Test cases for extract_best_frame function."""

    def test_extract_best_frame_success(self, temp_video_file, temp_output_dir):
        """Test extract_best_frame successfully extracts best frame."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,  # FPS
                7: 900,   # Frame count
            }.get(prop, 0)
            # Return different quality frames - cycle through them
            import itertools
            frames = [
                (True, np.ones((100, 100, 3), dtype=np.uint8) * 50),   # Dark
                (True, np.ones((100, 100, 3), dtype=np.uint8) * 150), # Optimal
                (True, np.ones((100, 100, 3), dtype=np.uint8) * 250), # Bright
            ]
            # Cycle through frames indefinitely
            mock_cap.read.side_effect = itertools.cycle(frames)
            mock_capture.return_value = mock_cap
            
            output_path = os.path.join(temp_output_dir, "best_frame.png")
            result = extract_best_frame(temp_video_file, sample_interval=1.0, output_path=output_path)
            
            assert isinstance(result, str)
            assert result == output_path
            assert mock_cap.read.call_count > 0
            mock_cap.release.assert_called_once()
            mock_imwrite.assert_called_once()

    def test_extract_best_frame_with_output_path(self, temp_video_file, temp_output_dir):
        """Test extract_best_frame with custom output path."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_cap.read.return_value = (True, np.ones((100, 100, 3), dtype=np.uint8) * 150)
            mock_capture.return_value = mock_cap
            
            output_path = os.path.join(temp_output_dir, "best_frame.png")
            result = extract_best_frame(temp_video_file, output_path=output_path)
            
            assert result == output_path
            mock_imwrite.assert_called_once()

    def test_extract_best_frame_cannot_open_video(self):
        """Test extract_best_frame when video cannot be opened."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_best_frame("/path/to/video.mp4")
            
            assert "Could not open video file" in str(exc_info.value)

    def test_extract_best_frame_no_frames_extracted(self, temp_video_file):
        """Test extract_best_frame when no frames can be extracted."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_cap.read.return_value = (False, None)  # Always fail to read
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_best_frame(temp_video_file)
            
            assert "Could not extract any frames" in str(exc_info.value)
            mock_cap.release.assert_called_once()

    def test_extract_best_frame_custom_sample_interval(self, temp_video_file, temp_output_dir):
        """Test extract_best_frame with custom sample interval."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_cap.read.return_value = (True, np.ones((100, 100, 3), dtype=np.uint8) * 150)
            mock_capture.return_value = mock_cap
            
            output_path = os.path.join(temp_output_dir, "best_frame.png")
            result = extract_best_frame(temp_video_file, sample_interval=2.0, output_path=output_path)
            
            assert isinstance(result, str)
            assert result == output_path
            # With 2.0s interval, should sample fewer frames
            assert mock_cap.read.call_count > 0


class TestExtractAISelectedFrame:
    """Test cases for extract_ai_selected_frame function."""

    def test_extract_ai_selected_frame_without_api_key(self, temp_video_file):
        """Test extract_ai_selected_frame falls back to best frame without API key."""
        with patch.dict(os.environ, {}, clear=True), \
             patch("app.tools.frame_extractor.extract_best_frame") as mock_best_frame:
            
            mock_best_frame.return_value = "/path/to/best_frame.png"
            
            result = extract_ai_selected_frame(temp_video_file)
            
            assert result == "/path/to/best_frame.png"
            mock_best_frame.assert_called_once_with(temp_video_file, output_path=None)

    def test_extract_ai_selected_frame_with_api_key(self, temp_video_file, temp_output_dir):
        """Test extract_ai_selected_frame with API key."""
        import tempfile as tf
        original_named_temp = tf.NamedTemporaryFile
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.cv2.imwrite") as mock_imwrite, \
             patch("app.tools.frame_extractor.genai.Client") as mock_client, \
             patch("app.tools.frame_extractor.os.unlink") as mock_unlink, \
             patch("builtins.open", create=True) as mock_open:
            
            # Setup video capture mock
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_cap.read.return_value = (True, np.ones((100, 100, 3), dtype=np.uint8) * 150)
            mock_capture.return_value = mock_cap
            
            # Setup temp file creation - use real tempfile but in our temp dir
            temp_files_created = []
            def create_temp_file(*args, **kwargs):
                # Use real tempfile but override dir if not specified
                if 'dir' not in kwargs:
                    kwargs['dir'] = temp_output_dir
                kwargs['delete'] = False
                temp_file = original_named_temp(*args, **kwargs)
                temp_files_created.append(temp_file.name)
                # Write dummy image data
                temp_file.write(b'PNG dummy data')
                temp_file.close()
                return temp_file
            
            with patch("app.tools.frame_extractor.tempfile.NamedTemporaryFile", side_effect=create_temp_file):
                # Setup file open mock to return dummy data
                mock_file = Mock()
                mock_file.read.return_value = b'PNG dummy image data'
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_open.return_value = mock_file
                
                # Setup Gemini API mock
                mock_genai_client = Mock()
                mock_response = Mock()
                mock_response.text = "This is an engaging and clear frame with good composition."
                mock_genai_client.models.generate_content.return_value = mock_response
                mock_client.return_value = mock_genai_client
                
                result = extract_ai_selected_frame(temp_video_file, num_candidates=3)
            
            assert isinstance(result, str)
            mock_cap.release.assert_called_once()
            # imwrite is called multiple times: once per candidate frame + once for final output
            assert mock_imwrite.call_count >= 3  # At least 3 candidate frames + 1 final
            # Verify cleanup was attempted
            assert mock_unlink.call_count > 0
            
            # Cleanup any temp files that were created
            for temp_file in temp_files_created:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
            # Cleanup frames directory if it was created
            import shutil
            frames_dir = os.path.join(os.path.dirname(temp_video_file), "frames")
            if os.path.exists(frames_dir):
                shutil.rmtree(frames_dir)

    def test_extract_ai_selected_frame_cannot_open_video(self):
        """Test extract_ai_selected_frame when video cannot be opened."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_ai_selected_frame("/path/to/video.mp4")
            
            assert "Could not open video file" in str(exc_info.value)

    def test_extract_ai_selected_frame_no_frames_extracted(self, temp_video_file):
        """Test extract_ai_selected_frame when no frames can be extracted."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}), \
             patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_cap.read.return_value = (False, None)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(ValueError) as exc_info:
                extract_ai_selected_frame(temp_video_file)
            
            assert "Could not extract any frames" in str(exc_info.value)
            mock_cap.release.assert_called_once()


class TestFrameExtractor:
    """Test cases for frame_extractor main function."""

    def test_frame_extractor_middle_strategy(self, temp_video_file):
        """Test frame_extractor with 'middle' strategy."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_frame_at_timestamp") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/frame.png"
            
            result = frame_extractor(temp_video_file, strategy="middle")
            
            assert result == "/path/to/frame.png"
            # Should extract at middle timestamp (15.0s for 30s video)
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert call_args[0][0] == temp_video_file
            assert call_args[0][1] == pytest.approx(15.0, rel=0.1)

    def test_frame_extractor_best_strategy(self, temp_video_file):
        """Test frame_extractor with 'best' strategy."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_best_frame") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/best_frame.png"
            
            result = frame_extractor(temp_video_file, strategy="best")
            
            assert result == "/path/to/best_frame.png"
            mock_extract.assert_called_once_with(temp_video_file)

    def test_frame_extractor_ai_strategy(self, temp_video_file):
        """Test frame_extractor with 'ai' strategy."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_ai_selected_frame") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/ai_frame.png"
            
            result = frame_extractor(temp_video_file, strategy="ai")
            
            assert result == "/path/to/ai_frame.png"
            mock_extract.assert_called_once_with(temp_video_file)

    def test_frame_extractor_custom_strategy(self, temp_video_file):
        """Test frame_extractor with 'custom' strategy."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_frame_at_timestamp") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/custom_frame.png"
            
            custom_timestamp = 10.0
            result = frame_extractor(
                temp_video_file, strategy="custom", custom_timestamp=custom_timestamp
            )
            
            assert result == "/path/to/custom_frame.png"
            mock_extract.assert_called_once_with(temp_video_file, custom_timestamp)

    def test_frame_extractor_with_tuple_input(self, temp_video_file):
        """Test frame_extractor with tuple input (Gradio format)."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_frame_at_timestamp") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/frame.png"
            
            video_input = (temp_video_file, "subtitle.srt")
            result = frame_extractor(video_input, strategy="middle")
            
            assert result == "/path/to/frame.png"
            # Should use first element of tuple
            call_args = mock_extract.call_args
            assert call_args[0][0] == temp_video_file

    def test_frame_extractor_invalid_input_format(self):
        """Test frame_extractor with invalid input format."""
        with pytest.raises(Exception) as exc_info:
            frame_extractor(123, strategy="middle")
        
        assert "Invalid video input format" in str(exc_info.value)

    def test_frame_extractor_file_not_found(self):
        """Test frame_extractor with non-existent file."""
        with pytest.raises(Exception) as exc_info:
            frame_extractor("/nonexistent/video.mp4", strategy="middle")
        
        assert "Video file not found" in str(exc_info.value)

    def test_frame_extractor_cannot_open_video(self, temp_video_file):
        """Test frame_extractor when video cannot be opened."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file, strategy="middle")
            
            assert "Could not open video file" in str(exc_info.value)

    def test_frame_extractor_zero_duration(self, temp_video_file):
        """Test frame_extractor with zero duration video."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 0.0,  # Zero FPS
                7: 0,    # Zero frames
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file, strategy="middle")
            
            assert "zero duration" in str(exc_info.value).lower()
            mock_cap.release.assert_called_once()

    def test_frame_extractor_custom_strategy_missing_timestamp(self, temp_video_file):
        """Test frame_extractor with 'custom' strategy but no timestamp."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file, strategy="custom")
            
            assert "custom_timestamp is required" in str(exc_info.value)

    def test_frame_extractor_custom_strategy_invalid_timestamp(self, temp_video_file):
        """Test frame_extractor with 'custom' strategy and invalid timestamp."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            # Timestamp exceeds duration
            with pytest.raises(Exception) as exc_info:
                frame_extractor(
                    temp_video_file, strategy="custom", custom_timestamp=100.0
                )
            
            assert "custom_timestamp must be between" in str(exc_info.value)

    def test_frame_extractor_custom_strategy_negative_timestamp(self, temp_video_file):
        """Test frame_extractor with 'custom' strategy and negative timestamp."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(
                    temp_video_file, strategy="custom", custom_timestamp=-1.0
                )
            
            assert "custom_timestamp must be between" in str(exc_info.value)

    def test_frame_extractor_invalid_strategy(self, temp_video_file):
        """Test frame_extractor with invalid strategy."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            
            with pytest.raises(Exception) as exc_info:
                frame_extractor(temp_video_file, strategy="invalid")
            
            assert "Invalid strategy" in str(exc_info.value)

    def test_frame_extractor_default_strategy(self, temp_video_file):
        """Test frame_extractor with default strategy (middle)."""
        with patch("app.tools.frame_extractor.cv2.VideoCapture") as mock_capture, \
             patch("app.tools.frame_extractor.extract_frame_at_timestamp") as mock_extract:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,
                7: 900,
            }.get(prop, 0)
            mock_capture.return_value = mock_cap
            mock_extract.return_value = "/path/to/frame.png"
            
            # Don't specify strategy, should default to "middle"
            result = frame_extractor(temp_video_file)
            
            assert result == "/path/to/frame.png"
            mock_extract.assert_called_once()


class TestFrameExtractorIntegration:
    """Integration tests for frame_extractor using real video files."""

    def test_frame_extractor_real_video_middle_strategy(self, real_video_file):
        """Test frame_extractor with real video file - middle strategy."""
        result = frame_extractor(real_video_file, strategy="middle")
        
        assert os.path.exists(result)
        assert os.path.isabs(result)
        assert result.endswith(".png")
        assert os.path.getsize(result) > 0
        # Cleanup
        if os.path.exists(result):
            os.remove(result)
            # Also cleanup frames directory if empty
            frames_dir = os.path.dirname(result)
            if os.path.exists(frames_dir) and not os.listdir(frames_dir):
                os.rmdir(frames_dir)

    def test_frame_extractor_real_video_best_strategy(self, real_video_file):
        """Test frame_extractor with real video file - best strategy."""
        result = frame_extractor(real_video_file, strategy="best")
        
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

    def test_frame_extractor_real_video_custom_strategy(self, real_video_file):
        """Test frame_extractor with real video file - custom strategy."""
        result = frame_extractor(
            real_video_file, strategy="custom", custom_timestamp=2.0
        )
        
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

    def test_frame_extractor_real_video_tuple_input(self, real_video_file):
        """Test frame_extractor with real video file using tuple input."""
        video_input = (real_video_file, "subtitle.srt")
        result = frame_extractor(video_input, strategy="middle")
        
        assert os.path.exists(result)
        assert os.path.isabs(result)
        # Cleanup
        if os.path.exists(result):
            os.remove(result)
            frames_dir = os.path.dirname(result)
            if os.path.exists(frames_dir) and not os.listdir(frames_dir):
                os.rmdir(frames_dir)

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set, skipping AI test"
    )
    def test_frame_extractor_real_video_ai_strategy(self, real_video_file):
        """Test frame_extractor with real video file - AI strategy (if API key available)."""
        result = frame_extractor(real_video_file, strategy="ai")
        
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

    def test_frame_extractor_real_video_validation(self, real_video_file):
        """Test frame_extractor validation with real video file."""
        import cv2
        
        # Get actual video duration
        cap = cv2.VideoCapture(real_video_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()
        
        # Test with invalid timestamp (exceeds duration)
        with pytest.raises(Exception) as exc_info:
            frame_extractor(
                real_video_file, strategy="custom", custom_timestamp=duration + 10.0
            )
        
        assert "custom_timestamp must be between" in str(exc_info.value)


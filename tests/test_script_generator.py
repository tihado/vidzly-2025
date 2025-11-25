"""
Unit tests for script_generator tool.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.script_generator import script_generator


class TestScriptGenerator:
    """Test cases for script_generator function."""

    def test_script_generator_with_multiple_videos(self, temp_video_file):
        """Test script_generator with multiple video inputs."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = """Here's a comprehensive video script:

```json
{
  "concept": "Energetic travel montage",
  "target_duration": 30.0,
  "total_duration": 30.0,
  "scenes": [
    {
      "scene_id": 1,
      "source_video": 0,
      "start_time": 0.0,
      "end_time": 10.0,
      "duration": 10.0,
      "description": "Opening scene",
      "transition_in": "fade",
      "transition_out": "crossfade"
    }
  ],
  "audio": {
    "mood": "energetic",
    "style": "upbeat",
    "bpm": 120,
    "volume": 0.7
  },
  "text_overlays": [],
  "visual_effects": ["color_grading"],
  "call_to_action": "Subscribe for more"
}
```

This is a narrative description of the script."""
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            video_inputs = [temp_video_file, temp_video_file]

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator(
                    video_inputs, user_prompt="Create an energetic video"
                )

            result_json = json.loads(result)
            assert "videos_analyzed" in result_json
            assert "script_narrative" in result_json
            assert len(result_json["videos_analyzed"]) == 2

    def test_script_generator_without_prompt(self, temp_video_file):
        """Test script_generator without user prompt."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = "Auto-generated script based on video analysis."
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            video_inputs = [temp_video_file]

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator(video_inputs)

            result_json = json.loads(result)
            assert "videos_analyzed" in result_json
            assert "script_narrative" in result_json
            assert result_json["user_prompt"] == "Auto-generated based on materials"

    def test_script_generator_with_string_input(self, temp_video_file):
        """Test script_generator with single string video input."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = "Generated script."
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator(temp_video_file)

            result_json = json.loads(result)
            assert "videos_analyzed" in result_json
            assert len(result_json["videos_analyzed"]) == 1

    def test_script_generator_with_tuple_input(self, temp_video_file):
        """Test script_generator with tuple input (Gradio format)."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = "Generated script."
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            video_input = (temp_video_file, "subtitle.srt")

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator(video_input)

            result_json = json.loads(result)
            assert "videos_analyzed" in result_json

    def test_script_generator_with_empty_input(self):
        """Test script_generator with no video input."""
        result = script_generator([])
        result_json = json.loads(result)
        assert "error" in result_json
        assert result_json["error"] == "No video files provided"

    def test_script_generator_with_nonexistent_file(self):
        """Test script_generator with nonexistent video file."""
        result = script_generator(["/nonexistent/video.mp4"])
        result_json = json.loads(result)
        assert "error" in result_json
        assert "not found" in result_json["error"]

    def test_script_generator_without_api_key(self, temp_video_file):
        """Test script_generator without GOOGLE_API_KEY."""
        with patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture:
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
                result = script_generator([temp_video_file])

            result_json = json.loads(result)
            assert "error" in result_json
            assert "GOOGLE_API_KEY" in result_json["error"]
            assert "videos_analyzed" in result_json

    def test_script_generator_with_invalid_video(self, temp_video_file):
        """Test script_generator with video that cannot be opened."""
        with patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_capture.return_value = mock_cap

            result = script_generator([temp_video_file])
            result_json = json.loads(result)
            assert "error" in result_json
            assert "Could not open video file" in result_json["error"]

    def test_script_generator_structured_script_parsing(self, temp_video_file):
        """Test that structured JSON is properly extracted and parsed."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = """Here's the script:

```json
{
  "concept": "Test concept",
  "target_duration": 30.0,
  "scenes": []
}
```

Narrative description."""
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator([temp_video_file])

            result_json = json.loads(result)
            assert "structured_script" in result_json
            assert result_json["structured_script"]["concept"] == "Test concept"
            assert result_json["structured_script"]["target_duration"] == 30.0

    def test_script_generator_with_custom_prompt(self, temp_video_file):
        """Test script_generator with custom user prompt."""
        with (
            patch("app.tools.script_generator.cv2.VideoCapture") as mock_capture,
            patch("app.tools.script_generator.genai.Client") as mock_client,
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
            mock_response.text = "Custom prompt response."
            mock_genai_client.models.generate_content.return_value = mock_response
            mock_client.return_value = mock_genai_client

            custom_prompt = "Create a dramatic product reveal"

            with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
                result = script_generator([temp_video_file], user_prompt=custom_prompt)

            result_json = json.loads(result)
            assert result_json["user_prompt"] == custom_prompt
            assert "script_narrative" in result_json

"""
Unit tests for video_composer tool.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.video_composer import video_composer


class TestVideoComposer:
    """Test cases for video_composer function."""

    @pytest.fixture
    def sample_script(self):
        """Sample script JSON for testing."""
        return {
            "total_duration": 30.0,
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video by index
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "duration": 5.0,
                    "transition_in": "fade",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 2,
                    "source_video": 1,  # Reference second video by index
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration": 5.0,
                    "transition_in": "crossfade",
                    "transition_out": "cut",
                },
            ],
            "music": {"mood": "energetic", "bpm": 120, "volume": 0.5},
        }

    @pytest.fixture
    def sample_script_json(self, sample_script):
        """Sample script as JSON string."""
        return json.dumps(sample_script)

    def test_video_composer_missing_scenes_key(self, temp_output_dir):
        """Test video_composer with script missing 'scenes' key."""
        invalid_script = {"total_duration": 30.0}
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        with pytest.raises(Exception) as exc_info:
            video_composer(invalid_script, video_clips=[clip1_path])

        assert "Script must contain a 'scenes' key" in str(exc_info.value)

    def test_video_composer_empty_scenes(self, temp_output_dir):
        """Test video_composer with empty scenes list."""
        invalid_script = {"scenes": []}
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        with pytest.raises(Exception) as exc_info:
            video_composer(invalid_script, video_clips=[clip1_path])

        assert "Script must contain at least one scene" in str(exc_info.value)

    def test_video_composer_invalid_source_video_index(
        self, sample_script, temp_output_dir
    ):
        """Test video_composer with invalid source_video index."""
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        # Update script to use index 2 (out of range for single video)
        sample_script["scenes"][0]["source_video"] = 2

        with pytest.raises(Exception) as exc_info:
            video_composer(sample_script, video_clips=[clip1_path])

        assert "source_video index" in str(exc_info.value)
        assert "out of range" in str(exc_info.value)

    def test_video_composer_missing_source_video(self, temp_output_dir):
        """Test video_composer with scene missing source_video."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "start_time": 0.0,
                    "end_time": 5.0,
                }
            ]
        }
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        with pytest.raises(Exception) as exc_info:
            video_composer(script, video_clips=[clip1_path])

        assert "missing 'source_video'" in str(exc_info.value)

    def test_video_composer_source_video_not_found(self, temp_output_dir):
        """Test video_composer with source_video filename not found in video_clips."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": "nonexistent.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                }
            ]
        }
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        with pytest.raises(Exception) as exc_info:
            video_composer(script, video_clips=[clip1_path])

        assert "source_video" in str(exc_info.value)
        assert "not found in video_clips" in str(exc_info.value)

    def test_video_composer_clip_not_found(self, sample_script, temp_output_dir):
        """Test video_composer with non-existent clip file in video_clips."""
        nonexistent_clip = os.path.join(temp_output_dir, "nonexistent.mp4")
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        Path(clip1_path).touch()

        with pytest.raises(Exception) as exc_info:
            video_composer(sample_script, video_clips=[clip1_path, nonexistent_clip])

        assert "Video clip not found" in str(exc_info.value)


class TestVideoComposerIntegration:
    """Integration tests for video_composer using real video files."""

    def test_video_composer_real_video_basic_composition(
        self, real_video_file, temp_output_dir
    ):
        """Test video_composer with real video file - basic composition."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video by index
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "duration": 2.0,
                    "transition_in": "cut",
                    "transition_out": "fade",
                },
                {
                    "scene_id": 2,
                    "source_video": 0,  # Same video, different time range
                    "start_time": 2.0,
                    "end_time": 4.0,
                    "duration": 2.0,
                    "transition_in": "fade",
                    "transition_out": "cut",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_output.mp4")

        result = video_composer(
            script, video_clips=[real_video_file], output_path=output_path
        )

        # Assertions
        assert os.path.exists(result), f"Composed video file should exist at {result}"
        assert os.path.isabs(result)
        assert result == os.path.abspath(output_path)
        assert os.path.getsize(result) > 0, "Composed video should have content"

    def test_video_composer_real_video_with_preclipped(
        self, real_video_file, temp_output_dir
    ):
        """Test video_composer with real video using pre-clipped clips."""
        from app.tools.video_clipper import video_clipper

        # Create pre-clipped videos
        clip1_path = os.path.join(temp_output_dir, "clip1.mp4")
        clip2_path = os.path.join(temp_output_dir, "clip2.mp4")

        video_clipper(real_video_file, 0.0, 2.0, clip1_path)
        video_clipper(real_video_file, 2.0, 4.0, clip2_path)

        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "transition_in": "cut",
                    "transition_out": "fade",
                },
                {
                    "scene_id": 2,
                    "source_video": 1,  # Reference second video
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "transition_in": "fade",
                    "transition_out": "cut",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_preclipped.mp4")

        result = video_composer(
            script,
            video_clips=[clip1_path, clip2_path],
            output_path=output_path,
        )

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_video_composer_real_video_crossfade(
        self, real_video_file, temp_output_dir
    ):
        """Test video_composer with real video using crossfade transitions."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video by index
                    "start_time": 0.0,
                    "end_time": 1.5,
                    "transition_in": "cut",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 2,
                    "source_video": 0,  # Same video, different time range
                    "start_time": 1.5,
                    "end_time": 3.0,
                    "transition_in": "crossfade",
                    "transition_out": "cut",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_crossfade.mp4")

        result = video_composer(
            script, video_clips=[real_video_file], output_path=output_path
        )

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_video_composer_multiple_source_videos(
        self, real_video_file, real_video_file_2, temp_output_dir
    ):
        """Test video_composer composing from multiple different source videos."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video by index
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "duration": 2.0,
                    "transition_in": "fade",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 2,
                    "source_video": 1,  # Reference second video by index
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "duration": 2.0,
                    "transition_in": "crossfade",
                    "transition_out": "fade",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_multiple_sources.mp4")

        result = video_composer(
            script,
            video_clips=[real_video_file, real_video_file_2],
            output_path=output_path,
        )

        assert os.path.exists(result)
        assert os.path.isabs(result)
        assert result == os.path.abspath(output_path)
        assert os.path.getsize(result) > 0

    def test_video_composer_real_video_with_second_file_preclipped(
        self, real_video_file, real_video_file_2, temp_output_dir
    ):
        """Test video_composer with clips from both video files."""
        from app.tools.video_clipper import video_clipper

        # Create pre-clipped videos from both sources
        clip1_path = os.path.join(temp_output_dir, "clip1_from_dodo1.mp4")
        clip2_path = os.path.join(temp_output_dir, "clip2_from_dodo2.mp4")

        video_clipper(real_video_file, 0.0, 2.0, clip1_path)
        video_clipper(real_video_file_2, 0.0, 2.0, clip2_path)

        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "transition_in": "cut",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 2,
                    "source_video": 1,  # Reference second video
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "transition_in": "crossfade",
                    "transition_out": "cut",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_two_sources.mp4")

        result = video_composer(
            script,
            video_clips=[clip1_path, clip2_path],
            output_path=output_path,
        )

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_video_composer_real_video_three_scenes_from_two_files(
        self, real_video_file, real_video_file_2, temp_output_dir
    ):
        """Test video_composer with three scenes from two different source videos."""
        script = {
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,  # Reference first video by index
                    "start_time": 0.0,
                    "end_time": 1.5,
                    "transition_in": "fade",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 2,
                    "source_video": 1,  # Reference second video by index
                    "start_time": 0.0,
                    "end_time": 1.5,
                    "transition_in": "crossfade",
                    "transition_out": "crossfade",
                },
                {
                    "scene_id": 3,
                    "source_video": 0,  # Reference first video again, different time range
                    "start_time": 1.5,
                    "end_time": 3.0,
                    "transition_in": "crossfade",
                    "transition_out": "fade",
                },
            ]
        }

        output_path = os.path.join(temp_output_dir, "composed_three_scenes.mp4")

        result = video_composer(
            script,
            video_clips=[real_video_file, real_video_file_2],
            output_path=output_path,
        )

        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

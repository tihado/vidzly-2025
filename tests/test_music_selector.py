"""
Unit tests for music_selector tool.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.tools.music_selector import music_selector


class TestMusicSelector:
    """Test cases for music_selector function."""

    def test_music_selector_basic(self, temp_output_dir):
        """Test music_selector with basic parameters."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            # Setup mock
            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic", target_duration=10.0, output_path=output_path
            )

            # Assertions
            assert os.path.isabs(result)
            assert result == os.path.abspath(output_path)
            assert os.path.exists(result)
            mock_elevenlabs_class.assert_called_once_with(api_key="test_key")
            mock_convert.assert_called_once()

            # Check API was called with correct parameters
            call_kwargs = mock_convert.call_args[1]
            assert "text" in call_kwargs
            assert "energetic" in call_kwargs["text"]
            assert call_kwargs["duration_seconds"] == 10.0
            assert call_kwargs["output_format"] == "mp3_44100_128"

    @pytest.mark.parametrize("mood_input,expected_moods", [
        ("energetic, calm, dramatic", ["energetic", "calm", "dramatic"]),
        (["fun", "professional"], ["fun", "professional"]),
    ])
    def test_music_selector_mood_formats(self, temp_output_dir, mood_input, expected_moods):
        """Test music_selector with different mood input formats."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood=mood_input,
                target_duration=15.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            for expected_mood in expected_moods:
                assert expected_mood in call_kwargs["text"]

    def test_music_selector_with_style(self, temp_output_dir):
        """Test music_selector with style parameter."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                style="cinematic",
                target_duration=25.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert "cinematic" in call_kwargs["text"]
            assert "style" in call_kwargs["text"]

    def test_music_selector_with_bpm(self, temp_output_dir):
        """Test music_selector with BPM parameter."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic", bpm=120, target_duration=15.0, output_path=output_path
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert "120" in call_kwargs["text"]
            assert "BPM" in call_kwargs["text"]

    def test_music_selector_with_looping(self, temp_output_dir):
        """Test music_selector with looping enabled."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                looping=True,
                target_duration=10.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert call_kwargs["loop"] is True

    def test_music_selector_with_prompt_influence(self, temp_output_dir):
        """Test music_selector with prompt_influence parameter."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                prompt_influence=0.7,
                target_duration=10.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert call_kwargs["prompt_influence"] == 0.7

    def test_music_selector_without_output_path(self, temp_output_dir):
        """Test music_selector generates output path when not provided."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            result = music_selector(mood="energetic", target_duration=10.0)

            assert os.path.isabs(result)
            assert os.path.exists(result)
            assert result.endswith(".mp3")
            # Should contain mood in filename
            assert "energetic" in os.path.basename(result).lower()

    def test_music_selector_duration_clamping_max(self, temp_output_dir):
        """Test music_selector clamps duration to maximum 30 seconds."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                target_duration=50.0,  # Exceeds max
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert call_kwargs["duration_seconds"] == 30.0

    def test_music_selector_prompt_influence_clamping(self, temp_output_dir):
        """Test music_selector clamps prompt_influence to 0-1 range."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")

            # Test with value > 1
            result = music_selector(
                mood="energetic",
                prompt_influence=2.0,
                target_duration=10.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert call_kwargs["prompt_influence"] == 1.0

            # Test with value < 0
            result = music_selector(
                mood="energetic",
                prompt_influence=-0.5,
                target_duration=10.0,
                output_path=output_path,
            )

            call_kwargs = mock_convert.call_args[1]
            assert call_kwargs["prompt_influence"] == 0.0

    def test_music_selector_empty_mood_defaults(self, temp_output_dir):
        """Test music_selector uses default mood when empty."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="", target_duration=10.0, output_path=output_path
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert "energetic" in call_kwargs["text"]

    def test_music_selector_with_sync_points(self, temp_output_dir):
        """Test music_selector with sync_points parameter."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                sync_points=[0.0, 5.0, 10.0],
                target_duration=10.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            assert "beat markers" in call_kwargs["text"]

    def test_music_selector_creates_output_directory(self, temp_output_dir):
        """Test music_selector creates output directory if it doesn't exist."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_dir = os.path.join(temp_output_dir, "nested", "path")
            output_path = os.path.join(output_dir, "test_sound.mp3")

            result = music_selector(
                mood="energetic", target_duration=10.0, output_path=output_path
            )

            assert os.path.exists(output_dir)
            assert os.path.exists(result)

    def test_music_selector_no_api_key(self):
        """Test music_selector raises error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                music_selector(mood="energetic", target_duration=10.0)

            assert "ELEVENLABS_API_KEY" in str(exc_info.value)

    def test_music_selector_elevenlabs_not_installed(self):
        """Test music_selector raises error when elevenlabs is not installed."""
        with patch("app.tools.music_selector.ElevenLabs", None), patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            with pytest.raises(Exception) as exc_info:
                music_selector(mood="energetic", target_duration=10.0)

            assert "elevenlabs package is not installed" in str(exc_info.value)

    def test_music_selector_api_error_handling(self, temp_output_dir):
        """Test music_selector handles API errors gracefully."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(side_effect=Exception("API Error"))
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            with pytest.raises(Exception) as exc_info:
                music_selector(
                    mood="energetic", target_duration=10.0, output_path=output_path
                )

            assert "Error generating sound effect" in str(exc_info.value)

    def test_music_selector_audio_data_bytes(self, temp_output_dir):
        """Test music_selector handles bytes audio data."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_bytes_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic", target_duration=10.0, output_path=output_path
            )

            assert os.path.exists(result)
            # Verify file was written
            with open(result, "rb") as f:
                assert f.read() == b"fake_audio_bytes_data"

    def test_music_selector_audio_data_iterable(self, temp_output_dir):
        """Test music_selector handles iterable audio data (generator/list)."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            # Return list of byte chunks
            mock_convert = Mock(return_value=[b"chunk1", b"chunk2", b"chunk3"])
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic", target_duration=10.0, output_path=output_path
            )

            assert os.path.exists(result)
            # Verify file contains all chunks
            with open(result, "rb") as f:
                content = f.read()
                assert b"chunk1" in content
                assert b"chunk2" in content
                assert b"chunk3" in content

    def test_music_selector_all_parameters(self, temp_output_dir):
        """Test music_selector with all parameters provided."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic, calm",
                style="cinematic",
                target_duration=25.0,
                bpm=120,
                sync_points=[0.0, 5.0, 10.0],
                looping=True,
                prompt_influence=0.5,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]

            # Verify all parameters are in the prompt or API call
            assert "energetic" in call_kwargs["text"]
            assert "calm" in call_kwargs["text"]
            assert "cinematic" in call_kwargs["text"]
            assert "120" in call_kwargs["text"]
            assert "beat markers" in call_kwargs["text"]
            assert call_kwargs["duration_seconds"] == 25.0
            assert call_kwargs["loop"] is True
            assert call_kwargs["prompt_influence"] == 0.5
            assert call_kwargs["output_format"] == "mp3_44100_128"

    def test_music_selector_looping_false(self, temp_output_dir):
        """Test music_selector with looping disabled."""
        with patch(
            "app.tools.music_selector.ElevenLabs"
        ) as mock_elevenlabs_class, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": "test_key"}
        ):

            mock_client = Mock()
            mock_text_to_sound = Mock()
            mock_convert = Mock(return_value=b"fake_audio_data")
            mock_text_to_sound.convert = mock_convert
            mock_client.text_to_sound_effects = mock_text_to_sound
            mock_elevenlabs_class.return_value = mock_client

            output_path = os.path.join(temp_output_dir, "test_sound.mp3")
            result = music_selector(
                mood="energetic",
                looping=False,
                target_duration=10.0,
                output_path=output_path,
            )

            assert os.path.exists(result)
            call_kwargs = mock_convert.call_args[1]
            # When looping is False, loop parameter should not be in the call
            # (or should be False if included)
            if "loop" in call_kwargs:
                assert call_kwargs["loop"] is False

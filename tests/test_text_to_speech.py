"""
Tests for the Text-to-Speech converter.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.app.tools.text_to_speech import text_to_speech_simple


class TestTextToSpeechSimple:
    """Test suite for the simple text-to-speech function using gTTS."""

    def test_basic_text_to_speech(self, tmp_path, monkeypatch):
        """Test basic text-to-speech conversion."""
        # Mock gTTS
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            # Change output directory to tmp_path
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hello, world!")

            # Verify gTTS was called correctly with default parameters
            mock_gtts_class.assert_called_once_with(
                text="Hello, world!", lang="en", slow=False, tld="com"
            )
            mock_tts.save.assert_called_once()
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_srt_subtitle_conversion(self, tmp_path, monkeypatch):
        """Test conversion of SRT subtitle format."""
        srt_content = """1
00:00:00,000 --> 00:00:03,500
Welcome to our video.

2
00:00:03,500 --> 00:00:07,000
Today we will learn something new."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(srt_content, format_type="srt")

            # Check that dialogues were combined
            call_args = mock_gtts_class.call_args
            combined_text = call_args[1]["text"]
            assert "Welcome to our video" in combined_text
            assert "Today we will learn" in combined_text
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_vtt_subtitle_conversion(self, tmp_path, monkeypatch):
        """Test conversion of VTT subtitle format."""
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:03.500
Hello world.

00:00:03.500 --> 00:00:07.000
Welcome to the tutorial."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(vtt_content, format_type="vtt")

            call_args = mock_gtts_class.call_args
            combined_text = call_args[1]["text"]
            assert "Hello world" in combined_text
            assert "Welcome to the tutorial" in combined_text
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_json_subtitle_conversion(self, tmp_path, monkeypatch):
        """Test conversion of JSON scenario format."""
        json_content = (
            '{"scenes": [{"dialogue": "First line"}, {"dialogue": "Second line"}]}'
        )

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(json_content, format_type="json")

            call_args = mock_gtts_class.call_args
            combined_text = call_args[1]["text"]
            assert "First line" in combined_text
            assert "Second line" in combined_text
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_auto_detect_srt(self, tmp_path, monkeypatch):
        """Test auto-detection of SRT format."""
        srt_content = """1
00:00:00,000 --> 00:00:03,500
Auto-detected SRT."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(srt_content, format_type="auto")

            mock_gtts_class.assert_called_once()
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_auto_detect_vtt(self, tmp_path, monkeypatch):
        """Test auto-detection of VTT format."""
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:03.500
Auto-detected VTT."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(vtt_content, format_type="auto")

            mock_gtts_class.assert_called_once()
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            text_to_speech_simple("")

    def test_whitespace_only_text_raises_error(self):
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            text_to_speech_simple("   ")

    def test_long_text_conversion(self, tmp_path, monkeypatch):
        """Test conversion of longer text."""
        long_text = "This is a longer piece of text. " * 10

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(long_text)

            mock_gtts_class.assert_called_once()
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_gtts_not_installed(self):
        """Test behavior when gTTS is not installed."""
        # Mock the entire import to fail
        with patch.dict("sys.modules", {"gtts": None}):
            with patch(
                "builtins.__import__", side_effect=ImportError("No module named 'gtts'")
            ):
                result = text_to_speech_simple("test")
                assert "Please install gTTS" in result

    def test_gtts_save_error(self):
        """Test handling of gTTS save errors."""
        mock_tts = Mock()
        mock_tts.save.side_effect = Exception("Save failed")
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            with pytest.raises(RuntimeError, match="Failed to generate audio"):
                text_to_speech_simple("test")

    def test_special_characters_in_text(self, tmp_path, monkeypatch):
        """Test text with special characters."""
        text_with_special = "Hello! How are you? I'm fine, thanks. 😊"

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(text_with_special)

            mock_gtts_class.assert_called_once_with(
                text=text_with_special, lang="en", slow=False, tld="com"
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_multiline_text(self, tmp_path, monkeypatch):
        """Test text with multiple lines."""
        multiline_text = """Line one.
Line two.
Line three."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(multiline_text)

            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_output_directory_creation(self, tmp_path, monkeypatch):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "outputs" / "audio"

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        def mock_path(path_str):
            if "outputs/audio" in str(path_str):
                return output_dir
            return Path(path_str)

        with patch("gtts.gTTS", mock_gtts_class):
            with patch("src.app.tools.text_to_speech.Path", side_effect=mock_path):
                text_to_speech_simple("test")

                # Verify directory would be created
                assert mock_tts.save.called

    def test_numbers_and_punctuation(self, tmp_path, monkeypatch):
        """Test text with numbers and various punctuation."""
        text = "The year is 2024! Count: 1, 2, 3... Ready? Let's go!"

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(text)

            mock_gtts_class.assert_called_once_with(
                text=text, lang="en", slow=False, tld="com"
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_male_voice_selection(self, tmp_path, monkeypatch):
        """Test male voice selection uses correct TLD."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hello", voice="male")

            mock_gtts_class.assert_called_once_with(
                text="Hello",
                lang="en",
                slow=False,
                tld="co.uk",  # British English for male voice
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_female_voice_selection(self, tmp_path, monkeypatch):
        """Test female voice selection uses correct TLD."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hello", voice="female")

            mock_gtts_class.assert_called_once_with(
                text="Hello",
                lang="en",
                slow=False,
                tld="com.au",  # Australian English for female voice
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_neutral_voice_selection(self, tmp_path, monkeypatch):
        """Test neutral voice selection uses correct TLD."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hello", voice="neutral")

            mock_gtts_class.assert_called_once_with(
                text="Hello",
                lang="en",
                slow=False,
                tld="com",  # US English for neutral voice
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_language_selection(self, tmp_path, monkeypatch):
        """Test different language selection."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hola", language="es")

            mock_gtts_class.assert_called_once_with(
                text="Hola", lang="es", slow=False, tld="com"
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_slow_speed_selection(self, tmp_path, monkeypatch):
        """Test slow speed selection."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple("Hello", speed="slow")

            mock_gtts_class.assert_called_once_with(
                text="Hello", lang="en", slow=True, tld="com"  # Slow speed enabled
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")

    def test_combined_options(self, tmp_path, monkeypatch):
        """Test combining voice, language, and speed options."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                "Bonjour", voice="female", language="fr", speed="slow"
            )

            mock_gtts_class.assert_called_once_with(
                text="Bonjour", lang="fr", slow=True, tld="com.au"
            )
            assert "generated_speech.mp3" in result or result.endswith(".mp3")


class TestTimedAudioSegments:
    """Test suite for timed audio segment generation."""

    def test_srt_timed_segments(self, tmp_path, monkeypatch):
        """Test generating timed audio segments from SRT format."""
        srt_content = """1
00:00:00,000 --> 00:00:03,500
Welcome to our video.

2
00:00:03,500 --> 00:00:07,000
Today we will learn something new."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                srt_content, format_type="srt", generate_segments=True
            )

            # Parse JSON result
            result_data = json.loads(result)

            # Verify structure
            assert "segments" in result_data
            assert len(result_data["segments"]) == 2

            # Check first segment
            segment1 = result_data["segments"][0]
            assert segment1["segment_id"] == 1
            assert segment1["start_time"] == 0.0
            assert segment1["end_time"] == 3.5
            assert segment1["duration"] == 3.5
            assert segment1["dialogue"] == "Welcome to our video."
            assert "segment_1.mp3" in segment1["audio_file"]

            # Check second segment
            segment2 = result_data["segments"][1]
            assert segment2["segment_id"] == 2
            assert segment2["start_time"] == 3.5
            assert segment2["end_time"] == 7.0
            assert segment2["duration"] == 3.5
            assert segment2["dialogue"] == "Today we will learn something new."
            assert "segment_2.mp3" in segment2["audio_file"]

            # Verify gTTS was called twice (once per segment)
            assert mock_gtts_class.call_count == 2

    def test_vtt_timed_segments(self, tmp_path, monkeypatch):
        """Test generating timed audio segments from VTT format."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:02.500
First subtitle here.

2
00:00:02.500 --> 00:00:05.000
Second subtitle here."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                vtt_content, format_type="vtt", generate_segments=True
            )

            # Parse JSON result
            result_data = json.loads(result)

            # Verify structure
            assert "segments" in result_data
            assert len(result_data["segments"]) == 2

            # Check timing
            segment1 = result_data["segments"][0]
            assert segment1["start_time"] == 0.0
            assert segment1["end_time"] == 2.5
            assert segment1["dialogue"] == "First subtitle here."

            segment2 = result_data["segments"][1]
            assert segment2["start_time"] == 2.5
            assert segment2["end_time"] == 5.0
            assert segment2["dialogue"] == "Second subtitle here."

    def test_json_timed_segments(self, tmp_path, monkeypatch):
        """Test generating timed audio segments from JSON format."""
        json_content = json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": 1,
                        "start_time": 0.0,
                        "end_time": 4.0,
                        "dialogue": "Scene one dialogue.",
                    },
                    {
                        "scene_id": 2,
                        "start_time": 4.0,
                        "duration": 3.0,
                        "dialogue": "Scene two dialogue.",
                    },
                ]
            }
        )

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                json_content, format_type="json", generate_segments=True
            )

            # Parse JSON result
            result_data = json.loads(result)

            # Verify structure
            assert "segments" in result_data
            assert len(result_data["segments"]) == 2

            # Check first segment
            segment1 = result_data["segments"][0]
            assert segment1["start_time"] == 0.0
            assert segment1["end_time"] == 4.0
            assert segment1["duration"] == 4.0
            assert segment1["dialogue"] == "Scene one dialogue."

            # Check second segment (end_time calculated from duration)
            segment2 = result_data["segments"][1]
            assert segment2["start_time"] == 4.0
            assert segment2["end_time"] == 7.0
            assert segment2["duration"] == 3.0
            assert segment2["dialogue"] == "Scene two dialogue."

    def test_auto_detect_srt_with_segments(self, tmp_path, monkeypatch):
        """Test auto-detection of SRT format with segment generation."""
        srt_content = """1
00:00:00,000 --> 00:00:02,000
Auto-detected SRT."""

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                srt_content, format_type="auto", generate_segments=True
            )

            # Parse JSON result
            result_data = json.loads(result)

            # Verify auto-detection worked
            assert "segments" in result_data
            assert len(result_data["segments"]) == 1
            assert result_data["segments"][0]["dialogue"] == "Auto-detected SRT."

    def test_plain_text_with_segments_returns_single_file(self, tmp_path, monkeypatch):
        """Test that plain text with generate_segments=True returns single file path."""
        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                "Plain text", format_type="text", generate_segments=True
            )

            # Plain text should return file path, not JSON
            assert "generated_speech.mp3" in result or result.endswith(".mp3")
            assert not result.startswith("{")

    def test_empty_subtitle_segments(self, tmp_path, monkeypatch):
        """Test handling of empty dialogue in timed segments (uses placeholder)."""
        json_content = json.dumps(
            {
                "scenes": [
                    {"scene_id": 1, "start_time": 0.0, "end_time": 2.0, "dialogue": ""},
                    {
                        "scene_id": 2,
                        "start_time": 2.0,
                        "end_time": 4.0,
                        "dialogue": "Valid dialogue",
                    },
                ]
            }
        )

        mock_tts = Mock()
        mock_gtts_class = Mock(return_value=mock_tts)

        with patch("gtts.gTTS", mock_gtts_class):
            monkeypatch.setattr(
                "src.app.tools.text_to_speech.Path",
                lambda x: tmp_path / x if "outputs/audio" in x else Path(x),
            )

            result = text_to_speech_simple(
                json_content, format_type="json", generate_segments=True
            )

            # Parse JSON result
            result_data = json.loads(result)

            # Both segments should be generated (empty dialogue gets placeholder)
            assert len(result_data["segments"]) == 2
            assert (
                result_data["segments"][0]["dialogue"] == "Scene 1"
            )  # Placeholder for empty dialogue
            assert result_data["segments"][1]["dialogue"] == "Valid dialogue"

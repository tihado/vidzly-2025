import os
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from elevenlabs import ElevenLabs
except ImportError:
    ElevenLabs = None


def music_selector(
    mood: Union[str, List[str]] = "energetic",
    style: Optional[str] = None,
    target_duration: float = 30.0,
    bpm: Optional[int] = None,
    looping: bool = True,
    prompt_influence: float = 0.3,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate appropriate background sound effects based on mood/style from script.
    Uses ElevenLabs API to generate sound effects that match the video's mood and style.

    Args:
        mood: Mood tags (str or list of str) describing the desired mood.
              Can be comma-separated string or list (e.g., "energetic", "calm, dramatic, fun")
        style: Optional style description (e.g., "cinematic", "modern", "retro")
        target_duration: Target duration in seconds (default: 30.0, max: 30.0 for ElevenLabs)
        bpm: Optional beats per minute for rhythm matching (used in prompt generation)
        sync_points: Optional list of sync points in seconds for beat alignment (used in prompt)
        looping: Whether the sound effect should be loopable (default: True).
                Maps to ElevenLabs API parameter "loop"
        prompt_influence: How closely the output should match the prompt (0-1, default: 0.3).
                         Higher values = more literal interpretation, lower = more creative
        output_path: Optional path where the audio file should be saved.
                    If not provided, saves to a temporary file.

    Returns:
        str: Path to the generated audio file (MP3 format)

    Raises:
        ImportError: If elevenlabs package is not installed
        ValueError: If ELEVENLABS_API_KEY is not set in environment
        Exception: If sound effect generation fails
    """
    try:
        # Check if ElevenLabs is available
        if ElevenLabs is None:
            raise ImportError(
                "elevenlabs package is not installed. Install it with: pip install elevenlabs"
            )

        # Get API key from environment
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=api_key)

        # Process mood input (can be string or list)
        if isinstance(mood, str):
            # Handle comma-separated mood tags
            mood_tags = [m.strip() for m in mood.split(",") if m.strip()]
            if not mood_tags:
                mood_tags = ["energetic"]  # Default
        elif isinstance(mood, list):
            mood_tags = [str(m).strip() for m in mood if str(m).strip()]
            if not mood_tags:
                mood_tags = ["energetic"]  # Default
        else:
            mood_tags = ["energetic"]  # Default

        # Build prompt for sound effect generation
        prompt_parts = []

        # Add mood description
        mood_description = ", ".join(mood_tags)
        prompt_parts.append(f"{mood_description} background sound")

        # Add style if provided
        if style and str(style).strip():
            prompt_parts.append(f"{str(style).strip()} style")

        # Add rhythm information if provided
        if bpm is not None and bpm > 0:
            prompt_parts.append(f"{int(bpm)} BPM rhythm")

        # Combine into final prompt
        prompt = ", ".join(prompt_parts)

        # Clamp duration to ElevenLabs limits (max 30 seconds)
        if target_duration > 30.0:
            target_duration = 30.0
        elif target_duration <= 0:
            target_duration = 5.0  # Minimum reasonable duration

        # Clamp prompt_influence to valid range (0-1)
        prompt_influence = max(0, min(1, prompt_influence))

        # Generate sound effect using ElevenLabs API
        # According to ElevenLabs API documentation:
        # - Required: text
        # - Optional: duration_seconds (0.5 to 30 seconds)
        # - Optional: loop (boolean) - enables seamless looping
        # - Optional: prompt_influence (float 0-1) - how closely output matches prompt
        # - Optional: output_format (e.g., "mp3_44100_128")

        # Build parameters for the API call
        api_params = {
            "text": prompt,
        }

        # Add duration_seconds parameter (must be between 0.5 and 30 seconds)
        if target_duration and 0.5 <= target_duration <= 30.0:
            api_params["duration_seconds"] = target_duration

        # Add looping parameter (API uses "loop" not "looping")
        if looping:
            api_params["loop"] = looping

        # Add prompt_influence parameter (0-1 range)
        if prompt_influence is not None:
            api_params["prompt_influence"] = prompt_influence

        # Add output format for MP3
        api_params["output_format"] = "mp3_44100_128"

        # Call the API
        audio_data = client.text_to_sound_effects.convert(**api_params)

        # Determine output path
        if output_path is None:
            # Create a temporary file with appropriate extension
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            output_path = os.path.join(
                temp_dir,
                f"sound_effect_{mood_tags[0]}_{int(target_duration)}s_{timestamp}.mp3",
            )

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Save audio data to file
        # The audio_data should be bytes that can be written directly
        if isinstance(audio_data, bytes):
            with open(output_path, "wb") as f:
                f.write(audio_data)
        elif hasattr(audio_data, "__iter__"):
            # If it's an iterable (generator, list, etc.), read all chunks
            with open(output_path, "wb") as f:
                for chunk in audio_data:
                    if isinstance(chunk, bytes):
                        f.write(chunk)
                    else:
                        # Try to convert to bytes
                        try:
                            f.write(bytes(chunk))
                        except (TypeError, ValueError):
                            # If conversion fails, try string encoding
                            if isinstance(chunk, str):
                                f.write(chunk.encode())
        else:
            # Try to write directly
            with open(output_path, "wb") as f:
                try:
                    f.write(bytes(audio_data))
                except (TypeError, ValueError):
                    raise ValueError(f"Unexpected audio data type: {type(audio_data)}")

        # Return absolute path
        return os.path.abspath(output_path)

    except Exception as e:
        raise Exception(f"Error generating sound effect: {str(e)}")

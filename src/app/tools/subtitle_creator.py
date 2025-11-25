import os
import json
import tempfile
from pathlib import Path
from typing import List, Optional, Union, TypedDict, Tuple
from moviepy import VideoFileClip, TextClip, CompositeVideoClip


class SubtitleSegment(TypedDict, total=False):
    """Subtitle segment definition with timing and styling."""

    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Subtitle text content
    position: Optional[str]  # Position: 'bottom', 'top', 'center', or tuple (x, y)
    font: Optional[str]  # Font name (default: 'Arial')
    fontsize: Optional[int]  # Font size (default: 48)
    color: Optional[str]  # Text color (default: 'white')
    bg_color: Optional[str]  # Background color (default: 'black')
    stroke_color: Optional[str]  # Stroke/outline color (optional)
    stroke_width: Optional[int]  # Stroke width (optional)


class RequiredSubtitleSegment(TypedDict):
    """Required fields for a subtitle segment."""

    start: float
    end: float
    text: str


class TranscriptData(TypedDict, total=False):
    """Complete transcript structure with subtitle segments."""

    subtitles: List[SubtitleSegment]
    default_style: Optional[dict]  # Default styling for all subtitles


# Type alias for Gradio video input
GradioVideoInput = Union[
    str,  # Single file path
    Tuple[str, str],  # Gradio video format: (video_path, subtitle_path)
]


def subtitle_creator(
    video_input: GradioVideoInput,
    transcript_json: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Add subtitles to a video based on a JSON transcript with timestamps.
    Creates text overlays at specified times with customizable styling.

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        transcript_json (str): JSON string containing subtitle segments with timing and styling
        output_path (str, optional): Path where the subtitled video should be saved.
                                     If not provided, saves to a temporary file.

    Returns:
        str: Path to the subtitled video file

    Example transcript JSON format:
    {
        "subtitles": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello, welcome to the video!",
                "position": "bottom",
                "fontsize": 48,
                "color": "white"
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "This is a subtitle example.",
                "fontsize": 52,
                "color": "yellow"
            }
        ],
        "default_style": {
            "fontsize": 48,
            "color": "white",
            "bg_color": "black",
            "position": "bottom",
            "transparent": True
        }
    }
    """
    try:
        # Handle Gradio video input format
        if isinstance(video_input, tuple):
            video_path = video_input[0]
        elif isinstance(video_input, str):
            video_path = video_input
        else:
            raise ValueError("Invalid video input format. Expected string or tuple.")

        # Validate video file exists
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Parse transcript JSON
        try:
            transcript_data: TranscriptData = json.loads(transcript_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in transcript: {str(e)}")

        # Validate transcript structure
        if "subtitles" not in transcript_data or not transcript_data["subtitles"]:
            raise ValueError(
                "Transcript must contain 'subtitles' array with at least one subtitle"
            )

        subtitles = transcript_data["subtitles"]
        default_style = transcript_data.get("default_style", {})

        # Set default styling values
        default_font = default_style.get("font", None) if default_style else None
        default_fontsize = default_style.get("fontsize", 48) if default_style else 48
        default_color = default_style.get("color", "white") if default_style else "white"
        default_bg_color = default_style.get("bg_color", "black") if default_style else "black"
        default_position = default_style.get("position", "bottom") if default_style else "bottom"
        default_transparent = default_style.get("transparent", True) if default_style else True

        # Load the video
        video = VideoFileClip(video_path)
        video_duration = video.duration
        video_width, video_height = video.size

        # Validate all subtitle timings
        for idx, subtitle in enumerate(subtitles):
            if "start" not in subtitle or "end" not in subtitle or "text" not in subtitle:
                raise ValueError(
                    f"Subtitle {idx} must have 'start', 'end', and 'text' fields"
                )

            start = subtitle["start"]
            end = subtitle["end"]

            if start < 0 or end < 0:
                raise ValueError(f"Subtitle {idx}: start and end times must be >= 0")

            if end <= start:
                raise ValueError(
                    f"Subtitle {idx}: end time must be greater than start time"
                )

            if start >= video_duration:
                raise ValueError(
                    f"Subtitle {idx}: start time {start}s exceeds video duration {video_duration}s"
                )

        # Create text clips for each subtitle
        text_clips = []

        for idx, subtitle in enumerate(subtitles):
            # Access required fields with validation already done above
            text = str(subtitle.get("text", ""))
            start = float(subtitle.get("start", 0.0))
            end = float(subtitle.get("end", 0.0))

            # Get styling for this subtitle (use segment-specific or default)
            font = subtitle.get("font", default_font)
            fontsize = int(subtitle.get("fontsize", default_fontsize))  # type: ignore
            color = str(subtitle.get("color", default_color))
            bg_color = subtitle.get("bg_color", default_bg_color)
            position = subtitle.get("position", default_position)
            stroke_color = subtitle.get("stroke_color")
            stroke_width = int(subtitle.get("stroke_width", 2))  # type: ignore
            transparent = subtitle.get("transparent", default_transparent)

            # Clamp end time to video duration
            if end > video_duration:
                end = video_duration

            # Calculate position
            if isinstance(position, str):
                if position == "bottom":
                    text_position = ("center", video_height - 100)
                elif position == "top":
                    text_position = ("center", 100)
                elif position == "center":
                    text_position = ("center", "center")
                else:
                    # Default to bottom if invalid
                    text_position = ("center", video_height - 100)
            elif isinstance(position, (list, tuple)) and len(position) == 2:
                text_position = tuple(position)
            else:
                text_position = ("center", video_height - 100)

            # Create text clip with styling
            try:
                text_clip = TextClip(
                    text=text,
                    font=font,
                    font_size=fontsize,
                    color=color,
                    bg_color=bg_color,
                    stroke_color=stroke_color if stroke_color else None,
                    stroke_width=stroke_width if stroke_color and stroke_width else 0,
                    size=(video_width - 100, None),  # Max width with padding
                    method="caption",  # Wrap text
                    transparent=transparent,
                )

                # Set timing and position
                text_clip = text_clip.with_start(start).with_end(end)
                text_clip = text_clip.with_position(text_position)

                text_clips.append(text_clip)

            except Exception as e:
                raise ValueError(
                    f"Error creating subtitle {idx} ('{text[:30]}...'): {str(e)}"
                )

        # Composite video with all text overlays
        final_video = CompositeVideoClip([video] + text_clips)

        # Determine output path
        if output_path is None:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(
                temp_dir, f"subtitled_video_{os.urandom(8).hex()}.mp4"
            )
        else:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Write the final video with subtitles
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(tempfile.gettempdir(), f"temp_audio_{os.urandom(8).hex()}.m4a"),
            remove_temp=True,
            fps=video.fps,
        )

        # Clean up
        video.close()
        final_video.close()
        for clip in text_clips:
            clip.close()

        return output_path

    except FileNotFoundError as e:
        raise e
    except ValueError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error creating subtitled video: {str(e)}")

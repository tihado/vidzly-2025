"""
LangChain tool wrappers for video processing tools.

This module wraps existing video processing tools as LangChain tools
so they can be used by the LangChain ReAct agent.
"""

import json
from typing import Optional, List, Union
from langchain_core.tools import tool

from .video_summarizer import video_summarizer
from .video_script_generator import video_script_generator
from .music_selector import music_selector
from .frame_extractor import frame_extractor
from .thumbnail_generator import thumbnail_generator
from .video_composer import video_composer


@tool
def video_summarizer_tool(video_path: str, fps: float = 2.0) -> str:
    """
    Analyze video content and generate a comprehensive summary.

    This tool analyzes a video file and returns a JSON summary containing:
    - Overall video description
    - Key scenes and moments with timestamps
    - Detected objects, people, and activities
    - Mood and style tags (e.g., energetic, calm, dramatic, fun)
    - Visual style description
    - Recommended thumbnail timestamp (in seconds)

    Args:
        video_path: Path to the video file to analyze
        fps: Frames per second for video processing (default: 2.0, range: 0.1-24.0)

    Returns:
        JSON string containing video summary with all analysis details
    """
    return video_summarizer(video_path, fps=fps)


@tool
def video_script_generator_tool(
    video_summaries: str,
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
) -> str:
    """
    Generate a detailed video composition script from video summaries.

    This tool creates a comprehensive script/storyboard for video composition that includes:
    - Scene sequence with source video references and timestamps
    - Duration for each scene segment (sums to approximately target_duration)
    - Transition types between scenes (cut, fade, crossfade)
    - Pacing and rhythm plan
    - Music synchronization points
    - Overall narrative structure and flow
    - Visual style recommendations

    Args:
        video_summaries: JSON string containing video summaries (can be single summary or array)
        user_description: Optional description of desired mood, style, or content
        target_duration: Target duration in seconds for the final video (default: 30.0)

    Returns:
        JSON string containing detailed script with scene information and composition details
    """
    return video_script_generator(video_summaries, user_description, target_duration)


@tool
def music_selector_tool(
    mood: str,
    style: Optional[str] = None,
    target_duration: float = 30.0,
    bpm: Optional[int] = None,
    looping: bool = True,
    prompt_influence: float = 0.3,
) -> str:
    """
    Generate background music or sound effects matching the video's mood and style.

    This tool uses ElevenLabs API to generate appropriate background music that matches
    the video content. The music is generated based on mood tags, style preferences,
    and duration requirements.

    Args:
        mood: Mood tags describing the desired mood (e.g., "energetic", "calm, dramatic")
        style: Optional style description (e.g., "cinematic", "modern", "retro")
        target_duration: Target duration in seconds (default: 30.0, max: 30.0)
        bpm: Optional beats per minute for rhythm matching
        looping: Whether the sound effect should be loopable (default: True)
        prompt_influence: How closely output matches prompt (0-1, default: 0.3)

    Returns:
        Path to the generated audio file (MP3 format)
    """
    return music_selector(
        mood=mood,
        style=style,
        target_duration=target_duration,
        bpm=bpm,
        looping=looping,
        prompt_influence=prompt_influence,
    )


@tool
def frame_extractor_tool(
    video_path: str, thumbnail_timeframe: Optional[float] = None
) -> str:
    """
    Extract a representative frame from a video for thumbnail creation.

    This tool extracts a frame from a video at a specific timestamp. If no timestamp
    is provided, it uses AI to analyze the video and select the best frame.

    Args:
        video_path: Path to the video file
        thumbnail_timeframe: Optional timestamp in seconds to extract frame.
                           If not provided, AI will select the best frame.

    Returns:
        Path to the extracted frame image (PNG format)
    """
    return frame_extractor(video_path, thumbnail_timeframe=thumbnail_timeframe)


@tool
def thumbnail_generator_tool(image_path: str, summary: str) -> str:
    """
    Generate an engaging thumbnail image with text overlays and stickers.

    This tool creates a professional thumbnail image using the provided frame image
    as a background. It adds catchy text, stickers, and visual elements based on the
    video summary to create an attention-grabbing thumbnail.

    Args:
        image_path: Path to the frame image to use as background
        summary: Text summary of the video content (used to generate appropriate text and stickers)

    Returns:
        Path to the generated thumbnail image (PNG format)
    """
    return thumbnail_generator(image_path, summary)


@tool
def video_composer_tool(
    script: str,
    video_clips: str,
    music_path: Optional[str] = None,
    thumbnail_image: Optional[str] = None,
) -> str:
    """
    Compose a final video from multiple clips according to a script.

    This tool combines video clips, adds music, applies transitions, and optionally
    overlays a thumbnail image on the first frame. It follows the script exactly to
    create the final composed video.

    Args:
        script: JSON string containing scene information with transitions and timing
        video_clips: JSON string array of video file paths, or comma-separated paths
        music_path: Optional path to background music file
        thumbnail_image: Optional path to thumbnail image to overlay on first frame

    Returns:
        Path to the final composed video file
    """
    # Handle video_clips - can be JSON array string or comma-separated paths
    if video_clips.strip().startswith("["):
        # JSON array
        clips_list = json.loads(video_clips)
    else:
        # Comma-separated paths
        clips_list = [path.strip() for path in video_clips.split(",") if path.strip()]

    return video_composer(
        script=script,
        video_clips=clips_list,
        music_path=music_path,
        thumbnail_image=thumbnail_image,
    )


# List of all tools for easy import
ALL_TOOLS = [
    video_summarizer_tool,
    video_script_generator_tool,
    music_selector_tool,
    frame_extractor_tool,
    thumbnail_generator_tool,
    video_composer_tool,
]

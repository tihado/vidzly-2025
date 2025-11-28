"""
LangChain tool wrappers for video processing tools.

This module wraps existing video processing tools as LangChain tools
so they can be used by the LangChain ReAct agent.

All tools use Pydantic models for structured output to ensure consistent
tool response formats and prevent parsing errors.
"""

import json
import os
from typing import Optional, List, Union
from langchain_core.tools import tool

from .video_summarizer import video_summarizer
from .video_script_generator import video_script_generator
from .music_selector import music_selector
from .frame_extractor import frame_extractor
from .thumbnail_generator import thumbnail_generator
from .video_composer import video_composer
from .tool_schemas import (
    VideoSummary,
    VideoScript,
    MusicSelectorResult,
    FrameExtractorResult,
    ThumbnailGeneratorResult,
    VideoComposerResult,
)


# Global registry to store valid video paths for path resolution
_VIDEO_PATH_REGISTRY: List[str] = []


def register_video_paths(paths: List[str]) -> None:
    """Register valid video paths for path resolution."""
    global _VIDEO_PATH_REGISTRY
    _VIDEO_PATH_REGISTRY = [
        os.path.abspath(p) for p in paths if p and os.path.exists(p)
    ]


def _resolve_video_path(video_path: str) -> Optional[str]:
    """
    Resolve a potentially corrupted video path by:
    1. Checking if the path exists as-is
    2. Trying to find a matching path in the registry
    3. Trying common path fixes (normalization, absolute path conversion)
    """
    # Clean the path
    video_path = video_path.strip()

    # Try direct path first
    if os.path.exists(video_path):
        return os.path.abspath(video_path)

    # Try absolute path conversion
    abs_path = os.path.abspath(video_path)
    if os.path.exists(abs_path):
        return abs_path

    # Try to find matching path in registry by filename
    if _VIDEO_PATH_REGISTRY:
        filename = os.path.basename(video_path)
        for registered_path in _VIDEO_PATH_REGISTRY:
            if os.path.basename(registered_path) == filename:
                if os.path.exists(registered_path):
                    return registered_path

        # Try fuzzy matching - check if the path is similar to any registered path
        # This handles cases where the path got corrupted (e.g., missing characters)
        for registered_path in _VIDEO_PATH_REGISTRY:
            # Check if the corrupted path is a substring of the registered path
            # or if they share the same directory structure
            if filename in registered_path or registered_path.endswith(filename):
                if os.path.exists(registered_path):
                    return registered_path

    return None


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

    The output follows the VideoSummary schema for consistent formatting.

    Args:
        video_path: Path to the video file to analyze
        fps: Frames per second for video processing (default: 2.0, range: 0.1-24.0)

    Returns:
        JSON string containing video summary with all analysis details matching VideoSummary schema
    """
    # Try to resolve the path in case it got corrupted
    resolved_path = _resolve_video_path(video_path)
    if resolved_path:
        result_json = video_summarizer(resolved_path, fps=fps)
    else:
        # If resolution failed, try the original path anyway
        result_json = video_summarizer(video_path, fps=fps)

    # Validate and ensure the result matches VideoSummary schema
    try:
        parsed = json.loads(result_json)
        # Validate against Pydantic model (this ensures consistency)
        VideoSummary(**parsed)
        return result_json
    except Exception:
        # If validation fails, return as-is (backward compatibility)
        return result_json


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

    The output follows the VideoScript schema for consistent formatting.

    Args:
        video_summaries: JSON string containing video summaries (can be single summary or array)
        user_description: Optional description of desired mood, style, or content
        target_duration: Target duration in seconds for the final video (default: 30.0)

    Returns:
        JSON string containing detailed script with scene information and composition details matching VideoScript schema
    """
    result_json = video_script_generator(
        video_summaries, user_description, target_duration
    )

    # Validate and ensure the result matches VideoScript schema
    try:
        parsed = json.loads(result_json)
        # Validate against Pydantic model (this ensures consistency)
        VideoScript(**parsed)
        return result_json
    except Exception:
        # If validation fails, return as-is (backward compatibility)
        return result_json


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

    The output follows the MusicSelectorResult schema for consistent formatting.

    Args:
        mood: Mood tags describing the desired mood (e.g., "energetic", "calm, dramatic")
        style: Optional style description (e.g., "cinematic", "modern", "retro")
        target_duration: Target duration in seconds (default: 30.0, max: 30.0)
        bpm: Optional beats per minute for rhythm matching
        looping: Whether the sound effect should be loopable (default: True)
        prompt_influence: How closely output matches prompt (0-1, default: 0.3)

    Returns:
        JSON string with audio_path field matching MusicSelectorResult schema
    """
    audio_path = music_selector(
        mood=mood,
        style=style,
        target_duration=target_duration,
        bpm=bpm,
        looping=looping,
        prompt_influence=prompt_influence,
    )

    # Return as JSON string matching MusicSelectorResult schema
    result = MusicSelectorResult(audio_path=audio_path)
    return result.model_dump_json()


@tool
def frame_extractor_tool(
    video_path: str, thumbnail_timeframe: Optional[float] = None
) -> str:
    """
    Extract a representative frame from a video for thumbnail creation.

    This tool extracts a frame from a video at a specific timestamp. If no timestamp
    is provided, it uses AI to analyze the video and select the best frame.

    The output follows the FrameExtractorResult schema for consistent formatting.

    Args:
        video_path: Path to the video file
        thumbnail_timeframe: Optional timestamp in seconds to extract frame.
                           If not provided, AI will select the best frame.

    Returns:
        JSON string with frame_path field matching FrameExtractorResult schema
    """
    # Try to resolve the path in case it got corrupted
    resolved_path = _resolve_video_path(video_path)
    if resolved_path:
        frame_path = frame_extractor(
            resolved_path, thumbnail_timeframe=thumbnail_timeframe
        )
    else:
        # If resolution failed, try the original path anyway
        frame_path = frame_extractor(
            video_path, thumbnail_timeframe=thumbnail_timeframe
        )

    # Return as JSON string matching FrameExtractorResult schema
    result = FrameExtractorResult(frame_path=frame_path)
    return result.model_dump_json()


@tool
def thumbnail_generator_tool(image_path: str, summary: str) -> str:
    """
    Generate an engaging thumbnail image with text overlays and stickers.

    This tool creates a professional thumbnail image using the provided frame image
    as a background. It adds catchy text, stickers, and visual elements based on the
    video summary to create an attention-grabbing thumbnail.

    The output follows the ThumbnailGeneratorResult schema for consistent formatting.

    Args:
        image_path: Path to the frame image to use as background
        summary: Text summary of the video content (used to generate appropriate text and stickers)

    Returns:
        JSON string with thumbnail_path field matching ThumbnailGeneratorResult schema
    """
    thumbnail_path = thumbnail_generator(image_path, summary)

    # Return as JSON string matching ThumbnailGeneratorResult schema
    result = ThumbnailGeneratorResult(thumbnail_path=thumbnail_path)
    return result.model_dump_json()


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

    The output follows the VideoComposerResult schema for consistent formatting.

    Args:
        script: JSON string containing scene information with transitions and timing
        video_clips: JSON string array of video file paths, or comma-separated paths
        music_path: Optional path to background music file
        thumbnail_image: Optional path to thumbnail image to overlay on first frame

    Returns:
        JSON string with video_path field matching VideoComposerResult schema
    """
    # Handle video_clips - can be JSON array string or comma-separated paths
    if video_clips.strip().startswith("["):
        # JSON array
        clips_list = json.loads(video_clips)
    else:
        # Comma-separated paths
        clips_list = [path.strip() for path in video_clips.split(",") if path.strip()]

    # Resolve all video clip paths in case they got corrupted
    resolved_clips = []
    for clip_path in clips_list:
        resolved_path = _resolve_video_path(clip_path)
        if resolved_path:
            resolved_clips.append(resolved_path)
        else:
            # If resolution failed, try the original path anyway
            resolved_clips.append(clip_path)

    video_path = video_composer(
        script=script,
        video_clips=resolved_clips,
        music_path=music_path,
        thumbnail_image=thumbnail_image,
    )

    # Return as JSON string matching VideoComposerResult schema
    result = VideoComposerResult(video_path=video_path)
    return result.model_dump_json()


# List of all tools for easy import
ALL_TOOLS = [
    video_summarizer_tool,
    video_script_generator_tool,
    music_selector_tool,
    frame_extractor_tool,
    thumbnail_generator_tool,
    video_composer_tool,
]

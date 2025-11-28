"""
Pydantic models for tool output schemas.

These models ensure consistent, structured output from all tools,
preventing issues with inconsistent tool response formats.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class VideoSummary(BaseModel):
    """Schema for video summarizer tool output."""

    duration: float = Field(..., description="Video duration in seconds")
    resolution: str = Field(..., description="Video resolution (e.g., '1920x1080')")
    fps: float = Field(..., description="Frames per second")
    frame_count: int = Field(..., description="Total number of frames")
    summary: str = Field(..., description="Detailed video summary and analysis")
    mood_tags: List[str] = Field(
        default_factory=list, description="List of mood/style tags"
    )
    thumbnail_timeframe: float = Field(
        ..., description="Recommended timestamp for thumbnail extraction (seconds)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "duration": 26.39,
                "resolution": "1080x1920",
                "fps": 29.98,
                "frame_count": 791,
                "summary": "A comprehensive video analysis...",
                "mood_tags": ["casual", "bright"],
                "thumbnail_timeframe": 13.2,
            }
        }


class VideoScript(BaseModel):
    """Schema for video script generator tool output."""

    total_duration: float = Field(
        ..., description="Total duration of the script in seconds"
    )
    scenes: List[dict] = Field(..., description="List of scene objects")
    music: Optional[dict] = Field(None, description="Music configuration")
    pacing: Optional[str] = Field(None, description="Pacing description")
    narrative_structure: Optional[str] = Field(None, description="Narrative structure")
    visual_style: Optional[str] = Field(None, description="Visual style description")

    class Config:
        json_schema_extra = {
            "example": {
                "total_duration": 30.0,
                "scenes": [
                    {
                        "scene_id": 1,
                        "source_video": 0,
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "duration": 5.0,
                        "description": "Opening scene",
                        "transition_in": "fade",
                        "transition_out": "crossfade",
                    }
                ],
                "music": {"mood": "energetic", "bpm": 120, "volume": 0.5},
                "pacing": "fast",
                "narrative_structure": "hook -> build -> climax -> resolution",
                "visual_style": "bright, colorful, dynamic",
            }
        }


class MusicSelectorResult(BaseModel):
    """Schema for music selector tool output."""

    audio_path: str = Field(..., description="Path to the generated audio file")

    class Config:
        json_schema_extra = {
            "example": {"audio_path": "/tmp/sound_effect_energetic_30s_1234567890.mp3"}
        }


class FrameExtractorResult(BaseModel):
    """Schema for frame extractor tool output."""

    frame_path: str = Field(..., description="Path to the extracted frame image")

    class Config:
        json_schema_extra = {
            "example": {"frame_path": "/path/to/video_frame_ai_13s.png"}
        }


class ThumbnailGeneratorResult(BaseModel):
    """Schema for thumbnail generator tool output."""

    thumbnail_path: str = Field(
        ..., description="Path to the generated thumbnail image"
    )

    class Config:
        json_schema_extra = {
            "example": {"thumbnail_path": "/tmp/thumbnail_1234567890.png"}
        }


class VideoComposerResult(BaseModel):
    """Schema for video composer tool output."""

    video_path: str = Field(..., description="Path to the final composed video file")

    class Config:
        json_schema_extra = {"example": {"video_path": "/tmp/composed_video_12345.mp4"}}

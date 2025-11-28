import os
import json
import tempfile
from pathlib import Path
from typing import List, Optional, Union, TypedDict, Literal, Tuple
from moviepy import (
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    concatenate_videoclips,
    ImageClip,
)

try:
    from moviepy.audio import concatenate_audioclips
except ImportError:
    from moviepy import concatenate_audioclips


# Type definitions for script structure
TransitionType = Literal["cut", "fade", "crossfade"]


class Scene(TypedDict, total=False):
    """Scene definition in the video composition script."""

    scene_id: int
    source_video: Union[
        int, str
    ]  # Index (int) or filename (str) referencing video_clips
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    transition_in: TransitionType
    transition_out: TransitionType


class Music(TypedDict, total=False):
    """Music configuration in the video composition script."""

    mood: str
    bpm: int
    sync_points: List[float]
    volume: float


class ScriptData(TypedDict, total=False):
    """Complete script structure for video composition."""

    total_duration: float
    scenes: List[Scene]
    music: Music


# Type aliases for Gradio file inputs
GradioVideoInput = Union[
    str,  # Single file path
    Tuple[str, str],  # Gradio video format: (video_path, subtitle_path)
    List[Union[str, Tuple[str, str]]],  # List of files
]

GradioMusicInput = Union[
    str,  # File path
    Tuple[str, ...],  # Gradio file format: (file_path, ...)
]

GradioImageInput = Union[
    str,  # File path
    Tuple[str, ...],  # Gradio file format: (file_path, ...)
]


def video_composer(
    script: Union[str, ScriptData],
    video_clips: GradioVideoInput,
    music_path: Optional[GradioMusicInput] = None,
    thumbnail_image: Optional[GradioImageInput] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Combine video clips, add music, and apply transitions according to a script.
    Creates a final composed video from multiple video segments.

    Args:
        script: Script JSON string or dict containing scene information with transitions.
                Expected format:
                {
                    "total_duration": 30.0,
                    "scenes": [
                        {
                            "scene_id": 1,
                            "source_video": 0,  # Index into video_clips list, or filename
                            "start_time": 5.2,
                            "end_time": 8.5,
                            "duration": 3.3,
                            "transition_in": "fade",
                            "transition_out": "crossfade"
                        },
                        {
                            "scene_id": 2,
                            "source_video": 0,  # Same video can be used in multiple scenes
                            "start_time": 10.0,
                            "end_time": 15.0,
                            "duration": 5.0,
                            "transition_in": "crossfade",
                            "transition_out": "fade"
                        },
                        ...
                    ],
                    "music": {
                        "mood": "energetic",
                        "bpm": 120,
                        "sync_points": [0.0, 7.5, 15.0, 22.5, 30.0]
                    }
                }
                Note: source_video can be:
                - An integer index (0-based) into the video_clips list
                - A filename (string) that matches the basename of one of the videos in video_clips
                The same source_video can be used in multiple scenes with different
                time ranges. Each scene will extract its own clip from the referenced video.
        video_clips: Required list of source video file paths or single path.
                     Each scene's source_video references a video from this list.
                     Can be a list, single string (from Gradio File component).
        music_path: Optional path to background music file. If provided, will be added
                   to the final video. Can be a string path or tuple (from Gradio File component).
        thumbnail_image: Optional path to thumbnail image file. If provided, will be overlaid
                        on the first frame of the video. Can be a string path or tuple (from Gradio File component).
        output_path: Optional path where the composed video should be saved.
                    If not provided, saves to a temporary file.

    Returns:
        str: Path to the final composed video file
    """
    try:
        # Handle Gradio file input formats
        if isinstance(video_clips, tuple):
            # Single tuple from Gradio: (video_path, subtitle_path)
            video_clips = [video_clips[0]] if video_clips else []
        elif isinstance(video_clips, str):
            # Single file path
            video_clips = [video_clips]
        elif isinstance(video_clips, list):
            # List of file paths (may contain tuples from Gradio)
            processed_clips = []
            for clip in video_clips:
                if isinstance(clip, tuple):
                    # Gradio video format: (video_path, subtitle_path)
                    processed_clips.append(clip[0])
                elif isinstance(clip, str):
                    processed_clips.append(clip)
            video_clips = processed_clips if processed_clips else []
        else:
            raise ValueError(
                "video_clips must be a string, tuple, or list of strings/tuples"
            )

        # Validate video_clips is not empty
        if not video_clips:
            raise ValueError("video_clips is required and cannot be empty")

        # Validate all video files exist
        for clip_path in video_clips:
            if not os.path.exists(clip_path):
                raise FileNotFoundError(f"Video clip not found: {clip_path}")

        # Handle Gradio music file input format
        if music_path is not None:
            if isinstance(music_path, tuple):
                # Gradio file format: (file_path, ...)
                music_path = music_path[0] if music_path else None
            elif not isinstance(music_path, str):
                music_path = None

        # Handle Gradio thumbnail image input format
        thumbnail_path = None
        if thumbnail_image is not None:
            if isinstance(thumbnail_image, tuple):
                # Gradio file format: (file_path, ...)
                thumbnail_path = thumbnail_image[0] if thumbnail_image else None
            elif isinstance(thumbnail_image, str):
                thumbnail_path = thumbnail_image
            else:
                thumbnail_path = None

        # Validate thumbnail image exists if provided
        if thumbnail_path and not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail image not found: {thumbnail_path}")

        # Parse script if it's a string
        if isinstance(script, str):
            try:
                script_data: ScriptData = json.loads(script)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for script")
        else:
            script_data = script

        # Validate script structure
        if not isinstance(script_data, dict) or "scenes" not in script_data:
            raise ValueError(
                "Script must contain a 'scenes' key with scene information"
            )

        scenes: List[Scene] = script_data.get("scenes", [])
        if not scenes:
            raise ValueError("Script must contain at least one scene")

        # Helper function to resolve source_video reference
        def resolve_source_video(
            source_video_ref: Union[int, str], video_clips_list: List[str]
        ) -> str:
            """Resolve source_video reference to actual video path.

            Args:
                source_video_ref: Can be an integer index or a filename string
                video_clips_list: List of video file paths

            Returns:
                str: Path to the source video
            """
            if isinstance(source_video_ref, int):
                # Index-based reference
                # Validation should have been done before calling this function,
                # but add safety check here too
                if source_video_ref < 0:
                    source_video_ref = 0
                elif source_video_ref >= len(video_clips_list):
                    source_video_ref = len(video_clips_list) - 1
                return video_clips_list[source_video_ref]
            elif isinstance(source_video_ref, str):
                # Filename-based reference - match by basename
                for clip_path in video_clips_list:
                    if os.path.basename(clip_path) == source_video_ref:
                        return clip_path
                    # Also try matching the full path
                    if clip_path == source_video_ref:
                        return clip_path
                raise ValueError(
                    f"source_video '{source_video_ref}' not found in video_clips. "
                    f"Available videos: {[os.path.basename(v) for v in video_clips_list]}"
                )
            else:
                raise ValueError(
                    f"source_video must be an integer index or filename string, "
                    f"got {type(source_video_ref).__name__}"
                )

        # Extract clips from source videos based on script
        clip_paths = []
        for scene in scenes:
            source_video_ref = scene.get("source_video")
            start_time = scene.get("start_time", 0.0)
            end_time = scene.get("end_time")
            duration = scene.get("duration")

            if source_video_ref is None:
                raise ValueError(
                    f"Scene {scene.get('scene_id', 'unknown')} missing 'source_video'"
                )

            # Validate and clamp source_video index before resolving
            if isinstance(source_video_ref, int):
                if source_video_ref < 0:
                    source_video_ref = 0
                    scene["source_video"] = 0
                elif source_video_ref >= len(video_clips):
                    source_video_ref = len(video_clips) - 1
                    scene["source_video"] = source_video_ref

            # Resolve source_video reference to actual video path
            source_video = resolve_source_video(source_video_ref, video_clips)

            # Load video to get actual duration for validation
            temp_video = VideoFileClip(source_video)
            video_duration = temp_video.duration
            temp_video.close()

            # Calculate end_time from duration if not provided
            if end_time is None and duration is not None:
                end_time = start_time + duration
            elif end_time is None:
                end_time = video_duration

            # Validate and clamp timestamps to video duration
            # If start_time exceeds duration, adjust to use the end of the video
            if start_time >= video_duration:
                # Use the last portion of the video (last 2 seconds or video duration, whichever is smaller)
                clip_duration = min(2.0, video_duration)
                start_time = max(0.0, video_duration - clip_duration)
                end_time = video_duration
            else:
                # Clamp start_time to be within bounds
                start_time = max(0.0, min(start_time, video_duration - 0.1))
                # Clamp end_time to be within bounds and greater than start_time
                end_time = max(start_time + 0.1, min(end_time, video_duration))

            # Clip the video segment
            from .video_clipper import video_clipper

            clipped_path = video_clipper(source_video, start_time, end_time)
            clip_paths.append(clipped_path)

        # Load all video clips and validate durations
        video_clips_loaded = []
        expected_total_duration = 0.0
        actual_total_duration = 0.0
        
        for i, (clip_path, scene) in enumerate(zip(clip_paths, scenes)):
            if not os.path.exists(clip_path):
                raise FileNotFoundError(f"Video clip not found: {clip_path}")
            
            clip = VideoFileClip(clip_path)
            actual_duration = clip.duration
            expected_duration = scene.get("duration", actual_duration)
            
            # Use actual duration for calculations, not expected
            actual_total_duration += actual_duration
            expected_total_duration += expected_duration
            
            # Log duration mismatch if significant
            if abs(actual_duration - expected_duration) > 0.5:
                print(f"Warning: Scene {i+1} expected duration {expected_duration:.2f}s but actual clip duration is {actual_duration:.2f}s")
            
            video_clips_loaded.append(clip)
        
        print(f"Total expected duration from script: {expected_total_duration:.2f}s")
        print(f"Total actual duration from clips: {actual_total_duration:.2f}s")

        # Apply transitions and compose clips
        transition_duration = 0.5  # Default transition duration in seconds
        has_crossfade = False

        # Check if any scene uses crossfade
        for scene in scenes:
            if (
                scene.get("transition_in") == "crossfade"
                or scene.get("transition_out") == "crossfade"
            ):
                has_crossfade = True
                break

        processed_clips = []

        for i, (clip, scene) in enumerate(zip(video_clips_loaded, scenes)):
            transition_in = scene.get("transition_in", "cut")
            transition_out = scene.get("transition_out", "cut")

            # Apply transition in (except for first clip)
            if i > 0 and transition_in != "cut":
                if transition_in in ("fade", "crossfade"):
                    # Try fadein if available, otherwise skip transition
                    if hasattr(clip, "fadein"):
                        clip = clip.fadein(transition_duration)
                    # If fadein not available, continue without transition

            # Apply transition out (except for last clip)
            if i < len(video_clips_loaded) - 1 and transition_out != "cut":
                if transition_out in ("fade", "crossfade"):
                    # Try fadeout if available, otherwise skip transition
                    if hasattr(clip, "fadeout"):
                        clip = clip.fadeout(transition_duration)
                    # If fadeout not available, continue without transition

            processed_clips.append(clip)

        # Compose clips based on transition type
        if has_crossfade:
            # Use CompositeVideoClip for crossfades (overlapping clips)
            final_clips = []
            current_time = 0.0

            for i, (clip, scene) in enumerate(zip(processed_clips, scenes)):
                transition_in = scene.get("transition_in", "cut")

                if i > 0 and transition_in == "crossfade":
                    # Overlap for crossfade - this reduces total duration
                    clip_start = current_time - transition_duration
                else:
                    clip_start = current_time

                clip = clip.with_start(clip_start)
                final_clips.append(clip)
                # Use actual clip duration, not script duration
                current_time = clip_start + clip.duration

            final_video = CompositeVideoClip(final_clips)
        else:
            # Use concatenate_videoclips for simple sequential composition
            final_video = concatenate_videoclips(processed_clips, method="compose")
        
        # Validate final video duration
        actual_final_duration = final_video.duration
        target_duration = script_data.get("total_duration", expected_total_duration)
        
        # Log duration information
        print(f"Final composed video duration: {actual_final_duration:.2f}s")
        print(f"Target duration from script: {target_duration:.2f}s")
        
        if abs(actual_final_duration - target_duration) > 1.0:
            print(f"Warning: Final video duration ({actual_final_duration:.2f}s) is shorter than target duration ({target_duration:.2f}s)")
            print(f"Expected total from scenes: {expected_total_duration:.2f}s")
            print(f"Actual total from clips: {actual_total_duration:.2f}s")
            
            # If the actual duration is significantly shorter, it might be due to:
            # 1. Frame reading issues in clipped videos
            # 2. Crossfade overlaps reducing duration
            # 3. Clips being truncated during extraction
            if actual_final_duration < actual_total_duration * 0.8:
                print(f"Warning: Final video is significantly shorter than sum of clip durations. This may indicate frame reading issues.")

        # Add thumbnail image to first frame if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                from PIL import Image as PILImage

                # Get video dimensions
                video_width = final_video.w
                video_height = final_video.h

                # Load and resize thumbnail image using PIL
                pil_image = PILImage.open(thumbnail_path)
                pil_image = pil_image.resize(
                    (video_width, video_height), PILImage.Resampling.LANCZOS
                )

                # Save resized image to temporary file
                import tempfile

                temp_thumbnail = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                )
                pil_image.save(temp_thumbnail.name, "PNG")
                temp_thumbnail.close()

                # Load the resized thumbnail as ImageClip
                thumbnail_clip = ImageClip(temp_thumbnail.name)

                # Set duration to match one frame duration (very short)
                # This ensures it only appears on the first frame
                # MoviePy 2.x uses with_duration instead of set_duration
                fps = final_video.fps if final_video.fps > 0 else 30.0
                frame_duration = 1.0 / fps
                thumbnail_clip = thumbnail_clip.with_duration(frame_duration)

                # Position at the start (t=0) so it overlays the first frame
                # MoviePy 2.x uses with_start instead of set_start
                thumbnail_clip = thumbnail_clip.with_start(0)

                # Composite the thumbnail over the video
                # The thumbnail will appear on top of the first frame
                final_video = CompositeVideoClip([final_video, thumbnail_clip])

                # Clean up temporary file after composition
                try:
                    os.unlink(temp_thumbnail.name)
                except:
                    pass
            except Exception as e:
                # If thumbnail overlay fails, continue without thumbnail
                print(f"Warning: Could not add thumbnail image: {str(e)}")

        # Add music if provided
        if music_path and os.path.exists(music_path):
            try:
                audio_clip = AudioFileClip(music_path)
                video_duration = final_video.duration

                # Trim or loop music to match video duration
                if audio_clip.duration > video_duration:
                    audio_clip = audio_clip.subclipped(0, video_duration)
                elif audio_clip.duration < video_duration:
                    # Loop the music if it's shorter than video
                    loops_needed = int(video_duration / audio_clip.duration) + 1
                    audio_clips = [audio_clip] * loops_needed
                    audio_clip = concatenate_audioclips(audio_clips).subclipped(
                        0, video_duration
                    )

                # Set audio volume (can be adjusted based on script music settings)
                audio_volume = script_data.get("music", {}).get("volume", 0.5)

                # Apply volume adjustment using MoviePy 2.x API
                # MoviePy 2.1.2+ uses with_volume_scaled instead of volumex
                audio_clip = audio_clip.with_volume_scaled(audio_volume)

                # Combine video with audio
                # MoviePy 2.x uses with_audio instead of set_audio
                final_video = final_video.with_audio(audio_clip)
            except Exception as e:
                # If music loading fails, continue without music
                print(f"Warning: Could not add music: {str(e)}")

        # Determine output path
        if output_path is None:
            video_ext = ".mp4"
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(
                temp_dir, f"composed_video_{os.getpid()}{video_ext}"
            )

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Write the final composed video
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=tempfile.mktemp(suffix=".m4a"),
            remove_temp=True,
            logger=None,
        )

        # Clean up
        final_video.close()
        for clip in video_clips_loaded:
            clip.close()
        if music_path and "audio_clip" in locals():
            try:
                audio_clip.close()
            except:
                pass

        # Clean up temporary clipped files (always created from source videos)
        for clip_path in clip_paths:
            try:
                if os.path.exists(clip_path) and "clipped_" in os.path.basename(
                    clip_path
                ):
                    os.remove(clip_path)
            except:
                pass

        # Return absolute path
        return os.path.abspath(output_path)

    except Exception as e:
        # Clean up video objects if they exist
        try:
            if "video_clips_loaded" in locals():
                for clip in video_clips_loaded:
                    try:
                        clip.close()
                    except:
                        pass
            if "final_video" in locals():
                try:
                    final_video.close()
                except:
                    pass
            if "audio_clip" in locals():
                try:
                    audio_clip.close()
                except:
                    pass
        except:
            pass
        raise Exception(f"Error composing video: {str(e)}")

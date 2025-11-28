import os
import tempfile
from pathlib import Path
from moviepy import VideoFileClip


def video_clipper(
    video_input, start_time: float, end_time: float, output_path: str = None
) -> str:
    """
    Extract a specific segment from a video file based on start and end times.

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        start_time (float): Start time in seconds (0-based)
        end_time (float): End time in seconds (must be > start_time)
        output_path (str, optional): Path where the clipped video should be saved.
                                    If not provided, saves to a temporary file.

    Returns:
        str: Path to the clipped video file
    """
    try:
        # Handle Gradio video input format (can be tuple or string)
        if isinstance(video_input, tuple):
            video_path = video_input[0]
        elif isinstance(video_input, str):
            video_path = video_input
        else:
            raise ValueError("Invalid video input format. Expected string or tuple.")

        # Validate video file exists
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Validate time parameters
        if start_time < 0:
            raise ValueError("Start time must be >= 0")

        if end_time <= start_time:
            raise ValueError("End time must be greater than start time")

        # Load the video file
        video = VideoFileClip(video_path)

        # Validate time range against video duration
        video_duration = video.duration
        if start_time >= video_duration:
            video.close()
            raise ValueError(
                f"Start time ({start_time}s) exceeds video duration ({video_duration:.2f}s)"
            )

        # Clamp end_time to video duration if necessary
        if end_time > video_duration:
            end_time = video_duration

        # Extract the segment (using subclipped for MoviePy 2.1.2+)
        clipped_video = video.subclipped(start_time, end_time)
        expected_duration = end_time - start_time

        # Determine output path
        if output_path is None:
            # Create a temporary file with appropriate extension
            video_ext = Path(video_path).suffix or ".mp4"
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(
                temp_dir,
                f"clipped_{os.path.basename(video_path)}_{start_time}_{end_time}{video_ext}",
            )

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Write the clipped video with explicit duration to ensure accuracy
        clipped_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=tempfile.mktemp(suffix=".m4a"),
            remove_temp=True,
            logger=None,
            preset="medium",  # Use medium preset for better quality and reliability
        )

        # Clean up
        clipped_video.close()
        video.close()

        # Verify the clipped video duration by reloading it
        # This helps catch any frame reading issues early
        verify_clip = VideoFileClip(output_path)
        actual_duration = verify_clip.duration
        verify_clip.close()

        # Log if there's a significant duration mismatch
        if abs(actual_duration - expected_duration) > 0.5:
            print(
                f"Warning: Clipped video expected {expected_duration:.2f}s but actual duration is {actual_duration:.2f}s"
            )

        # Return absolute path
        return os.path.abspath(output_path)

    except Exception as e:
        # Clean up video object if it exists
        try:
            if "video" in locals() and video is not None:
                video.close()
            if "clipped_video" in locals() and clipped_video is not None:
                clipped_video.close()
        except:
            pass
        raise Exception(f"Error clipping video: {str(e)}")

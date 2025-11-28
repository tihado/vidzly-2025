import cv2
import os
import re
from pathlib import Path
from typing import Optional
import mimetypes
import google.genai as genai


def frame_extractor(
    video_input,
    output_path: Optional[str] = None,
    thumbnail_timeframe: Optional[float] = None,
) -> str:
    """
    Extract a representative frame from video.

    If thumbnail_timeframe is provided, uses that timestamp directly. Otherwise,
    uses Gemini AI to analyze the video and determine the best timestamp for
    frame extraction.

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        output_path: Optional output path for frame image
        thumbnail_timeframe: Optional timestamp in seconds to use for frame extraction.
                           If provided, skips AI analysis and uses this timestamp directly.

    Returns:
        str: Path to extracted frame image (PNG format)
    """
    try:
        # Handle Gradio video input format (can be tuple or string)
        if isinstance(video_input, tuple):
            video_path = video_input[0]
        elif isinstance(video_input, str):
            video_path = video_input
        else:
            raise ValueError("Invalid video input format")

        # Validate video file exists
        if not video_path or not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        # Get video metadata
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        if duration == 0:
            cap.release()
            raise ValueError("Video has zero duration")

        cap.release()

        # Use provided thumbnail_timeframe if available, otherwise use Gemini API
        if thumbnail_timeframe is not None:
            # Use the provided timestamp directly
            best_timestamp = float(thumbnail_timeframe)
            # Ensure timestamp is within video duration
            best_timestamp = max(0.0, min(best_timestamp, duration - 0.1))
        else:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY environment variable is required for AI frame extraction when thumbnail_timeframe is not provided"
                )

            # Use Gemini Vision API to analyze video and get best timestamp
            client = genai.Client(api_key=api_key)

            # Read video file as bytes
            with open(video_path, "rb") as f:
                video_data = f.read()

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(video_path)
            if not mime_type or not mime_type.startswith("video/"):
                # Default to mp4 if cannot determine
                mime_type = "video/mp4"

            # Create prompt asking for best timestamp
            prompt = f"""Analyze this video and identify the best timestamp (in seconds) to extract a representative, engaging frame for a thumbnail.

Consider these factors:
- Visual appeal and composition quality
- Subject clarity and focus
- Color and lighting quality
- Overall engagement and representativeness of the video content
- Avoid frames with motion blur or poor quality

The video duration is approximately {duration:.2f} seconds.

Respond with ONLY the timestamp in seconds as a number (e.g., "12.5" or "8.3"). Do not include any other text or explanation."""

            # Create VideoMetadata with fps parameter for efficient processing
            # Using 2.0 fps for good balance between speed and accuracy
            video_metadata = genai.types.VideoMetadata(fps=2.0)
            video_blob = genai.types.Blob(data=video_data, mime_type=mime_type)
            video_part = genai.types.Part(
                inline_data=video_blob,
                videoMetadata=video_metadata,
            )

            # Use Gemini's native video understanding to analyze the entire video
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[prompt, video_part],
            )

            # Extract timestamp from response
            response_text = response.text.strip()

            # Try to extract numeric timestamp from response
            # Look for patterns like "12.5", "8.3", "15", etc.
            timestamp_match = re.search(r"(\d+\.?\d*)", response_text)
            if timestamp_match:
                best_timestamp = float(timestamp_match.group(1))
                # Ensure timestamp is within video duration
                best_timestamp = max(0.0, min(best_timestamp, duration - 0.1))
            else:
                # Fallback: use middle of video if we can't parse the response
                best_timestamp = duration / 2

        # Extract frame at the selected timestamp
        cap = cv2.VideoCapture(video_path)
        frame_number = int(best_timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, best_frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError(f"Could not extract frame at timestamp {best_timestamp}s")

        # Generate output path if not provided
        if output_path is None:
            video_name = Path(video_path).stem
            output_dir = Path(video_path).parent / "frames"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                output_dir / f"{video_name}_frame_ai_{int(best_timestamp)}s.png"
            )

        # Save selected frame
        cv2.imwrite(output_path, best_frame)
        return output_path

    except Exception as e:
        raise Exception(f"Error extracting frame: {str(e)}")

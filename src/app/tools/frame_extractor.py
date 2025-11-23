import cv2
import os
import numpy as np
import tempfile
from pathlib import Path
from typing import Literal, Optional
import google.genai as genai


def calculate_sharpness(frame: np.ndarray) -> float:
    """
    Calculate the sharpness of a frame using Laplacian variance.
    Higher values indicate sharper images.

    Args:
        frame: Grayscale image array

    Returns:
        float: Sharpness score
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def calculate_contrast(frame: np.ndarray) -> float:
    """
    Calculate the contrast of a frame using standard deviation.
    Higher values indicate better contrast.

    Args:
        frame: Grayscale image array

    Returns:
        float: Contrast score
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    return np.std(gray)


def calculate_brightness(frame: np.ndarray) -> float:
    """
    Calculate the brightness of a frame.
    Returns a value between 0 and 255.

    Args:
        frame: Grayscale image array

    Returns:
        float: Average brightness value
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    return np.mean(gray)


def calculate_frame_quality(frame: np.ndarray) -> float:
    """
    Calculate a composite quality score for a frame.
    Combines sharpness, contrast, and brightness metrics.

    Args:
        frame: Image array

    Returns:
        float: Composite quality score
    """
    sharpness = calculate_sharpness(frame)
    contrast = calculate_contrast(frame)
    brightness = calculate_brightness(frame)

    # Normalize scores (approximate ranges)
    # Sharpness: typically 0-1000+, normalize to 0-1
    normalized_sharpness = min(sharpness / 1000.0, 1.0)

    # Contrast: typically 0-100, normalize to 0-1
    normalized_contrast = min(contrast / 100.0, 1.0)

    # Brightness: 0-255, prefer middle range (100-200), normalize to 0-1
    # Penalize too dark (<50) or too bright (>200)
    if 100 <= brightness <= 200:
        normalized_brightness = 1.0
    elif brightness < 50:
        normalized_brightness = brightness / 50.0
    elif brightness > 200:
        normalized_brightness = 1.0 - (brightness - 200) / 55.0
    else:
        normalized_brightness = 0.8

    # Weighted combination
    quality_score = (
        0.5 * normalized_sharpness
        + 0.3 * normalized_contrast
        + 0.2 * normalized_brightness
    )

    return quality_score


def extract_frame_at_timestamp(
    video_path: str, timestamp: float, output_path: Optional[str] = None
) -> str:
    """
    Extract a single frame from video at a specific timestamp.

    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds
        output_path: Optional output path for frame image

    Returns:
        str: Path to extracted frame image
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_number = int(timestamp * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError(f"Could not extract frame at timestamp {timestamp}s")

    # Generate output path if not provided
    if output_path is None:
        video_name = Path(video_path).stem
        output_dir = Path(video_path).parent / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{video_name}_frame_{int(timestamp)}s.png")

    # Save frame
    cv2.imwrite(output_path, frame)
    return output_path


def extract_best_frame(
    video_path: str,
    sample_interval: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    """
    Extract the best quality frame from video by analyzing multiple frames.

    Args:
        video_path: Path to video file
        sample_interval: Interval in seconds to sample frames (default: 1.0)
        output_path: Optional output path for frame image

    Returns:
        str: Path to extracted frame image
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    best_frame = None
    best_quality = -1
    best_timestamp = 0

    # Sample frames at intervals
    current_time = 0
    while current_time < duration:
        frame_number = int(current_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            quality = calculate_frame_quality(frame)
            if quality > best_quality:
                best_quality = quality
                best_frame = frame.copy()
                best_timestamp = current_time

        current_time += sample_interval

    cap.release()

    if best_frame is None:
        raise ValueError("Could not extract any frames from video")

    # Generate output path if not provided
    if output_path is None:
        video_name = Path(video_path).stem
        output_dir = Path(video_path).parent / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(
            output_dir / f"{video_name}_frame_best_{int(best_timestamp)}s.png"
        )

    # Save best frame
    cv2.imwrite(output_path, best_frame)
    return output_path


def extract_ai_selected_frame(
    video_path: str,
    num_candidates: int = 5,
    output_path: Optional[str] = None,
) -> str:
    """
    Use AI (Gemini Vision API) to select the most engaging frame from video.

    Args:
        video_path: Path to video file
        num_candidates: Number of candidate frames to analyze (default: 5)
        output_path: Optional output path for frame image

    Returns:
        str: Path to extracted frame image
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Fallback to best frame selection if API key not available
        return extract_best_frame(video_path, output_path=output_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    # Sample frames evenly across video
    candidate_frames = []
    candidate_timestamps = []

    for i in range(num_candidates):
        timestamp = (duration / (num_candidates + 1)) * (i + 1)
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            candidate_frames.append(frame)
            candidate_timestamps.append(timestamp)

    cap.release()

    if not candidate_frames:
        raise ValueError("Could not extract any frames from video")

    # Use Gemini Vision API to select best frame
    client = genai.Client(api_key=api_key)

    # Encode frames as images
    frame_paths = []
    try:
        for i, frame in enumerate(candidate_frames):
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, mode="wb"
            )
            cv2.imwrite(temp_file.name, frame)
            frame_paths.append(temp_file.name)
            temp_file.close()

        # Analyze frames with Gemini
        best_idx = 0
        best_score = 0

        prompt = """Analyze these video frames and select the most engaging, representative frame. 
        Consider: visual appeal, subject clarity, composition, color, and overall engagement.
        Respond with just the frame number (1-{}) that is the best choice.""".format(
            len(candidate_frames)
        )

        # For simplicity, analyze each frame individually and score them
        # In a production system, you might send all frames in one request
        scores = []
        for frame_path in frame_paths:
            with open(frame_path, "rb") as f:
                image_data = f.read()

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[
                    prompt,
                    genai.types.Part(
                        inline_data=genai.types.Blob(
                            data=image_data, mime_type="image/png"
                        )
                    ),
                ],
            )

            # Simple scoring: count positive keywords in response
            response_text = response.text.lower()
            positive_keywords = [
                "engaging",
                "clear",
                "good",
                "best",
                "representative",
                "appealing",
            ]
            score = sum(1 for keyword in positive_keywords if keyword in response_text)
            scores.append(score)

        # Select frame with highest score
        best_idx = scores.index(max(scores))

    finally:
        # Cleanup temp files
        for path in frame_paths:
            try:
                os.unlink(path)
            except:
                pass

    best_frame = candidate_frames[best_idx]
    best_timestamp = candidate_timestamps[best_idx]

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


def frame_extractor(
    video_input,
    strategy: Literal["middle", "best", "ai", "custom"] = "middle",
    custom_timestamp: Optional[float] = None,
) -> str:
    """
    Extract a representative frame from video.

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        strategy: Extraction strategy - "middle" (default), "best", "ai", or "custom"
        custom_timestamp: Timestamp in seconds (required if strategy is "custom")

    Returns:
        str: Path to extracted frame image (PNG format)

    Extraction Strategies:
        - "middle": Extract frame at middle of video (15s for 30s video)
        - "best": Analyze multiple frames and select best based on quality metrics
        - "ai": Use Gemini Vision API to select most engaging frame
        - "custom": Extract frame at specified timestamp
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

        # Get video duration for middle frame calculation
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        if duration == 0:
            raise ValueError("Video has zero duration")

        # Extract frame based on strategy
        if strategy == "middle":
            # Extract frame at middle of video
            timestamp = duration / 2.0
            return extract_frame_at_timestamp(video_path, timestamp)

        elif strategy == "best":
            # Extract best quality frame
            return extract_best_frame(video_path)

        elif strategy == "ai":
            # Use AI to select best frame
            return extract_ai_selected_frame(video_path)

        elif strategy == "custom":
            # Extract frame at custom timestamp
            if custom_timestamp is None:
                raise ValueError("custom_timestamp is required when strategy is 'custom'")
            if custom_timestamp < 0 or custom_timestamp > duration:
                raise ValueError(
                    f"custom_timestamp must be between 0 and {duration} seconds"
                )
            return extract_frame_at_timestamp(video_path, custom_timestamp)

        else:
            raise ValueError(
                f"Invalid strategy: {strategy}. Must be 'middle', 'best', 'ai', or 'custom'"
            )

    except Exception as e:
        raise Exception(f"Error extracting frame: {str(e)}")


import cv2
import os
import tempfile
from pathlib import Path
from typing import Optional
import google.genai as genai


def frame_extractor(
    video_input,
    num_candidates: int = 5,
    output_path: Optional[str] = None,
) -> str:
    """
    Extract a representative frame from video using AI (Gemini Vision API).

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        num_candidates: Number of candidate frames to analyze (default: 5)
        output_path: Optional output path for frame image

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

        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for AI frame extraction"
            )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        if duration == 0:
            cap.release()
            raise ValueError("Video has zero duration")

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

    except Exception as e:
        raise Exception(f"Error extracting frame: {str(e)}")


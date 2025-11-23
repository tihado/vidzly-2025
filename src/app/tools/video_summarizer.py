import cv2
import json
import os
import mimetypes
import re
import google.genai as genai


def video_summarizer(video_input, fps: float = 2.0) -> str:
    """
    Analyze video content and generate a text summary describing what's in the video.
    Uses Google Gemini's native video understanding capabilities.

    Args:
        video_input: Video file path (str) or tuple (video_path, subtitle_path) from Gradio
        fps (float): Frames per second for video processing by Gemini (default: 2.0, range: 0.1-24.0)

    Returns:
        str: JSON string containing video summary with key scenes, detected objects/activities, mood tags, and thumbnail_timeframe (in seconds)
    """
    try:
        # Handle Gradio video input format (can be tuple or string)
        if isinstance(video_input, tuple):
            video_path = video_input[0]
        elif isinstance(video_input, str):
            video_path = video_input
        else:
            return json.dumps({"error": "Invalid video input format"})

        # Validate video file exists
        if not video_path or not os.path.exists(video_path):
            return json.dumps({"error": f"Video file not found: {video_path}"})

        # Extract video metadata for response
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return json.dumps({"error": "Could not open video file"})

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / video_fps if video_fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Use Google Gemini API to analyze video
        # Note: You'll need to set GOOGLE_API_KEY environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback: return basic metadata without AI analysis
            # Use middle of video as default thumbnail timeframe
            thumbnail_timeframe = round(duration / 2, 2) if duration > 0 else 0
            return json.dumps(
                {
                    "duration": round(duration, 2),
                    "resolution": f"{width}x{height}",
                    "fps": round(video_fps, 2),
                    "frame_count": frame_count,
                    "summary": "Video analysis requires GOOGLE_API_KEY environment variable",
                    "key_scenes": [],
                    "detected_objects": [],
                    "mood_tags": [],
                    "thumbnail_timeframe": thumbnail_timeframe,
                }
            )

        # Initialize the client with API key
        client = genai.Client(api_key=api_key)

        # Read video file as bytes
        with open(video_path, "rb") as f:
            video_data = f.read()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type or not mime_type.startswith("video/"):
            # Default to mp4 if cannot determine
            mime_type = "video/mp4"

        # Create comprehensive prompt for video analysis
        prompt = """Analyze this video and provide a comprehensive summary including:

1. Overall video description - What is the main content and purpose of this video?
2. Key scenes and moments - Describe the most important scenes, their timestamps, and what happens in each
3. Detected objects/activities - List the main objects, people, activities, or subjects visible in the video
4. Mood and style tags - Identify the mood and style (e.g., energetic, calm, dramatic, fun, professional, casual, bright, dark, colorful, minimalist, fast-paced, slow-paced)
5. Visual style description - Describe the visual aesthetics, color palette, lighting, and overall style
6. Recommended thumbnail timestamp - Suggest the best timestamp (in seconds) to use as a thumbnail. This should be a visually representative moment that captures the essence of the video. Format your answer as: "THUMBNAIL_TIMESTAMP: X.XX seconds" where X.XX is the timestamp.

Format your response as a structured, detailed summary that captures the essence of the video."""

        # Create VideoMetadata with fps parameter and create a Part with inline data
        video_metadata = genai.types.VideoMetadata(fps=fps)
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

        # Parse and structure the response
        summary_text = response.text

        # Extract mood tags (simple keyword extraction)
        mood_keywords = [
            "energetic",
            "calm",
            "dramatic",
            "fun",
            "professional",
            "casual",
            "bright",
            "dark",
            "colorful",
            "minimalist",
            "fast-paced",
            "slow-paced",
        ]
        detected_moods = [
            mood for mood in mood_keywords if mood.lower() in summary_text.lower()
        ]

        # Extract thumbnail timestamp from response
        thumbnail_timeframe = None
        # Try to find "THUMBNAIL_TIMESTAMP: X.XX seconds" pattern
        timestamp_pattern = r"THUMBNAIL_TIMESTAMP:\s*([\d.]+)\s*seconds?"
        match = re.search(timestamp_pattern, summary_text, re.IGNORECASE)
        if match:
            try:
                thumbnail_timeframe = float(match.group(1))
                # Ensure timestamp is within video duration
                if thumbnail_timeframe > duration:
                    thumbnail_timeframe = duration / 2
                elif thumbnail_timeframe < 0:
                    thumbnail_timeframe = 0
            except ValueError:
                thumbnail_timeframe = None
        
        # Fallback: use middle of video if extraction failed
        if thumbnail_timeframe is None:
            thumbnail_timeframe = round(duration / 2, 2) if duration > 0 else 0

        # Structure the response
        result = {
            "duration": round(duration, 2),
            "resolution": f"{width}x{height}",
            "fps": round(video_fps, 2),
            "frame_count": frame_count,
            "summary": summary_text,
            "mood_tags": detected_moods if detected_moods else ["general"],
            "thumbnail_timeframe": round(thumbnail_timeframe, 2),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error processing video: {str(e)}"})

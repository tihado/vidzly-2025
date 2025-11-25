import cv2
import json
import os
import mimetypes
import google.genai as genai
from typing import Optional


def script_generator(video_inputs, user_prompt: Optional[str] = None) -> str:
    """
    Generate a detailed video script based on multiple video materials.
    Uses Google Gemini's native video understanding to analyze material videos
    and create a comprehensive script for making a short video.

    Args:
        video_inputs: List of video file paths or Gradio video inputs
        user_prompt (str, optional): User's custom prompt/request. If not provided,
                                    AI will generate a script based on material analysis.

    Returns:
        str: JSON string containing a detailed video script with scene breakdowns,
             timing, transitions, and creative suggestions
    """
    try:
        # Handle various input formats
        if not video_inputs:
            return json.dumps({"error": "No video files provided"})

        # Normalize video inputs to list of paths
        video_paths = []
        if isinstance(video_inputs, list):
            for video_input in video_inputs:
                if isinstance(video_input, tuple):
                    video_paths.append(video_input[0])
                elif isinstance(video_input, str):
                    video_paths.append(video_input)
        elif isinstance(video_inputs, str):
            video_paths = [video_inputs]
        elif isinstance(video_inputs, tuple):
            video_paths = [video_inputs[0]]
        else:
            return json.dumps({"error": "Invalid video input format"})

        # Validate all video files exist and extract metadata
        videos_metadata = []
        for idx, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                return json.dumps({"error": f"Video file not found: {video_path}"})

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return json.dumps({"error": f"Could not open video file: {video_path}"})

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / video_fps if video_fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            videos_metadata.append({
                "index": idx,
                "filename": os.path.basename(video_path),
                "duration": round(duration, 2),
                "resolution": f"{width}x{height}",
                "fps": round(video_fps, 2),
                "frame_count": frame_count,
            })

        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return json.dumps({
                "error": "GOOGLE_API_KEY environment variable not set",
                "videos_analyzed": videos_metadata,
                "script": "AI script generation requires GOOGLE_API_KEY",
            })

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Prepare video parts for multimodal input
        video_parts = []
        for video_path in video_paths:
            with open(video_path, "rb") as f:
                video_data = f.read()

            mime_type, _ = mimetypes.guess_type(video_path)
            if not mime_type or not mime_type.startswith("video/"):
                mime_type = "video/mp4"

            video_metadata = genai.types.VideoMetadata(fps=2.0)
            video_blob = genai.types.Blob(data=video_data, mime_type=mime_type)
            video_part = genai.types.Part(
                inline_data=video_blob,
                videoMetadata=video_metadata,
            )
            video_parts.append(video_part)

        # Create comprehensive prompt
        if user_prompt and user_prompt.strip():
            # Use user's prompt
            base_prompt = f"""User Request: {user_prompt}

Based on the user's request above and the provided video materials, create a detailed video production script."""
        else:
            # Generate default prompt
            base_prompt = """Analyze the provided video materials and create a comprehensive video production script for making an engaging short video."""

        full_prompt = f"""{base_prompt}

I have {len(video_paths)} video file(s) as source material. Please analyze each video and create a detailed script that includes:

1. **Concept Overview**: Describe the overall theme, message, and creative direction for the final video.

2. **Target Duration**: Recommend optimal video length based on content (typically 15-60 seconds for short-form).

3. **Scene Breakdown**: For each scene in the final video, specify:
   - Scene number and description
   - Which source video to use (reference by index: 0, 1, 2, etc.)
   - Exact start and end timestamps from the source video
   - Duration of the scene
   - Visual description and key moments
   - Suggested transitions (e.g., "fade", "crossfade", "wipe", "zoom")

4. **Audio Recommendations**: 
   - Background music mood and style
   - BPM (beats per minute) suggestion
   - Volume levels and audio effects
   - Any voiceover or text-to-speech suggestions

5. **Text Overlays**: Suggest any text, captions, or titles to add, including:
   - Text content
   - Timing (when to appear)
   - Style suggestions (font, size, position, animation)

6. **Visual Effects**: Recommend any filters, color grading, speed adjustments, or special effects.

7. **Pacing & Flow**: Explain the rhythm and flow of the video, including any build-ups, climaxes, or emotional arcs.

8. **Call-to-Action**: Suggest ending elements (e.g., logo, text, link, subscribe prompt).

Please provide the script in a structured JSON format that includes:
- "concept": overall theme and message
- "target_duration": recommended total duration in seconds
- "total_duration": sum of all scene durations
- "scenes": array of scene objects with fields:
  - "scene_id": integer
  - "source_video": index of source video (0-based)
  - "start_time": start timestamp in source video (seconds)
  - "end_time": end timestamp in source video (seconds)
  - "duration": scene duration (seconds)
  - "description": what happens in this scene
  - "transition_in": transition effect when entering scene
  - "transition_out": transition effect when exiting scene
- "audio": object with "mood", "style", "bpm", "volume"
- "text_overlays": array of text overlay objects
- "visual_effects": array of suggested effects
- "call_to_action": string description

Also provide a human-readable narrative version of the script."""

        # Call Gemini API with all video materials
        contents = [full_prompt] + video_parts
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,  # type: ignore
        )

        # Parse response
        script_text: str = response.text if response.text else ""

        # Try to extract JSON if present
        json_match = None
        if "```json" in script_text:
            # Extract JSON code block
            import re
            json_pattern = r"```json\s*([\s\S]*?)\s*```"
            match = re.search(json_pattern, script_text)
            if match:
                json_match = match.group(1)

        # Structure the response
        result = {
            "videos_analyzed": videos_metadata,
            "user_prompt": user_prompt if user_prompt else "Auto-generated based on materials",
            "script_narrative": script_text,
        }

        # If we found structured JSON, try to parse and include it
        if json_match:
            try:
                structured_script = json.loads(json_match)
                result["structured_script"] = structured_script
            except json.JSONDecodeError:
                result["structured_script_parse_error"] = "Could not parse JSON from response"

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error generating script: {str(e)}"})

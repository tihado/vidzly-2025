import os
import json
import tempfile
from typing import Optional, List, Union, Tuple, Callable
from pathlib import Path
import google.genai as genai

from tools.video_summarizer import video_summarizer
from tools.video_clipper import video_clipper
from tools.video_composer import video_composer
from tools.music_selector import music_selector

# Import agent workflow to use as the full workflow
from workflow_agent import agent_workflow


def generate_script_from_summary(
    video_summaries: List[dict],
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
) -> dict:
    """
    Generate a video composition script from video summaries and user description.
    Uses Google Gemini to intelligently create a script for a 30-second video.

    Args:
        video_summaries: List of video summary dictionaries from video_summarizer
        user_description: Optional user description of desired mood/style
        target_duration: Target duration in seconds (default: 30.0)

    Returns:
        dict: Script dictionary compatible with video_composer
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback: create a simple script using first video
            if not video_summaries:
                raise ValueError("No video summaries provided")

            summary = video_summaries[0]
            duration = summary.get("duration", target_duration)
            clip_duration = min(duration, target_duration)

            return {
                "total_duration": clip_duration,
                "scenes": [
                    {
                        "scene_id": 1,
                        "source_video": 0,
                        "start_time": 0.0,
                        "end_time": clip_duration,
                        "duration": clip_duration,
                        "transition_in": "fade",
                        "transition_out": "fade",
                    }
                ],
            }

        client = genai.Client(api_key=api_key)

        # Build prompt for script generation
        summaries_text = "\n\n".join(
            [
                f"Video {i+1}:\n{json.dumps(s, indent=2)}"
                for i, s in enumerate(video_summaries)
            ]
        )

        user_desc_text = (
            f"\n\nUser Description: {user_description}" if user_description else ""
        )

        prompt = f"""You are a professional video editor creating a {target_duration}-second short-form video.

Here are the video summaries:
{summaries_text}
{user_desc_text}

Create a detailed video composition script that:
1. Selects the most engaging and relevant scenes from the videos
2. Creates a coherent narrative flow
3. Uses appropriate transitions (cut, fade, or crossfade)
4. Ensures the total duration is approximately {target_duration} seconds
5. Distributes scenes evenly across the duration

Return ONLY a valid JSON object with this exact structure:
{{
    "total_duration": {target_duration},
    "scenes": [
        {{
            "scene_id": 1,
            "source_video": 0,
            "start_time": 0.0,
            "end_time": 5.0,
            "duration": 5.0,
            "transition_in": "fade",
            "transition_out": "crossfade"
        }}
    ],
    "music": {{
        "mood": "energetic",
        "bpm": 120,
        "volume": 0.5
    }}
}}

Rules:
- source_video is 0-based index (0 for first video, 1 for second, etc.)
- Each scene must have start_time, end_time, and duration
- Total of all scene durations should be approximately {target_duration} seconds
- Use transitions: "cut", "fade", or "crossfade"
- Extract mood tags from the video summaries for the music section
- Return ONLY the JSON, no other text"""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt],
        )

        # Extract JSON from response
        response_text = response.text.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        script = json.loads(response_text)

        # Validate and ensure total_duration is set
        if "total_duration" not in script:
            script["total_duration"] = target_duration

        return script

    except json.JSONDecodeError as e:
        # Fallback to simple script
        if not video_summaries:
            raise ValueError("No video summaries provided")

        summary = video_summaries[0]
        duration = summary.get("duration", target_duration)
        clip_duration = min(duration, target_duration)

        # Extract mood from summary
        mood_tags = summary.get("mood_tags", ["energetic"])
        mood = mood_tags[0] if mood_tags else "energetic"

        return {
            "total_duration": clip_duration,
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,
                    "start_time": 0.0,
                    "end_time": clip_duration,
                    "duration": clip_duration,
                    "transition_in": "fade",
                    "transition_out": "fade",
                }
            ],
            "music": {
                "mood": mood,
                "volume": 0.5,
            },
        }
    except Exception as e:
        raise Exception(f"Error generating script: {str(e)}")


def full_workflow(
    video_inputs: Union[str, List[str], Tuple],
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
    fps: float = 2.0,
    generate_music: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str, str]:
    """
    Complete agent-controlled workflow: AI Agent analyzes videos, generates script,
    creates music, and composes the final video using MCP tools.

    This function uses the agent_workflow which intelligently orchestrates the entire
    video creation process using AI reasoning and MCP tools.

    Args:
        video_inputs: Single video path, list of video paths, or Gradio file input
        user_description: Optional description of desired mood/style
        target_duration: Target duration in seconds (default: 30.0)
        fps: FPS for video analysis (default: 2.0, used internally by agent)
        generate_music: Whether to generate music (default: True)
        progress_callback: Optional callback function(status_message) for progress updates

    Returns:
        Tuple of (final_video_path, summary_json, script_json)
    """
    # Delegate to agent_workflow (fps parameter is handled internally by agent)
    return agent_workflow(
        video_inputs=video_inputs,
        user_description=user_description,
        target_duration=target_duration,
        generate_music=generate_music,
        progress_callback=progress_callback,
    )

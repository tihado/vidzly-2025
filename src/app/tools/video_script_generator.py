import os
import json
from typing import Optional, List, Union
import google.genai as genai


def video_script_generator(
    video_summaries: Union[str, List[dict], List[str]],
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
) -> str:
    """
    Create a detailed script/storyboard for the final 30-second video.
    Uses Google Gemini API to intelligently generate a script based on video summaries
    and user requirements.

    Args:
        video_summaries: Video summaries from video_summarizer tool.
                        Can be:
                        - JSON string (single summary)
                        - List of dict objects (multiple summaries)
                        - List of JSON strings (multiple summaries)
        user_description: Optional user description of desired mood/style/content
        target_duration: Target duration in seconds (default: 30.0)

    Returns:
        str: JSON string containing detailed script with:
            - Scene sequence with source video and timestamps
            - Duration for each scene segment (must sum to ~target_duration seconds)
            - Transition types between scenes (cut, fade, crossfade)
            - Pacing and rhythm plan
            - Music synchronization points (beat markers, mood changes)
            - Overall narrative structure and flow
            - Visual style recommendations

    Example output format:
    {
        "total_duration": 30.0,
        "scenes": [
            {
                "scene_id": 1,
                "source_video": 0,
                "start_time": 5.2,
                "end_time": 8.5,
                "duration": 3.3,
                "description": "Opening shot of landscape",
                "transition_in": "fade",
                "transition_out": "crossfade"
            },
            ...
        ],
        "music": {
            "mood": "energetic",
            "bpm": 120,
            "sync_points": [0.0, 7.5, 15.0, 22.5, 30.0],
            "volume": 0.5
        },
        "pacing": "fast",
        "narrative_structure": "hook -> build -> climax -> resolution",
        "visual_style": "bright, colorful, dynamic"
    }
    """
    try:
        # Parse video summaries input
        summaries_list = []
        if isinstance(video_summaries, str):
            # JSON string - could be a single object or an array
            try:
                parsed = json.loads(video_summaries)
                if isinstance(parsed, list):
                    # It's a JSON array
                    summaries_list = parsed
                else:
                    # It's a single JSON object
                    summaries_list = [parsed]
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for video_summaries")
        elif isinstance(video_summaries, list):
            # List of summaries
            for summary in video_summaries:
                if isinstance(summary, str):
                    try:
                        summaries_list.append(json.loads(summary))
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"Invalid JSON format in video_summaries: {summary}"
                        )
                elif isinstance(summary, dict):
                    summaries_list.append(summary)
                else:
                    raise ValueError(
                        f"Invalid summary type: {type(summary).__name__}. "
                        "Expected dict or JSON string."
                    )
        else:
            raise ValueError(
                f"Invalid video_summaries type: {type(video_summaries).__name__}. "
                "Expected str, list of dicts, or list of JSON strings."
            )

        if not summaries_list:
            raise ValueError("No video summaries provided")

        # Validate target_duration
        if target_duration <= 0:
            raise ValueError("target_duration must be greater than 0")

        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback: create a simple script using first video
            summary = summaries_list[0]
            duration = summary.get("duration", target_duration)
            clip_duration = min(duration, target_duration)

            # Extract mood from summary
            mood_tags = summary.get("mood_tags", ["energetic"])
            mood = mood_tags[0] if mood_tags else "energetic"

            fallback_script = {
                "total_duration": clip_duration,
                "scenes": [
                    {
                        "scene_id": 1,
                        "source_video": 0,
                        "start_time": 0.0,
                        "end_time": clip_duration,
                        "duration": clip_duration,
                        "description": summary.get("summary", "Video clip")[:100],
                        "transition_in": "fade",
                        "transition_out": "fade",
                    }
                ],
                "music": {
                    "mood": mood,
                    "volume": 0.5,
                },
                "pacing": "moderate",
                "narrative_structure": "single scene",
            }
            return json.dumps(fallback_script, indent=2)

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Build prompt for script generation
        summaries_text = "\n\n".join(
            [
                f"Video {i+1}:\n{json.dumps(s, indent=2)}"
                for i, s in enumerate(summaries_list)
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
2. Creates a coherent narrative flow with a clear structure (hook -> build -> climax -> resolution)
3. Uses appropriate transitions (cut, fade, or crossfade) between scenes
4. Ensures the total duration is approximately {target_duration} seconds (within ±2 seconds)
5. Distributes scenes evenly across the duration, considering pacing
6. Identifies music mood, BPM, and sync points for rhythm matching
7. Provides visual style recommendations based on the content

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
            "description": "Brief description of what happens in this scene",
            "transition_in": "fade",
            "transition_out": "crossfade"
        }},
        {{
            "scene_id": 2,
            "source_video": 1,
            "start_time": 10.0,
            "end_time": 15.0,
            "duration": 5.0,
            "description": "Brief description of what happens in this scene",
            "transition_in": "crossfade",
            "transition_out": "fade"
        }}
    ],
    "music": {{
        "mood": "energetic",
        "bpm": 120,
        "sync_points": [0.0, 7.5, 15.0, 22.5, 30.0],
        "volume": 0.5
    }},
    "pacing": "fast",
    "narrative_structure": "hook -> build -> climax -> resolution",
    "visual_style": "bright, colorful, dynamic"
}}

Rules:
- source_video is 0-based index (0 for first video, 1 for second, etc.)
- Each scene must have start_time, end_time, and duration
- Total of all scene durations should be approximately {target_duration} seconds (±2 seconds tolerance)
- Use transitions: "cut", "fade", or "crossfade"
- Extract mood tags from the video summaries for the music section
- sync_points should be evenly distributed or aligned to scene transitions
- pacing should be one of: "slow", "moderate", "fast", "very-fast"
- narrative_structure should describe the flow (e.g., "hook -> build -> climax -> resolution")
- visual_style should describe the aesthetic (e.g., "bright, colorful, dynamic" or "dark, moody, cinematic")
- Return ONLY the JSON, no other text or markdown formatting"""

        # Generate script using Gemini
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

        # Validate script structure
        if not isinstance(script, dict):
            raise ValueError("Generated script is not a valid dictionary")

        # Ensure required fields exist
        if "total_duration" not in script:
            script["total_duration"] = target_duration

        if "scenes" not in script:
            raise ValueError("Generated script missing 'scenes' field")

        if not isinstance(script["scenes"], list) or len(script["scenes"]) == 0:
            raise ValueError("Generated script must contain at least one scene")

        # Validate scene durations sum to approximately target_duration
        total_scene_duration = sum(
            scene.get("duration", 0) for scene in script["scenes"]
        )
        if abs(total_scene_duration - target_duration) > 5.0:
            # Adjust durations proportionally if they're way off
            if total_scene_duration > 0:
                scale_factor = target_duration / total_scene_duration
                for scene in script["scenes"]:
                    if "duration" in scene:
                        scene["duration"] = round(scene["duration"] * scale_factor, 2)
                    if "start_time" in scene and "end_time" in scene:
                        # Recalculate end_time based on scaled duration
                        scene["end_time"] = round(
                            scene["start_time"] + scene["duration"], 2
                        )
                script["total_duration"] = target_duration

        # Ensure music section exists
        if "music" not in script:
            # Extract mood from summaries
            mood_tags = []
            for summary in summaries_list:
                tags = summary.get("mood_tags", [])
                if isinstance(tags, list):
                    mood_tags.extend(tags)
            mood = mood_tags[0] if mood_tags else "energetic"
            script["music"] = {
                "mood": mood,
                "volume": 0.5,
            }

        # Add optional fields if missing
        if "pacing" not in script:
            script["pacing"] = "moderate"

        if "narrative_structure" not in script:
            script["narrative_structure"] = "linear"

        if "visual_style" not in script:
            script["visual_style"] = "standard"

        return json.dumps(script, indent=2)

    except json.JSONDecodeError as e:
        # Fallback to simple script
        if not summaries_list:
            raise ValueError("No video summaries provided")

        summary = summaries_list[0]
        duration = summary.get("duration", target_duration)
        clip_duration = min(duration, target_duration)

        # Extract mood from summary
        mood_tags = summary.get("mood_tags", ["energetic"])
        mood = mood_tags[0] if mood_tags else "energetic"

        fallback_script = {
            "total_duration": clip_duration,
            "scenes": [
                {
                    "scene_id": 1,
                    "source_video": 0,
                    "start_time": 0.0,
                    "end_time": clip_duration,
                    "duration": clip_duration,
                    "description": (
                        summary.get("summary", "Video clip")[:100]
                        if isinstance(summary.get("summary"), str)
                        else "Video clip"
                    ),
                    "transition_in": "fade",
                    "transition_out": "fade",
                }
            ],
            "music": {
                "mood": mood,
                "volume": 0.5,
            },
            "pacing": "moderate",
            "narrative_structure": "single scene",
        }
        return json.dumps(fallback_script, indent=2)

    except Exception as e:
        raise Exception(f"Error generating video script: {str(e)}")

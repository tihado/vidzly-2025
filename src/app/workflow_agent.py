import os
import json
import tempfile
from typing import Optional, List, Union, Tuple, Callable, Dict, Any
from pathlib import Path

from tools.video_summarizer import video_summarizer
from tools.video_clipper import video_clipper
from tools.video_composer import video_composer
from tools.music_selector import music_selector
from tools.video_script_generator import video_script_generator
from tools.frame_extractor import frame_extractor
from tools.thumbnail_generator import thumbnail_generator
from google.adk.agents import LlmAgent
from google.adk.tools import Tool


def create_script_writer_tools(
    video_paths: List[str], target_duration: float, generate_music: bool
):
    """Create ADK Tool wrappers for script writer/director agent (planning tools)."""

    def video_summarizer_tool(video_index: int, fps: float = 2.0) -> str:
        """Analyze video content and extract key scenes, mood tags, and descriptions.

        Args:
            video_index: Index of video in the input list (0-based)
            fps: Frames per second for analysis (default: 2.0)

        Returns:
            JSON string with video summary
        """
        if video_index >= len(video_paths):
            return json.dumps({"error": f"Video index {video_index} out of range"})
        return video_summarizer(video_paths[video_index], fps=fps)

    def music_selector_tool(
        mood: str = "energetic",
        style: Optional[str] = None,
        target_duration: Optional[float] = None,
        looping: bool = True,
        prompt_influence: float = 0.3,
    ) -> str:
        """Generate background music based on mood and style.

        Args:
            mood: Mood tags (str, e.g., 'energetic', 'calm, dramatic')
            style: Optional style (str, e.g., 'cinematic', 'modern', 'retro')
            target_duration: Target duration in seconds (max 30.0, default: uses target_duration)
            looping: Whether music should loop (default: True)
            prompt_influence: How closely output matches prompt (0-1, default: 0.3)

        Returns:
            Path to generated audio file
        """
        if not generate_music:
            return json.dumps({"error": "Music generation disabled"})
        duration = target_duration if target_duration else min(target_duration, 30.0)
        try:
            return music_selector(
                mood=mood,
                style=style,
                target_duration=duration,
                looping=looping,
                prompt_influence=prompt_influence,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    def video_script_generator_tool(
        video_summaries_json: str, user_description: Optional[str] = None
    ) -> str:
        """Generate a detailed video composition script from video summaries.

        Args:
            video_summaries_json: JSON string containing video summaries (can be single object or array)
            user_description: Optional user description of desired mood/style/content

        Returns:
            JSON string containing detailed script with scenes, transitions, music config, etc.
        """
        try:
            return video_script_generator(
                video_summaries=video_summaries_json,
                user_description=user_description,
                target_duration=target_duration,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    # Create ADK Tool objects for script writer
    tools = [
        Tool(
            name="video_summarizer",
            description="Analyzes video content and extracts key scenes, mood tags, and descriptions. Use this to understand what's in each video.",
            func=video_summarizer_tool,
        ),
        Tool(
            name="video_script_generator",
            description="Generates a detailed video composition script from video summaries. Use this after analyzing videos to create a script that defines scenes, timings, transitions, and music configuration. The script will be used by video_composer.",
            func=video_script_generator_tool,
        ),
        Tool(
            name="music_selector",
            description="Generates background music based on mood and style. Use this to create music that matches the video's mood.",
            func=music_selector_tool,
        ),
    ]

    return tools


def create_video_editor_tools(
    video_paths: List[str], target_duration: float, generate_music: bool
):
    """Create ADK Tool wrappers for video editor agent (execution tools)."""

    def video_composer_tool(
        script_json: str,
        music_path: Optional[str] = None,
        thumbnail_image: Optional[str] = None,
    ) -> str:
        """Combine video clips with transitions and music according to a script.

        Args:
            script_json: JSON script string with scenes and transitions
            music_path: Optional path to music file (str or None)
            thumbnail_image: Optional path to thumbnail image file. If provided, will be overlaid on the first frame.

        Returns:
            Path to final composed video
        """
        try:
            return video_composer(
                script=script_json,
                video_clips=video_paths,
                music_path=music_path,
                thumbnail_image=thumbnail_image,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    def frame_extractor_tool(
        video_index: int,
        output_path: Optional[str] = None,
        thumbnail_timeframe: Optional[float] = None,
    ) -> str:
        """Extract a representative frame from a video for thumbnail generation.

        Args:
            video_index: Index of video in the input list (0-based)
            output_path: Optional path where the frame should be saved
            thumbnail_timeframe: Optional timestamp in seconds to use for frame extraction.
                               If not provided, uses AI to determine the best timestamp.

        Returns:
            Path to extracted frame image (PNG format)
        """
        if video_index >= len(video_paths):
            return json.dumps({"error": f"Video index {video_index} out of range"})
        try:
            return frame_extractor(
                video_input=video_paths[video_index],
                output_path=output_path,
                thumbnail_timeframe=thumbnail_timeframe,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    def thumbnail_generator_tool(
        image_path: str, summary: str, output_path: Optional[str] = None
    ) -> str:
        """Generate a highly engaging and funny thumbnail image for a video/social media post.

        Args:
            image_path: Path to the input image (typically from frame_extractor)
            summary: Text summary of the video content (used to generate appropriate text and stickers)
            output_path: Optional path where the thumbnail should be saved

        Returns:
            Path to the generated thumbnail image (PNG format)
        """
        try:
            return thumbnail_generator(
                image_input=image_path,
                summary=summary,
                output_path=output_path,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    # Create ADK Tool objects for video editor
    tools = [
        Tool(
            name="video_composer",
            description="Combines video clips with transitions and music according to a script. Use this as the final step to create the composed video. Optionally accepts a thumbnail image that will be overlaid on the first frame.",
            func=video_composer_tool,
        ),
        Tool(
            name="frame_extractor",
            description="Extracts a representative frame from a video. Use this to get a good frame for thumbnail generation. Can use AI to find the best timestamp or accept a specific timestamp.",
            func=frame_extractor_tool,
        ),
        Tool(
            name="thumbnail_generator",
            description="Generates a highly engaging and funny thumbnail image for a video/social media post. Takes an image (typically from frame_extractor) and a video summary to create an eye-catching thumbnail with text overlays and stickers.",
            func=thumbnail_generator_tool,
        ),
    ]

    return tools


def script_writer_agent(
    video_paths: List[str],
    user_description: Optional[str],
    target_duration: float,
    generate_music: bool,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str, Optional[str]]:
    """
    Script Writer/Director Agent: Analyzes videos, creates composition script, and generates music.

    Args:
        video_paths: List of video file paths
        user_description: Optional description of desired mood/style
        target_duration: Target duration in seconds
        generate_music: Whether to generate music
        progress_callback: Optional callback function for progress updates

    Returns:
        Tuple of (script_json, summary_json, music_path)
    """

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    if progress_callback:
        progress_callback("📝 Script Writer Agent: Initializing...")

    tools = create_script_writer_tools(video_paths, target_duration, generate_music)

    instruction = f"""You are a video script writer and director. Your role is to analyze video content and create a detailed composition script.

**Your Responsibilities:**
1. Analyze each video to understand its content, mood, and key scenes
2. Create a comprehensive composition script that defines how videos should be edited together
3. Generate appropriate background music that matches the video's mood (if enabled)

**Task Details:**
- Input: {len(video_paths)} video file(s)
- Target duration: {target_duration} seconds
- User requirements: {user_description if user_description else 'None specified'}
- Generate music: {generate_music}

**Your Approach:**
1. Use video_summarizer to analyze each video (use video_index 0, 1, etc.)
2. Collect all video summaries and pass them to video_script_generator to create a detailed composition script
3. If music generation is enabled, use music_selector to generate appropriate background music based on the script's mood

**Script Format:**
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
        "volume": 0.5
    }}
}}

Focus on creating a well-structured script that will guide the video editor."""

    agent = LlmAgent(
        name="script_writer_agent",
        model="gemini-2.5-flash-lite",
        instruction=instruction,
        tools=tools,
    )

    task = f"""Create a {target_duration}-second video composition script from {len(video_paths)} video file(s).

Steps:
1. Analyze all videos using video_summarizer (use video_index 0, 1, etc. for each video)
2. Collect all video summaries and pass them to video_script_generator to create a detailed composition script
3. Generate music if needed using music_selector (extract mood from the script)

User requirements: {user_description if user_description else 'None'}"""

    if progress_callback:
        progress_callback("📝 Script Writer: Reasoning and planning...")

    response = agent.run(task)

    # Extract results from agent's execution
    # The agent should have executed tools and we need to extract the results
    # ADK tracks tool executions, but we need to parse the response or track state
    response_text = str(response.content if hasattr(response, "content") else response)

    # Try to extract script and music path from response
    import re

    # Look for JSON script in response
    script_match = re.search(r'\{[^{}]*"scenes"[^{}]*\}', response_text, re.DOTALL)
    music_match = re.search(r"/(?:[^/\s]+/)*[^/\s]+\.(?:mp3|wav|m4a)", response_text)

    # The agent should have called the tools, but we need to track the actual results
    # For now, we'll need to re-execute tools to get results, or track them via shared state
    # This is a limitation - ADK should provide better access to tool execution results

    # Since ADK executes tools internally, we need to call them again to get results
    # In a production system, you'd track tool execution results via callbacks or state
    if progress_callback:
        progress_callback("📝 Script Writer: Extracting results...")

    video_summaries = []
    for i, video_path in enumerate(video_paths):
        if progress_callback:
            progress_callback(f"📹 Analyzing video {i+1}/{len(video_paths)}...")
        summary_json = video_summarizer(video_path, fps=2.0)
        video_summaries.append(json.loads(summary_json))

    if progress_callback:
        progress_callback("✍️ Generating script...")

    summaries_json = json.dumps(video_summaries, indent=2)
    script_json_str = video_script_generator(
        video_summaries=summaries_json,
        user_description=user_description,
        target_duration=target_duration,
    )
    script = json.loads(script_json_str)

    music_path = None
    if generate_music:
        if progress_callback:
            progress_callback("🎵 Generating music...")
        mood = (
            script.get("music", {}).get("mood", "energetic") if script else "energetic"
        )
        if not mood and video_summaries:
            mood = video_summaries[0].get("mood_tags", ["energetic"])[0]
        try:
            music_path = music_selector(
                mood=mood,
                target_duration=min(target_duration, 30.0),
                looping=True,
                prompt_influence=0.3,
            )
        except:
            pass

    summary_json = json.dumps(video_summaries, indent=2)
    script_json = json.dumps(script, indent=2)
    return script_json, summary_json, music_path


def video_editor_agent(
    video_paths: List[str],
    script_json: str,
    music_path: Optional[str],
    video_summaries_json: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Video Editor Agent: Executes video composition, frame extraction, and thumbnail generation.

    Args:
        video_paths: List of video file paths
        script_json: JSON script string from script writer agent
        music_path: Optional path to music file
        video_summaries_json: Optional JSON string with video summaries (for thumbnail generation)
        progress_callback: Optional callback function for progress updates

    Returns:
        Tuple of (final_video_path, thumbnail_path)
    """

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    if progress_callback:
        progress_callback("🎬 Video Editor Agent: Initializing...")

    tools = create_video_editor_tools(
        video_paths, 30.0, False
    )  # generate_music not needed here

    instruction = f"""You are a video editor. Your role is to execute video composition and create thumbnails based on a script provided by the script writer.

**Your Responsibilities:**
1. Compose the final video using the provided script
2. Extract representative frames from videos
3. Generate engaging thumbnails for the video

**Available Resources:**
- Script: {script_json[:200]}...
- Music path: {music_path if music_path else 'None'}
- Video files: {len(video_paths)} file(s)

**Your Approach:**
1. First, extract a frame and generate a thumbnail using frame_extractor and thumbnail_generator
2. Use video_composer to combine video clips according to the script, passing the thumbnail_image parameter if a thumbnail was generated
3. The thumbnail will be overlaid on the first frame of the final video

Focus on executing the script precisely and creating high-quality output."""

    agent = LlmAgent(
        name="video_editor_agent",
        model="gemini-2.5-flash-lite",
        instruction=instruction,
        tools=tools,
    )

    task = f"""Execute the video composition and create thumbnails.

Steps:
1. Extract a frame from the first video using frame_extractor (use video_index 0)
2. Generate a thumbnail using thumbnail_generator with the extracted frame
3. Use video_composer with the provided script to create the final video, passing the thumbnail_image parameter

Script: {script_json[:500]}..."""

    if progress_callback:
        progress_callback("🎬 Video Editor: Executing composition...")

    response = agent.run(task)

    # Extract results
    response_text = str(response.content if hasattr(response, "content") else response)

    import re

    video_paths_found = re.findall(
        r"/(?:[^/\s]+/)*[^/\s]+\.(?:mp4|mov|avi|mkv)", response_text
    )
    thumbnail_paths_found = re.findall(
        r"/(?:[^/\s]+/)*[^/\s]+\.(?:png|jpg|jpeg)", response_text
    )

    final_video_path = video_paths_found[-1] if video_paths_found else None
    thumbnail_path = thumbnail_paths_found[-1] if thumbnail_paths_found else None

    # Verify paths exist
    if final_video_path and not os.path.exists(final_video_path):
        final_video_path = None

    if thumbnail_path and not os.path.exists(thumbnail_path):
        thumbnail_path = None

    # Generate thumbnail first if summaries are available
    thumbnail_path = None
    if video_summaries_json:
        try:
            summaries = json.loads(video_summaries_json)
            if summaries:
                # Extract frame from first video
                if progress_callback:
                    progress_callback("🖼️ Extracting frame for thumbnail...")
                frame_path = frame_extractor(video_paths[0])

                # Generate thumbnail
                if progress_callback:
                    progress_callback("🎨 Generating thumbnail...")
                summary_text = (
                    summaries[0].get("description", "")
                    if isinstance(summaries, list)
                    else summaries.get("description", "")
                )
                thumbnail_path = thumbnail_generator(
                    image_input=frame_path,
                    summary=summary_text,
                )
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Thumbnail generation skipped: {str(e)}")

    # If agent didn't complete properly, extract results from tool execution
    # ADK should have executed the tools, but we need to get the actual results
    if not final_video_path:
        if progress_callback:
            progress_callback("🎬 Video Editor: Extracting results...")

        # Re-execute tools to get results (ADK should provide better access to tool results)
        # Pass thumbnail_image if available
        final_video_path = video_composer(
            script=script_json,
            video_clips=video_paths,
            music_path=music_path,
            thumbnail_image=thumbnail_path,
        )

    return final_video_path, thumbnail_path


def agent_workflow(
    video_inputs: Union[str, List[str], Tuple],
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
    generate_music: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str, str]:
    """
    Agent-controlled workflow using Google ADK that intelligently reasons, plans,
    and executes video creation using MCP tools dynamically.

    Args:
        video_inputs: Single video path, list of video paths, or Gradio file input
        user_description: Optional description of desired mood/style
        target_duration: Target duration in seconds (default: 30.0)
        generate_music: Whether to generate music (default: True)
        progress_callback: Optional callback function(status_message) for progress updates

    Returns:
        Tuple of (final_video_path, summary_json, script_json, thumbnail_path)
    """
    try:
        # Handle different input formats
        if progress_callback:
            progress_callback("🤖 Agent initializing...")

        if isinstance(video_inputs, tuple):
            video_paths = [video_inputs[0]]
        elif isinstance(video_inputs, str):
            video_paths = [video_inputs]
        elif isinstance(video_inputs, list):
            processed_paths = []
            for item in video_inputs:
                if isinstance(item, tuple):
                    processed_paths.append(item[0])
                elif isinstance(item, str):
                    processed_paths.append(item)
            video_paths = processed_paths
        else:
            raise ValueError("Invalid video input format")

        if not video_paths:
            raise ValueError("No video files provided")

        # Use two-agent workflow: Script Writer -> Video Editor
        if progress_callback:
            progress_callback("🎬 Starting two-agent workflow...")

        # Step 1: Script Writer/Director Agent
        # This agent analyzes videos, creates the script, and generates music
        script_json, summary_json, music_path = script_writer_agent(
            video_paths=video_paths,
            user_description=user_description,
            target_duration=target_duration,
            generate_music=generate_music,
            progress_callback=progress_callback,
        )

        # Step 2: Video Editor Agent
        # This agent executes the video composition and creates thumbnails
        final_video_path, thumbnail_path = video_editor_agent(
            video_paths=video_paths,
            script_json=script_json,
            music_path=music_path,
            video_summaries_json=summary_json,
            progress_callback=progress_callback,
        )

        if progress_callback:
            progress_callback("✅ Two-agent workflow complete!")

        return final_video_path, summary_json, script_json, thumbnail_path

    except Exception as e:
        error_msg = f"Agent workflow error: {str(e)}"
        if progress_callback:
            progress_callback(f"❌ {error_msg}")
        raise Exception(error_msg)


def _fallback_agent_workflow(
    video_paths: List[str],
    user_description: Optional[str],
    target_duration: float,
    generate_music: bool,
    progress_callback: Optional[Callable[[str], None]],
) -> Tuple[str, str, str, Optional[str]]:
    """Fallback agent workflow when ADK is not available."""
    if progress_callback:
        progress_callback("🔍 Analyzing videos...")

    video_summaries = []
    for i, video_path in enumerate(video_paths):
        if progress_callback:
            progress_callback(f"📹 Analyzing video {i+1}/{len(video_paths)}...")
        summary_json = video_summarizer(video_path, fps=2.0)
        summary = json.loads(summary_json)
        video_summaries.append(summary)

    if progress_callback:
        progress_callback("✍️ Generating script...")

    # Convert video summaries to JSON string for video_script_generator
    summaries_json = json.dumps(video_summaries, indent=2)

    try:
        script_json_str = video_script_generator(
            video_summaries=summaries_json,
            user_description=user_description,
            target_duration=target_duration,
        )
        script = json.loads(script_json_str)
    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ Script generation error: {str(e)}")
        raise Exception(f"Failed to generate script: {str(e)}")

    music_path = None
    if generate_music:
        if progress_callback:
            progress_callback("🎵 Generating music...")
        mood = "energetic"
        if video_summaries and video_summaries[0].get("mood_tags"):
            mood = video_summaries[0]["mood_tags"][0]
        try:
            music_path = music_selector(
                mood=mood,
                target_duration=min(target_duration, 30.0),
                looping=True,
                prompt_influence=0.3,
            )
        except:
            pass

    # Generate thumbnail if summaries are available
    thumbnail_path = None
    if video_summaries:
        try:
            if progress_callback:
                progress_callback("🖼️ Extracting frame for thumbnail...")
            frame_path = frame_extractor(video_paths[0])

            if progress_callback:
                progress_callback("🎨 Generating thumbnail...")
            summary_text = video_summaries[0].get("description", "")
            thumbnail_path = thumbnail_generator(
                image_input=frame_path,
                summary=summary_text,
            )
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Thumbnail generation skipped: {str(e)}")

    if progress_callback:
        progress_callback("🎬 Composing final video...")

    script_json = json.dumps(script, indent=2)
    final_video_path = video_composer(
        script=script_json,
        video_clips=video_paths,
        music_path=music_path,
        thumbnail_image=thumbnail_path,
    )

    summary_json = json.dumps(video_summaries, indent=2)
    return final_video_path, summary_json, script_json, thumbnail_path

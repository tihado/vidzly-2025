import os
import json
import tempfile
from typing import Optional, List, Union, Tuple, Callable, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google ADK imports
try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import FunctionTool
except ImportError as e:
    raise ImportError(
        "google-adk package is required. Install it with: poetry add google-adk"
    ) from e

# Import all tool functions
from tools.video_summarizer import video_summarizer
from tools.video_script_generator import video_script_generator
from tools.music_selector import music_selector
from tools.frame_extractor import frame_extractor
from tools.thumbnail_generator import thumbnail_generator
from tools.video_composer import video_composer


def _normalize_video_inputs(video_inputs: Union[str, List[str], Tuple]) -> List[str]:
    """
    Normalize video inputs to a list of absolute file paths.

    Args:
        video_inputs: Single video path, list of video paths, or Gradio file input

    Returns:
        List of absolute file paths
    """
    video_paths = []

    if isinstance(video_inputs, str):
        # Single file path
        video_paths = [video_inputs]
    elif isinstance(video_inputs, tuple):
        # Gradio format: (video_path, subtitle_path) or single tuple
        if len(video_inputs) > 0:
            video_paths = [video_inputs[0]]
    elif isinstance(video_inputs, list):
        # List of files (may contain tuples from Gradio)
        for item in video_inputs:
            if isinstance(item, tuple):
                video_paths.append(item[0])
            elif isinstance(item, str):
                video_paths.append(item)
    else:
        raise ValueError(f"Invalid video_inputs type: {type(video_inputs)}")

    # Convert to absolute paths and validate
    absolute_paths = []
    for path in video_paths:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Video file not found: {abs_path}")
        absolute_paths.append(abs_path)

    return absolute_paths


def _create_tool_wrappers():
    """
    Create ADK FunctionTool wrappers for all MCP tools.

    Returns:
        Dict mapping tool names to FunctionTool objects
    """
    tools = {}

    # Video Summarizer Tool
    tools["video_summarizer"] = FunctionTool(
        func=video_summarizer,
    )

    # Video Script Generator Tool
    tools["video_script_generator"] = FunctionTool(
        func=video_script_generator,
    )

    # Music Selector Tool
    tools["music_selector"] = FunctionTool(
        func=music_selector,
    )

    # Frame Extractor Tool
    tools["frame_extractor"] = FunctionTool(
        func=frame_extractor,
    )

    # Thumbnail Generator Tool
    tools["thumbnail_generator"] = FunctionTool(
        func=thumbnail_generator,
    )

    # Video Composer Tool
    tools["video_composer"] = FunctionTool(
        func=video_composer,
    )

    return tools


def _create_script_writer_agent(
    tools: Dict[str, FunctionTool],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> LlmAgent:
    """
    Create Script Writer Agent for video analysis, script generation, and music selection.

    Args:
        tools: Dictionary of available tools
        progress_callback: Optional callback for progress updates

    Returns:
        LlmAgent configured as Script Writer
    """
    script_writer_tools = [
        tools["video_summarizer"],
        tools["video_script_generator"],
        tools["music_selector"],
    ]

    instruction = """You are a Script Writer Agent specialized in video content analysis and script generation.

Your responsibilities:
1. Analyze video content using video_summarizer to understand what's in each video
2. Generate detailed composition scripts using video_script_generator based on video summaries and user requirements
3. Generate appropriate background music using music_selector based on the mood and style identified in the videos

When working:
- Always analyze all provided videos first to understand the content
- Generate scripts that match the target duration and user description
- Select music that matches the mood tags from video analysis
- Return structured results: video summaries (JSON), script (JSON), and music file path

Be thorough and creative in your analysis and script generation."""

    return LlmAgent(
        model="gemini-2.5-flash-lite",
        name="script_writer",
        instruction=instruction,
        tools=script_writer_tools,
    )


def _create_video_editor_agent(
    tools: Dict[str, FunctionTool],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> LlmAgent:
    """
    Create Video Editor Agent for frame extraction, thumbnail generation, and video composition.

    Args:
        tools: Dictionary of available tools
        progress_callback: Optional callback for progress updates

    Returns:
        LlmAgent configured as Video Editor
    """
    video_editor_tools = [
        tools["frame_extractor"],
        tools["thumbnail_generator"],
        tools["video_composer"],
    ]

    instruction = """You are a Video Editor Agent specialized in video composition and thumbnail creation.

Your responsibilities:
1. Extract representative frames from videos using frame_extractor (use thumbnail_timeframe from video summaries if available)
2. Generate engaging thumbnails using thumbnail_generator with the extracted frame and video summary
3. Compose the final video using video_composer with the script, video clips, music, and thumbnail

When working:
- Use the thumbnail_timeframe from video summaries when extracting frames
- Generate thumbnails that are engaging and match the video content
- Compose videos following the script exactly, including transitions and music
- Return structured results: thumbnail path and final video path

Be precise and ensure high-quality output."""

    return LlmAgent(
        model="gemini-2.5-flash-lite",
        name="video_editor",
        instruction=instruction,
        tools=video_editor_tools,
    )


def _create_manager_agent(
    tools: Dict[str, FunctionTool],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> LlmAgent:
    """
    Create Manager Agent that orchestrates the workflow.

    Args:
        tools: Dictionary of all available tools
        progress_callback: Optional callback for progress updates

    Returns:
        LlmAgent configured as Manager
    """
    # Manager has access to all tools for coordination
    all_tools = list(tools.values())

    instruction = """You are a Manager Agent that orchestrates video creation workflows.

You coordinate the video creation process through two phases:

Phase 1 - Script Writing:
- Analyze all input videos using video_summarizer to understand content
- Generate composition script using video_script_generator based on summaries and user requirements
- Generate background music using music_selector based on mood and style (if requested)

Phase 2 - Video Editing:
- Extract representative frame using frame_extractor (use thumbnail_timeframe from summaries if available)
- Generate engaging thumbnail using thumbnail_generator with frame and summary
- Compose final video using video_composer with script, video clips, music, and thumbnail

You have direct access to all tools. Coordinate the workflow step by step, ensuring proper data flow between phases.
Always return structured results with file paths and JSON data."""

    return LlmAgent(
        model="gemini-2.5-flash-lite",
        name="manager",
        instruction=instruction,
        tools=all_tools,
    )


def agent_workflow(
    video_inputs: Union[str, List[str], Tuple],
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
    generate_music: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str, str, str]:
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
        Tuple of (final_video_path: str, summary_json: str, script_json: str, thumbnail_path: str)
    """
    try:
        # Validate API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        # Normalize video inputs
        if progress_callback:
            progress_callback("📥 Processing video inputs...")
        video_paths = _normalize_video_inputs(video_inputs)

        if not video_paths:
            raise ValueError("No valid video files provided")

        # Create tool wrappers
        tools = _create_tool_wrappers()

        # Create specialized agents (available for future use or complex reasoning)
        script_writer_agent = _create_script_writer_agent(tools, progress_callback)
        video_editor_agent = _create_video_editor_agent(tools, progress_callback)

        # Create manager agent for orchestration
        manager_agent = _create_manager_agent(tools, progress_callback)

        # Phase 1: Analyze videos and generate script
        if progress_callback:
            progress_callback("🎬 Phase 1: Analyzing videos and generating script...")

        # Analyze all videos using direct tool calls (more reliable)
        video_summaries = []
        for i, video_path in enumerate(video_paths):
            if progress_callback:
                progress_callback(f"📹 Analyzing video {i+1}/{len(video_paths)}...")

            summary_json = video_summarizer(video_path, fps=2.0)
            video_summaries.append(summary_json)

        # Generate script using agent for intelligent reasoning
        if progress_callback:
            progress_callback("✍️ Generating composition script...")

        print(f"Video summaries: {video_summaries}")

        summaries_input = (
            json.dumps(video_summaries)
            if len(video_summaries) > 1
            else video_summaries[0]
        )
        script_json = video_script_generator(
            video_summaries=summaries_input,
            user_description=user_description,
            target_duration=target_duration,
        )

        print(f"Script JSON: {script_json}")

        # Extract mood for music generation
        mood = "energetic"
        bpm = None
        try:
            script_data = json.loads(script_json)
            if isinstance(script_data, dict):
                if "structured_script" in script_data:
                    script_data = script_data["structured_script"]
                if "music" in script_data:
                    mood = script_data["music"].get("mood", "energetic")
                    bpm = script_data["music"].get("bpm")
        except:
            # Fallback: extract from first video summary
            if video_summaries:
                try:
                    first_summary = (
                        json.loads(video_summaries[0])
                        if isinstance(video_summaries[0], str)
                        else video_summaries[0]
                    )
                    mood_tags = first_summary.get("mood_tags", [])
                    mood = mood_tags[0] if mood_tags else "energetic"
                except:
                    pass

        # Generate music if requested
        music_path = None
        if generate_music:
            if progress_callback:
                progress_callback("🎵 Generating background music...")

            music_path = music_selector(
                mood=mood,
                target_duration=target_duration,
                bpm=bpm,
                looping=True,
                prompt_influence=0.3,
            )

        # Phase 2: Extract frame, generate thumbnail, compose video
        if progress_callback:
            progress_callback("🎨 Phase 2: Creating thumbnail and composing video...")

        # Extract frame from first video
        if progress_callback:
            progress_callback("🖼️ Extracting representative frame...")

        # Get thumbnail timeframe from first video summary
        thumbnail_timeframe = None
        summary_text = ""
        if video_summaries:
            try:
                first_summary = (
                    json.loads(video_summaries[0])
                    if isinstance(video_summaries[0], str)
                    else video_summaries[0]
                )
                thumbnail_timeframe = first_summary.get("thumbnail_timeframe")
                summary_text = first_summary.get("summary", "")[:500]  # Limit length
            except:
                pass

        frame_path = frame_extractor(
            video_input=video_paths[0],
            thumbnail_timeframe=thumbnail_timeframe,
        )

        print(f"Frame path: {frame_path}")

        # Generate thumbnail
        if progress_callback:
            progress_callback("🎨 Generating thumbnail...")

        if not summary_text:
            summary_text = "Video content"

        thumbnail_path = thumbnail_generator(
            image_input=frame_path,
            summary=summary_text,
        )

        # Compose final video
        if progress_callback:
            progress_callback("🎬 Composing final video...")

        final_video_path = video_composer(
            script=script_json,
            video_clips=video_paths,
            music_path=music_path,
            thumbnail_image=thumbnail_path,
        )

        # Combine summaries into single JSON
        summary_json = (
            json.dumps(video_summaries, indent=2)
            if len(video_summaries) > 1
            else video_summaries[0]
        )

        if progress_callback:
            progress_callback("✅ Video creation complete!")

        return (final_video_path, summary_json, script_json, thumbnail_path)

    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ Error: {str(e)}")
        raise

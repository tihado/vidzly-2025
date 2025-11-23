import os
import json
import tempfile
from typing import Optional, List, Union, Tuple, Callable, Dict, Any
from pathlib import Path

from tools.video_summarizer import video_summarizer
from tools.video_clipper import video_clipper
from tools.video_composer import video_composer
from tools.music_selector import music_selector

try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import Tool

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    # Fallback to manual implementation if ADK not available
    import google.genai as genai


def create_adk_tools(
    video_paths: List[str], target_duration: float, generate_music: bool
):
    """Create ADK Tool wrappers for MCP tools."""

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

    def video_composer_tool(script_json: str, music_path: Optional[str] = None) -> str:
        """Combine video clips with transitions and music according to a script.

        Args:
            script_json: JSON script string with scenes and transitions
            music_path: Optional path to music file (str or None)

        Returns:
            Path to final composed video
        """
        try:
            return video_composer(
                script=script_json,
                video_clips=video_paths,
                music_path=music_path,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    # Create ADK Tool objects
    tools = [
        Tool(
            name="video_summarizer",
            description="Analyzes video content and extracts key scenes, mood tags, and descriptions. Use this to understand what's in each video.",
            func=video_summarizer_tool,
        ),
        Tool(
            name="music_selector",
            description="Generates background music based on mood and style. Use this to create music that matches the video's mood.",
            func=music_selector_tool,
        ),
        Tool(
            name="video_composer",
            description="Combines video clips with transitions and music according to a script. Use this as the final step to create the composed video.",
            func=video_composer_tool,
        ),
    ]

    return tools


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
        Tuple of (final_video_path, summary_json, script_json)
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

        # Check if ADK is available
        if not ADK_AVAILABLE:
            if progress_callback:
                progress_callback("⚠️ Google ADK not available, using fallback...")
            return _fallback_agent_workflow(
                video_paths,
                user_description,
                target_duration,
                generate_music,
                progress_callback,
            )

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for agent workflow"
            )

        # Create ADK tools
        if progress_callback:
            progress_callback("🔧 Setting up agent tools...")

        tools = create_adk_tools(video_paths, target_duration, generate_music)

        # Create agent instruction
        instruction = f"""You are an intelligent video editing agent. Your goal is to create a polished {target_duration}-second video from the provided footage.

**Task Details:**
- Input: {len(video_paths)} video file(s)
- Target duration: {target_duration} seconds
- User requirements: {user_description if user_description else 'None specified'}
- Generate music: {generate_music}

**Your Approach:**
1. Use video_summarizer to analyze each video and understand the content
2. Based on the summaries, reason about which scenes to select and how to structure the video
3. Create a composition script (JSON format) that:
   - Selects the best scenes from the videos
   - Creates a coherent narrative flow
   - Uses appropriate transitions (cut, fade, or crossfade)
   - Ensures total duration is approximately {target_duration} seconds
   - Matches the user's requirements if provided
4. If music generation is enabled, use music_selector to generate appropriate background music
5. Use video_composer to combine everything into the final video

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

Think step by step, use tools as needed, and create the final video."""

        # Create ADK agent
        if progress_callback:
            progress_callback("🤖 Creating ADK agent...")

        agent = LlmAgent(
            name="video_editing_agent",
            model="gemini-2.5-flash-lite",
            instruction=instruction,
            tools=tools,
        )

        # Run agent
        if progress_callback:
            progress_callback("🚀 Agent reasoning and executing...")

        # Agent state to collect results
        agent_state = {
            "video_summaries": [],
            "script": None,
            "music_path": None,
            "final_video_path": None,
        }

        # Create initial task for agent
        task = f"""Create a {target_duration}-second video from {len(video_paths)} video file(s).
        
Steps:
1. Analyze all videos using video_summarizer (use video_index 0, 1, etc. for each video)
2. Based on the summaries, create a composition script
3. Generate music if needed using music_selector
4. Compose the final video using video_composer

User requirements: {user_description if user_description else 'None'}"""

        # Execute agent - ADK will handle all tool calling dynamically
        if progress_callback:
            progress_callback("🚀 Agent reasoning and executing...")

        # Let the agent handle the entire workflow
        # It will decide which tools to use and when
        response = agent.run(task)

        # Extract results from agent's execution
        # ADK tracks tool calls, we need to get the final video path
        # The agent should have called video_composer which returns the path

        # Track tool executions to extract results
        # Since ADK executes tools, we need to capture the results
        # For now, we'll need to re-execute or track via a shared state

        # Alternative: Use ADK's execution context to track results
        # Or let the agent return the final path in its response

        # Extract final video path from agent's response or tool execution
        response_text = str(
            response.content if hasattr(response, "content") else response
        )

        # Try to extract file path from response
        import re

        # Look for file paths in the response
        path_pattern = r"/(?:[^/\s]+/)*[^/\s]+\.(?:mp4|mov|avi|mkv)"
        paths = re.findall(path_pattern, response_text)

        final_video_path = None
        if paths:
            # Use the last path found (likely the final video)
            final_video_path = paths[-1]
            if not os.path.exists(final_video_path):
                final_video_path = None

        # If agent didn't complete, fallback to guided execution
        if not final_video_path:
            if progress_callback:
                progress_callback("📊 Agent planning complete, executing workflow...")

            # Let agent guide us, but execute tools ourselves
            # Analyze videos
            video_summaries = []
            for i in range(len(video_paths)):
                if progress_callback:
                    progress_callback(f"📹 Analyzing video {i+1}/{len(video_paths)}...")
                summary_json = video_summarizer(video_paths[i], fps=2.0)
                video_summaries.append(json.loads(summary_json))

            # Let agent create script
            summaries_text = "\n\n".join(
                [
                    f"Video {i+1}:\n{json.dumps(s, indent=2)}"
                    for i, s in enumerate(video_summaries)
                ]
            )

            script_prompt = f"""Create a composition script based on these summaries:

{summaries_text}

User requirements: {user_description if user_description else 'None'}
Target duration: {target_duration} seconds

Return ONLY valid JSON script."""

            script_response = agent.run(script_prompt)
            script_text = str(
                script_response.content
                if hasattr(script_response, "content")
                else script_response
            )

            # Extract JSON script
            if "```json" in script_text:
                script_text = script_text.split("```json")[1].split("```")[0].strip()
            elif "```" in script_text:
                script_text = script_text.split("```")[1].split("```")[0].strip()

            json_match = re.search(r"\{.*\}", script_text, re.DOTALL)
            script = None
            if json_match:
                try:
                    script = json.loads(json_match.group())
                except:
                    pass

            if not script:
                from workflow import generate_script_from_summary

                script = generate_script_from_summary(
                    video_summaries,
                    user_description=user_description,
                    target_duration=target_duration,
                )

            # Generate music if needed
            music_path = None
            if generate_music:
                if progress_callback:
                    progress_callback("🎵 Generating music...")
                mood = (
                    script.get("music", {}).get("mood", "energetic")
                    if script
                    else "energetic"
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

            # Compose final video
            if progress_callback:
                progress_callback("🎬 Composing final video...")

            script_json = json.dumps(script, indent=2)
            final_video_path = video_composer(
                script=script_json,
                video_clips=video_paths,
                music_path=music_path,
            )

            summary_json = json.dumps(video_summaries, indent=2)
            script_json = script_json
        else:
            # Agent completed, extract summaries and script from state if available
            summary_json = "[]"
            script_json = "{}"
            # Try to reconstruct from agent's execution if possible
            # For now, return minimal info since agent handled it

        if progress_callback:
            progress_callback("✅ Agent workflow complete!")

        return final_video_path, summary_json, script_json

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
) -> Tuple[str, str, str]:
    """Fallback agent workflow when ADK is not available."""
    # Use the original workflow approach
    from workflow import generate_script_from_summary

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

    script = generate_script_from_summary(
        video_summaries,
        user_description=user_description,
        target_duration=target_duration,
    )

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

    if progress_callback:
        progress_callback("🎬 Composing final video...")

    script_json = json.dumps(script, indent=2)
    final_video_path = video_composer(
        script=script_json,
        video_clips=video_paths,
        music_path=music_path,
    )

    summary_json = json.dumps(video_summaries, indent=2)
    return final_video_path, summary_json, script_json

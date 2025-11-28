"""
Agent workflow for video creation using LangChain agent.

This module implements the main workflow that orchestrates video processing
tools to create polished videos from raw footage using a central agent.
"""

import os
import json
import re
from typing import List, Optional, Generator, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain v1.0 uses create_agent instead of create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from tools.langchain_tools import ALL_TOOLS


def _normalize_video_inputs(video_inputs) -> List[str]:
    """
    Normalize video inputs from Gradio format to list of absolute paths.

    Args:
        video_inputs: Can be:
            - List of file paths
            - List of tuples (from Gradio: (video_path, subtitle_path))
            - Single file path
            - Single tuple

    Returns:
        List of absolute file paths
    """
    if not video_inputs:
        return []

    # Handle single input
    if not isinstance(video_inputs, list):
        video_inputs = [video_inputs]

    normalized = []
    for item in video_inputs:
        if isinstance(item, tuple):
            # Gradio format: (video_path, subtitle_path)
            video_path = item[0]
        elif isinstance(item, str):
            video_path = item
        else:
            continue

        # Convert to absolute path
        if video_path and os.path.exists(video_path):
            normalized.append(os.path.abspath(video_path))

    return normalized


def _extract_json_from_text(text: str) -> Optional[str]:
    """Extract JSON from text if present."""
    if "{" in text and "}" in text:
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
    return None


def _extract_file_path_from_text(text: str, extensions: List[str]) -> Optional[str]:
    """Extract file path from text if present."""
    # First check if the text itself is a valid path
    if os.path.exists(text.strip()):
        return text.strip()

    # Try to find path pattern in text
    pattern = r"([/\\][^\s]+\.(" + "|".join(extensions) + "))"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def agent_workflow(
    video_inputs,
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
    generate_music: bool = True,
) -> Generator[Tuple[Optional[str], str, str, str, str], None, None]:
    """
    Main agent workflow that orchestrates video creation using a central agent.

    This is a generator function that yields progress updates as the workflow progresses.
    Each yield contains: (final_path, summary_json, script_json, thumbnail_path, status)

    Args:
        video_inputs: Video file(s) from Gradio (can be list, tuple, or string)
        user_description: Optional description of desired mood, style, or content
        target_duration: Target duration in seconds for final video
        generate_music: Whether to generate background music

    Yields:
        Tuple of (final_path, summary_json, script_json, thumbnail_path, status)
        - final_path: Path to final video (None until complete)
        - summary_json: JSON string of video summaries
        - script_json: JSON string of generated script
        - thumbnail_path: Path to thumbnail image (None until generated)
        - status: Status message for UI
    """
    # Initialize outputs
    final_path = None
    summary_json = ""
    script_json = ""
    thumbnail_path = None
    status = "Starting workflow...\n"

    try:
        # Normalize video inputs
        status += "📥 Processing video inputs...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        video_paths = _normalize_video_inputs(video_inputs)
        if not video_paths:
            status += "❌ No valid video files found.\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
            return

        status += f"✅ Found {len(video_paths)} video file(s).\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            status += "❌ GOOGLE_API_KEY not found in environment.\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
            return

        # Create LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.7,
        )

        # Create central agent with all tools
        status += "\n🤖 Initializing AI agent...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        agent = create_agent(llm, tools=ALL_TOOLS)

        # Build comprehensive workflow prompt
        video_paths_str = "\n".join([f"- {path}" for path in video_paths])
        user_desc_text = (
            f"\nUser Description: {user_description}" if user_description else ""
        )
        music_instruction = (
            "Generate background music matching the video's mood and style."
            if generate_music
            else "Do not generate background music."
        )

        workflow_prompt = f"""You are a professional video editor creating short-form videos. Your task is to transform raw video footage into a polished, engaging video.

WORKFLOW TASKS (execute in order):

Step 1. VIDEO ANALYSIS using the video_summarizer_tool
   - Video files to analyze:
{video_paths_str}
   - Use fps=2.0 for analysis
   - Collect all video summaries

Step 2. SCRIPT GENERATION using the video_script_generator_tool
   - Target duration: {target_duration} seconds
   - The script should include:
     * Scene sequences with source video references and timestamps
     * Transitions (cut, fade, crossfade)
     * Music configuration with mood and style
     * Pacing and narrative structure
{user_desc_text}

Step 3. BACKGROUND MUSIC GENERATION (if enabled) using the music_selector_tool:
   - {music_instruction}
   - Extract mood from the script or video summaries
   - Target duration: {target_duration} seconds

Step 4. FRAME EXTRACTION using the frame_extractor_tool
   - Extract a representative frame from the first video
   - Use the thumbnail_timeframe from the first video's summary if available

Step 5. THUMBNAIL GENERATION using thumbnail_generator_tool
   - Use the extracted frame and video summary

Step 6. VIDEO COMPOSITION using the video_composer_tool
   - Provide the script JSON, video clips, music (if generated), and thumbnail
   - The video_clips parameter should be a JSON array of video file paths

IMPORTANT INSTRUCTIONS:
- Execute all steps in sequence
- Use the tools to accomplish each task
- Extract and preserve JSON outputs (scripts, summaries) for the final result
- Extract file paths from tool outputs (music, thumbnail, final video)
- Think step by step and use the appropriate tools for each task
- Do not skip any steps
- Report progress as you complete each step

Begin by analyzing the videos."""

        status += "\n🎬 Starting video creation workflow...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        # Stream agent execution for real-time updates
        status += "🤖 Agent is working...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        # Invoke agent and stream results
        result = agent.invoke(
            {"messages": [{"role": "user", "content": workflow_prompt}]}
        )

        print(result)

        # Process agent result to extract outputs
        if result and "messages" in result:
            # Track tool outputs
            summaries = []
            music_path = None

            # Extract information from all messages (including tool messages)
            for message in result["messages"]:
                # Check if this is a tool message (contains tool output)
                message_type = (
                    getattr(message, "type", None) if hasattr(message, "type") else None
                )
                content = (
                    message.content if hasattr(message, "content") else str(message)
                )

                # Update status with agent's progress
                if content:
                    # Check for tool outputs - video_summarizer returns JSON
                    if (
                        "video_summarizer" in str(message).lower()
                        or "summary" in content.lower()
                    ):
                        extracted_json = _extract_json_from_text(content)
                        if extracted_json:
                            try:
                                parsed = json.loads(extracted_json)
                                if isinstance(parsed, list):
                                    summaries.extend(parsed)
                                elif isinstance(parsed, dict) and "summary" in parsed:
                                    summaries.append(parsed)
                            except:
                                pass

                    # Check for script output
                    if "script" in content.lower() or "scenes" in content:
                        extracted_json = _extract_json_from_text(content)
                        if extracted_json:
                            try:
                                parsed = json.loads(extracted_json)
                                if "scenes" in parsed:
                                    script_json = extracted_json
                                    status += "✅ Script generated.\n"
                                    yield final_path, summary_json, script_json, thumbnail_path, status
                            except:
                                pass

                    # Check for music file path
                    if "music" in content.lower() or "sound" in content.lower():
                        music_path = _extract_file_path_from_text(
                            content, ["mp3", "wav", "m4a"]
                        )
                        if music_path and os.path.exists(music_path):
                            status += f"✅ Music generated.\n"
                            yield final_path, summary_json, script_json, thumbnail_path, status

                    # Check for thumbnail file path
                    if "thumbnail" in content.lower() or "frame" in content.lower():
                        thumb_path = _extract_file_path_from_text(
                            content, ["png", "jpg", "jpeg"]
                        )
                        if thumb_path and os.path.exists(thumb_path):
                            thumbnail_path = thumb_path
                            status += f"✅ Thumbnail generated.\n"
                            yield final_path, summary_json, script_json, thumbnail_path, status

                    # Check for final video path
                    if (
                        "compose" in content.lower()
                        or "final" in content.lower()
                        or "video" in content.lower()
                    ):
                        video_path = _extract_file_path_from_text(
                            content, ["mp4", "avi", "mov"]
                        )
                        if video_path and os.path.exists(video_path):
                            final_path = video_path
                            status += f"✅ Final video created.\n"
                            yield final_path, summary_json, script_json, thumbnail_path, status

            # Compile summaries if collected
            if summaries:
                summary_json = json.dumps(summaries, indent=2)
                status += f"✅ Analyzed {len(summaries)} video(s).\n"
                yield final_path, summary_json, script_json, thumbnail_path, status

            # Final extraction from last message as fallback
            if result["messages"]:
                last_message = result["messages"][-1]
                final_content = (
                    last_message.content
                    if hasattr(last_message, "content")
                    else str(last_message)
                )

                # Final attempt to extract missing outputs
                if not script_json:
                    script_json = _extract_json_from_text(final_content) or ""

                if not summary_json:
                    summary_json = _extract_json_from_text(final_content) or ""

                if not thumbnail_path:
                    thumbnail_path = _extract_file_path_from_text(
                        final_content, ["png", "jpg", "jpeg"]
                    )

                if not final_path:
                    final_path = _extract_file_path_from_text(
                        final_content, ["mp4", "avi", "mov"]
                    )

        # Final status update
        if final_path:
            status += "\n✅ Video creation complete! 🎉\n"
        else:
            status += "\n⚠️ Workflow completed, but final video path not found.\n"
            status += "Check agent output for details.\n"

        yield final_path, summary_json, script_json, thumbnail_path, status

    except Exception as e:
        status += f"\n❌ Workflow error: {str(e)}\n"
        import traceback

        status += f"\nDetails:\n{traceback.format_exc()}\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

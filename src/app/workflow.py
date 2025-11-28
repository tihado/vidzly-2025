"""
Parallel workflow for video creation.

This module implements the main workflow that orchestrates video processing
tools to create polished videos from raw footage using parallel tool calls
where possible to optimize performance.
"""

import os
import json
from typing import List, Optional, Generator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import tool functions directly
from tools.video_summarizer import video_summarizer
from tools.video_script_generator import video_script_generator
from tools.music_selector import music_selector
from tools.frame_extractor import frame_extractor
from tools.thumbnail_generator import thumbnail_generator
from tools.video_composer import video_composer


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


def agent_workflow(
    video_inputs,
    user_description: Optional[str] = None,
    target_duration: float = 30.0,
    generate_music: bool = True,
) -> Generator[Tuple[Optional[str], str, str, str, str], None, None]:
    """
    Parallel workflow that orchestrates video creation using direct tool calls.

    This workflow parallelizes operations where possible:
    - Video analysis: All videos are analyzed concurrently
    - Music generation and frame extraction: Run in parallel
    
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

        # Step 1: Analyze videos in parallel
        status += "\n📊 Step 1: Analyzing videos (in parallel)...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        summaries = []
        
        def analyze_video(video_path, index):
            """Helper function to analyze a single video."""
            try:
                summary_result = video_summarizer(video_path, fps=2.0)
                summary_dict = json.loads(summary_result)
                return (index, summary_dict, None)
            except json.JSONDecodeError as e:
                return (index, None, f"Could not parse summary: {str(e)}")
            except Exception as e:
                return (index, None, f"Error analyzing video: {str(e)}")

        # Analyze all videos in parallel
        with ThreadPoolExecutor(max_workers=min(len(video_paths), 5)) as executor:
            # Submit all tasks
            future_to_video = {
                executor.submit(analyze_video, video_path, i): (i, video_path)
                for i, video_path in enumerate(video_paths)
            }
            
            # Process results as they complete
            results = [None] * len(video_paths)
            for future in as_completed(future_to_video):
                index, summary_dict, error = future.result()
                
                if error:
                    status += f"  ⚠️ Warning: Video {index+1}/{len(video_paths)} - {error}\n"
                elif summary_dict:
                    results[index] = summary_dict
                    status += f"  ✅ Completed video {index+1}/{len(video_paths)}\n"
                else:
                    status += f"  ⚠️ Warning: Video {index+1}/{len(video_paths)} - No summary generated\n"
                
                yield final_path, summary_json, script_json, thumbnail_path, status

        # Collect successful summaries in order
        summaries = [r for r in results if r is not None]

        if not summaries:
            status += "❌ Failed to analyze videos.\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
            return

        summary_json = json.dumps(summaries, indent=2)
        status += f"✅ Analyzed {len(summaries)} video(s) in parallel.\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        # Step 2: Generate script
        status += "\n📝 Step 2: Generating video script...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        script_json = video_script_generator(
            video_summaries=summary_json,
            user_description=user_description,
            target_duration=target_duration,
        )
        status += "✅ Script generated.\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        # Parse script to extract music mood
        try:
            script_data = json.loads(script_json)
            music_mood = None
            if script_data.get("music") and isinstance(script_data["music"], dict):
                music_mood = script_data["music"].get("mood", "energetic")
            else:
                # Fallback: extract mood from first video summary
                if summaries and summaries[0].get("mood_tags"):
                    music_mood = summaries[0]["mood_tags"][0] if summaries[0]["mood_tags"] else "energetic"
                else:
                    music_mood = "energetic"
        except:
            music_mood = "energetic"

        # Step 3 & 4: Generate music and extract frame in parallel
        status += "\n🎵 Step 3 & 4: Generating music and extracting frame (in parallel)...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        music_path = None
        frame_path = None
        first_video_path = video_paths[0]
        thumbnail_timeframe = None
        if summaries and summaries[0].get("thumbnail_timeframe"):
            thumbnail_timeframe = summaries[0]["thumbnail_timeframe"]

        def generate_music_task():
            """Helper function to generate music."""
            try:
                path = music_selector(
                    mood=music_mood,
                    target_duration=target_duration,
                    looping=True,
                    prompt_influence=0.3,
                )
                return path, None
            except Exception as e:
                return None, str(e)

        def extract_frame_task():
            """Helper function to extract frame."""
            try:
                path = frame_extractor(
                    first_video_path, thumbnail_timeframe=thumbnail_timeframe
                )
                return path, None
            except Exception as e:
                return None, str(e)

        # Run music generation and frame extraction in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            if generate_music:
                futures["music"] = executor.submit(generate_music_task)
            futures["frame"] = executor.submit(extract_frame_task)

            # Wait for both to complete
            for task_name, future in futures.items():
                result, error = future.result()
                if task_name == "music":
                    if error:
                        status += f"⚠️ Warning: Music generation failed: {error}\n"
                    elif result:
                        music_path = result
                        status += "✅ Music generated.\n"
                elif task_name == "frame":
                    if error:
                        status += f"❌ Frame extraction failed: {error}\n"
                        yield final_path, summary_json, script_json, thumbnail_path, status
                        return
                    elif result:
                        frame_path = result
                        status += "✅ Frame extracted.\n"
                
                yield final_path, summary_json, script_json, thumbnail_path, status

        # Step 5: Generate thumbnail
        status += "\n🎨 Step 5: Generating thumbnail...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        try:
            video_summary_text = summaries[0].get("summary", "") if summaries else ""
            thumbnail_path = thumbnail_generator(frame_path, video_summary_text)
            status += "✅ Thumbnail generated.\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
        except Exception as e:
            status += f"❌ Thumbnail generation failed: {str(e)}\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
            return

        # Step 6: Compose final video
        status += "\n🎬 Step 6: Composing final video...\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

        try:
            final_path = video_composer(
                script=script_json,
                video_clips=video_paths,
                music_path=music_path,
                thumbnail_image=thumbnail_path,
            )
            status += "✅ Final video created.\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
        except Exception as e:
            status += f"❌ Video composition failed: {str(e)}\n"
            yield final_path, summary_json, script_json, thumbnail_path, status
            return

        # Final status update
        status += "\n✅ Video creation complete! 🎉\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

    except Exception as e:
        status += f"\n❌ Workflow error: {str(e)}\n"
        import traceback

        status += f"\nDetails:\n{traceback.format_exc()}\n"
        yield final_path, summary_json, script_json, thumbnail_path, status

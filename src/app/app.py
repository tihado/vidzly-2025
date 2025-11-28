import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import gradio as gr
from introduction import introduction
from tools.video_summarizer import video_summarizer
from tools.video_clipper import video_clipper
from tools.frame_extractor import frame_extractor
from tools.thumbnail_generator import thumbnail_generator
from tools.video_composer import video_composer
from tools.music_selector import music_selector
from tools.video_script_generator import video_script_generator
from workflow_ui import workflow_ui
from tools.text_to_speech import text_to_speech_simple
from tools.script_generator import script_generator
from tools.subtitle_creator import subtitle_creator


def text_to_speech_wrapper(
    text, voice, language, speed, format_type, generate_segments
):
    """
    Wrapper to return audio file for Gradio.
    """
    result = text_to_speech_simple(
        text, voice, language, speed, format_type, generate_segments
    )
    # Always return audio file path (Gradio will render audio player)
    return result


def video_composer_wrapper(script, video_clips, music_path=None):
    """
    Wrapper to return both video and script JSON for easy workflow.
    """
    video_path = video_composer(video_clips, music_path)
    # Return video path and the original script (for subtitle generator)
    return video_path


def frame_extractor_wrapper(video_input, thumbnail_timeframe=None):
    """
    Wrapper function for frame_extractor to handle Gradio interface inputs.
    Maps the Gradio inputs to the correct function parameters.
    """
    return frame_extractor(
        video_input=video_input,
        output_path=None,
        thumbnail_timeframe=thumbnail_timeframe,
    )


with gr.Blocks() as demo:
    with gr.Tab("Vidzly"):
        # Introduction section
        introduction()

        # Full workflow UI
        gr.Markdown("---")
        workflow_ui()

    with gr.Tab("MCP Tools"):
        with gr.Tab("Video Summarizer"):
            gr.Interface(
                fn=video_summarizer,
                inputs=[
                    gr.Video(label="Upload Video"),
                    gr.Slider(
                        value=2.0,
                        label="FPS (frames per second for video processing)",
                        minimum=0.1,
                        maximum=24.0,
                        step=0.1,
                    ),
                ],
                outputs=[gr.Textbox(label="Video Summary (JSON)", lines=20)],
                title="Video Summarizer",
                description="Upload a video to get an AI-generated summary of its content, including key scenes, detected objects, and mood tags. Uses Google Gemini's native video understanding.",
                api_name="video_summarizer",
            )

        with gr.Tab("Video Clipper"):
            gr.Interface(
                fn=video_clipper,
                inputs=[
                    gr.Video(label="Upload Video"),
                    gr.Number(
                        value=0.0,
                        label="Start Time (seconds)",
                        minimum=0.0,
                        step=0.1,
                    ),
                    gr.Number(
                        value=10.0,
                        label="End Time (seconds)",
                        minimum=0.1,
                        step=0.1,
                    ),
                ],
                outputs=[gr.Video(label="Clipped Video")],
                title="Video Clipper",
                description="Extract a specific segment from a video file. Enter the start and end times in seconds to create a clipped version of your video.",
                api_name="video_clipper",
            )

        with gr.Tab("Frame Extractor"):
            gr.Interface(
                fn=frame_extractor_wrapper,
                inputs=[
                    gr.Video(label="Upload Video"),
                    gr.Number(
                        value=None,
                        label="Thumbnail Timeframe (Optional - seconds)",
                        minimum=0.0,
                        step=0.1,
                        info="Optional: Provide a timestamp in seconds to extract a frame at that specific time. If not provided, AI will analyze the video to find the best frame. You can get this value from the 'thumbnail_timeframe' field in Video Summarizer's JSON output.",
                    ),
                ],
                outputs=[gr.Image(label="Extracted Frame", type="filepath")],
                title="Frame Extractor",
                description="Extract a representative frame from a video. If you provide a thumbnail timeframe (e.g., from Video Summarizer), it will use that timestamp directly without calling AI. Otherwise, it uses Gemini AI to analyze the video and select the most engaging frame.",
                api_name="frame_extractor",
            )

        with gr.Tab("Thumbnail Generation"):
            gr.Interface(
                fn=thumbnail_generator,
                inputs=[
                    gr.Image(
                        label="Frame Image",
                        type="filepath",
                    ),
                    gr.Textbox(
                        label="Video Summary",
                        placeholder="Enter the video summary text here...",
                        lines=10,
                        info="Enter the video summary text (extract the 'summary' field from Video Summarizer JSON output).",
                    ),
                ],
                outputs=[gr.Image(label="Generated Thumbnail", type="filepath")],
                title="Thumbnail Generation",
                description="Automatically generate engaging thumbnails with AI-generated text and stickers. Uses Gemini AI to analyze the frame and video summary to create context-aware thumbnail designs with optimal text placement and sticker recommendations.",
                api_name="thumbnail_generation",
            )

        with gr.Tab("Video Composer"):
            gr.Interface(
                fn=video_composer_wrapper,
                inputs=[
                    gr.Textbox(
                        label="Script (JSON)",
                        placeholder='{"total_duration": 30.0, "scenes": [{"scene_id": 1, "source_video": 0, "start_time": 0.0, "end_time": 5.0, "duration": 5.0, "transition_in": "fade", "transition_out": "crossfade"}]}',
                        lines=10,
                    ),
                    gr.File(
                        label="Video Clips (Required - source videos)",
                        file_count="multiple",
                        file_types=["video"],
                    ),
                    gr.File(
                        label="Music File (Optional)",
                        file_count="single",
                        file_types=["audio"],
                    ),
                    gr.Image(
                        label="Thumbnail Image (Optional)",
                        type="filepath",
                    ),
                ],
                outputs=[
                    gr.Video(label="Composed Video"),
                    gr.Textbox(
                        label="Script JSON (Copy this to Subtitle Generator)", lines=10
                    ),
                ],
                title="Video Composer",
                description="Combine video clips, add music, and apply transitions according to a script. Upload source videos, then provide a JSON script where each scene's 'source_video' references a video by index (0-based) or filename. The same video can be used in multiple scenes with different time ranges. The script JSON output can be copied directly to Subtitle Generator.",
                api_name="video_composer",
            )

        with gr.Tab("Music Selector"):
            gr.Interface(
                fn=music_selector,
                inputs=[
                    gr.Textbox(
                        label="Mood",
                        placeholder="energetic, calm, dramatic, fun",
                        value="energetic",
                        info="Enter mood tags (comma-separated) or a single mood",
                    ),
                    gr.Textbox(
                        label="Style (Optional)",
                        placeholder="cinematic, modern, retro",
                        value="",
                    ),
                    gr.Number(
                        value=5.0,
                        label="Target Duration (seconds)",
                        minimum=1.0,
                        maximum=30.0,
                        step=0.5,
                        info="Maximum 30 seconds for ElevenLabs",
                    ),
                    gr.Number(
                        value=60,
                        label="BPM (Optional)",
                        minimum=60,
                        maximum=200,
                        step=1,
                        info="Beats per minute for rhythm matching (optional)",
                    ),
                    gr.Checkbox(
                        value=True,
                        label="Looping",
                        info="Enable seamless looping for continuous playback",
                    ),
                    gr.Slider(
                        value=0.3,
                        label="Prompt Influence",
                        minimum=0,
                        maximum=1,
                        step=0.01,
                        info="How closely the output matches the prompt (0-1)",
                    ),
                ],
                outputs=[gr.Audio(label="Generated Sound Effect (MP3)")],
                title="Music Selector",
                description="Generate background sound effects using ElevenLabs API based on mood, style, and duration. The generated audio can be used as background music or sound effects for videos. Requires ELEVENLABS_API_KEY in your .env file.",
                api_name="music_selector",
            )

        with gr.Tab("Video Script Generator"):
            gr.Interface(
                fn=video_script_generator,
                inputs=[
                    gr.Textbox(
                        label="Video Summaries (JSON)",
                        placeholder='[{"duration": 30.0, "summary": "...", "mood_tags": ["energetic"]}] or paste JSON string from Video Summarizer',
                        lines=15,
                        info="Enter video summaries as JSON. Can be a single JSON string, or a JSON array of summary objects. You can copy the JSON output from Video Summarizer tool.",
                    ),
                    gr.Textbox(
                        label="User Description (Optional)",
                        placeholder="e.g., Create an energetic and fast-paced video with dynamic transitions...",
                        lines=3,
                        info="Optional description of desired mood, style, or content for the final video",
                    ),
                    gr.Number(
                        value=30.0,
                        label="Target Duration (seconds)",
                        minimum=1.0,
                        maximum=300.0,
                        step=0.5,
                        info="Target duration for the final video in seconds",
                    ),
                ],
                outputs=[gr.Textbox(label="Generated Script (JSON)", lines=20)],
                title="Video Script Generator",
                description="Create a detailed script/storyboard for a video composition. Uses Google Gemini AI to intelligently generate a script based on video summaries and user requirements. The script includes scene sequences, timings, transitions, music configuration, pacing, and narrative structure. Requires GOOGLE_API_KEY in your .env file.",
                api_name="video_script_generator",
            )

        with gr.Tab("Text-to-Speech"):
            gr.Interface(
                fn=text_to_speech_wrapper,
                inputs=[
                    gr.Textbox(
                        label="Text or Subtitle Content",
                        placeholder='Enter text or paste subtitle content (SRT/VTT/JSON)...\n\nPlain text example:\n"Welcome to our video tutorial on AI."\n\nSRT example:\n1\n00:00:00,000 --> 00:00:03,500\nWelcome to our video.\n\n2\n00:00:03,500 --> 00:00:07,000\nToday we will learn.',
                        lines=8,
                        info="Enter plain text OR paste subtitle content. Format will be auto-detected. All subtitle dialogues will be combined into narration.",
                    ),
                    gr.Radio(
                        choices=["neutral", "male", "female"],
                        value="neutral",
                        label="Voice Type",
                        info="Select voice accent: Male (British), Female (Australian), or Neutral (US)",
                    ),
                    gr.Dropdown(
                        choices=[
                            ("English", "en"),
                            ("Spanish", "es"),
                            ("French", "fr"),
                            ("German", "de"),
                            ("Italian", "it"),
                            ("Portuguese", "pt"),
                            ("Chinese", "zh"),
                            ("Japanese", "ja"),
                            ("Korean", "ko"),
                            ("Arabic", "ar"),
                        ],
                        value="en",
                        label="Language",
                        info="Select the language for text-to-speech conversion",
                    ),
                    gr.Radio(
                        choices=["normal", "slow"],
                        value="normal",
                        label="Speed",
                        info="Speech speed: Normal or Slow (for learning/clarity)",
                    ),
                    gr.Radio(
                        choices=["auto", "text", "srt", "vtt", "json"],
                        value="auto",
                        label="Input Format",
                        info="Auto-detect format or manually specify: Plain text, SRT subtitle, VTT subtitle, or JSON scenario",
                    ),
                    gr.Checkbox(
                        value=False,
                        label="Generate Timed Segments",
                        info="Create separate audio files for each subtitle segment with timing info (for video synchronization). Only works with subtitle input formats.",
                    ),
                ],
                outputs=[gr.Audio(label="Generated Audio", type="filepath")],
                title="Text-to-Speech Converter",
                description="Convert text or subtitles to audio using Google Text-to-Speech. Supports plain text, SRT, VTT, and JSON formats. Enable 'Generate Timed Segments' to create individual audio files for each subtitle with timing metadata (perfect for video synchronization with Video Composer output).",
                api_name="text_to_speech",
            )

        with gr.Tab("Script Generator"):
            gr.Interface(
                fn=script_generator,
                inputs=[
                    gr.File(
                        label="Video Materials (Required - upload multiple videos)",
                        file_count="multiple",
                        file_types=["video"],
                    ),
                    gr.Textbox(
                        label="User Prompt (Optional)",
                        placeholder="e.g., 'Create an energetic travel montage with upbeat pacing' or 'Make a dramatic product reveal video'",
                        lines=3,
                        info="Optional: Provide specific instructions or creative direction. If left empty, the AI will generate a script based on the video content analysis.",
                    ),
                ],
                outputs=[gr.Textbox(label="Video Production Script (JSON)", lines=25)],
                title="Script Generator",
                description="Generate comprehensive video production scripts from multiple video materials. Upload your source videos and optionally provide creative direction. The AI will analyze the content and create a detailed script including scene breakdowns, timing, transitions, audio recommendations, and visual effects. Outputs both structured JSON and narrative formats.",
                api_name="script_generator",
            )

        with gr.Tab("Subtitle Creator"):
            gr.Interface(
                fn=subtitle_creator,
                inputs=[
                    gr.Video(label="Upload Video"),
                    gr.Textbox(
                        label="Transcript (JSON)",
                        placeholder='{"subtitles": [{"start": 0.0, "end": 2.5, "text": "Hello!", "position": "bottom", "fontsize": 48, "color": "white"}], "default_style": {"fontsize": 48, "color": "white", "bg_color": "#00000042", "position": "bottom", "transparent": true}}',
                        lines=15,
                        info="Provide subtitle transcript in JSON format with timestamps, text, and optional styling (position, font, fontsize, color, bg_color, stroke_color, stroke_width).",
                    ),
                ],
                outputs=[gr.Video(label="Video with Subtitles")],
                title="Subtitle Creator",
                description="Add customizable subtitles to your videos. Upload a video and provide a JSON transcript with timestamps, text content, and styling options. Supports multiple subtitle segments with individual positioning (top/center/bottom), fonts, colors, and background styling.",
                api_name="subtitle_creator",
            )

    with gr.Tab("MCP Guide"):
        # Read and display the MCP guide
        # Calculate path to project root (app.py is in src/app/)
        current_dir = os.path.dirname(os.path.abspath(__file__))  # src/app/
        project_root = os.path.dirname(os.path.dirname(current_dir))  # project root
        mcp_guide_path = os.path.join(project_root, "MCPGUIDE.md")

        try:
            with open(mcp_guide_path, "r", encoding="utf-8") as f:
                mcp_guide_content = f.read()
        except FileNotFoundError:
            mcp_guide_content = "# MCP Configuration Guide\n\nGuide file not found. Please check the MCPGUIDE.md file in the project root."

        gr.Markdown(mcp_guide_content)


if __name__ == "__main__":
    demo.launch(mcp_server=True, share=True, server_name="0.0.0.0", server_port=7860)

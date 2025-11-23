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
        # Tell about this project
        # Agent full workflow here

        introduction()

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
                fn=video_composer,
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
                ],
                outputs=[gr.Video(label="Composed Video")],
                title="Video Composer",
                description="Combine video clips, add music, and apply transitions according to a script. Upload source videos, then provide a JSON script where each scene's 'source_video' references a video by index (0-based) or filename. The same video can be used in multiple scenes with different time ranges.",
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
                        value=None,
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


if __name__ == "__main__":
    demo.launch(mcp_server=True)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import gradio as gr
from introduction import introduction
from tools.video_summarizer import video_summarizer
from tools.video_clipper import video_clipper
from tools.video_composer import video_composer


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


if __name__ == "__main__":
    demo.launch(mcp_server=True)

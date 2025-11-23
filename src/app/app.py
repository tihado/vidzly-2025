import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import gradio as gr
from introduction import introduction
from mcps.video_summarizer import video_summarizer


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


if __name__ == "__main__":
    demo.launch(mcp_server=True)

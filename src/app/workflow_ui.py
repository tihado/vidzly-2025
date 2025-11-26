import gradio as gr
import traceback
from workflow_agent import agent_workflow


def run_workflow(videos, description, duration, music):
    """Wrapper function to run the workflow with progress updates."""
    # Handle empty or None input
    if not videos or (isinstance(videos, list) and len(videos) == 0):
        return None, "❌ Please upload at least one video file.", "", "", None

    # Collect all progress messages
    progress_messages = []

    # Progress callback function that collects messages
    def progress_callback(msg):
        progress_messages.append(msg)
        print(f"Progress: {msg}")  # Print to console for visibility

    try:
        # Run the agent-controlled workflow
        final_path, summary_json, script_json, thumbnail_path = agent_workflow(
            video_inputs=videos,
            user_description=description.strip() if description else None,
            target_duration=float(duration),
            generate_music=bool(music),
            progress_callback=progress_callback,
        )

        # Build status message showing all progress steps
        if progress_messages:
            status = "\n".join(progress_messages)
        else:
            status = "✅ Video creation complete!"

        return final_path, status, summary_json, script_json, thumbnail_path

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n\nDetails: {traceback.format_exc()}"
        if progress_messages:
            error_msg = "\n".join(progress_messages) + "\n\n" + error_msg
        return None, error_msg, "", "", None


def workflow_ui():
    """Create the full workflow UI interface."""
    with gr.Column():
        # Header
        gr.Markdown(
            """
            # 🤖 Vidzly - AI Agent Workflow
            
            Transform your raw footage into a polished video with AI agent-powered editing.
            Our intelligent agent uses MCP tools to analyze, plan, and create your video automatically.
            Upload your videos, describe your vision, and let the AI agent handle the rest!
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                # Input section
                gr.Markdown("### 📥 Input")

                video_input = gr.File(
                    label="Upload Video(s)",
                    file_count="multiple",
                    file_types=["video"],
                    height=200,
                )

                user_description = gr.Textbox(
                    label="Describe Your Vision (Optional)",
                    placeholder="e.g., energetic and fast-paced, calm and cinematic, fun and colorful...",
                    lines=3,
                    info="Describe the mood, style, or vibe you want for your video",
                )

                with gr.Row():
                    target_duration = gr.Slider(
                        value=30.0,
                        label="Target Duration (seconds)",
                        minimum=5.0,
                        maximum=60.0,
                        step=1.0,
                        info="Length of the final video",
                    )

                    generate_music = gr.Checkbox(
                        value=True,
                        label="Generate Background Music",
                        info="Automatically generate music matching the video mood",
                    )

                create_btn = gr.Button(
                    "🎬 Create Video",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=1):
                # Output section
                gr.Markdown("### 📤 Output")

                progress_status = gr.Textbox(
                    label="Status",
                    value="Ready to create your video!",
                    interactive=False,
                    lines=10,
                    max_lines=20,
                )

                final_video = gr.Video(
                    label="Final Video",
                    height=400,
                )

                thumbnail_image = gr.Image(
                    label="Generated Thumbnail",
                    type="filepath",
                    height=300,
                    visible=True,
                )

                with gr.Accordion("📋 Details", open=False):
                    summary_display = gr.Textbox(
                        label="Video Analysis Summary",
                        lines=10,
                        interactive=False,
                    )

                    script_display = gr.Textbox(
                        label="Generated Script",
                        lines=10,
                        interactive=False,
                    )

        # Connect the button to the workflow
        create_btn.click(
            fn=run_workflow,
            inputs=[
                video_input,
                user_description,
                target_duration,
                generate_music,
            ],
            outputs=[
                final_video,
                progress_status,
                summary_display,
                script_display,
                thumbnail_image,
            ],
        )

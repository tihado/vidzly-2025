import gradio as gr
from introduction import introduction
from mcps.letter_counter import letter_counter


with gr.Blocks() as demo:
    with gr.Tab("Vidzly"):
        # Tell about this project
        # Agent full workflow here

        introduction()

    with gr.Tab("MCP Tools"):
        with gr.Tab("Demo Letter Counter"):
            gr.Interface(
                fn=letter_counter,
                inputs=[gr.Textbox("strawberry"), gr.Textbox("r")],
                outputs=[gr.Number()],
                title="Letter Counter",
                description="Enter text and a letter to count how many times the letter appears in the text.",
                api_name="predict",
            )


if __name__ == "__main__":
    demo.launch(mcp_server=True)

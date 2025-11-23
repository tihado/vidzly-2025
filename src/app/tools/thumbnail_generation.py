import os
from pathlib import Path
from typing import Optional
import google.genai as genai


def thumbnail_generation(
    frame_image_input,
    video_summary: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate an engaging thumbnail with AI-generated text and stickers directly from Gemini.

    Uses Google Gemini API to generate a complete thumbnail image with text overlays
    and stickers based on the frame and video summary.

    Args:
        frame_image_input: Frame image file path (str) from Gradio or frame_extractor
        video_summary (str): Video summary text string (extracted from Video Summarizer JSON)
        output_path (str, optional): Path where the thumbnail should be saved.
                                    If not provided, saves to a temporary file.

    Returns:
        str: Path to generated thumbnail image (PNG format)
    """
    try:
        # Handle Gradio image input format (can be tuple or string)
        if isinstance(frame_image_input, tuple):
            frame_path = frame_image_input[0]
        elif isinstance(frame_image_input, str):
            frame_path = frame_image_input
        else:
            raise ValueError("Invalid frame image input format")

        # Validate frame image file exists
        if not frame_path or not os.path.exists(frame_path):
            raise ValueError(f"Frame image file not found: {frame_path}")

        # Validate video summary is provided
        if not video_summary or not video_summary.strip():
            raise ValueError("Video summary cannot be empty")

        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for thumbnail generation"
            )

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Read frame image as bytes for Gemini
        with open(frame_path, "rb") as f:
            image_data = f.read()

        prompt = f"""Generate a complete, engaging YouTube-style thumbnail image based on this video frame and summary.

VIDEO SUMMARY:
{video_summary}

INSTRUCTIONS:
1. Use the provided frame as the base image
2. Add engaging title text (3-7 words) that captures the video's essence - make it bold and readable
3. Optionally add subtitle text (5-10 words) if it adds value
4. Add appropriate stickers/badges (NEW, HOT, TRENDING, arrows, stars, etc.) if they enhance the thumbnail
5. Ensure text has good contrast with the background (use outlines or shadows if needed)
6. Position elements to avoid covering important visual elements (faces, main subjects)
7. Match the style to the video's mood and pacing
8. Create a clean, professional, and engaging thumbnail that would attract viewers

The thumbnail should be production-ready with all text and graphics already rendered in the image.
Generate the complete thumbnail image with all overlays included."""

        # Use Gemini to generate the thumbnail image directly
        # Request image output using GenerateContentConfig (not GenerationConfig)
        # GenerateContentConfig has both response_mime_type and tools fields
        config = genai.types.GenerateContentConfig(
            response_mime_type="image/png",
            tools=None,
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                prompt,
                genai.types.Part(
                    inline_data=genai.types.Blob(
                        data=image_data, mime_type="image/png"
                    )
                ),
            ],
            config=config,
        )
        
        # Extract image from response
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    thumbnail_data = part.inline_data.data
                    
                    # Generate output path if not provided
                    if output_path is None:
                        frame_name = Path(frame_path).stem
                        output_dir = Path(frame_path).parent / "thumbnails"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_path = str(output_dir / f"{frame_name}_thumbnail.png")
                    
                    # Ensure output directory exists
                    output_dir = os.path.dirname(output_path)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                    
                    # Save thumbnail
                    with open(output_path, "wb") as f:
                        f.write(thumbnail_data)
                    
                    return os.path.abspath(output_path)
        
        raise ValueError("Gemini did not return image data in the response")

    except Exception as e:
        raise Exception(f"Error generating thumbnail: {str(e)}")


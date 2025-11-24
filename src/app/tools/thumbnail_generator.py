import os
import tempfile
import time
from typing import Optional
from dotenv import load_dotenv
import google.genai as genai
from PIL import Image
from io import BytesIO
import mimetypes

# Load environment variables
load_dotenv()


def thumbnail_generator(
    image_input,
    summary: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a highly engaging and funny thumbnail image for a TikTok video/social media post.
    Uses Gemini AI to generate the complete thumbnail image directly, using the input image as
    a background and adding strategically placed text overlays and humorous stickers/emojis.

    Args:
        image_input: Image file path (str) or tuple from Gradio - used as the background image
        summary: Text summary of the video content (used to generate appropriate text and stickers)
        output_path: Optional path where the thumbnail should be saved.
                    If not provided, saves to a temporary file.

    Returns:
        str: Path to the generated thumbnail image (PNG format)

    Raises:
        ValueError: If image file not found or GOOGLE_API_KEY not set
        Exception: If thumbnail generation fails
    """
    try:
        # Handle Gradio image input format (can be tuple or string)
        if isinstance(image_input, tuple):
            image_path = image_input[0]
        elif isinstance(image_input, str):
            image_path = image_input
        else:
            raise ValueError("Invalid image input format")

        # Validate image file exists
        if not image_path or not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_path}")

        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Read image file as bytes
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            # Default to png if cannot determine
            mime_type = "image/png"

        # Create comprehensive prompt for thumbnail generation
        prompt = f"""Generate a highly engaging and funny thumbnail image for a TikTok video/social media post.

Use the provided background image as the foundation, and create a complete thumbnail that includes:

BACKGROUND IMAGE: Use the provided image as the base. This is a high-quality, captivating photograph that should fill the entire thumbnail area.

TEXT OVERLAY: Add prominent, dramatic text that is:
- Catchy, attention-grabbing, and creates curiosity based on this video summary: "{summary}"
- Keep it short (3-8 words max) and impactful
- Use bright, contrasting colors (neon yellow, electric green, vibrant orange) with a dark outline for maximum readability
- Position the text in an empty or less busy area (upper left, upper right, or bottom) so it doesn't obscure key subjects
- Make the text bold and large enough to be easily readable

STICKER/EMOJI: Add a large, expressive, high-contrast sticker or emoji that enhances the comedic effect:
- Options: 🚨 (siren/emergency), 😰 (sweating face), ☠️ (skull), 😱 (screaming), 🔥 (fire), ⚠️ (warning), 💥 (explosion)
- Position it near the main subject or focal point, as if it's an extension of the dramatic reaction
- Make it large and prominent without covering the main subject entirely

OVERALL DESIGN:
- Vibe: absurd, dramatic, high-energy, slightly chaotic
- Colors: vibrant and eye-catching
- Style: professional yet intentionally over-the-top
- Integration: all overlays should be seamlessly integrated for comedic effect
- The final image should be engaging, funny, and make viewers curious to watch the video

Generate the complete thumbnail image with all these elements integrated."""

        # Create image blob
        image_blob = genai.types.Blob(data=image_data, mime_type=mime_type)
        image_part = genai.types.Part(inline_data=image_blob)

        # Use Gemini to generate the thumbnail image directly
        # Use gemini-2.5-flash-image model which supports image generation
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, image_part],
                config={
                    "response_modalities": ["IMAGE"],
                },
            )
        except Exception as e:
            # If response_modalities doesn't work, try without it
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt, image_part],
                )
            except:
                raise Exception(f"Failed to generate image with Gemini: {str(e)}")

        # Extract the generated image from the response
        generated_image = None

        # Check if response has image data
        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and candidate.content:
                    if hasattr(candidate.content, "parts"):
                        for part in candidate.content.parts:
                            # Check for inline_data (image data)
                            if hasattr(part, "inline_data") and part.inline_data:
                                generated_image = part.inline_data.data
                                break
                            # Check for blob (alternative format)
                            elif hasattr(part, "blob") and part.blob:
                                generated_image = part.blob.data
                                break

        # If no image found in candidates, try alternative response structure
        if generated_image is None:
            # Try to get image from response directly
            if hasattr(response, "parts"):
                for part in response.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        generated_image = part.inline_data.data
                        break
                    elif hasattr(part, "blob") and part.blob:
                        generated_image = part.blob.data
                        break

        # If still no image, the model might have returned text describing the image
        # In that case, we'll need to handle it differently or raise an error
        if generated_image is None:
            # Check if response has text (might indicate the model didn't generate an image)
            if hasattr(response, "text") and response.text:
                raise Exception(
                    f"Gemini returned text instead of image. This model may not support image generation. "
                    f"Response: {response.text[:200]}"
                )
            else:
                raise Exception(
                    "Failed to extract generated image from Gemini response"
                )

        # Convert image data to PIL Image
        thumbnail = Image.open(BytesIO(generated_image)).convert("RGB")

        # Determine output path
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            output_path = os.path.join(temp_dir, f"thumbnail_{timestamp}.png")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Save thumbnail
        thumbnail.save(output_path, "PNG", quality=95)

        # Return absolute path
        return os.path.abspath(output_path)

    except Exception as e:
        raise Exception(f"Error generating thumbnail: {str(e)}")

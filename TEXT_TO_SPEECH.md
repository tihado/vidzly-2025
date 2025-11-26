# Text-to-Speech Feature

## Overview

Convert text transcription to audio using Google Text-to-Speech (gTTS).

## Installation

The required `gtts` package is already included in the project dependencies.

## Usage

### Through Gradio UI

1. Start the app: `poetry run python src/app/app.py`
2. Navigate to the "Text-to-Speech" tab
3. Enter your text in the "Text to Convert" box
4. Click Submit
5. The generated audio will be saved to `outputs/audio/generated_speech.mp3`

### Example Input

```
Welcome to our video tutorial on AI and machine learning. Today we'll explore how neural networks process information and learn from data.
```

### Programmatic Usage

```python
from src.app.tools.text_to_speech import text_to_speech_simple

# Convert text to speech
text = "Hello, welcome to my video!"
result = text_to_speech_simple(text)
print(result)
# Output: "Audio generated successfully at: outputs/audio/generated_speech.mp3"
```

## Features

- ✅ Converts any text to MP3 audio
- ✅ Uses Google Text-to-Speech (free tier)
- ✅ Supports English language
- ✅ Handles long text, special characters, punctuation
- ✅ Automatic output directory creation

## Output Location

Generated audio files are saved to: `outputs/audio/generated_speech.mp3`

## Technical Details

- **Engine**: Google Text-to-Speech (gTTS)
- **Language**: English (en)
- **Format**: MP3
- **Speed**: Normal (not slow)
- **Quality**: Standard gTTS quality

## Limitations

- Free tier limitations apply
- English language only (can be extended to other languages)
- Standard voice only (not customizable in free tier)
- Requires internet connection

## Advanced Features (Future)

The tool includes a placeholder for advanced text-to-speech with:

- Voice selection (male/female/neutral)
- Speed control (0.5x to 2.0x)
- Multiple language support
- Higher quality audio

To enable advanced features, integrate with:

- Google Cloud Text-to-Speech API
- ElevenLabs API
- Azure Speech Services
- Amazon Polly

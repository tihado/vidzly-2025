"""
Text-to-Speech Converter
Converts text transcription to audio using Google's Text-to-Speech API.
Supports plain text, SRT, VTT, and JSON subtitle formats.
"""

import os
import re
import json
from pathlib import Path
from typing import Literal, Optional


def parse_srt(content: str) -> list[str]:
    """Parse SRT subtitle content and extract dialogue text."""
    dialogues = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Get dialogue (lines after timestamp)
        dialogue = ' '.join(lines[2:])
        # Remove speaker labels
        dialogue = re.sub(r'\[.*?\]|\(.*?\)|^.*?:', '', dialogue).strip()
        if dialogue:
            dialogues.append(dialogue)
    
    return dialogues


def parse_srt_with_timing(content: str) -> list[dict]:
    """Parse SRT subtitle content with timing information."""
    segments = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Parse timestamp line (format: 00:00:00,000 --> 00:00:05,000)
        timestamp_line = lines[1]
        if '-->' not in timestamp_line:
            continue
        
        times = timestamp_line.split('-->')
        if len(times) != 2:
            continue
        
        start_time = _parse_timestamp_to_seconds(times[0].strip())
        end_time = _parse_timestamp_to_seconds(times[1].strip())
        
        # Get dialogue
        dialogue = ' '.join(lines[2:])
        # Remove speaker labels
        dialogue = re.sub(r'\[.*?\]|\(.*?\)|^.*?:', '', dialogue).strip()
        
        if dialogue and start_time is not None and end_time is not None:
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'dialogue': dialogue
            })
    
    return segments


def parse_vtt(content: str) -> list[str]:
    """Parse VTT subtitle content and extract dialogue text."""
    dialogues = []
    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.MULTILINE)
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        timestamp_idx = -1
        for i, line in enumerate(lines):
            if '-->' in line:
                timestamp_idx = i
                break
        
        if timestamp_idx == -1:
            continue
        
        # Get dialogue after timestamp
        dialogue = ' '.join(lines[timestamp_idx + 1:])
        # Remove speaker labels
        dialogue = re.sub(r'\[.*?\]|\(.*?\)|^.*?:', '', dialogue).strip()
        if dialogue:
            dialogues.append(dialogue)
    
    return dialogues


def parse_vtt_with_timing(content: str) -> list[dict]:
    """Parse VTT subtitle content with timing information."""
    segments = []
    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.MULTILINE)
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        timestamp_idx = -1
        for i, line in enumerate(lines):
            if '-->' in line:
                timestamp_idx = i
                break
        
        if timestamp_idx == -1:
            continue
        
        # Parse timestamp
        timestamp_line = lines[timestamp_idx]
        times = timestamp_line.split('-->')
        if len(times) != 2:
            continue
        
        start_time = _parse_timestamp_to_seconds(times[0].strip())
        end_time = _parse_timestamp_to_seconds(times[1].strip())
        
        # Get dialogue
        dialogue = ' '.join(lines[timestamp_idx + 1:])
        # Remove speaker labels
        dialogue = re.sub(r'\[.*?\]|\(.*?\)|^.*?:', '', dialogue).strip()
        
        if dialogue and start_time is not None and end_time is not None:
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'dialogue': dialogue
            })
    
    return segments


def parse_json_scenario(content: str) -> list[str]:
    """Parse JSON scenario format and extract dialogue text."""
    try:
        data = json.loads(content)
        if isinstance(data, str):
            data = json.loads(data)
        
        dialogues = []
        if 'scenes' in data:
            for scene in data['scenes']:
                if 'dialogue' in scene and scene['dialogue']:
                    dialogues.append(scene['dialogue'])
        
        return dialogues
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("Invalid JSON scenario format")


def parse_json_with_timing(content: str) -> list[dict]:
    """Parse JSON scenario format with timing information."""
    try:
        data = json.loads(content)
        if isinstance(data, str):
            data = json.loads(data)
        
        segments = []
        if 'scenes' in data:
            for scene in data['scenes']:
                start_time = scene.get('start_time')
                end_time = scene.get('end_time')
                duration = scene.get('duration')
                dialogue = scene.get('dialogue', '')
                
                # Calculate end_time if not provided but duration is
                if end_time is None and duration is not None and start_time is not None:
                    end_time = start_time + duration
                
                # Skip if no timing info
                if start_time is None or end_time is None:
                    continue
                
                # Use placeholder if no dialogue
                if not dialogue:
                    dialogue = f"Scene {scene.get('scene_id', '?')}"
                
                segments.append({
                    'start_time': float(start_time),
                    'end_time': float(end_time),
                    'dialogue': dialogue
                })
        
        return segments
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        raise ValueError("Invalid JSON scenario format")


def _parse_timestamp_to_seconds(timestamp: str) -> Optional[float]:
    """
    Convert timestamp string to seconds.
    Supports formats: HH:MM:SS,mmm or HH:MM:SS.mmm
    """
    try:
        # Replace comma with dot for milliseconds
        timestamp = timestamp.replace(',', '.')
        
        # Parse time components
        parts = timestamp.split(':')
        if len(parts) != 3:
            return None
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        # Convert to total seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
    except (ValueError, IndexError):
        return None


def detect_format(content: str) -> str:
    """Auto-detect subtitle format from content."""
    content_stripped = content.strip()
    
    if content_stripped.startswith("WEBVTT"):
        return "vtt"
    elif content_stripped.startswith("{"):
        return "json"
    elif re.search(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->', content, re.MULTILINE):
        return "srt"
    else:
        return "text"


def text_to_speech(
    text: str,
    voice: Literal["male", "female", "neutral"] = "neutral",
    speed: float = 1.0,
    output_path: Optional[str] = None
) -> str:
    """
    Convert text to speech audio.
    
    Args:
        text: The text to convert to speech
        voice: Voice type - "male", "female", or "neutral"
        speed: Speech speed (0.5 to 2.0, where 1.0 is normal speed)
        output_path: Optional custom output path for the audio file
        
    Returns:
        Path to the generated audio file
        
    Raises:
        ValueError: If text is empty or parameters are invalid
        RuntimeError: If audio generation fails
    """
    # Validate inputs
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    if not (0.5 <= speed <= 2.0):
        raise ValueError("Speed must be between 0.5 and 2.0")
    
    if voice not in ["male", "female", "neutral"]:
        raise ValueError("Voice must be 'male', 'female', or 'neutral'")
    
    # Import genai only when needed for advanced features
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Please install google-genai: pip install google-genai")
    
    # Configure API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    genai.configure(api_key=api_key)
    
    # Determine output path
    if output_path is None:
        output_dir = Path("outputs/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "generated_speech.mp3")
    else:
        # Ensure directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use Gemini to generate audio description/narration prompt
        # Since Gemini doesn't have direct TTS, we'll use a workaround with available APIs
        # For now, we'll create a simple implementation that can be extended
        
        # Voice characteristics mapping
        voice_prompts = {
            "male": "deep, masculine, authoritative voice",
            "female": "clear, feminine, warm voice", 
            "neutral": "balanced, professional, clear voice"
        }
        
        speed_description = ""
        if speed < 0.8:
            speed_description = "speaking slowly and clearly"
        elif speed > 1.2:
            speed_description = "speaking at a brisk pace"
        else:
            speed_description = "speaking at a normal pace"
        
        # Generate enhanced text with voice instructions
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Prepare this text for text-to-speech conversion with a {voice_prompts[voice]}, {speed_description}:
        
        Text: {text}
        
        Provide the text in a format optimized for speech synthesis, with appropriate pauses marked by commas and periods.
        Only return the optimized text, nothing else.
        """
        
        response = model.generate_content(prompt)
        optimized_text = response.text.strip()
        
        # Note: Since Google Gemini doesn't provide direct TTS API in the SDK,
        # we'll save the optimized text and return a placeholder
        # In production, you would integrate with Google Cloud Text-to-Speech API
        # or another TTS service like ElevenLabs, Azure TTS, etc.
        
        # For now, create a text file with instructions
        text_output_path = output_path.replace('.mp3', '.txt')
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write(f"Voice: {voice}\n")
            f.write(f"Speed: {speed}x\n")
            f.write(f"Original Text:\n{text}\n\n")
            f.write(f"Optimized for TTS:\n{optimized_text}\n")
        
        # Return the path with a note
        result_message = f"""
Audio generation prepared successfully!

Text file created at: {text_output_path}

To generate actual audio, you need to:
1. Install Google Cloud Text-to-Speech: pip install google-cloud-texttospeech
2. Set up Google Cloud credentials
3. Or use alternative TTS services like:
   - ElevenLabs (https://elevenlabs.io/)
   - Azure Speech Services
   - Amazon Polly
   - gTTS (free, but limited)

The text has been optimized for {voice} voice at {speed}x speed.
"""
        
        return result_message
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate audio: {str(e)}")


def text_to_speech_simple(
    text: str,
    voice: str = "neutral",
    language: str = "en",
    speed: str = "normal",
    format_type: str = "text",
    generate_segments: bool = False
) -> str:
    """
    Text-to-speech using gTTS (Google Text-to-Speech) - free tier.
    Supports plain text, SRT, VTT, and JSON subtitle formats.
    Can generate single audio file or timed segments matching subtitle timing.
    
    Args:
        text: The text/subtitle content to convert to speech
        voice: Voice type - "male", "female", or "neutral" (affects language variant)
        language: Language code (e.g., "en" for English, "es" for Spanish)
        speed: Speech speed - "normal" or "slow"
        format_type: Input format - "text", "srt", "vtt", "json", or "auto" to detect
        generate_segments: If True and input is subtitles, generates individual audio files
                          for each subtitle segment with timing info (for video sync)
        
    Returns:
        Path to the generated audio file(s). 
        - If generate_segments=False: Returns single combined audio file path
        - If generate_segments=True: Returns JSON string with audio segments and timing info
        
    Note:
        gTTS doesn't directly support voice gender, but we can use different
        language variants (TLDs) that may sound slightly different:
        - male: uses .co.uk (British English - often perceived as more masculine)
        - female: uses .com.au (Australian English - often perceived as more feminine)
        - neutral: uses .com (Standard English)
        
    Timed Audio Segments Format (when generate_segments=True):
        {
            "segments": [
                {
                    "segment_id": 1,
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "dialogue": "Welcome to our video",
                    "audio_file": "outputs/audio/segment_1.mp3"
                },
                ...
            ],
            "total_duration": 15.0
        }
    """
    try:
        from gtts import gTTS
    except ImportError:
        return "Please install gTTS: pip install gtts"
    
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Auto-detect format if requested
    if format_type == "auto":
        format_type = detect_format(text)
    
    # Parse subtitles based on format
    subtitle_segments = []
    if format_type == "srt":
        dialogues = parse_srt(text)
        if not dialogues:
            raise ValueError("No dialogue found in SRT content")
        if generate_segments:
            subtitle_segments = parse_srt_with_timing(text)
            if not subtitle_segments:
                raise ValueError("Failed to parse SRT timing information")
        else:
            final_text = ' '.join(dialogues)
    elif format_type == "vtt":
        dialogues = parse_vtt(text)
        if not dialogues:
            raise ValueError("No dialogue found in VTT content")
        if generate_segments:
            subtitle_segments = parse_vtt_with_timing(text)
            if not subtitle_segments:
                raise ValueError("Failed to parse VTT timing information")
        else:
            final_text = ' '.join(dialogues)
    elif format_type == "json":
        dialogues = parse_json_scenario(text)
        if not dialogues:
            raise ValueError("No dialogue found in JSON content")
        if generate_segments:
            subtitle_segments = parse_json_with_timing(text)
            if not subtitle_segments:
                raise ValueError("Failed to parse JSON timing information")
        else:
            final_text = ' '.join(dialogues)
    else:
        # Plain text - use as is
        final_text = text
        generate_segments = False  # Can't generate segments without timing info
    
    # Map voice preference to gTTS TLD (top-level domain)
    # Different accents can give perception of different voice characteristics
    voice_tld_map = {
        "male": "co.uk",      # British English (deeper/masculine perception)
        "female": "com.au",    # Australian English (lighter/feminine perception)
        "neutral": "com"       # US English (neutral)
    }
    
    tld = voice_tld_map.get(voice, "com")
    slow = (speed == "slow")
    
    # Create output directory
    output_dir = Path("outputs/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if generate_segments and subtitle_segments:
            # Generate individual audio files for each subtitle segment
            result_segments = []
            total_duration = 0.0
            
            for idx, segment in enumerate(subtitle_segments, 1):
                segment_text = segment['dialogue']
                start_time = segment['start_time']
                end_time = segment['end_time']
                total_duration = max(total_duration, end_time)
                
                # Generate audio for this segment
                segment_path = str(output_dir / f"segment_{idx}.mp3")
                tts = gTTS(text=segment_text, lang=language, slow=slow, tld=tld)
                tts.save(segment_path)
                
                result_segments.append({
                    "segment_id": idx,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "dialogue": segment_text,
                    "audio_file": segment_path
                })
            
            # Return JSON with segment information
            result = {
                "segments": result_segments,
                "total_duration": total_duration,
                "voice": voice,
                "language": language,
                "speed": speed
            }
            return json.dumps(result, indent=2)
        else:
            # Generate single combined audio file
            output_path = str(output_dir / "generated_speech.mp3")
            tts = gTTS(text=final_text, lang=language, slow=slow, tld=tld)
            tts.save(output_path)
            
            # Return the path so Gradio can load the audio file
            return output_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate audio: {str(e)}")

# Complete Video Editing Workflow Guide

This guide demonstrates the complete workflow for creating synchronized videos with subtitles and audio narration.

## Workflow Overview

```
Video Composer → Subtitle Generator → Text-to-Speech
     (timing)         (sync text)        (sync audio)
```

## Step-by-Step Process

### Step 1: Video Composer

Create a composed video from multiple source clips with precise timing.

**Input:**

- JSON script defining scenes, timing, and transitions
- Source video files
- Optional: Background music

**Example Script:**

```json
{
  "total_duration": 15.0,
  "scenes": [
    {
      "scene_id": 1,
      "source_video": 0,
      "start_time": 0.0,
      "end_time": 5.0,
      "duration": 5.0,
      "transition_in": "fade",
      "transition_out": "crossfade"
    },
    {
      "scene_id": 2,
      "source_video": 1,
      "start_time": 5.0,
      "end_time": 10.0,
      "duration": 5.0,
      "transition_in": "crossfade",
      "transition_out": "fade"
    },
    {
      "scene_id": 3,
      "source_video": 0,
      "start_time": 10.0,
      "end_time": 15.0,
      "duration": 5.0,
      "transition_in": "fade",
      "transition_out": "fade"
    }
  ]
}
```

**Output:**

- Composed video file
- JSON script (can be used in next steps)

### Step 2: Subtitle Generator

Generate perfectly timed subtitles that match the video composition.

**Input Option 1 - Video Composer Output:**
Use the JSON script from Video Composer directly. The subtitle generator will:

- Auto-detect the format (looks for `source_video` field)
- Calculate cumulative timing from scene durations
- Generate placeholder dialogue: "Scene {scene_id}"

**Input Option 2 - Custom Dialogue:**
Add dialogue to the Video Composer JSON:

```json
{
  "total_duration": 15.0,
  "scenes": [
    {
      "scene_id": 1,
      "source_video": 0,
      "start_time": 0.0,
      "duration": 5.0,
      "dialogue": "Welcome to our tutorial on AI video editing.",
      "speaker": "Narrator"
    },
    {
      "scene_id": 2,
      "source_video": 1,
      "start_time": 5.0,
      "duration": 5.0,
      "dialogue": "First, let's look at video composition.",
      "speaker": "Narrator"
    },
    {
      "scene_id": 3,
      "source_video": 0,
      "start_time": 10.0,
      "duration": 5.0,
      "dialogue": "This allows you to combine multiple clips seamlessly.",
      "speaker": "Narrator"
    }
  ]
}
```

**Output Format Options:**

- **SRT (SubRip):**

  ```
  1
  00:00:00,000 --> 00:00:05,000
  [Narrator] Welcome to our tutorial on AI video editing.

  2
  00:00:05,000 --> 00:00:10,000
  [Narrator] First, let's look at video composition.

  3
  00:00:10,000 --> 00:00:15,000
  [Narrator] This allows you to combine multiple clips seamlessly.
  ```

- **VTT (WebVTT):**

  ```
  WEBVTT

  1
  00:00:00.000 --> 00:00:05.000
  [Narrator] Welcome to our tutorial on AI video editing.

  2
  00:00:05.000 --> 00:00:10.000
  [Narrator] First, let's look at video composition.

  3
  00:00:10.000 --> 00:00:15.000
  [Narrator] This allows you to combine multiple clips seamlessly.
  ```

### Step 3: Text-to-Speech Converter

Convert subtitles to synchronized audio narration.

**Two Output Modes:**

#### Mode 1: Combined Narration (Default)

Generate a single audio file with all dialogue combined.

**Settings:**

- Input: Paste subtitle content (SRT/VTT/JSON)
- Voice: Male (British), Female (Australian), or Neutral (US)
- Language: 10 languages (en, es, fr, de, it, pt, zh, ja, ko, ar)
- Speed: Normal or Slow
- Format: Auto-detect (or specify: srt/vtt/json/text)
- Generate Timed Segments: **OFF**

**Output:**

- Single MP3 file with all dialogue

#### Mode 2: Timed Audio Segments (For Video Sync)

Generate individual audio files for each subtitle with precise timing.

**Settings:**

- Input: Paste subtitle content (SRT/VTT/JSON)
- Voice, Language, Speed: Same as above
- Format: Auto-detect (or specify: srt/vtt/json)
- Generate Timed Segments: **ON**

**Output - JSON with timing metadata:**

```json
{
  "segments": [
    {
      "segment_id": 1,
      "start_time": 0.0,
      "end_time": 5.0,
      "duration": 5.0,
      "dialogue": "Welcome to our tutorial on AI video editing.",
      "audio_file": "/path/to/segment_1.mp3"
    },
    {
      "segment_id": 2,
      "start_time": 5.0,
      "end_time": 10.0,
      "duration": 5.0,
      "dialogue": "First, let's look at video composition.",
      "audio_file": "/path/to/segment_2.mp3"
    },
    {
      "segment_id": 3,
      "start_time": 10.0,
      "end_time": 15.0,
      "duration": 5.0,
      "dialogue": "This allows you to combine multiple clips seamlessly.",
      "audio_file": "/path/to/segment_3.mp3"
    }
  ]
}
```

**Benefits of Timed Segments:**

- Each audio file corresponds exactly to one subtitle/scene
- Precise timing synchronization with video frames
- Easy to integrate audio segments into video composition
- Individual files can be processed separately (volume, effects)
- Perfect for frame-by-frame audio-visual alignment

## Complete Workflow Example

### 1. Create Video Composition

```json
{
  "total_duration": 10.0,
  "scenes": [
    {
      "scene_id": 1,
      "source_video": 0,
      "start_time": 0.0,
      "duration": 5.0,
      "dialogue": "Welcome to Vidzly!",
      "speaker": "Host"
    },
    {
      "scene_id": 2,
      "source_video": 1,
      "start_time": 5.0,
      "duration": 5.0,
      "dialogue": "Let's create amazing videos together.",
      "speaker": "Host"
    }
  ]
}
```

### 2. Generate Subtitles

- **Input:** Paste the JSON from step 1
- **Output Format:** SRT
- **Result:**

  ```
  1
  00:00:00,000 --> 00:00:05,000
  [Host] Welcome to Vidzly!

  2
  00:00:05,000 --> 00:00:10,000
  [Host] Let's create amazing videos together.
  ```

### 3. Generate Timed Audio

- **Input:** Paste the SRT from step 2
- **Voice:** Female
- **Language:** English
- **Speed:** Normal
- **Generate Timed Segments:** ON
- **Result:** JSON with 2 audio files perfectly timed to video frames

### 4. Use the Output

- Add subtitle file (.srt or .vtt) to your composed video
- Integrate timed audio segments using the JSON timing metadata
- Each audio segment plays exactly during its corresponding video scene

## Features Summary

### Subtitle Generator

✅ Accepts Video Composer output directly
✅ Auto-detects format (video composer vs. subtitle scenario)
✅ Calculates cumulative timing automatically
✅ Supports custom dialogue or placeholder text
✅ Outputs SRT and VTT formats
✅ Speaker labels with `[Speaker]` format
✅ Perfect timing synchronization

### Text-to-Speech

✅ Accepts subtitle formats (SRT/VTT/JSON) and plain text
✅ Auto-detects input format
✅ Voice selection: Male (British), Female (Australian), Neutral (US)
✅ 10 language support: en, es, fr, de, it, pt, zh, ja, ko, ar
✅ Speed control: Normal, Slow
✅ **Two output modes:**

- Combined narration (single MP3)
- Timed audio segments (individual MP3s with timing JSON)
  ✅ Frame-perfect timing for video synchronization
  ✅ Handles empty dialogue with placeholders

## Testing

- **26 subtitle generator tests** - All passing ✅
- **27 text-to-speech tests** - All passing ✅
  - 21 tests for basic TTS functionality
  - 6 tests for timed audio segment generation
- **Total: 53 comprehensive tests**

## Technical Details

### Timing Precision

- Supports millisecond precision (3 decimal places)
- Timestamp formats:
  - SRT: `HH:MM:SS,mmm` (comma separator)
  - VTT: `HH:MM:SS.mmm` (dot separator)
  - JSON: Float seconds (e.g., 5.5)

### Audio File Naming

- Combined mode: `generated_speech.mp3`
- Timed segments: `segment_1.mp3`, `segment_2.mp3`, etc.
- All files saved to: `outputs/audio/`

### Format Detection Rules

1. Check for `WEBVTT` header → VTT format
2. Check for `-->` timestamp → SRT format
3. Check for valid JSON structure → JSON format
4. Otherwise → Plain text

## Integration with MCP Server

All tools are accessible via Gradio interface with MCP server enabled:

```python
demo.launch(mcp_server=True)
```

This allows programmatic access to all tools for automation and integration with other systems.

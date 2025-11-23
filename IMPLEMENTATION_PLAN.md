# Complete Vidzly Workflow Implementation Plan

## System Architecture Overview

The Vidzly system will process user-uploaded videos and descriptions to create polished 30-second short videos through the following workflow:

1. **Input**: Multiple video files + user description
2. **Analysis**: Understand video content and user requirements
3. **Script Generation**: Create detailed script/storyboard for the final video
4. **Selection**: Choose relevant scenes and music based on script
5. **Processing**: Clip, edit, and combine videos according to script
6. **Output**: Final 30-second video

## Required MCP Tools

### Phase 1: Video Analysis Tools

#### 1.1 Video Summarizer (`video_summarizer.py`)

- **Purpose**: Analyze video content and generate text summaries
- **Input**: Video file path
- **Output**: JSON with video summary, key scenes, detected objects/activities, mood tags
- **Technology**: OpenCV for frame extraction, Google Gemini Vision API for analysis
- **Returns**: Structured summary including duration, scene descriptions, visual elements

#### 1.2 Video Metadata Extractor (`video_metadata.py`)

- **Purpose**: Extract technical metadata from videos
- **Input**: Video file path
- **Output**: Duration, resolution, fps, codec, file size
- **Technology**: MoviePy or ffmpeg-python
- **Returns**: Technical specifications for processing decisions

### Phase 2: Content Understanding Tools

#### 2.1 Description Parser (`description_parser.py`)

- **Purpose**: Parse and understand user descriptions to extract requirements
- **Input**: User description text
- **Output**: Structured requirements (mood, style, key elements, target length)
- **Technology**: Google Gemini API for natural language understanding
- **Returns**: JSON with extracted mood, style preferences, key topics, pacing

#### 2.2 Scene Matcher (`scene_matcher.py`)

- **Purpose**: Match video scenes to user requirements
- **Input**: Video summaries + parsed requirements
- **Output**: List of matching scenes with timestamps and relevance scores
- **Technology**: Semantic similarity matching using embeddings
- **Returns**: Ranked list of scene segments to use

### Phase 3: Script Generation & Planning

#### 3.1 Video Script Generator (`video_script_generator.py`)

- **Purpose**: Create a detailed script/storyboard for the final 30-second video
- **Input**: Video summaries, matched scenes, parsed user requirements
- **Output**: Detailed script with scene sequence, timings, transitions, and structure
- **Technology**: Google Gemini API for intelligent script generation
- **Returns**: JSON script containing:
  - Scene sequence with source video and timestamps
  - Duration for each scene segment (must sum to ~30 seconds)
  - Transition types between scenes (cut, fade, crossfade, etc.)
  - Pacing and rhythm plan
  - Music synchronization points (beat markers, mood changes)
  - Overall narrative structure and flow
  - Visual style recommendations

### Phase 4: Video Processing Tools

#### 4.1 Video Clipper (`video_clipper.py`)

- **Purpose**: Extract specific segments from videos based on script
- **Input**: Video path, start time, end time
- **Output**: Clipped video file path
- **Technology**: MoviePy or ffmpeg-python
- **Returns**: Path to clipped video segment

#### 4.2 Scene Selector (`scene_selector.py`)

- **Purpose**: Intelligently select best scenes to fit 30-second target (if script needs refinement)
- **Input**: List of matched scenes, target duration (30s), script requirements
- **Output**: Optimized scene selection with timestamps
- **Technology**: Algorithm to maximize relevance while fitting duration
- **Returns**: Final scene list with precise timestamps aligned to script

### Phase 5: Audio & Composition Tools

#### 5.1 Music Selector (`music_selector.py`)

- **Purpose**: Generate appropriate background sound effects based on mood/style from script
- **Input**:
  - Mood/style tags (comma-separated string or list)
  - Target duration (0.5-30 seconds)
  - Optional: style description, BPM, sync points
  - Optional: looping (boolean), prompt_influence (0-1 float)
- **Output**: Generated audio file path (MP3 format)
- **Technology**: ElevenLabs API for sound effect generation
- **Returns**: Path to generated MP3 audio file
- **API Parameters**:
  - `text`: Prompt describing the desired sound effect
  - `duration_seconds`: Duration in seconds (0.5-30)
  - `loop`: Boolean for seamless looping
  - `prompt_influence`: Float (0-1) controlling how closely output matches prompt
  - `output_format`: Audio format (default: "mp3_44100_128")

#### 5.2 Video Composer (`video_composer.py`)

- **Purpose**: Combine video clips, add music, apply transitions according to script
- **Input**:
  - `script`: JSON script with scene information (required)
  - `video_clips`: List of source video file paths (required)
  - `music_path`: Background music file path (optional)
  - `output_path`: Output file path (optional)
- **Script Format**:
  - Each scene's `source_video` references a video from `video_clips` by:
    - Integer index (0-based): `"source_video": 0` references the first video
    - Filename string: `"source_video": "video.mp4"` matches by basename
  - The same video can be used in multiple scenes with different time ranges
  - Each scene specifies `start_time`, `end_time`, and transition types
- **Output**: Final composed video file path
- **Technology**: MoviePy for video composition, transitions, audio mixing
- **Returns**: Path to final 30-second video

### Phase 6: Workflow Orchestration

#### 6.1 Video Workflow Orchestrator (`video_workflow.py`)

- **Purpose**: Main workflow that coordinates all tools
- **Input**: List of video files, user description
- **Output**: Final video file path, processing summary, generated script
- **Technology**: Orchestrates all MCP tools in sequence
- **Returns**: Final video, processing report, and script JSON

## Implementation Phases

### Phase 1: Foundation (Dependencies & Basic Tools)

1. Add video processing dependencies (opencv-python, moviepy, ffmpeg-python, numpy, pillow)
2. Implement Video Metadata Extractor
3. Implement Video Summarizer
4. Set up temporary file storage system

### Phase 2: Understanding Layer

1. Implement Description Parser
2. Implement Scene Matcher
3. Test analysis and matching pipeline

### Phase 3: Script Generation

1. Implement Video Script Generator
2. Test script generation with various inputs
3. Validate script timing (must sum to ~30 seconds)

### Phase 4: Processing Layer

1. Implement Video Clipper
2. Implement Scene Selector
3. Test video clipping and selection based on scripts

### Phase 5: Composition Layer

1. Implement Music Selector (start with simple mood-based selection)
2. Implement Video Composer
3. Test full composition pipeline with script

### Phase 6: Integration & UI

1. Implement Video Workflow Orchestrator
2. Create main Vidzly UI in app.py (upload, description, progress, script preview, output)
3. Integrate all MCP tools into Gradio interface
4. Add error handling and user feedback

### Phase 7: Polish & Optimization

1. Add progress tracking
2. Optimize processing speed
3. Add preview functionality
4. Improve error messages and edge case handling
5. Add script editing/refinement capability

## File Structure

```
src/app/
├── app.py                    # Main Gradio app with Vidzly workflow UI
├── introduction.py           # Existing intro component
├── tools/
│   ├── __init__.py
│   ├── video_metadata.py     # Extract video technical info
│   ├── video_summarizer.py   # Analyze and summarize video content
│   ├── description_parser.py # Parse user descriptions
│   ├── scene_matcher.py      # Match scenes to requirements
│   ├── video_script_generator.py # Generate detailed video script
│   ├── video_clipper.py      # Extract video segments
│   ├── scene_selector.py     # Select optimal scenes for 30s video
│   ├── music_selector.py     # Choose background music
│   ├── video_composer.py     # Combine clips and add music
│   └── video_workflow.py     # Main workflow orchestrator
└── utils/
    ├── __init__.py
    ├── file_manager.py       # Handle temporary file storage
    └── video_utils.py        # Shared video processing utilities
```

## File Storage Strategy

### Storage Locations

1. **Uploaded Videos (Gradio Temporary Directory)**

   - Gradio automatically stores uploaded files in system temp directory
   - Can be customized with `GRADIO_TEMP_DIR` environment variable
   - Files accessible via file paths returned by `gr.File` component
   - These are temporary and may be cleaned up by Gradio

2. **Processing Working Directory**

   - Create: `src/app/temp/` or use system temp with unique session IDs
   - Store: Clipped video segments, intermediate processing files
   - Structure: `temp/{session_id}/clips/`, `temp/{session_id}/final/`
   - Cleanup: Delete after processing completes or on session timeout

3. **Final Output Storage**
   - Store final videos in: `src/app/outputs/` or `temp/{session_id}/final/`
   - Return file path to Gradio `gr.Video` component for display/download
   - Gradio will serve the file from this path
   - Implement cleanup policy (e.g., delete after 24 hours)

### File Manager Implementation

The `file_manager.py` utility should:

- Create session-based temporary directories
- Generate unique file names to avoid conflicts
- Provide cleanup functions (session cleanup, old file cleanup)
- Handle path resolution (absolute paths for Gradio serving)
- Track file lifecycle (uploaded, processing, final, deleted)

### Gradio File Handling

- **Input**: Use `gr.File(file_count="multiple")` for video uploads
  - Returns list of file paths (temporary Gradio paths)
  - Copy to working directory immediately for processing
- **Output**: Use `gr.Video()` component
  - Accepts file path (absolute or relative to working directory)
  - Gradio serves the file and provides download capability
  - File must exist at the path when component renders

### Best Practices

1. **Immediate Copy**: Copy uploaded files from Gradio temp to working directory
2. **Absolute Paths**: Use absolute paths for all file operations
3. **Session Management**: Use unique session IDs to isolate user workflows
4. **Cleanup Strategy**:
   - Clean up intermediate files after final video is created
   - Keep final videos for a retention period (e.g., 1 hour)
   - Implement background cleanup task for old files
5. **Error Handling**: Ensure cleanup happens even if processing fails

## Technical Stack

### Dependencies to Add

- `opencv-python` - Video frame extraction and basic processing
- `moviepy` - Video editing, clipping, composition
- `ffmpeg-python` - Alternative/additional video processing
- `numpy` - Array operations for video processing
- `pillow` - Image processing for frame analysis

### Existing Dependencies

- `gradio` (with MCP) - UI and MCP server
- `google-genai` - AI analysis and understanding

## Main Workflow UI Design

The "Vidzly" tab in app.py will include:

1. **Video Upload Section**: Multiple file upload component
2. **Description Input**: Text area for user description
3. **Process Button**: Trigger workflow
4. **Progress Display**: Show current step (analyzing, generating script, selecting scenes, composing, etc.)
5. **Script Preview**: Display generated script (optional, collapsible)
6. **Output Video**: Display final 30-second video
7. **Download Button**: Allow user to download result

## Workflow Sequence

1. User uploads multiple videos
2. User provides description
3. System analyzes all videos (parallel processing)
4. System parses user description
5. System matches scenes to requirements
6. **System generates detailed script for 30-second video**
7. System clips selected scenes based on script
8. System selects appropriate music based on script
9. System composes final video according to script
10. System returns final video and script

## Script Format Example

```json
{
  "total_duration": 30.0,
  "scenes": [
    {
      "scene_id": 1,
      "source_video": "video1.mp4",
      "start_time": 5.2,
      "end_time": 8.5,
      "duration": 3.3,
      "description": "Opening shot of landscape",
      "transition_in": "fade",
      "transition_out": "crossfade"
    },
    {
      "scene_id": 2,
      "source_video": "video2.mp4",
      "start_time": 12.0,
      "end_time": 18.5,
      "duration": 6.5,
      "description": "Action sequence",
      "transition_in": "crossfade",
      "transition_out": "cut"
    }
  ],
  "music": {
    "mood": "energetic",
    "bpm": 120,
    "sync_points": [0.0, 7.5, 15.0, 22.5, 30.0]
  },
  "pacing": "fast",
  "narrative_structure": "hook -> build -> climax -> resolution"
}
```

## Error Handling Strategy

- Validate video file formats on upload
- Handle corrupted or unsupported videos gracefully
- Provide clear error messages for each failure point
- Allow partial success (e.g., if one video fails, continue with others)
- Timeout handling for long processing operations
- Validate script timing (must sum to ~30 seconds)
- Handle script generation failures with fallback

## Performance Considerations

- Process videos in parallel where possible
- Use efficient frame sampling (not every frame)
- Cache video summaries to avoid re-analysis
- Optimize video composition for speed
- Consider async processing for long operations
- Generate script before heavy processing to validate feasibility

## Testing Strategy

- Unit tests for each MCP tool
- Integration tests for workflow steps
- Test script generation with various inputs
- End-to-end test with sample videos
- Test with various video formats and sizes
- Test edge cases (very short videos, very long videos, etc.)
- Test script validation (timing, scene availability)

## Implementation Todos

1. **Phase 1: Foundation**

   - Add video processing dependencies to pyproject.toml
   - Implement video_metadata.py
   - Implement video_summarizer.py
   - Create utils/file_manager.py

2. **Phase 2: Understanding**

   - Implement description_parser.py
   - Implement scene_matcher.py

3. **Phase 3: Script Generation**

   - Implement video_script_generator.py
   - Add script validation logic

4. **Phase 4: Processing**

   - Implement video_clipper.py
   - Implement scene_selector.py

5. **Phase 5: Composition**

   - Implement music_selector.py
   - Implement video_composer.py

6. **Phase 6: Integration**

   - Implement video_workflow.py
   - Create main Vidzly UI in app.py
   - Integrate all MCP tools
   - Add error handling

7. **Phase 7: Polish**
   - Add progress tracking
   - Optimize performance
   - Add preview functionality
   - Improve UX

# Vidzly Workflow Explanation

## Overview

Vidzly is an AI-powered video creation platform that transforms raw video footage into polished, engaging short videos. The system uses a **hybrid approach** combining:
- **Direct tool calls** for reliable, deterministic operations
- **AI agents (ADK)** for intelligent, creative decisions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio Web Interface                      │
│  (app.py) - Two tabs: Vidzly Workflow + MCP Tools          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Workflow UI (workflow_ui.py)                   │
│  - User inputs: videos, description, duration, music flag   │
│  - Real-time progress display                               │
│  - Output: final video, thumbnail, summaries, script         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Agent Workflow (workflow_agent.py)                   │
│  - Orchestrates entire video creation process               │
│  - Uses ADK agents for intelligent operations               │
│  - Falls back to direct tool calls for reliability          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ADK Agents   │  │ Tool Helpers │  │ MCP Tools    │
│ - Script     │  │ - Session    │  │ - Video      │
│   Writer     │  │   Manager    │  │   Summarizer │
│ - Video      │  │ - Result     │  │ - Script     │
│   Editor     │  │   Extractors│  │   Generator  │
│ - Manager    │  │              │  │ - Music      │
└──────────────┘  └──────────────┘  │   Selector   │
                                    │ - Frame      │
                                    │   Extractor  │
                                    │ - Thumbnail  │
                                    │   Generator  │
                                    │ - Video      │
                                    │   Composer   │
                                    └──────────────┘
```

## Complete Workflow Steps

### Phase 0: Initialization

1. **User Access**: User opens Gradio web interface (`app.py`)
2. **Tab Selection**: User navigates to "Vidzly" tab
3. **Input Collection**: User provides:
   - Video files (one or multiple)
   - Optional description (mood, style, vibe)
   - Target duration (default: 30 seconds)
   - Music generation flag (default: enabled)

### Phase 1: Video Analysis & Script Generation

#### Step 1.1: Video Input Processing
```
User uploads videos → workflow_ui.py → agent_workflow()
→ _normalize_video_inputs() → Validates and converts to absolute paths
```

**Implementation**: Direct processing (no agent needed)
- Handles Gradio file format
- Validates file existence
- Converts to absolute paths

#### Step 1.2: Video Summarization
```
For each video:
  video_summarizer(video_path, fps=2.0) → JSON summary
```

**Implementation**: **Direct tool call** (deterministic)
- Uses Google Gemini Vision API
- Extracts frames at specified FPS
- Analyzes content, objects, activities
- Returns JSON with:
  - Summary text
  - Key scenes
  - Detected objects/activities
  - Mood tags
  - Recommended thumbnail timeframe

**Why Direct Call**: Needs specific parameters (FPS), reliable operation

#### Step 1.3: Script Generation
```
Video summaries + User description → script_writer_agent
→ invoke_agent_simple() → ADK session manager
→ Agent reasons about content → video_script_generator tool
→ JSON script with scenes, timings, transitions
```

**Implementation**: **Agent-driven** (intelligent reasoning)
- Agent analyzes video summaries
- Considers user requirements
- Generates composition script with:
  - Scene sequence
  - Timestamps for each scene
  - Transitions (fade, crossfade, cut)
  - Music configuration
  - Pacing and narrative structure

**Fallback**: If agent fails → direct `video_script_generator()` call

**Why Agent**: Requires reasoning about content, user intent, and creative decisions

#### Step 1.4: Music Generation (if enabled)
```
Script JSON + Mood tags → script_writer_agent
→ invoke_agent_simple() → music_selector tool
→ Generated music file (MP3)
```

**Implementation**: **Agent-driven** (intelligent selection)
- Agent analyzes script mood and style
- Matches music to video content
- Generates appropriate background music

**Fallback**: If agent fails → direct `music_selector()` call with extracted mood

**Why Agent**: Requires understanding of mood/style matching

### Phase 2: Thumbnail & Video Composition

#### Step 2.1: Frame Extraction
```
First video + thumbnail_timeframe → frame_extractor()
→ Representative frame image (PNG/JPG)
```

**Implementation**: **Direct tool call** (deterministic)
- Extracts frame at recommended timestamp (from summary)
- Or uses AI to select best frame
- Returns image file path

**Why Direct Call**: Straightforward operation, specific timestamp needed

#### Step 2.2: Thumbnail Generation
```
Frame image + Video summary + Script → video_editor_agent
→ invoke_agent_simple() → thumbnail_generator tool
→ Thumbnail with AI-generated text and stickers
```

**Implementation**: **Agent-driven** (creative decisions)
- Agent analyzes frame and content
- Makes design decisions:
  - Text placement and content
  - Sticker selection
  - Color scheme
  - Layout optimization

**Fallback**: If agent fails → direct `thumbnail_generator()` call

**Why Agent**: Requires creative design decisions

#### Step 2.3: Video Composition
```
Script JSON + Video clips + Music + Thumbnail → video_composer()
→ Final composed video with transitions, music, thumbnail overlay
```

**Implementation**: **Direct tool call** (deterministic)
- Follows script exactly
- Applies transitions
- Mixes audio
- Overlays thumbnail on first frame
- Returns final video file

**Why Direct Call**: Follows script precisely, no reasoning needed

### Phase 3: Output & Display

```
Final video + Thumbnail + Summaries + Script → workflow_ui.py
→ Gradio UI updates → User sees results
```

**Outputs**:
- Final video (MP4)
- Thumbnail image (PNG)
- Video summaries (JSON)
- Generated script (JSON)

## Agent Architecture

### Three Specialized Agents

1. **Script Writer Agent** (`script_writer_agent`)
   - **Tools**: video_summarizer, video_script_generator, music_selector
   - **Purpose**: Analysis, planning, music selection
   - **Used for**: Script generation, music generation

2. **Video Editor Agent** (`video_editor_agent`)
   - **Tools**: frame_extractor, thumbnail_generator, video_composer
   - **Purpose**: Execution, composition, thumbnail creation
   - **Used for**: Thumbnail generation

3. **Manager Agent** (`manager_agent`)
   - **Tools**: All tools
   - **Purpose**: Full orchestration (available for future use)
   - **Status**: Created but not actively used (specialized agents preferred)

### Agent Invocation Flow

```
User Prompt
    ↓
invoke_agent_simple()
    ↓
ADKSessionManager.run_agent_sync()
    ↓
create_invocation_context()
    ↓
Set prompt on context (if supported)
    ↓
agent.run_live(context)
    ↓
Agent reasons and calls tools
    ↓
Extract results from events
    ↓
Return response
```

**Note**: The prompt passing mechanism attempts to set the prompt on the InvocationContext, but ADK's exact message passing API may require adjustment. Fallback mechanisms ensure the workflow continues even if agent invocation has issues.

## Error Handling & Fallbacks

### Robust Fallback Strategy

Every agent-driven operation has a fallback:

1. **Try Agent First**
   ```python
   try:
       agent_response = invoke_agent_simple(agent, prompt)
       result = extract_result(agent_response)
   ```

2. **Fallback on Error**
   ```python
   except Exception as e:
       status += "⚠️ Agent error, using direct tool call..."
       result = direct_tool_call(...)
   ```

3. **Fallback on Invalid Response**
   ```python
   if not result:
       status += "⚠️ Could not extract result, using direct tool call..."
       result = direct_tool_call(...)
   ```

### Benefits

- ✅ **Reliability**: Workflow always completes
- ✅ **Intelligence**: Agents add value when they work
- ✅ **Transparency**: Status updates show what's happening
- ✅ **Graceful Degradation**: Falls back without breaking

## Data Flow

```
Input Videos
    ↓
[Video Summarization] → Video Summaries (JSON)
    ↓
[Script Generation] → Script JSON
    ↓
[Music Generation] → Music File (MP3)
    ↓
[Frame Extraction] → Frame Image (PNG)
    ↓
[Thumbnail Generation] → Thumbnail Image (PNG)
    ↓
[Video Composition] → Final Video (MP4)
    ↓
Output to User
```

## Key Components

### 1. `app.py`
- **Role**: Main Gradio application
- **Features**: 
  - Two tabs: "Vidzly" (workflow) and "MCP Tools" (individual tools)
  - MCP server support for AI agent integration

### 2. `workflow_ui.py`
- **Role**: Workflow-specific UI
- **Features**:
  - Input collection (videos, description, settings)
  - Real-time progress display
  - Output display (video, thumbnail, details)

### 3. `workflow_agent.py`
- **Role**: Core workflow orchestration
- **Features**:
  - Agent creation and management
  - Tool wrapper creation
  - Workflow execution with progress updates
  - Error handling and fallbacks

### 4. `agent_helpers.py`
- **Role**: Agent invocation utilities
- **Features**:
  - `invoke_agent_simple()` - Simplified agent invocation
  - Result extraction functions
  - Text/JSON/file path extraction

### 5. `adk_session_manager.py`
- **Role**: ADK session management
- **Features**:
  - Session creation and management (with app_name, user_id parameters)
  - InvocationContext setup
  - Async agent execution handling
  - Synchronous wrapper for agent invocation

### 6. Tool Functions (`tools/`)
- **Role**: Individual MCP tools
- **Tools**:
  - `video_summarizer.py` - Video analysis
  - `video_script_generator.py` - Script generation
  - `music_selector.py` - Music generation
  - `frame_extractor.py` - Frame extraction
  - `thumbnail_generator.py` - Thumbnail creation
  - `video_composer.py` - Video composition

## Execution Modes

### Mode 1: Agent-Driven (Intelligent)
- **When**: Script generation, music selection, thumbnail creation
- **How**: Agent reasons about content and makes decisions
- **Benefits**: More creative, context-aware results
- **Fallback**: Direct tool calls if agent fails

### Mode 2: Direct Tool Calls (Deterministic)
- **When**: Video summarization, frame extraction, video composition
- **How**: Direct function calls with specific parameters
- **Benefits**: Reliable, predictable, fast
- **No Fallback Needed**: These are the fallbacks

## Progress Tracking

The workflow provides real-time progress updates:

```
Starting workflow...
📥 Processing video inputs...
🎬 Phase 1: Analyzing videos and generating script...
📹 Analyzing video 1/2...
📹 Analyzing video 2/2...
✍️ Generating composition script with AI agent...
🎵 Generating background music with AI agent...
🎨 Phase 2: Creating thumbnail and composing video...
🖼️ Extracting representative frame...
🎨 Generating thumbnail with AI agent...
🎬 Composing final video...
✅ Video creation complete!
```

Each step yields progress updates that update the UI in real-time.

## Example Execution

### Input
- Videos: `video1.mp4`, `video2.mp4`
- Description: "Energetic and fast-paced"
- Duration: 30 seconds
- Music: Enabled

### Execution Flow

1. **Normalize inputs** → `['/path/video1.mp4', '/path/video2.mp4']`

2. **Summarize videos**:
   - Video 1 → `{"summary": "...", "mood_tags": ["energetic"], ...}`
   - Video 2 → `{"summary": "...", "mood_tags": ["dynamic"], ...}`

3. **Generate script** (Agent):
   - Agent analyzes summaries
   - Creates script with scenes from both videos
   - Matches 30-second duration
   - Returns JSON script

4. **Generate music** (Agent):
   - Agent reads script mood
   - Generates energetic music
   - Returns MP3 file path

5. **Extract frame**:
   - Uses recommended timestamp from summary
   - Extracts frame → `frame.png`

6. **Generate thumbnail** (Agent):
   - Agent analyzes frame and content
   - Adds text and stickers
   - Returns `thumbnail.png`

7. **Compose video**:
   - Follows script
   - Combines clips with transitions
   - Adds music
   - Overlays thumbnail
   - Returns `final_video.mp4`

### Output
- Final video: `final_video.mp4`
- Thumbnail: `thumbnail.png`
- Summaries: JSON with both video analyses
- Script: JSON with composition details

## Summary

The Vidzly workflow is a **hybrid intelligent system** that:

1. ✅ **Reliably processes videos** using direct tool calls
2. ✅ **Intelligently creates content** using AI agents
3. ✅ **Gracefully handles errors** with automatic fallbacks
4. ✅ **Provides real-time feedback** through progress updates
5. ✅ **Produces professional results** with minimal user input

The system balances **reliability** (direct calls) with **intelligence** (agents) to create a robust, user-friendly video creation platform.


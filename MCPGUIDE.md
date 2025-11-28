# 🔌 Vidzly MCP Client Configuration Guide

Vidzly exposes all video processing tools as MCP (Model Context Protocol) tools, enabling seamless integration with AI clients like Cursor, Windsurf, Cline, and Claude Desktop. This guide will help you configure Vidzly's MCP server in your preferred AI client.


## 🚀 SSE (Server-Sent Events) Transport

For clients that support SSE transport (e.g., **Cursor**, **Windsurf**, **Cline**), add the following configuration to your MCP settings.

### Hugging Face Spaces Configuration

Add this to your MCP configuration file (typically `~/.cursor/mcp.json` for Cursor or similar location for other clients):

```json
{
  "mcpServers": {
    "vidzly": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp-1st-birthday-vidzly.hf.space/gradio_api/mcp/sse",
        "--transport",
        "sse-only"
      ]
    }
  }
}
```

---

## 📡 STDIO Transport

For clients that only support STDIO transport (e.g., **Claude Desktop**), you'll need to use the `mcp-remote` package to bridge SSE to STDIO.

### Prerequisites

1. Install [Node.js](https://nodejs.org/) (version 14 or higher)
2. Ensure `npx` is available in your PATH

### Hugging Face Spaces Configuration

Add this to your Claude Desktop MCP configuration file (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):


**Example:**
```json
{
  "mcpServers": {
    "vidzly": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp-1st-birthday-vidzly.hf.space/gradio_api/mcp/"
      ]
    }
  }
}
```

### Configuration Steps for Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Open the configuration file in a text editor

3. Add the Vidzly MCP server configuration to the `mcpServers` object

4. Save the file and restart Claude Desktop

5. Verify the connection by checking Claude Desktop's MCP server status

---

## 🛠️ Available MCP Tools

Once configured, the following Vidzly tools will be available to your AI client:

### Video Processing Tools

- **`video_summarizer`** - Analyze video content and generate detailed summaries including key scenes, detected objects, mood tags, and recommended thumbnail timestamps
- **`video_clipper`** - Extract specific segments from videos by specifying start and end times
- **`frame_extractor`** - Extract representative frames from videos, with AI-powered selection or manual timestamp specification
- **`video_composer`** - Combine multiple video clips with transitions (fade, crossfade, cut) and optional background music according to a JSON script
- **`video_script_generator`** - Create detailed video composition scripts with scene sequences, transitions, and timing based on video summaries

### Media Generation Tools

- **`thumbnail_generator`** - Generate engaging thumbnails with AI-generated text and stickers based on video frames and summaries
- **`music_selector`** - Generate background music and sound effects using ElevenLabs API based on mood, style, duration, BPM, and other parameters
- **`text_to_speech`** - Convert text to speech with multiple voices, languages, and speed options
- **`subtitle_creator`** - Add customizable subtitles to videos with JSON transcript format

### Utility Tools

- **`script_generator`** - Generate comprehensive video production scripts from multiple video materials

---

## ✅ Verification

After configuring the MCP server, verify the connection:

1. **Check Server Status**: Most clients will show MCP server status in their settings or status bar
2. **Test Tool Availability**: Ask your AI client to list available MCP tools - you should see all Vidzly tools listed
3. **Try a Simple Command**: Ask your AI to use a Vidzly tool, for example: "Use the video_summarizer tool to analyze a video"

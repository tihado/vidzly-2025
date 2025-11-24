<p align="center">
  <img src="./app.png" alt="Vidzly Logo"/>
</p>

# 🎬 Vidzly - Your AI-Powered Short Video Creator

> **Transform raw footage into viral-ready content in seconds. No skills required. No expensive gear needed. Just your vision and our AI.**

## ✨ What is Vidzly?

Vidzly is an intelligent automation platform that revolutionizes short-form video creation. Whether you're a micro-influencer, content creator, or business owner, Vidzly transforms your raw clips into polished, engaging videos that stop the scroll.

### 🚀 Why Vidzly?

- **Zero Learning Curve**: No video editing skills? No problem. Use our intuitive web interface.
- **AI-Powered Magic**: Advanced AI handles video analysis, cutting, transitions, music generation, and thumbnail creation automatically.
- **Lightning Fast**: What takes hours in traditional editing software takes minutes with Vidzly.
- **Professional Quality**: Get studio-quality results without the studio price tag.
- **MCP Tools Integration**: All tools are available as MCP (Model Context Protocol) tools for AI agent integration.

### 🎯 Perfect For

- 📱 Micro-influencers building their social media presence
- 🎨 Content creators who want to focus on creativity, not editing
- 💼 Small businesses creating marketing content
- 🎓 Educators making engaging educational clips
- 🎪 Anyone who wants to create stunning videos effortlessly

## 🎬 How It Works

1. **Upload Your Raw Footage** - Drop your clips through the Gradio web interface
2. **Describe Your Vision** - Optionally provide a description of the mood, style, or vibe you want
3. **AI Agents Work Their Magic** - Our two-agent system intelligently plans and executes:
   - **Script Writer/Director Agent**: Analyzes videos, creates composition scripts, and generates music
   - **Video Editor Agent**: Executes video composition, extracts frames, and generates thumbnails
4. **Get Your Masterpiece** - Receive a polished video with thumbnail overlay on the first frame

## 🛠️ Available Tools

Vidzly provides a comprehensive suite of MCP tools accessible through a Gradio web interface:

- 🎥 **Video Summarizer**: Uses Google Gemini AI to analyze video content and generate detailed summaries including key scenes, detected objects, mood tags, and recommended thumbnail timestamps
- ✂️ **Video Clipper**: Extract specific segments from videos by specifying start and end times
- 🖼️ **Frame Extractor**: Extract representative frames from videos, with AI-powered selection or manual timestamp specification
- 🎨 **Thumbnail Generator**: Automatically generate engaging thumbnails with AI-generated text and stickers based on video frames and summaries
- 🎬 **Video Composer**: Combine multiple video clips with transitions (fade, crossfade, cut) and optional background music according to a JSON script. Supports optional thumbnail image overlay on the first frame
- 🎵 **Music Selector**: Generate background music and sound effects using ElevenLabs API based on mood, style, duration, BPM, and other parameters

## 🏗️ Architecture

- **Web Interface**: Built with Gradio (with MCP server support)
- **AI Agents**: Google ADK (Agent Development Kit) with two specialized agents:
  - **Script Writer/Director Agent**: Plans video composition using video analysis and script generation
  - **Video Editor Agent**: Executes video composition, frame extraction, and thumbnail generation
- **AI Integration**: Google Gemini for video understanding, analysis, and script generation
- **Audio Generation**: ElevenLabs API for music and sound effect generation
- **Video Processing**: MoviePy for video editing and composition
- **Image Processing**: OpenCV and Pillow for frame extraction and thumbnail generation
- **Testing**: Comprehensive pytest test suite with unit and integration tests

## Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Installing Poetry

If you don't have Poetry installed, you can install it using:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on macOS with Homebrew:

```bash
brew install poetry
```

### Installing Dependencies

Once Poetry is installed, install the project dependencies:

```bash
poetry install
```

This will create a virtual environment and install all dependencies specified in `pyproject.toml`.

### Activating the Virtual Environment

To activate the Poetry virtual environment:

```bash
poetry shell
```

Alternatively, you can run commands within the virtual environment without activating it:

```bash
poetry run <command>
```

### Adding Dependencies

To add a new dependency:

```bash
poetry add <package-name>
```

To add a development dependency:

```bash
poetry add --group dev <package-name>
```

### Removing Dependencies

To remove a dependency:

```bash
poetry remove <package-name>
```

### Updating Dependencies

To update all dependencies to their latest compatible versions:

```bash
poetry update
```

### Code Formatting with Black and Lefthook

This project uses [Black](https://black.readthedocs.io/) for code formatting and [Lefthook](https://github.com/evilmartians/lefthook) for git hooks to automatically format code before commits.

After installing dependencies, set up lefthook:

```bash
poetry run lefthook install
```

This will install git hooks that will:

- **Before commit**: Automatically format staged Python files with Black
- **Before push**: Check that all Python files in `src/` and `tests/` are properly formatted

To manually format code:

```bash
poetry run black src/ tests/
```

To check formatting without making changes:

```bash
poetry run black --check src/ tests/
```

### Setting Up Environment Variables

Create a `.env` file in the root directory and add your environment variables.

```bash
GOOGLE_API_KEY=your_google_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

**Note**: The application requires Google ADK (Agent Development Kit) to be installed. The `google-adk` package is required for the two-agent workflow architecture.

### Running the Application

Start the Gradio web interface:

```bash
poetry run python src/app/app.py
```

This will launch a web interface with:

- **Vidzly Tab**: Project introduction and overview
- **MCP Tools Tab**: Access to all 6 video processing tools

The application runs with MCP server support, allowing AI agents to interact with the tools programmatically.

## Testing

This project includes comprehensive unit and integration tests. See [tests/README.md](tests/README.md) for detailed testing documentation.

### Running Tests

Run all tests:

```bash
poetry run pytest
```

Run with coverage:

```bash
poetry run pytest --cov=src/app/tools --cov-report=html
```

Run specific test file:

```bash
poetry run pytest tests/test_video_summarizer.py
```

### Test Structure

- **Unit Tests**: Mocked tests for input validation, error handling, and logic
- **Integration Tests**: Real video file tests for actual functionality
- All tools have corresponding test files in the `tests/` directory

## Technology Stack

- **Python 3.12+**: Core language
- **Gradio 6.0+**: Web interface with MCP support
- **Google ADK (Agent Development Kit)**: Two-agent architecture for intelligent workflow orchestration
- **Google Gemini API**: Video understanding, analysis, script generation, and thumbnail creation
- **ElevenLabs API**: Music and sound effect generation
- **MoviePy 2.2.1**: Video editing, composition, and image overlay
- **OpenCV 4.12+**: Video processing and frame extraction
- **Pillow 11**: Image processing for thumbnails
- **Poetry**: Dependency management
- **pytest**: Testing framework

### Contributors

- 🐱 [honghanhh](https://github.com/honghanhh) 🐱
- 🦊 [nvti](https://github.com/nvti) 🦊
- 🐻 [Nlag](https://github.com/NLag) 🐻
- 🐰 [DaphneeCh](https://github.com/DaphneeCh) 🐰

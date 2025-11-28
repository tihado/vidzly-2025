# Tests

This directory contains unit tests for the Vidzly tools.

## Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run specific test file
```bash
poetry run pytest tests/test_video_clipper.py
poetry run pytest tests/test_video_summarizer.py
poetry run pytest tests/test_video_composer.py
```

### Run with coverage
```bash
poetry run pytest --cov=src/app/tools --cov-report=html
```

### Run with verbose output
```bash
poetry run pytest -v
```

### Run specific test
```bash
poetry run pytest tests/test_video_clipper.py::TestVideoClipper::test_video_clipper_with_string_path
```

## Test Structure

- `conftest.py`: Shared pytest fixtures and configuration
- `test_video_clipper.py`: Unit tests and integration tests for the video_clipper tool
- `test_video_summarizer.py`: Unit tests and integration tests for the video_summarizer tool
- `test_video_composer.py`: Unit tests and integration tests for the video_composer tool
- `data/dodo.MOV`: Real video file used for integration tests
- `data/dodo_2.mov`: Additional real video file used for integration tests

## Test Coverage

### Unit Tests (Mocked)
The unit tests use mocking to avoid requiring actual video files or API keys:
- **video_clipper**: Tests input validation, file handling, time range validation, and error handling
- **video_summarizer**: Tests input validation, API integration (mocked), metadata extraction, and mood tag detection
- **video_composer**: Tests script validation, source_video reference resolution (index/filename), error handling, and scene validation

### Integration Tests (Real Video)
The integration tests use the real video files from `tests/data/`:
- **video_clipper**: Tests actual video clipping functionality with real video file
- **video_summarizer**: Tests actual video analysis with real video file (works with or without API key)
- **video_composer**: Tests actual video composition with real video files, including:
  - Basic composition with multiple scenes from the same video
  - Crossfade transitions
  - Multiple source videos
  - Three scenes from two different source videos
  - Pre-clipped video composition

## Notes

- **Unit tests** use `unittest.mock` to mock external dependencies (MoviePy, OpenCV, Google Gemini API)
- **Integration tests** use the real video files in `tests/data/` to test actual functionality
- Temporary files are created and cleaned up automatically via pytest fixtures
- Integration tests verify that the tools work correctly with real video files
- The video_summarizer integration test with API key is skipped if `GOOGLE_API_KEY` is not set
- **video_composer** requires `video_clips` parameter (list of source videos) and uses `source_video` in scenes to reference videos by index (0-based) or filename


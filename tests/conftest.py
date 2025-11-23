"""
Pytest configuration and shared fixtures for tests.
"""
import os
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def temp_video_file():
    """Create a temporary video file for testing."""
    # Create a minimal test video file
    # Note: In real tests, you might want to use an actual small video file
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "test_video.mp4")
    
    # Create an empty file (in real scenario, this would be a valid video)
    # For actual testing, you'd want to use a real small video file
    Path(video_path).touch()
    
    yield video_path
    
    # Cleanup
    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_video_duration():
    """Mock video duration in seconds."""
    return 30.0


@pytest.fixture
def sample_video_metadata():
    """Sample video metadata for testing."""
    return {
        "duration": 30.0,
        "resolution": "1920x1080",
        "fps": 30.0,
        "frame_count": 900,
    }


@pytest.fixture
def real_video_file():
    """Get path to real video file in tests/data directory."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(test_dir, "data", "dodo.MOV")
    
    if not os.path.exists(video_path):
        pytest.skip(f"Test video file not found: {video_path}")
    
    return video_path


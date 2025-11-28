# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# FFmpeg is required for video processing (MoviePy, OpenCV)
# Build tools are needed for some Python packages
# curl is needed for Poetry installation
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
# Using the official installer and configuring it to not create a virtual environment
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies using Poetry
# Only install production dependencies (exclude dev dependencies)
RUN poetry install --no-interaction --no-ansi --without dev

# Copy application code
COPY src/ ./src/

# Set environment variables
# Note: These should be provided at runtime via docker run -e or docker-compose
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Expose Gradio default port
EXPOSE 7860

# Run the application using Poetry
CMD ["poetry", "run", "python", "src/app/app.py"]


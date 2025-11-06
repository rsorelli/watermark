# Use official Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/main.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    PYTHONPATH=/app/src

# Create a non-root user
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app/src/watermark/static/output /app/src/watermark/static/zips && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy setup files first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt setup.py ./

# Copy the application code
COPY --chown=appuser:appuser src ./src

# Install dependencies and the application
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Switch to non-root user
USER appuser

# Create required directories with proper permissions
RUN chmod 755 /app/src/watermark/static/output /app/src/watermark/static/zips

# Expose the Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Start the Flask app
CMD ["python", "src/main.py"]

# Build stage
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy setup files first to leverage Docker cache
COPY requirements.txt setup.py ./

# Copy the application code
COPY src ./src

# Install dependencies and the application
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Runtime stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/main.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    PYTHONPATH=/app/src

# Install only runtime dependencies (no build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    libfreetype6 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user
RUN useradd -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser setup.py ./

# Create required directories with proper permissions as appuser
RUN mkdir -p /app/src/watermark/static/output /app/src/watermark/static/zips && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/src/watermark/static/output /app/src/watermark/static/zips

# Switch to non-root user
USER appuser

# Expose the Flask port
EXPOSE 5000

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/', timeout=5)" || exit 1

# Start the Flask app
CMD ["python", "src/main.py"]

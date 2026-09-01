# Base image with Python
FROM python:3.11-slim

# Install ffmpeg (needed for audio conversion and video merging) and
# build tools (needed so pip can build curl_cffi if a prebuilt wheel
# isn't available for this platform)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the app
COPY . .

# Render provides the PORT env var; default to 5000 for local testing
ENV PORT=5000
EXPOSE 5000

# Use gunicorn in production instead of Flask's dev server
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 app:app

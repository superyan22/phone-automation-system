# backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    android-tools-adb \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Note: scrcpy is optional and not available in Debian repos
# Install via pip if needed: pip install scrcpy

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

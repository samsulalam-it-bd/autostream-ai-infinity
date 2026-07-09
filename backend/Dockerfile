FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy and make startup script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create tmp video directory
RUN mkdir -p /tmp/videos

EXPOSE 8000

# Default: run only API (override with start.sh for all-in-one)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

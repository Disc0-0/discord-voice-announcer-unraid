FROM python:3.11-slim

# Install system dependencies and Docker CLI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        lsb-release \
        ca-certificates && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create docker group with placeholder GID (will be overridden at runtime)
RUN groupadd -g 999 docker

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directory with proper permissions
RUN mkdir -p /app/data && \
    chmod -R 777 /app/data

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DATA_DIR=/app/data
ENV BOT_CONTAINER_NAME=discord-voice-announcer
ENV PORT=5000
ENV FLASK_SECRET_KEY=change-me-in-production

# Expose port
EXPOSE 5000

# Volume for persistent data
VOLUME ["/app/data"]

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]


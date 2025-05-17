FROM python:3.11-slim

LABEL maintainer="Discord Voice Announcer Bot <https://github.com/Disc0-0/discord-voice-announcer>"
LABEL description="Discord bot that announces users joining/leaving voice channels using TTS"

# Set working directory
WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY commands.txt .
COPY README.md .

# Create and set permissions for data directory
RUN mkdir -p /app/data && \
    chmod -R 777 /app/data

# Default environment variables
ENV DISCORD_TOKEN=""
ENV VOICE_LANGUAGE="en"
ENV COMMAND_PREFIX="!"
ENV ANNOUNCE_JOINS="True"
ENV ANNOUNCE_LEAVES="True"
ENV WHITELIST_MODE="False"
ENV TZ="UTC"
ENV PUID="99"
ENV PGID="100"

# Volume for persistent data
VOLUME ["/app/data"]

# Create a script to adjust permissions and run the bot
RUN echo '#!/bin/bash\n\
# Create symlinks for data files if they don't exist in volume\n\
[ ! -f /app/data/custom_announcements.json ] && touch /app/data/custom_announcements.json\n\
[ ! -f /app/data/announcement_whitelist.json ] && touch /app/data/announcement_whitelist.json\n\
\n\
# Create .env file from environment variables\n\
echo "DISCORD_TOKEN=$DISCORD_TOKEN" > /app/.env\n\
echo "VOICE_LANGUAGE=$VOICE_LANGUAGE" >> /app/.env\n\
echo "COMMAND_PREFIX=$COMMAND_PREFIX" >> /app/.env\n\
echo "ANNOUNCE_JOINS=$ANNOUNCE_JOINS" >> /app/.env\n\
echo "ANNOUNCE_LEAVES=$ANNOUNCE_LEAVES" >> /app/.env\n\
echo "WHITELIST_MODE=$WHITELIST_MODE" >> /app/.env\n\
\n\
# Set data directory path in main.py\n\
sed -i "s|CUSTOM_ANNOUNCEMENTS_FILE = \"custom_announcements.json\"|CUSTOM_ANNOUNCEMENTS_FILE = \"/app/data/custom_announcements.json\"|g" /app/main.py\n\
sed -i "s|WHITELIST_FILE = \"announcement_whitelist.json\"|WHITELIST_FILE = \"/app/data/announcement_whitelist.json\"|g" /app/main.py\n\
\n\
# Run the bot\n\
exec python /app/main.py\n' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]


# syntax=docker/dockerfile:1
# Discord Voice Announcer Bot Dockerfile
# Optimized for security, performance, and maintainability

# ======== BUILD STAGE ========
FROM python:3.11.7-slim AS builder

# Set build-time environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ======== RUNTIME STAGE ========
FROM python:3.11.7-slim AS runtime

# Define ARGs with defaults for build-time configuration
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0
# Define default UID/GID but allow overriding at build time
ARG PUID=99
ARG PGID=100

# Set runtime environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONMALLOC=malloc \
    PYTHONHASHSEED=random \
    # Default configuration values (non-sensitive)
    VOICE_LANGUAGE="en" \
    COMMAND_PREFIX="!" \
    ANNOUNCE_JOINS="True" \
    ANNOUNCE_LEAVES="True" \
    WHITELIST_MODE="False" \
    TZ="Europe/Oslo" \
    # Memory limit can be overridden at runtime
    MEMORY_LIMIT="256m"

# Enhanced container metadata labels
LABEL maintainer="Discord Voice Announcer Bot <https://github.com/Disc0-0/discord-voice-announcer>" \
      description="Discord bot that announces users joining/leaving voice channels using TTS" \
      org.opencontainers.image.title="Discord Voice Announcer Bot" \
      org.opencontainers.image.description="Discord bot that announces users joining/leaving voice channels" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.url="https://github.com/Disc0-0/discord-voice-announcer" \
      org.opencontainers.image.documentation="https://github.com/Disc0-0/discord-voice-announcer/README.md" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="Discord Voice Announcer Contributors" \
      security.privileged="false" \
      com.docker.extension.publisher-url="https://github.com/Disc0-0/discord-voice-announcer"

# Set working directory
WORKDIR /app

# Install runtime dependencies and configure user/group
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    tzdata \
    curl \
    procps \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Create data directory
    && mkdir -p /app/data \
    # Create user and group with robust error handling
    && (grep -q ":${PGID}:" /etc/group || groupadd -g ${PGID} discordbot || groupadd discordbot) \
    && (grep -q ":${PUID}:" /etc/passwd || useradd -u ${PUID} -g $(getent group ${PGID} | cut -d: -f1) -d /app -s /bin/bash discordbot || useradd -g $(getent group ${PGID} | cut -d: -f1) -d /app -s /bin/bash discordbot) \
    # Set proper permissions
    && chown -R $(id -u discordbot):$(id -g discordbot) /app

# Copy application files
COPY --from=builder /root/.local /usr/local
COPY main.py commands.txt README.md /app/
COPY entrypoint.sh /app/entrypoint.sh

# Set proper permissions
RUN chmod +x /app/entrypoint.sh && \
    chown -R $(id -u discordbot):$(id -g discordbot) /app

# Volume for persistent data
VOLUME ["/app/data"]

# Add healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
    CMD curl --fail http://localhost:8080/health || exit 1

# Switch to non-root user
USER discordbot

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]


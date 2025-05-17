#!/bin/bash

# Setup script for Discord Voice Announcer with Web Interface

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Discord Voice Announcer with Web Interface...${NC}"

# Create data directory if it doesn't exist
mkdir -p ./data
echo -e "${GREEN}Created data directory${NC}"

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo -e "${YELLOW}Created .env file from example. Please edit it to add your Discord bot token.${NC}"
  else
    echo -e "${RED}Error: .env.example file not found. Please create a .env file manually.${NC}"
    exit 1
  fi
fi

# Get Docker group ID for permissions
DOCKER_GID=$(getent group docker | cut -d: -f3)
if [ -z "$DOCKER_GID" ]; then
  echo -e "${YELLOW}Could not detect Docker group ID. Using default value of 999.${NC}"
  DOCKER_GID=999
else
  echo -e "${GREEN}Detected Docker group ID: ${DOCKER_GID}${NC}"
  # Add Docker GID to .env file if not already present
  if ! grep -q "DOCKER_GID=" .env; then
    echo -e "\n# Docker GID for web interface permissions\nDOCKER_GID=${DOCKER_GID}" >> .env
    echo -e "${GREEN}Added DOCKER_GID to .env file${NC}"
  else
    # Update existing DOCKER_GID value
    sed -i "s/DOCKER_GID=.*/DOCKER_GID=${DOCKER_GID}/" .env
    echo -e "${GREEN}Updated DOCKER_GID in .env file${NC}"
  fi
fi

# Prompt to edit .env file
echo -e "${YELLOW}Please make sure to edit your .env file to add your Discord bot token.${NC}"
read -p "Do you want to edit the .env file now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  if command -v nano > /dev/null; then
    nano .env
  elif command -v vim > /dev/null; then
    vim .env
  else
    echo -e "${YELLOW}No editor found. Please edit the .env file manually.${NC}"
  fi
fi

# Start containers
echo -e "${GREEN}Starting containers...${NC}"
docker-compose up -d

# Show status
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}Discord Voice Announcer bot and Web Interface should now be running.${NC}"
echo -e "${GREEN}Access the web interface at http://localhost:5000${NC}"
echo -e "${YELLOW}If you experience any issues, check the logs with: docker-compose logs${NC}"


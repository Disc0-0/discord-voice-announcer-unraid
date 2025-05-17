# Discord Voice Announcer with Web Interface

This project provides a Discord bot that announces users joining and leaving voice channels using text-to-speech (TTS), along with a web interface for easy management.

## Features

- **Voice Announcements**: Announces when users join or leave voice channels
- **Custom Announcements**: Configure custom messages for specific users
- **Whitelist Mode**: Option to only announce specific users
- **Multiple Language Support**: TTS in various languages
- **Web Interface**: Easy-to-use web dashboard for configuration
- **Docker Integration**: Simple deployment with Docker

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- A Discord bot token ([Create a Discord Bot](https://discord.com/developers/applications))

### Installation

#### Windows

1. Clone this repository
2. Run the PowerShell setup script:
   ```powershell
   .\install.ps1
   ```
3. Enter your Discord bot token when prompted

#### Linux/macOS

1. Clone this repository
2. Run the bash setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. Enter your Discord bot token when prompted

### Manual Setup

1. Copy `.env.example` to `.env`
2. Edit `.env` and add your Discord bot token
3. Create the data directory:
   ```bash
   mkdir -p data
   ```
4. Run the containers:
   ```bash
   docker-compose up -d
   ```

## Accessing the Web Interface

Once the containers are running, you can access the web interface at:
```
http://localhost:5000
```

From here, you can:
- Configure environment variables
- Manage custom announcements
- Set up the whitelist
- Restart the bot when needed

## Configuration Options

The following environment variables can be configured in the `.env` file or through the web interface:

| Variable | Description | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | Your Discord bot token | (Required) |
| `VOICE_LANGUAGE` | Language for TTS announcements | `en` |
| `COMMAND_PREFIX` | Prefix for bot commands | `!` |
| `ANNOUNCE_JOINS` | Whether to announce users joining | `True` |
| `ANNOUNCE_LEAVES` | Whether to announce users leaving | `True` |
| `WHITELIST_MODE` | Whether to only announce whitelisted users | `False` |
| `TZ` | Timezone | `UTC` |

## Bot Commands

The bot supports the following Discord commands:

- `!announce [name]` - Test the announcement system
- `!status` - Show bot status and configuration
- `!togglejoins` - Toggle join announcements on/off
- `!toggleleaves` - Toggle leave announcements on/off
- `!togglewhitelist` - Toggle whitelist mode on/off
- `!whitelist add @user` - Add a user to the whitelist
- `!whitelist remove @user` - Remove a user from the whitelist
- `!whitelist list` - List all users in the whitelist
- `!addcustom @user join/leave [message]` - Add a custom message for a user
- `!removecustom @user join/leave/both` - Remove custom message(s) for a user
- `!listcustom` - List all custom announcements

## Support

For issues or questions, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Discord Voice Announcer Bot for Unraid

[![Unraid Template](https://img.shields.io/badge/Unraid-Template-green)](https://github.com/Disc0-0/discord-voice-announcer-unraid/blob/main/discord-voice-announcer.xml)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://github.com/Disc0-0/discord-voice-announcer-unraid/blob/main/Dockerfile)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289DA)](https://discord.com/developers/applications)

A Discord bot that announces users joining and leaving voice channels using Text-to-Speech (TTS) technology, optimized for deployment on Unraid servers.

## Features

- 🎙️ Voice channel join announcements using TTS
- 🎭 Voice channel join and leave announcements with toggle options
- 🎯 Custom announcements for specific users
- 📋 Whitelist mode to announce only specific users
- 🤖 Automatic voice channel connection management
- 🔊 Clear audio announcements using Google Text-to-Speech
- ⚙️ Configurable language and command prefix
- 🔍 Status command to monitor bot activity

## Unraid Installation Quick Start

### Prerequisites
- Unraid server with Docker enabled
- Discord bot token ([How to get one](#creating-a-discord-bot))
- Community Applications plugin (optional but recommende## Detailed Unraid Installation

### Installation via Community Applications

The easiest way to install on Unraid is through Community Applications:

1. Make sure you have the Community Applications plugin installed on your Unraid server
2. Search for "Discord Voice Announcer" in the Apps tab
3. Click "Install"
4. Configure the container:
   - Enter your Discord bot token
   - Set your timezone
   - Adjust any other optional parameters
5. Click "Apply" to create and start the container

### Manual Docker Installation

If you prefer to set up the container manually:

1. Navigate to the Docker tab in your Unraid web interface
2. Click "Add Container"
3. Configure the container with these settings:
   - **Repository**: `disc0/discord-voice-announcer`
   - **Name**: `discord-voice-announcer`
   - Add the following **Path**:
     - **Config Type**: Path
     - **Name**: Data
     - **Container Path**: `/app/data`
     - **Host Path**: `/mnt/user/appdata/discord-voice-announcer`
   - Add the following **Variable**:
     - **Config Type**: Variable
     - **Name**: DISCORD_TOKEN
     - **Key**: DISCORD_TOKEN  
     - **Value**: `your_discord_bot_token`
     - **Description**### Creating a Discord Bot
 additional environment variables as needed (see Configuration Options section)
4. Click "Apply" to create and start the container

### Docker Compose Installation

Alternatively, you can use Docker Compose by creating a `docker-compose.yml` file with:

```yaml
version: '3'

services:
  discord-voice-announcer:
    image: disc0/discord-voice-announcer:latest
    container_name: discord-voice-announcer
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=your_discord_bot_token_here
      - TZ=Europe/London
      - VOICE_LANGUAGE=en
      - COMMAND_PREFIX=!
      - ANNOUNCE_JOINS=True
      - ANNOUNCE_LEAVES=True
      - WHITELIST_MODE=False
    volumes:
      - /mnt/user/appdata/discord-voice-announcer:/app/data
```

And then run:
```bash
docker-compose up -d
```

### Unraid-Specific Notes

- The bot's data will be stored in `/mnt/user/appdata/discord-voice-announcer` on your Unraid server
- Custom announcements and whitelist configurations will persist across container restarts and updates
- The container logs can be viewed from the Docker tab by clicking on the container name
- For troubleshooting, view the logs with either:
  - The Unraid web interface (Docker tab > Container Logs)
  - The terminal command `docker logs discord-voice-announcer`

## Creating a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click "New Application" and give it a name.
3. Navigate to the "Bot" tab and click "Add Bot".
4. Under the "Privileged Gateway Intents" section, enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Save your changes.
6. Under the "TOKEN" section, click "Copy" to copy your bot's token.
   - **IMPORTANT**: Keep this token secret! It's like a password for your bot.

### Inviting the Bot to Your Server

1. In the Developer Portal, go to the "OAuth2" > "URL Generator" tab.
2. Under "Scopes", select "bot".
3. Under "Bot Permissions", select:
   - View Channels
   - Send Messages
   - Connect
   - Speak
4. Copy the generated URL and open it in your browser.
5. Select your server and authorize the bot.

## Traditional Installation (Non-Docker)

If you prefer to run the bot without Docker, follow these steps:

### 1. Install FFmpeg

#### Windows:
1. Download the FFmpeg build from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager like Chocolatey.
2. Add FFmpeg to your system PATH.
3. Verify the installation by running `ffmpeg -version` in your terminal.

#### Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

### 2. Configure and Run the Bot

1. Clone this repository:
   ```
   git clone https://github.com/Disc0-0/discord-voice-announcer-unraid.git
   cd discord-voice-announcer-unraid
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\Activate.ps1` (PowerShell) or `.\venv\Scripts\activate.bat` (Command Prompt)
   - Linux/macOS: `source venv/bin/activate`

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   VOICE_LANGUAGE=en
   COMMAND_PREFIX=!
   ANNOUNCE_JOINS=True
   ANNOUNCE_LEAVES=True
   WHITELIST_MODE=False
   ```

6. Start the bot:
   ```
   python main.py
   ```

## Usage

Once the bot is running and has joined your server, it will automatically join voice channels when someone enters and announce their arrival.

### Commands

The bot responds to the following commands:

- `!announce [message]` - Test the announcement system with an optional custom message
- `!status` - Display information about the bot's current status and configuration
- `!togglejoins` - Toggle whether the bot announces when users join voice channels
- `!toggleleaves` - Toggle whether the bot announces when users leave voice channels
- `!togglewhitelist` - Toggle between announcing all users or only whitelisted users
- `!whitelist add @user` - Add a user to the announcement whitelist
- `!whitelist remove @user` - Remove a user from the announcement whitelist
- `!whitelist list` - List all users in the announcement whitelist
- `!addcustom @user join|leave message` - Add a custom announcement message for a specific user
- `!removecustom @user join|leave|both` - Remove custom announcement message(s) for a specific user
- `!listcustom` - List all custom announcement messages

## Configuration Options

You can modify the following options in the `.env` file:

```
# Your Discord bot token (required)
DISCORD_TOKEN=your_discord_bot_token_here

# Language for TTS announcements (default: en)
VOICE_LANGUAGE=en

# Command prefix (default: !)
COMMAND_PREFIX=!

# Whether to announce when users join channels (default: True)
ANNOUNCE_JOINS=True

# Whether to announce when users leave channels (default: True)
ANNOUNCE_LEAVES=True

# Whether to only announce whitelisted users (default: False)
WHITELIST_MODE=False
```

## Custom Announcements

The bot supports custom personalized announcements for specific users. This feature allows you to set unique messages that play when certain users join or leave voice channels.

### Setting Up Custom Announcements

Custom announcements are stored in the `custom_announcements.json` file, but the recommended way to manage them is through bot commands.

#### Adding Custom Announcements

To add a custom announcement for a user:

```
!addcustom @Username join The legendary {username} has arrived!
```

Or for leave announcements:

```
!addcustom @Username leave {username} has vanished into thin air!
```

The `{username}` placeholder will be replaced with the user's display name.

#### Removing Custom Announcements

To remove custom announcements for a user:

```
!removecustom @Username join    # Remove just the join message
!removecustom @Username leave   # Remove just the leave message
!removecustom @Username both    # Remove both join and leave messages
```

#### Viewing Custom Announcements

To see all custom announcements:

```
!listcustom
```

### Example Use Cases

- Special announcements for administrators
- Fun custom messages for friends
- Themed announcements for special events
- Different styles for different channels or games

### Notes on Custom Announcements

- Custom announcements require administrator permissions to manage
- The `custom_announcements.json` file updates automatically
- You can use the same `{username}` placeholder multiple times in a message

## Whitelist Mode

The bot supports a whitelist mode that allows you to specify exactly which users should trigger voice announcements. When enabled, only users in the whitelist will generate join/leave announcements.

### Setting Up Whitelist Mode

Whitelist settings are stored in the `announcement_whitelist.json` file, but the recommended way to manage the whitelist is through bot commands.

#### Enabling/Disabling Whitelist Mode

To toggle whitelist mode on or off:

```
!togglewhitelist
```

When enabled, only users in the whitelist will trigger announcements. When disabled, all users will trigger announcements as usual (subject to the join/leave announcement toggles).

#### Managing the Whitelist

To add a user to the whitelist:

```
!whitelist add @Username
```

To remove a user from the whitelist:

```
!whitelist remove @Username
```

To see all users in the whitelist:

```
!whitelist list
```

### Using Whitelist Mode with Custom Announcements

Whitelist mode and custom announcements can be used together. When both are enabled:

1. Only whitelisted users will trigger announcements
2. If a whitelisted user also has a custom announcement, their custom message will be used
3. If a user is not in the whitelist, they won't trigger any announcements even if they have custom messages

### Example Use Cases

- Announce only for specific team members or administrators
- Limit announcements to main players in a gaming channel
- Reduce announcement frequency in busy servers
- Prevent announcement spam from users who frequently join/leave

### Notes on Whitelist Mode

- Requires administrator permissions to manage
- The whitelist is saved between bot restarts
- You can combine whitelist mode with custom announcements for maximum flexibility
- When whitelist mode is enabled but your whitelist is empty, no announcements will be made

## Troubleshooting

### Unraid/Docker Troubleshooting
- **Container keeps restarting**: Check the logs for error messages, particularly related to the Discord token
- **TTS not working**: The container includes FFmpeg, no additional installation is needed
- **Data not persisting**: Check the volume mapping and permissions on your host path
- **Invalid token error**: Verify your token in the container environment variables
- **Cannot find whitelist/custom announcements**: Ensure the data volume is properly mounted
- **Permission issues**: Try adjusting the PUID/PGID environment variables to match your Unraid user

### General Troubleshooting
- **Bot not connecting to voice channels**: Ensure FFmpeg is properly installed (only for non-Docker installations)
- **No sound playing**: Check that your bot has the "Speak" permission in your Discord server
- **Bot disconnecting immediately**: This may happen if the voice channel is empty or if there are connection issues

## Support and Links

- [GitHub Repository](https://github.com/Disc0-0/discord-voice-announcer-unraid)
- [Original Discord Voice Announcer Bot](https://github.com/Disc0-0/discord-voice-announcer)

## Web Interface

The Discord Voice Announcer now includes a web interface for easy management of your bot settings. This provides a user-friendly way to configure the bot without using Discord commands.

### Web Interface Features

- **Environment Configuration**: Edit bot settings like language, command prefix, etc.
- **Custom Announcements Management**: Add, edit, and remove custom announcements
- **Whitelist Control**: Manage the whitelist of users in a simple interface
- **Bot Controls**: Restart the bot when needed directly from the interface

### Accessing the Web Interface

Once running, the web interface is available at:
```
http://your-server-ip:5000
```

### Setting Up the Web Interface

The web interface is included in the docker-compose setup and will automatically be deployed when you follow the installation instructions above.

For manual configuration, the web interface requires:
1. Proper volume mapping to access the same data as the bot
2. Access to the Docker socket to control the bot container
3. Network connectivity to the bot container

The `docker-compose.yml` file includes all necessary configuration for the web interface to work properly.

## Quick Setup Guide

1. Clone this repository to your server
2. Edit the `.env` file and change the following:
   - Replace `your_discord_bot_token_here` with your Discord bot token
   - (Optional) Change the timezone (TZ) to match your location
3. Run `docker-compose up -d` to start both containers
4. Access the web interface at `http://your-server-ip:5000`

## Security Considerations

- The web interface uses a random secret key for sessions
- For additional security, consider:
  - Running behind a reverse proxy with authentication
  - Using a firewall to restrict access to port 5000
  - Using a VPN when accessing the interface remotely


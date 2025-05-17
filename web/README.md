# Discord Voice Announcer Web Interface

This web interface allows you to manage the Discord Voice Announcer bot settings through a user-friendly dashboard.

## Features

- Manage environment variables (Discord token, language, etc.)
- Configure custom announcements for specific users
- Manage the user whitelist
- Toggle features on/off

## Setup and Installation

### Using Docker Compose (Recommended)

The easiest way to run both the bot and the web interface is using the provided docker-compose.yml file:

1. Make sure you have Docker and Docker Compose installed.
2. Clone this repository.
3. Edit the `.env` file or set your Discord bot token in the docker-compose.yml.
4. Run:

```bash
docker-compose up -d
```

This will start both the Discord bot and the web interface.

### Accessing the Web Interface

Once running, you can access the web interface at:

```
http://your-server-ip:5000
```

## Environment Variables

The web interface accepts the following environment variables:

- `FLASK_ENV`: The Flask environment (production, development)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (important for security)
- `DATA_DIR`: Directory where the bot's data is stored (should match the bot's volume)
- `BOT_CONTAINER_NAME`: Name of the Discord bot container
- `PORT`: Port to run the web interface on (default: 5000)

## Security Considerations

- The web interface has no authentication by default. It is recommended to:
  - Change the default `FLASK_SECRET_KEY`
  - Run behind a reverse proxy with authentication (e.g., Nginx, Traefik)
  - Or limit access to your local network only

## Development

If you want to contribute or modify the web interface:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
flask run --debug
```

## License

This project is licensed under the same terms as the Discord Voice Announcer bot.


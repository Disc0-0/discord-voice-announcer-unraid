import os
import json
import logging
import docker
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voice_announcer_web')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'discord-voice-announcer-secret')

# Configuration constants
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
CUSTOM_ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, 'custom_announcements.json')
WHITELIST_FILE = os.path.join(DATA_DIR, 'announcement_whitelist.json')
BOT_CONTAINER_NAME = os.getenv('BOT_CONTAINER_NAME', 'discord-voice-announcer')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Create Docker client
try:
    docker_client = docker.from_env()
    logger.info("Docker client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Docker client: {e}")
    docker_client = None

# Helper functions
def load_json_file(file_path, default_value=None):
    """Load a JSON file or return a default value if it doesn't exist."""
    if default_value is None:
        default_value = {}
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"File not found: {file_path}, using default value")
            # Create the file with default value
            with open(file_path, 'w') as f:
                json.dump(default_value, f, indent=4)
            return default_value
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return default_value

def save_json_file(file_path, data):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")
        return False

def get_bot_env_vars():
    """Get environment variables from the bot container."""
    if docker_client is None:
        return {
            "DISCORD_TOKEN": "Not available - Docker client not initialized",
            "VOICE_LANGUAGE": "en",
            "COMMAND_PREFIX": "!",
            "ANNOUNCE_JOINS": "True",
            "ANNOUNCE_LEAVES": "True",
            "WHITELIST_MODE": "False",
            "TZ": "UTC"
        }
    
    try:
        container = docker_client.containers.get(BOT_CONTAINER_NAME)
        env_vars = {}
        
        # Get all environment variables from the container
        inspect_result = container.attrs['Config']['Env']
        for env_var in inspect_result:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                if key in ['DISCORD_TOKEN', 'VOICE_LANGUAGE', 'COMMAND_PREFIX', 
                          'ANNOUNCE_JOINS', 'ANNOUNCE_LEAVES', 'WHITELIST_MODE', 'TZ']:
                    env_vars[key] = value
        
        # Fill in missing variables with defaults
        defaults = {
            "VOICE_LANGUAGE": "en",
            "COMMAND_PREFIX": "!",
            "ANNOUNCE_JOINS": "True",
            "ANNOUNCE_LEAVES": "True",
            "WHITELIST_MODE": "False",
            "TZ": "UTC"
        }
        
        for key, default_value in defaults.items():
            if key not in env_vars:
                env_vars[key] = default_value
        
        return env_vars
    except Exception as e:
        logger.error(f"Error getting environment variables: {e}")
        return {
            "DISCORD_TOKEN": "Error retrieving token",
            "VOICE_LANGUAGE": "en",
            "COMMAND_PREFIX": "!",
            "ANNOUNCE_JOINS": "True",
            "ANNOUNCE_LEAVES": "True",
            "WHITELIST_MODE": "False",
            "TZ": "UTC"
        }

def update_bot_env_vars(env_vars):
    """Update environment variables in the bot container."""
    if docker_client is None:
        logger.error("Cannot update environment variables - Docker client not initialized")
        return False
    
    try:
        container = docker_client.containers.get(BOT_CONTAINER_NAME)
        
        # Need to stop and remove the container, then create a new one with updated environment
        # Since Docker doesn't allow direct env var updates while a container is running
        logger.info(f"Stopping container {BOT_CONTAINER_NAME} to update environment variables")
        container.stop()
        
        # Get the current container configuration
        config = container.attrs
        
        # Create environment list for the new container
        env_list = []
        for key, value in env_vars.items():
            env_list.append(f"{key}={value}")
        
        # Remove the container but keep the volumes
        container.remove()
        
        # Create a new container with the same configuration but updated environment variables
        image = config['Config']['Image']
        volumes = {m['Source']: {'bind': m['Destination'], 'mode': m['Mode']} 
                  for m in config['Mounts']}
        restart_policy = config['HostConfig']['RestartPolicy']['Name']
        
        new_container = docker_client.containers.create(
            image=image,
            name=BOT_CONTAINER_NAME,
            environment=env_list,
            volumes=volumes,
            restart_policy={"Name": restart_policy}
        )
        
        # Start the new container
        new_container.start()
        logger.info(f"Container {BOT_CONTAINER_NAME} restarted with updated environment variables")
        return True
    except Exception as e:
        logger.error(f"Error updating environment variables: {e}")
        return False

def restart_bot_container():
    """Restart the bot container."""
    if docker_client is None:
        logger.error("Cannot restart container - Docker client not initialized")
        return False
    
    try:
        container = docker_client.containers.get(BOT_CONTAINER_NAME)
        container.restart()
        logger.info(f"Container {BOT_CONTAINER_NAME} restarted")
        return True
    except Exception as e:
        logger.error(f"Error restarting container: {e}")
        return False

# Routes
@app.route('/')
def home():
    """Home page with links to other sections."""
    return render_template('home.html')

@app.route('/env', methods=['GET', 'POST'])
def environment_variables():
    """Page to view and edit environment variables."""
    if request.method == 'POST':
        # Get current environment variables
        current_env = get_bot_env_vars()
        
        # Update with form data
        new_env = {}
        for key in ['DISCORD_TOKEN', 'VOICE_LANGUAGE', 'COMMAND_PREFIX', 
                   'ANNOUNCE_JOINS', 'ANNOUNCE_LEAVES', 'WHITELIST_MODE', 'TZ']:
            if key == 'DISCORD_TOKEN' and not request.form.get(key):
                # Don't update token if empty
                new_env[key] = current_env[key]
            else:
                new_env[key] = request.form.get(key, current_env.get(key, ''))
        
        # Update container environment variables
        if update_bot_env_vars(new_env):
            flash('Environment variables updated successfully!', 'success')
        else:
            flash('Failed to update environment variables.', 'danger')
        
        return redirect(url_for('environment_variables'))
    
    # GET request
    env_vars = get_bot_env_vars()
    return render_template('env_vars.html', env_vars=env_vars)

@app.route('/custom_announcements', methods=['GET'])
def custom_announcements():
    """Page to view and manage custom announcements."""
    announcements = load_json_file(CUSTOM_ANNOUNCEMENTS_FILE, {"users": {}})
    return render_template('custom_announcements.html', announcements=announcements)

@app.route('/api/custom_announcements', methods=['GET'])
def get_custom_announcements():
    """API endpoint to get custom announcements."""
    announcements = load_json_file(CUSTOM_ANNOUNCEMENTS_FILE, {"users": {}})
    return jsonify(announcements)

@app.route('/api/custom_announcements/<user_id>', methods=['POST'])
def update_custom_announcement(user_id):
    """API endpoint to update a user's custom announcements."""
    announcements = load_json_file(CUSTOM_ANNOUNCEMENTS_FILE, {"users": {}})
    
    data = request.json
    display_name = data.get('display_name', 'Unknown User')
    join_message = data.get('join_message')
    leave_message = data.get('leave_message')
    
    if user_id not in announcements["users"]:
        announcements["users"][user_id] = {"display_name": display_name}
    
    if join_message is not None:
        announcements["users"][user_id]["join_message"] = join_message
    
    if leave_message is not None:
        announcements["users"][user_id]["leave_message"] = leave_message
    
    if save_json_file(CUSTOM_ANNOUNCEMENTS_FILE, announcements):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Failed to save custom announcements"}), 500

@app.route('/api/custom_announcements/<user_id>', methods=['DELETE'])
def delete_custom_announcement(user_id):
    """API endpoint to delete a user's custom announcements."""
    announcements = load_json_file(CUSTOM_ANNOUNCEMENTS_FILE, {"users": {}})
    
    if user_id in announcements["users"]:
        del announcements["users"][user_id]
        
        if save_json_file(CUSTOM_ANNOUNCEMENTS_FILE, announcements):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to save custom announcements"}), 500
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

@app.route('/whitelist', methods=['GET'])
def whitelist():
    """Page to view and manage whitelist."""
    whitelist_data = load_json_file(WHITELIST_FILE, {"users": []})
    
    # Ensure whitelist data is properly formatted
    if not isinstance(whitelist_data, dict) or "users" not in whitelist_data:
        whitelist_data = {"users": []}
    
    # Get environment variables to check if whitelist mode is enabled
    env_vars = get_bot_env_vars()
    whitelist_mode = env_vars.get("WHITELIST_MODE", "False").lower() in ('true', 'yes', '1', 't')
    
    return render_template('whitelist.html', whitelist=whitelist_data, whitelist_mode=whitelist_mode)

@app.route('/api/whitelist', methods=['GET'])
def get_whitelist():
    """API endpoint to get the whitelist."""
    whitelist_data = load_json_file(WHITELIST_FILE, {"users": []})
    return jsonify(whitelist_data)

@app.route('/api/whitelist/<user_id>', methods=['POST'])
def add_to_whitelist(user_id):
    """API endpoint to add a user to the whitelist."""
    whitelist_data = load_json_file(WHITELIST_FILE, {"users": []})
    
    # Ensure proper format
    if not isinstance(whitelist_data, dict):
        whitelist_data = {"users": []}
    if "users" not in whitelist_data:
        whitelist_data["users"] = []
    
    # Add user if not already in whitelist
    if user_id not in whitelist_data["users"]:
        whitelist_data["users"].append(user_id)
        
        if save_json_file(WHITELIST_FILE, whitelist_data):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to save whitelist"}), 500
    else:
        return jsonify({"status": "info", "message": "User already in whitelist"})

@app.route('/api/whitelist/<user_id>', methods=['DELETE'])
def remove_from_whitelist(user_id):
    """API endpoint to remove a user from the whitelist."""
    whitelist_data = load_json_file(WHITELIST_FILE, {"users": []})
    
    # Ensure proper format
    if not isinstance(whitelist_data, dict) or "users" not in whitelist_data:
        return jsonify({"status": "error", "message": "Invalid whitelist format"}), 500
    
    # Remove user if in whitelist
    if user_id in whitelist_data["users"]:
        whitelist_data["users"].remove(user_id)
        
        if save_json_file(WHITELIST_FILE, whitelist_data):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to save whitelist"}), 500
    else:
        return jsonify({"status": "info", "message": "User not in whitelist"})

@app.route('/api/toggle_whitelist_mode', methods=['POST'])
def toggle_whitelist_mode():
    """API endpoint to toggle whitelist mode."""
    env_vars = get_bot_env_vars()
    current_mode = env_vars.get("WHITELIST_MODE", "False").lower() in ('true', 'yes', '1', 't')
    
    # Toggle the mode
    new_mode = "False" if current_mode else "True"
    env_vars["WHITELIST_MODE"] = new_mode
    
    if update_bot_env_vars(env_vars):
        return jsonify({"status": "success", "whitelist_mode": new_mode})
    else:
        return jsonify({"status": "error", "message": "Failed to update whitelist mode"}), 500

@app.route('/restart', methods=['POST'])
def restart_bot():
    """Restart the bot container."""
    if restart_bot_container():
        return jsonify({"status": "success", "message": "Bot restarted successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to restart bot"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')

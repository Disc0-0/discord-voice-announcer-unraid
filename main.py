import os
import asyncio
import logging
import tempfile
import discord
from discord.ext import commands
from gtts import gTTS
from dotenv import load_dotenv
import json
import os.path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Load environment variables from .env file
load_dotenv()

# Discord Bot Token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN or TOKEN == "PASTE_YOUR_ACTUAL_TOKEN_HERE" or TOKEN.startswith("your_") or len(TOKEN) < 50:
    logger.error("No valid Discord token found. Please set the DISCORD_TOKEN in your .env file.")
    exit(1)

# Optional configuration from environment variables
VOICE_LANGUAGE = os.getenv('VOICE_LANGUAGE', 'en')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
ANNOUNCE_JOINS = os.getenv('ANNOUNCE_JOINS', 'True').lower() in ('true', 'yes', '1', 't')
ANNOUNCE_LEAVES = os.getenv('ANNOUNCE_LEAVES', 'True').lower() in ('true', 'yes', '1', 't')
WHITELIST_MODE = os.getenv('WHITELIST_MODE', 'False').lower() in ('true', 'yes', '1', 't')

# Bot configuration
intents = discord.Intents.default()
intents.voice_states = True  # Enable voice state updates
intents.message_content = True  # Enable message content

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Track voice connections to prevent multiple announcements
active_voice_clients = {}
# Track users in voice channels to avoid announcing if they're already there
users_in_voice = {}

# Custom announcement messages
custom_announcements = {"users": {}}
CUSTOM_ANNOUNCEMENTS_FILE = "custom_announcements.json"

# User whitelist for announcements
announcement_whitelist = set()
WHITELIST_FILE = "announcement_whitelist.json"

# Load whitelist if file exists
def load_whitelist():
    global announcement_whitelist
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "users" in data:
                    announcement_whitelist = set(data["users"])
                    logger.info(f"Loaded {len(announcement_whitelist)} users in announcement whitelist")
                else:
                    logger.warning(f"Invalid format in {WHITELIST_FILE}, using default empty whitelist")
        else:
            logger.info(f"No {WHITELIST_FILE} found, using default empty whitelist")
    except Exception as e:
        logger.error(f"Error loading whitelist: {e}")

# Save whitelist to file
def save_whitelist():
    try:
        with open(WHITELIST_FILE, 'w') as f:
            json.dump({"users": list(announcement_whitelist)}, f, indent=4)
        logger.info(f"Saved {len(announcement_whitelist)} users to announcement whitelist")
    except Exception as e:
        logger.error(f"Error saving whitelist: {e}")

# Load custom announcements if file exists
def load_custom_announcements():
    global custom_announcements
    try:
        if os.path.exists(CUSTOM_ANNOUNCEMENTS_FILE):
            with open(CUSTOM_ANNOUNCEMENTS_FILE, 'r') as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict) and "users" in loaded_data:
                    custom_announcements = loaded_data
                    logger.info(f"Loaded {len(custom_announcements['users']) - (1 if '_comment' in custom_announcements['users'] else 0)} custom announcements")
                else:
                    logger.warning(f"Invalid format in {CUSTOM_ANNOUNCEMENTS_FILE}, using default")
        else:
            logger.info(f"No {CUSTOM_ANNOUNCEMENTS_FILE} found, using default")
    except Exception as e:
        logger.error(f"Error loading custom announcements: {e}")

# Save custom announcements to file
def save_custom_announcements():
    try:
        with open(CUSTOM_ANNOUNCEMENTS_FILE, 'w') as f:
            json.dump(custom_announcements, f, indent=4)
        logger.info(f"Saved {len(custom_announcements['users']) - (1 if '_comment' in custom_announcements['users'] else 0)} custom announcements")
    except Exception as e:
        logger.error(f"Error saving custom announcements: {e}")

# Load custom announcements at startup
load_custom_announcements()

# Load whitelist at startup
load_whitelist()

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    logger.info(f'{bot.user.name} is connected to Discord!')
    logger.info(f'Bot is active in {len(bot.guilds)} servers')
    
    # Initialize the users_in_voice dictionary
    for guild in bot.guilds:
        users_in_voice[guild.id] = set()
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                users_in_voice[guild.id].add(member.id)
    
    if ANNOUNCE_JOINS and ANNOUNCE_LEAVES:
        activity_name = "voice channel activity"
    elif ANNOUNCE_JOINS:
        activity_name = "voice channel joins"
    elif ANNOUNCE_LEAVES:
        activity_name = "voice channel leaves"
    else:
        activity_name = "voice channels"
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=activity_name
    ))

@bot.event
async def on_voice_state_update(member, before, after):
    """
    Event triggered when a member changes their voice state.
    This includes joining, leaving, or moving between voice channels.
    """
    # Ignore bot's own voice state updates
    if member.id == bot.user.id:
        return
    
    # Initialize guild in tracking dict if not present
    if member.guild.id not in users_in_voice:
        users_in_voice[member.guild.id] = set()
    
    # Check if the member has joined a new voice channel
    if before.channel != after.channel and after.channel is not None:
        # Check if this is a new join (not just moving between channels in the same guild)
        is_new_join = before.channel is None or member.id not in users_in_voice[member.guild.id]
        
        # Add user to our tracking set
        users_in_voice[member.guild.id].add(member.id)
        
        # If this is a new join, announce it
        if is_new_join:
            logger.info(f"User {member.display_name} joined {after.channel.name}")
            
            # Only announce joins if the feature is enabled and user is in whitelist if whitelist mode is on
            if ANNOUNCE_JOINS and (not WHITELIST_MODE or str(member.id) in announcement_whitelist):
                try:
                    # Create and play the announcement
                    await announce_user_join(after.channel, member.display_name)
                except Exception as e:
                    logger.error(f"Error announcing user join: {e}")
    
    # Handle user leaving voice channels
    if after.channel is None and before.channel is not None:
        # User left voice channel
        if member.id in users_in_voice[member.guild.id]:
            logger.info(f"User {member.display_name} left {before.channel.name}")
            
            # Announce the leave if enabled and user is in whitelist if whitelist mode is on
            if ANNOUNCE_LEAVES and (not WHITELIST_MODE or str(member.id) in announcement_whitelist):
                try:
                    # Create and play the leave announcement
                    await announce_user_leave(before.channel, member.display_name)
                except Exception as e:
                    logger.error(f"Error announcing user leave: {e}")
            
            # Remove user from tracking
            users_in_voice[member.guild.id].remove(member.id)

async def generate_tts_file(text):
    """Generate a TTS audio file from text."""
    try:
        # Create a temporary file for the TTS audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        # Generate TTS audio
        tts = gTTS(text=text, lang=VOICE_LANGUAGE, slow=False)
        tts.save(temp_file.name)
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise

async def announce_user_join(voice_channel, username):
    """Join a voice channel and play a TTS announcement."""
    guild_id = voice_channel.guild.id
    
    try:
        # Check for custom announcement
        announcement_text = ""
        
        # Get custom join message if available
        user_id = None
        for member in voice_channel.members:
            if member.display_name.lower() == username.lower():
                user_id = str(member.id)
                break
        
        if user_id and user_id in custom_announcements["users"]:
            custom_msg = custom_announcements["users"][user_id].get("join_message")
            if custom_msg:
                announcement_text = custom_msg.format(username=username)
                logger.info(f"Using custom join message for {username}")
        
        # Use default if no custom message
        if not announcement_text:
            announcement_text = f"{username} joined the channel"
            
        tts_file = await generate_tts_file(announcement_text)
        
        # Connect to the voice channel
        voice_client = await connect_to_voice_channel(voice_channel)
        if not voice_client:
            logger.error("Failed to connect to voice channel")
            if os.path.exists(tts_file):
                os.unlink(tts_file)
            return
        
        # Play the announcement
        if os.path.exists(tts_file):
            audio_source = discord.FFmpegPCMAudio(tts_file)
            
            # Play the audio
            def after_callback(error):
                asyncio.run_coroutine_threadsafe(
                    handle_after_play(guild_id, tts_file, error), 
                    bot.loop
                )
            
            voice_client.play(audio_source, after=after_callback)
        else:
            logger.error(f"TTS file not found: {tts_file}")
            
    except Exception as e:
        logger.error(f"Error in announce_user_join: {e}")
        # Try to clean up resources
        if guild_id in active_voice_clients:
            try:
                await active_voice_clients[guild_id].disconnect()
                del active_voice_clients[guild_id]
            except Exception as disconnect_error:
                logger.error(f"Error disconnecting: {disconnect_error}")

async def announce_user_leave(voice_channel, username):
    """Join a voice channel and play a TTS announcement for a user leaving."""
    guild_id = voice_channel.guild.id
    
    try:
        # Check for custom announcement
        announcement_text = ""
        
        # Try to find user ID by username
        user_id = None
        for guild in bot.guilds:
            for member in guild.members:
                if member.display_name.lower() == username.lower():
                    user_id = str(member.id)
                    break
            if user_id:
                break
                
        # Get custom leave message if available
        if user_id and user_id in custom_announcements["users"]:
            custom_msg = custom_announcements["users"][user_id].get("leave_message")
            if custom_msg:
                announcement_text = custom_msg.format(username=username)
                logger.info(f"Using custom leave message for {username}")
        
        # Use default if no custom message
        if not announcement_text:
            announcement_text = f"{username} left the channel"
            
        tts_file = await generate_tts_file(announcement_text)
        
        # Connect to the voice channel
        voice_client = await connect_to_voice_channel(voice_channel)
        if not voice_client:
            logger.error("Failed to connect to voice channel")
            if os.path.exists(tts_file):
                os.unlink(tts_file)
            return
        
        # Play the announcement
        if os.path.exists(tts_file):
            audio_source = discord.FFmpegPCMAudio(tts_file)
            
            # Play the audio
            def after_callback(error):
                asyncio.run_coroutine_threadsafe(
                    handle_after_play(guild_id, tts_file, error), 
                    bot.loop
                )
            
            voice_client.play(audio_source, after=after_callback)
        else:
            logger.error(f"TTS file not found: {tts_file}")
            
    except Exception as e:
        logger.error(f"Error in announce_user_leave: {e}")
        # Try to clean up resources
        if guild_id in active_voice_clients:
            try:
                await active_voice_clients[guild_id].disconnect()
                del active_voice_clients[guild_id]
            except Exception as disconnect_error:
                logger.error(f"Error disconnecting: {disconnect_error}")

async def connect_to_voice_channel(voice_channel):
    """Connect to a voice channel, handling any existing connections."""
    guild_id = voice_channel.guild.id
    
    try:
        # Check if bot is already connected to a voice channel in this guild
        if guild_id in active_voice_clients:
            voice_client = active_voice_clients[guild_id]
            
            # If already connected to the target channel, use that connection
            if voice_client.is_connected() and voice_client.channel.id == voice_channel.id:
                return voice_client
            
            # If connected to a different channel, disconnect first
            if voice_client.is_connected():
                await voice_client.disconnect()
                # Wait a brief moment to ensure the disconnect completes
                await asyncio.sleep(0.5)
        
        # Connect to the voice channel
        voice_client = await voice_channel.connect(timeout=10, reconnect=True)
        active_voice_clients[guild_id] = voice_client
        return voice_client
    except Exception as e:
        logger.error(f"Error connecting to voice channel: {e}")
        return None

async def handle_after_play(guild_id, tts_file, error):
    """Handle cleanup after playing an announcement."""
    # Delete the temporary TTS file
    try:
        if os.path.exists(tts_file):
            os.unlink(tts_file)
    except Exception as e:
        logger.error(f"Error deleting TTS file: {e}")
    
    # Disconnect from voice channel after a delay
    try:
        # Wait a moment before disconnecting
        await asyncio.sleep(1)
        
        if guild_id in active_voice_clients:
            voice_client = active_voice_clients[guild_id]
            if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                await voice_client.disconnect()
                del active_voice_clients[guild_id]
    except Exception as e:
        logger.error(f"Error in handle_after_play: {e}")
    
    # Log any error that occurred during playback
    if error:
        logger.error(f"Error in voice playback: {error}")

# Command for testing announcement functionality
@bot.command(name='announce', help='Test the announcement system')
async def test_announce(ctx, *, message=None):
    """Command to test the announcement system."""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command.")
        return
    
    voice_channel = ctx.author.voice.channel
    username = message or ctx.author.display_name
    
    await ctx.send(f"Testing announcement system with: '{username}'")
    await announce_user_join(voice_channel, username)

# Command to show bot info and status
@bot.command(name='status', help='Show bot status and configuration')
async def status(ctx):
    """Command to show bot status and configuration."""
    embed = discord.Embed(
        title="Voice Announcer Bot Status",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Active Servers", 
        value=str(len(bot.guilds)),
        inline=True
    )
    
    active_voice_count = sum(1 for client in active_voice_clients.values() if client.is_connected())
    embed.add_field(
        name="Active Voice Connections", 
        value=str(active_voice_count),
        inline=True
    )
    
    embed.add_field(
        name="TTS Language", 
        value=VOICE_LANGUAGE,
        inline=True
    )
    
    tracked_users = sum(len(users) for users in users_in_voice.values())
    embed.add_field(
        name="Users in Voice Channels", 
        value=str(tracked_users),
        inline=True
    )
    
    embed.add_field(
        name="Join Announcements", 
        value="Enabled" if ANNOUNCE_JOINS else "Disabled",
        inline=True
    )
    
    embed.add_field(
        name="Leave Announcements", 
        value="Enabled" if ANNOUNCE_LEAVES else "Disabled",
        inline=True
    )
    
    custom_count = len(custom_announcements["users"]) - (1 if "_comment" in custom_announcements["users"] else 0)
    embed.add_field(
        name="Custom Announcements", 
        value=f"{custom_count} users",
        inline=True
    )
    
    whitelist_status = "Enabled" if WHITELIST_MODE else "Disabled"
    embed.add_field(
        name="Whitelist Mode", 
        value=f"{whitelist_status} ({len(announcement_whitelist)} users)",
        inline=True
    )
    
    await ctx.send(embed=embed)

# Command to toggle join announcements
@bot.command(name='togglejoins', help='Toggle join announcements on/off')
async def toggle_joins(ctx):
    """Command to toggle whether join announcements are enabled."""
    global ANNOUNCE_JOINS
    ANNOUNCE_JOINS = not ANNOUNCE_JOINS
    
    status = "enabled" if ANNOUNCE_JOINS else "disabled"
    await ctx.send(f"Join announcements are now {status}")
    
    # Update bot presence to reflect the change
    if ANNOUNCE_JOINS and ANNOUNCE_LEAVES:
        activity_name = "voice channel activity"
    elif ANNOUNCE_JOINS:
        activity_name = "voice channel joins"
    elif ANNOUNCE_LEAVES:
        activity_name = "voice channel leaves"
    else:
        activity_name = "voice channels"
        
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=activity_name
    ))

# Command to toggle leave announcements
@bot.command(name='toggleleaves', help='Toggle leave announcements on/off')
async def toggle_leaves(ctx):
    """Command to toggle whether leave announcements are enabled."""
    global ANNOUNCE_LEAVES
    ANNOUNCE_LEAVES = not ANNOUNCE_LEAVES
    
    status = "enabled" if ANNOUNCE_LEAVES else "disabled"
    await ctx.send(f"Leave announcements are now {status}")
    
    # Update bot presence to reflect the change
    if ANNOUNCE_JOINS and ANNOUNCE_LEAVES:
        activity_name = "voice channel activity"
    elif ANNOUNCE_JOINS:
        activity_name = "voice channel joins"
    elif ANNOUNCE_LEAVES:
        activity_name = "voice channel leaves"
    else:
        activity_name = "voice channels"
        
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=activity_name
    ))

# Command to toggle whitelist mode
@bot.command(name='togglewhitelist', help='Toggle between announcing all users or only whitelisted users')
@commands.has_permissions(administrator=True)
async def toggle_whitelist(ctx):
    """Command to toggle whether announcements are for all users or only whitelisted users."""
    global WHITELIST_MODE
    WHITELIST_MODE = not WHITELIST_MODE
    
    status = "enabled" if WHITELIST_MODE else "disabled"
    if WHITELIST_MODE and len(announcement_whitelist) == 0:
        await ctx.send(f"Whitelist mode is now {status}, but your whitelist is empty. Use `!whitelist add @user` to add users.")
    else:
        await ctx.send(f"Whitelist mode is now {status}. Only whitelisted users will trigger announcements." if WHITELIST_MODE 
                     else f"Whitelist mode is now {status}. All users will trigger announcements.")

# Commands for managing the announcement whitelist
@bot.group(name='whitelist', help='Manage the announcement whitelist')
async def whitelist(ctx):
    """Group command for managing the whitelist."""
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid whitelist command. Use `!help whitelist` for more information.")
        
@whitelist.command(name='add', help='Add a user to the announcement whitelist')
@commands.has_permissions(administrator=True)
async def whitelist_add(ctx, user: discord.Member):
    """Add a user to the announcement whitelist."""
    user_id = str(user.id)
    
    if user_id in announcement_whitelist:
        await ctx.send(f"{user.display_name} is already in the announcement whitelist.")
        return
        
    announcement_whitelist.add(user_id)
    save_whitelist()
    
    await ctx.send(f"{user.display_name} has been added to the announcement whitelist.")
    
    # If whitelist mode is off, suggest enabling it
    if not WHITELIST_MODE:
        await ctx.send("Note: Whitelist mode is currently disabled. Use `!togglewhitelist` to enable it.")

@whitelist.command(name='remove', help='Remove a user from the announcement whitelist')
@commands.has_permissions(administrator=True)
async def whitelist_remove(ctx, user: discord.Member):
    """Remove a user from the announcement whitelist."""
    user_id = str(user.id)
    
    if user_id not in announcement_whitelist:
        await ctx.send(f"{user.display_name} is not in the announcement whitelist.")
        return
        
    announcement_whitelist.remove(user_id)
    save_whitelist()
    
    await ctx.send(f"{user.display_name} has been removed from the announcement whitelist.")

@whitelist.command(name='list', help='List all users in the announcement whitelist')
async def whitelist_list(ctx):
    """List all users in the announcement whitelist."""
    if not announcement_whitelist:
        await ctx.send("The announcement whitelist is empty.")
        return
        
    embed = discord.Embed(
        title="Announcement Whitelist",
        color=discord.Color.blue(),
        description=f"Whitelist Mode: {'Enabled' if WHITELIST_MODE else 'Disabled'}"
    )
    
    # Get user objects for all IDs in the whitelist
    whitelist_members = []
    for user_id in announcement_whitelist:
        user = None
        for guild in bot.guilds:
            user = guild.get_member(int(user_id))
            if user:
                whitelist_members.append(user)
                break
    
    # Sort members by name for easier reading
    whitelist_members.sort(key=lambda m: m.display_name.lower() if m else "")
    
    # Create a string with all the members
    members_text = ""
    for i, member in enumerate(whitelist_members, 1):
        if member:
            members_text += f"{i}. {member.mention} ({member.display_name})\n"
        else:
            members_text += f"{i}. Unknown User (ID: {user_id})\n"
    
    if members_text:
        embed.add_field(name="Users", value=members_text, inline=False)
    else:
        embed.add_field(name="Users", value="No valid users found", inline=False)
    
    await ctx.send(embed=embed)

@whitelist.error
@whitelist_add.error
@whitelist_remove.error
@toggle_whitelist.error
async def whitelist_error(ctx, error):
    """Handle errors for whitelist commands."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments. Use `!help whitelist` for usage information.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You need administrator permissions to manage the whitelist.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid user. Please mention a valid user.")
    else:
        await ctx.send(f"An error occurred: {error}")
        logger.error(f"Whitelist command error: {error}")

# Commands for managing custom announcements
@bot.command(name='addcustom', help='Add custom join/leave messages for a user')
@commands.has_permissions(administrator=True)
async def add_custom(ctx, user: discord.Member, message_type: str, *, message: str):
    """
    Add custom join/leave messages for a specific user
    Parameters:
    - user: The user to add a custom message for (mention the user)
    - message_type: Either 'join' or 'leave'
    - message: The custom message (use {username} as placeholder for the user's name)
    """
    user_id = str(user.id)
    message_type = message_type.lower()
    
    if message_type not in ['join', 'leave']:
        await ctx.send("Message type must be either 'join' or 'leave'")
        return
    
    # Initialize user entry if not exists
    if user_id not in custom_announcements["users"]:
        custom_announcements["users"][user_id] = {
            "display_name": user.display_name
        }
    
    # Set the message
    if message_type == 'join':
        custom_announcements["users"][user_id]["join_message"] = message
    else:
        custom_announcements["users"][user_id]["leave_message"] = message
    
    # Save changes
    save_custom_announcements()
    
    await ctx.send(f"Custom {message_type} message for {user.display_name} has been set!")

@bot.command(name='removecustom', help='Remove custom join/leave messages for a user')
@commands.has_permissions(administrator=True)
async def remove_custom(ctx, user: discord.Member, message_type: str = "both"):
    """
    Remove custom join/leave messages for a specific user
    Parameters:
    - user: The user to remove custom messages for (mention the user)
    - message_type: 'join', 'leave', or 'both' (default)
    """
    user_id = str(user.id)
    message_type = message_type.lower()
    
    if message_type not in ['join', 'leave', 'both']:
        await ctx.send("Message type must be 'join', 'leave', or 'both'")
        return
    
    # Check if user has custom messages
    if user_id not in custom_announcements["users"]:
        await ctx.send(f"{user.display_name} has no custom messages")
        return
    
    # Remove specified messages
    if message_type == 'both':
        del custom_announcements["users"][user_id]
        message_info = "join and leave messages"
    else:
        if message_type + "_message" in custom_announcements["users"][user_id]:
            del custom_announcements["users"][user_id][message_type + "_message"]
            message_info = message_type + " message"
            
            # Remove user entry if empty
            if len(custom_announcements["users"][user_id]) <= 1:  # Only display_name remains
                del custom_announcements["users"][user_id]
        else:
            await ctx.send(f"{user.display_name} has no custom {message_type} message")
            return
    
    # Save changes
    save_custom_announcements()
    
    await ctx.send(f"Custom {message_info} for {user.display_name} removed!")

@bot.command(name='listcustom', help='List all custom announcements')
async def list_custom(ctx):
    """List all users with custom announcements"""
    
    if not custom_announcements["users"] or len(custom_announcements["users"]) == 0 or \
       (len(custom_announcements["users"]) == 1 and "_comment" in custom_announcements["users"]):
        await ctx.send("No custom announcements are set")
        return
    
    embed = discord.Embed(
        title="Custom Announcements",
        color=discord.Color.green(),
        description="Users with custom join/leave messages"
    )
    
    for user_id, data in custom_announcements["users"].items():
        if user_id == "_comment":
            continue
            
        display_name = data.get("display_name", "Unknown User")
        join_msg = data.get("join_message", "None")
        leave_msg = data.get("leave_message", "None")
        
        field_value = f"Join: {join_msg}\nLeave: {leave_msg}"
        embed.add_field(
            name=display_name,
            value=field_value,
            inline=False
        )
    
    await ctx.send(embed=embed)

@add_custom.error
@remove_custom.error
async def custom_error(ctx, error):
    """Handle errors for custom announcement commands"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments. Use !help <command> for usage information.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You need administrator permissions to use this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid user. Please mention a valid user.")
    else:
        await ctx.send(f"An error occurred: {error}")
        logger.error(f"Command error: {error}")

# Run the bot
if __name__ == "__main__":
    try:
        logger.info("Starting Discord Voice Announcer Bot...")
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord token. Please check your .env file.")
        logger.error(f"Error starting bot: {e}")


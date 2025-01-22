import discord
from discord import app_commands
from util import getResponse, initializeConversation  # Importing utility functions
import functools
import typing
import asyncio

# Replace with your guild ID and bot token
GUILD_ID = 000000000000000000  # replace with your guild id
MY_GUILD = discord.Object(id=GUILD_ID)
AI_LOADED = False
BOT_TOKEN = "YOUR-BOT-TOKEN"
conversation_history = {}

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

# Utility function to run blocking functions in an asynchronous event loop
def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")

@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")

@client.tree.command()
async def ping(interaction: discord.Interaction):
    """Simple Ping Pong!"""
    ping = round(client.latency * 1000)
    embed = discord.Embed(color=discord.Color.blurple())
    embed.set_author(
        icon_url=interaction.user.display_avatar.url, name=f"| Pong! (Took {ping}ms)"
    )
    await interaction.response.send_message(embed=embed)

# AI response handling with caching of conversation history
@to_thread
def get_ai(prompt, user_id):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Append the new prompt to conversation history
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    # Retrieve response based on conversation history
    response = getResponse(conversation_history[user_id])
    
    # Append AI response to the conversation
    conversation_history[user_id].append({"role": "ai", "content": response})
    
    return response

# Initialize AI with history context
@to_thread
def start_ai():
    global AI_LOADED
    initializeConversation()
    AI_LOADED = True
    return

# Command to send a prompt to the AI
@client.tree.command()
@app_commands.guild_only()
@app_commands.describe(prompt="The prompt you want to send to the AI")
async def prompt(interaction: discord.Interaction, prompt: str):
    """Sends a prompt to the AI with conversation history."""
    await interaction.response.defer()
    
    if not AI_LOADED:
        embed = discord.Embed(color=discord.Color.dark_orange(), title="AI Not Loaded")
        embed.description = "Ask the bot owner to reload the AI"
        return await interaction.followup.send(embed=embed)
    
    response = await get_ai(prompt, interaction.user.id)
    embed = discord.Embed(color=discord.Color.teal(), title=prompt)
    embed.description = response
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.timestamp = interaction.created_at
    return await interaction.followup.send(embed=embed)

# Command to start or reload the AI
@client.tree.command()
@app_commands.default_permissions()
@app_commands.guild_only()
async def start(interaction: discord.Interaction):
    """Reloads/Starts the AI with conversation context."""
    await interaction.response.defer()
    await start_ai()
    embed = discord.Embed(color=discord.Color.yellow(), title="AI Reloaded")
    embed.description = "To use the AI, use the `/prompt` command"
    return await interaction.followup.send(embed=embed)

# Command to display the list of commands
@client.tree.command()
@app_commands.guild_only()
async def help(interaction: discord.Interaction):
    """Lists all the commands."""
    embed = discord.Embed(
        color=discord.Color.blurple(),
        title="Help",
        description="Here are the commands you can use",
    )
    embed.add_field(name="`/hello`", value="Says hello!", inline=False)
    embed.add_field(name="`/ping`", value="Simple Ping Pong!", inline=False)
    embed.add_field(name="`/prompt`", value="Sends a prompt to the AI.", inline=False)
    embed.add_field(name="`/reload`", value="Reloads/Starts the AI", inline=False)
    embed.add_field(name="`/help`", value="Shows this message", inline=False)
    embed.add_field(name="`/invite`", value="Sends the invite link for the bot", inline=False)
    embed.add_field(name="`/shutdown`", value="Shuts down the AI", inline=False)
    await interaction.response.send_message(embed=embed)

# Command to send the bot invite link
@client.tree.command()
async def invite(interaction: discord.Interaction):
    """Sends the invite link for the bot."""
    embed = discord.Embed(
        color=discord.Color.blurple(),
        title="Invite 🔗",
        description="Here is the invite link for the bot 😊",
    )
    embed.url = "https://discord.com/api/oauth2/authorize?client_id=930499355918602250&permissions=8&scope=bot%20applications.commands"
    await interaction.response.send_message(embed=embed)

# Command to shut down the AI
@client.tree.command()
@app_commands.guild_only()
@app_commands.default_permissions()
async def shutdown(interaction: discord.Interaction):
    """Shuts down the AI."""
    global AI_LOADED
    AI_LOADED = False
    embed = discord.Embed(color=discord.Color.red(), title="AI Shut Down")
    embed.description = "Start the AI again using `/reload`"
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    client.run(BOT_TOKEN)

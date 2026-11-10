import os
import discord
from discord.ext import commands

# 1. Fetch token from environment (Removed strict GUILD/CHANNEL checks for multi-server support)
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in Railway Variables.")

# 2. Configure intents (Required to read messages and track members across all servers)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

# 3. Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# 4. On Ready Event
@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user}")
    print(f"Currently active in {len(bot.guilds)} servers.")
    
    # Sets the bot's status in the Discord sidebar
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="over 1shot and the community"
        )
    )

# ---------------------------------------------------------
# CORE COMMANDS
# ---------------------------------------------------------

@bot.command()
async def ping(ctx):
    """Check bot latency and active server."""
    latency = round(bot.latency * 1000)
    server_name = ctx.guild.name if ctx.guild else "DMs"
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms | Server: **{server_name}**")

# ---------------------------------------------------------
# COMMUNITY & GAMING COMMANDS
# ---------------------------------------------------------

@bot.command()
async def rank(ctx, *, game: str = None):
    """Assign game roles for matchmaking."""
    if not game:
        await ctx.send("Please specify a game: `!rank valorant` or `!rank apex`.")
        return

    game = game.lower()
    if game in ["valorant", "val"]:
        await ctx.send(f"{ctx.author.mention}, assigning the Valorant role! Check the LFG channels to queue up.")
    elif game in ["apex", "apex legends"]:
        await ctx.send(f"{ctx.author.mention}, assigning the Apex Legends role! Drop into the arenas.")
    else:
        await ctx.send(f"Role for '{game}' not found. Ask a moderator to add it.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def event(ctx, event_type: str):
    """Announce community events (Mod only)."""
    event_type = event_type.lower()
    if event_type == "music":
        await ctx.send("🎤 **Music Performance Showcase starting soon!** Jump into the event voice channel.")
    elif event_type == "pfp":
        await ctx.send("🖼️ **PFP Showcase!** Drop your best aesthetics in the chat.")
    elif event_type == "debate":
        await ctx.send("🗣️ **Debate Session is live!** Join the VC and keep it respectful.")
    else:
        await ctx.send("Usage: `!event music`, `!event pfp`, or `!event debate`.")

@event.error
async def event_error(ctx, error):
    """Error handler if a regular member tries to use the event command."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need `Manage Messages` permissions to announce events.")

# ---------------------------------------------------------
# PASTE YOUR ORIGINAL CUSTOM COMMANDS BELOW THIS LINE
# ---------------------------------------------------------
# Ensure none of your old commands use a hardcoded guild_id.
# Replace any fixed IDs with ctx.guild.id so they work everywhere.



# 6. Start the bot
if __name__ == "__main__":
    bot.run(TOKEN)

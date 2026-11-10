import os
import asyncio
import logging
from collections import Counter

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
MESSAGE_ID = int(os.getenv("MESSAGE_ID", "0"))  # Optional: reuse an existing message

API_BASE = "https://discord.com/api/v10"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("tag-stats")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Maps Discord user ID -> equipped tag text.
member_tags: dict[str, str] = {}
stats_message: discord.Message | None = None
refresh_task: asyncio.Task | None = None
startup_complete = False


def extract_tag(user_data: dict) -> str | None:
    """Return the visible equipped server tag, if supplied by Discord."""
    primary_guild = user_data.get("primary_guild")
    if not isinstance(primary_guild, dict):
        return None

    if primary_guild.get("identity_enabled") is not True:
        return None

    tag = primary_guild.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        return None

    return tag.strip().upper()


async def fetch_all_members() -> None:
    """Fetch the guild member list in pages and build the initial tag cache."""
    global member_tags

    headers = {"Authorization": f"Bot {TOKEN}"}
    scanned = 0
    discovered: dict[str, str] = {}
    after = "0"

    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        while True:
            url = f"{API_BASE}/guilds/{GUILD_ID}/members"
            params = {"limit": 1000, "after": after}

            while True:
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        payload = await response.json()
                        await asyncio.sleep(float(payload.get("retry_after", 2)))
                        continue

                    if response.status != 200:
                        body = await response.text()
                        raise RuntimeError(
                            f"Discord member scan failed ({response.status}): {body}"
                        )

                    batch = await response.json()
                    break

            if not batch:
                break

            for member in batch:
                user = member.get("user") or {}
                user_id = str(user.get("id", ""))
                if not user_id:
                    continue

                tag = extract_tag(user)
                if tag:
                    discovered[user_id] = tag

            scanned += len(batch)
            after = str(batch[-1]["user"]["id"])
            log.info("Scanned %s members; found %s equipped tags.", scanned, len(discovered))

            if len(batch) < 1000:
                break

    member_tags = discovered
    log.info("Initial scan complete: %s members scanned, %s tagged members found.",
             scanned, len(member_tags))


def build_embed() -> discord.Embed:
    counts = Counter(member_tags.values())
    embed = discord.Embed(
        title="1shot | Server Tag Statistics",
        description="Live count of equipped Discord server tags among 1shot members.",
        colour=discord.Colour.blurple(),
    )

    if counts:
        for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:25]:
            embed.add_field(name=f"🏷️ {tag}", value=f"**{count:,} members**", inline=True)

        embed.add_field(
            name="Total members with detected tags",
            value=f"**{sum(counts.values()):,}**",
            inline=False,
        )
    else:
        embed.add_field(
            name="No tag data detected",
            value=(
                "Discord did not provide equipped-tag data in the member responses yet. "
                "Check the bot permissions, privileged intent, and API response."
            ),
            inline=False,
        )

    embed.set_footer(text="1shot • Live tag statistics")
    return embed


async def get_channel():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(CHANNEL_ID)
    return channel


async def get_or_create_stats_message() -> discord.Message:
    global stats_message

    if stats_message is not None:
        return stats_message

    channel = await get_channel()

    if MESSAGE_ID:
        try:
            stats_message = await channel.fetch_message(MESSAGE_ID)
            return stats_message
        except discord.NotFound:
            log.warning("MESSAGE_ID was not found; creating a new statistics message.")

    stats_message = await channel.send(embed=build_embed())
    log.info("Created statistics message with ID %s.", stats_message.id)
    return stats_message


async def update_embed() -> None:
    try:
        message = await get_or_create_stats_message()
        await message.edit(embed=build_embed())
        log.info("Statistics embed updated.")
    except Exception:
        log.exception("Could not update the statistics embed.")


async def delayed_refresh() -> None:
    await asyncio.sleep(2)  # Debounce bursts of member updates.
    await update_embed()


def schedule_refresh() -> None:
    global refresh_task

    if refresh_task and not refresh_task.done():
        refresh_task.cancel()

    refresh_task = asyncio.create_task(delayed_refresh())


@bot.event
async def on_socket_response(payload):
    """Inspect raw Gateway payloads for member add/update/remove events."""
    if not isinstance(payload, dict):
        return

    event_name = payload.get("t")
    data = payload.get("d") or {}

    if event_name not in {
        "GUILD_MEMBER_UPDATE",
        "GUILD_MEMBER_ADD",
        "GUILD_MEMBER_REMOVE",
    }:
        return

    if str(data.get("guild_id", "")) != str(GUILD_ID):
        return

    user = data.get("user") or {}
    user_id = str(user.get("id", ""))
    if not user_id:
        return

    if event_name == "GUILD_MEMBER_REMOVE":
        member_tags.pop(user_id, None)
        schedule_refresh()
        return

    # Some Gateway payloads may omit optional user fields. Only change the
    # cache when primary_guild is actually present in the payload.
    if "primary_guild" not in user:
        return

    tag = extract_tag(user)
    if tag:
        member_tags[user_id] = tag
    else:
        member_tags.pop(user_id, None)

    schedule_refresh()


@bot.tree.command(
    name="tagstats",
    description="Refresh the 1shot server tag statistics.",
)
@app_commands.guilds(discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def tagstats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await update_embed()
    await interaction.followup.send(
        f"Statistics refreshed. Detected equipped tags for **{len(member_tags):,} members**.",
        ephemeral=True,
    )


@bot.event
async def on_ready():
    global startup_complete

    log.info("Logged in as %s (%s)", bot.user, bot.user.id)

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    except Exception:
        log.exception("Slash-command sync failed.")

    if startup_complete:
        return

    startup_complete = True
    try:
        await fetch_all_members()
        await update_embed()
    except Exception:
        startup_complete = False
        log.exception("Initial scan failed.")


if not TOKEN or not GUILD_ID or not CHANNEL_ID:
    raise RuntimeError(
        "Set DISCORD_TOKEN, GUILD_ID, and CHANNEL_ID in Railway Variables."
    )

bot.run(TOKEN)

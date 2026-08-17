import os

import discord

from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

from staff_scraper import (
    get_staff,
    ANIME_ALIASES,
    normalize,
)


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN is missing.\n"
        "Create a .env file containing:\n"
        "DISCORD_TOKEN=your_bot_token"
    )


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# COLORS
# ============================================================

EMBED_COLOR = discord.Color.from_rgb(
    112,
    88,
    255
)


# ============================================================
# SEASON DETECTION
# ============================================================

def detect_season(
    anime
):

    normalized = normalize(
        anime
    )

    # --------------------------------------------------------
    # Explicit alias
    # --------------------------------------------------------

    if normalized in ANIME_ALIASES:

        alias_slug = ANIME_ALIASES[
            normalized
        ]

        # Frieren
        if (
            alias_slug
            == "sousou-no-frieren-2nd-season"
        ):
            return 2

        # MHA
        for number in range(
            2,
            8
        ):

            if alias_slug == (
                f"my-hero-academia-{number}"
            ):

                return number

        if (
            alias_slug
            == "my-hero-academia-final-season"
        ):

            return 8

        # JJK
        if (
            alias_slug
            == "jujutsu-kaisen-2nd-season"
        ):
            return 2

        if (
            alias_slug
            == "jujutsu-kaisen-3rd-season-culling-game-part-1"
        ):
            return 3

        if (
            alias_slug
            == "jujutsu-kaisen-4th-season-culling-game-part-2"
        ):
            return 4

        # Bleach TYBW
        if (
            alias_slug
            == "bleach-thousand-year-blood-war"
        ):
            return 1

        if (
            alias_slug
            == "bleach-thousand-year-blood-war-the-separation"
        ):
            return 2

        if (
            alias_slug
            == "bleach-thousand-year-blood-war-the-conflict"
        ):
            return 3

        if (
            alias_slug
            == "bleach-thousand-year-blood-war-the-calamity"
        ):
            return 4

        # Mob
        if alias_slug == "mob-psycho-100":
            return 1

        if alias_slug == "mob-psycho-100-ii":
            return 2

        if alias_slug == "mob-psycho-100-iii":
            return 3

        # OPM
        if alias_slug == "one-punch-man":
            return 1

        if alias_slug == "one-punch-man-2":
            return 2

        if alias_slug == "one-punch-man-3":
            return 3

        # Solo Leveling
        if alias_slug == "solo-leveling":
            return 1

        if (
            alias_slug
            == "solo-leveling-season-2-arise-from-the-shadow"
        ):
            return 2

        # Naruto
        if alias_slug == "naruto":
            return 1

        if alias_slug == "naruto-shippuuden":
            return 2

    # --------------------------------------------------------
    # Direct text fallback
    # --------------------------------------------------------

    match = None

    import re

    match = re.search(
        r"(?:season|s)\s*(\d+)",
        normalized
    )

    if match:

        try:
            return int(
                match.group(1)
            )

        except ValueError:
            pass

    return 1


# ============================================================
# FORMAT NAMES
# ============================================================

def format_names(
    names
):

    if not names:
        return None

    names = list(
        dict.fromkeys(
            names
        )
    )

    return ", ".join(
        str(name)
        for name in names
    )


# ============================================================
# SPLIT LONG FIELD
# ============================================================

def split_text(
    text,
    limit=1024
):

    if len(text) <= limit:

        return [
            text
        ]

    parts = []

    current = ""

    # Split at commas where possible

    pieces = [
        x.strip()
        for x in text.split(",")
    ]

    for piece in pieces:

        if not piece:
            continue

        if not current:

            current = piece

        elif len(
            current
        ) + len(piece) + 2 <= limit:

            current += (
                ", "
                + piece
            )

        else:

            parts.append(
                current
            )

            current = piece

    if current:

        parts.append(
            current
        )

    return parts


# ============================================================
# ADD STAFF FIELD
# ============================================================

def add_staff_fields(
    embed,
    emoji,
    title,
    names
):

    if not names:
        return

    text = format_names(
        names
    )

    if not text:
        return

    chunks = split_text(
        text,
        1024
    )

    # --------------------------------------------------------
    # First chunk gets the title.
    # Additional chunks don't repeat the title.
    # --------------------------------------------------------

    for index, chunk in enumerate(
        chunks
    ):

        if index == 0:

            field_name = (
                f"{emoji} {title}"
            )

        else:

            field_name = (
                f"{emoji} {title} "
                f"(continued)"
            )

        embed.add_field(
            name=field_name,
            value=chunk,
            inline=False
        )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print()
    print(
        "=" * 60
    )

    print(
        f"Logged in as {bot.user}"
    )

    print(
        "=" * 60
    )

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} "
            f"slash commands."
        )

    except Exception as e:

        print(
            f"Command sync error: "
            f"{e!r}"
        )


# ============================================================
# STAFF COMMAND
# ============================================================

@bot.tree.command(
    name="staff",
    description="Look up anime episode staff"
)
@app_commands.describe(
    anime="Anime name or shortcut",
    episode="Episode number"
)
async def staff(
    interaction: discord.Interaction,
    anime: str,
    episode: int
):

    await interaction.response.defer()

    if episode < 1:

        await interaction.followup.send(
            "❌ Episode must be 1 or higher."
        )

        return

    season = detect_season(
        anime
    )

    print()
    print(
        "=" * 60
    )

    print(
        "STAFF DISCORD COMMAND"
    )

    print(
        "=" * 60
    )

    print(
        f"Input:   {anime}"
    )

    print(
        f"Season:  {season}"
    )

    print(
        f"Episode: {episode}"
    )

    print(
        "=" * 60
    )

    try:

        data = get_staff(
            anime,
            season,
            episode
        )

    except Exception as e:

        print(
            f"STAFF ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ Staff lookup encountered "
            "an error.\n"
            f"`{type(e).__name__}: {e}`"
        )

        return

    # ========================================================
    # NO DATA
    # ========================================================

    if not data:

        embed = discord.Embed(
            title="Episode Staff Credits",
            description=(
                f"**{anime}** — "
                f"Season {season} "
                f"Episode {episode}\n\n"
                "**No relevant staff "
                "credits found for this episode.**"
            ),
            color=EMBED_COLOR
        )

        embed.set_footer(
            text="Sakuga Staff"
        )

        await interaction.followup.send(
            embed=embed
        )

        return

    # ========================================================
    # EMBED
    # ========================================================

    embed = discord.Embed(
        title="Episode Staff Credits",
        description=(
            f"**{anime}** — "
            f"Season {season} "
            f"Episode {episode}"
        ),
        color=EMBED_COLOR
    )

    # ========================================================
    # STORYBOARD
    # ========================================================

    add_staff_fields(
        embed,
        "🎬",
        "Storyboard",
        data.get(
            "SB",
            []
        )
    )

    # ========================================================
    # EPISODE DIRECTOR
    # ========================================================

    add_staff_fields(
        embed,
        "🎞️",
        "Episode Director",
        data.get(
            "ED",
            []
        )
    )

    # ========================================================
    # ANIMATION DIRECTOR
    # ========================================================

    add_staff_fields(
        embed,
        "✏️",
        "Animation Director",
        data.get(
            "AD",
            []
        )
    )

    # ========================================================
    # ASSISTANT ANIMATION DIRECTOR
    # ========================================================

    add_staff_fields(
        embed,
        "🧩",
        "Assistant Animation Director",
        data.get(
            "Ass. AD",
            []
        )
    )

    # ========================================================
    # KEY ANIMATION
    # ========================================================

    add_staff_fields(
        embed,
        "🔥",
        "Key Animation",
        data.get(
            "KA",
            []
        )
    )

    # ========================================================
    # 2ND KEY ANIMATION
    # ========================================================

    second_ka = data.get(
        "2KA",
        0
    )

    if second_ka:

        embed.add_field(
            name="📝 2nd Key Animation",
            value=f"**{second_ka}**",
            inline=False
        )

    # ========================================================
    # FOOTER
    # ========================================================

    embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    # ========================================================
    # SEND
    # ========================================================

    try:

        await interaction.followup.send(
            embed=embed
        )

    except discord.HTTPException as e:

        print(
            f"EMBED ERROR: {e!r}"
        )

        # Emergency fallback
        await interaction.followup.send(
            "❌ The staff list was too large "
            "to display in the embed."
        )


# ============================================================
# RUN
# ============================================================

bot.run(
    TOKEN
)
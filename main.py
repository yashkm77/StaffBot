import os
import re

import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

from staff_scraper import (
    get_staff,
    ANIME_ALIASES,
    normalize,
)

from work_scraper import (
    get_animator_works,
)


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

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
    intents=intents,
)


# ============================================================
# COLORS
# ============================================================

EMBED_COLOR = discord.Color.from_rgb(
    112,
    88,
    255,
)


# ============================================================
# ROLE SHORT NAMES
# ============================================================

ROLE_SHORT_NAMES = {
    "Main Animator": "MA",
    "Key Animation": "KA",
    "Animation Director": "AD",
    "Assistant Animation Director": "Ass. AD",
    "Chief Animation Director": "CAD",
    "Storyboard": "SB",
    "Episode Director": "ED",
    "Storyboard / Episode Director": "SB/ED",
    "Character Design": "CD",
    "Art Board": "AB",
    "2nd Key Animation": "2KA",
    "Art Director": "Art Director",
}


# ============================================================
# SEASON DETECTION
# ============================================================

def detect_season(anime):

    normalized = normalize(anime)

    if normalized in ANIME_ALIASES:

        alias_slug = ANIME_ALIASES[normalized]

        # Frieren
        if alias_slug == "sousou-no-frieren-2nd-season":
            return 2

        # My Hero Academia
        for number in range(2, 8):
            if alias_slug == f"my-hero-academia-{number}":
                return number

        if alias_slug == "my-hero-academia-final-season":
            return 8

        # Jujutsu Kaisen
        if alias_slug == "jujutsu-kaisen":
            return 1

        if alias_slug == "jujutsu-kaisen-2nd-season":
            return 2

        if alias_slug == "jujutsu-kaisen-3rd-season-culling-game-part-1":
            return 3

        if alias_slug == "jujutsu-kaisen-4th-season-culling-game-part-2":
            return 4

        # Bleach TYBW
        if alias_slug == "bleach-thousand-year-blood-war":
            return 1

        if alias_slug == "bleach-thousand-year-blood-war-the-separation":
            return 2

        if alias_slug == "bleach-thousand-year-blood-war-the-conflict":
            return 3

        if alias_slug == "bleach-thousand-year-blood-war-the-calamity":
            return 4

        # Mob Psycho
        if alias_slug == "mob-psycho-100":
            return 1

        if alias_slug == "mob-psycho-100-ii":
            return 2

        if alias_slug == "mob-psycho-100-iii":
            return 3

        # One Punch Man
        if alias_slug == "one-punch-man":
            return 1

        if alias_slug == "one-punch-man-2":
            return 2

        if alias_slug == "one-punch-man-3":
            return 3

        # Solo Leveling
        if alias_slug == "solo-leveling":
            return 1

        if alias_slug == "solo-leveling-season-2-arise-from-the-shadow":
            return 2

        # Naruto
        if alias_slug == "naruto":
            return 1

        if alias_slug == "naruto-shippuuden":
            return 2

    match = re.search(
        r"(?:season|s)\s*(\d+)",
        normalized,
    )

    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return 1


# ============================================================
# GET ANIME SLUG
# ============================================================

def get_anime_slug(anime):

    normalized = normalize(anime)

    if normalized in ANIME_ALIASES:
        return ANIME_ALIASES[normalized]

    return re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip("-")


# ============================================================
# FORMAT NAMES
# ============================================================

def format_names(names):

    if not names:
        return None

    if not isinstance(names, list):
        names = [names]

    names = list(dict.fromkeys(names))

    return ", ".join(str(name) for name in names)


# ============================================================
# SPLIT LONG FIELD
# ============================================================

def split_text(text, limit=1024):

    if len(text) <= limit:
        return [text]

    parts = []
    current = ""

    pieces = [
        x.strip()
        for x in text.split(",")
    ]

    for piece in pieces:

        if not piece:
            continue

        if not current:
            current = piece

        elif len(current) + len(piece) + 2 <= limit:
            current += ", " + piece

        else:
            parts.append(current)
            current = piece

    if current:
        parts.append(current)

    return parts


# ============================================================
# ADD STAFF FIELD
# ============================================================

def add_staff_fields(
    embed,
    emoji,
    title,
    names,
):

    if not names:
        return

    text = format_names(names)

    if not text:
        return

    for index, chunk in enumerate(
        split_text(text, 1024)
    ):

        if index == 0:
            field_name = f"{emoji} {title}"
        else:
            field_name = f"{emoji} {title} (continued)"

        embed.add_field(
            name=field_name,
            value=chunk,
            inline=False,
        )


# ============================================================
# FORMAT WORK EPISODES
# ============================================================

def format_work_episodes(episodes):

    if not episodes:
        return ""

    if not isinstance(episodes, list):
        episodes = [episodes]

    formatted = []
    seen = set()

    for episode in episodes:

        if episode is None:
            continue

        text = str(episode).strip()

        if not text:
            continue

        # ----------------------------------------------------
        # OP / ED
        # ----------------------------------------------------

        if re.fullmatch(
            r"(?:OP|ED)\s*\d+",
            text,
            re.IGNORECASE,
        ):

            normalized = re.sub(
                r"\s+",
                "",
                text.upper(),
            )

            if normalized not in seen:
                formatted.append(normalized)
                seen.add(normalized)

            continue

        # ----------------------------------------------------
        # Preserve KFSL labels:
        #
        # #17
        # 17
        # 17 (BD)
        # #17 (BD)
        # ----------------------------------------------------

        if re.fullmatch(
            r"#?\s*\d+(?:\s*\([^)]*\))?",
            text,
        ):

            match = re.match(
                r"#?\s*(\d+)(.*)",
                text,
            )

            number = int(match.group(1))
            suffix = match.group(2).strip()

            # Keep BD / NC / etc.
            if suffix:
                formatted_text = (
                    f"{number:02d} {suffix}"
                )
            else:
                formatted_text = (
                    f"#{number:02d}"
                )

            if suffix:
                # If original had #, preserve it.
                if text.lstrip().startswith("#"):
                    formatted_text = (
                        f"#{number:02d} {suffix}"
                    )

            if formatted_text not in seen:
                formatted.append(formatted_text)
                seen.add(formatted_text)

            continue

        # ----------------------------------------------------
        # Everything else
        # ----------------------------------------------------

        if text not in seen:
            formatted.append(text)
            seen.add(text)

    return ", ".join(formatted)


# ============================================================
# NORMALIZE WORK GROUPS
# ============================================================

def normalize_work_groups(groups):

    if not isinstance(groups, dict):
        return {}

    normalized_groups = {}

    for role, info in groups.items():

        if not role:
            continue

        role = str(role).strip()

        # ----------------------------------------------------
        # List format
        #
        # "Storyboard": [17, "17 (BD)"]
        # ----------------------------------------------------

        if isinstance(info, list):

            normalized_groups[role] = {
                "episodes": info,
                "short": ROLE_SHORT_NAMES.get(
                    role,
                    role,
                ),
            }

            continue

        # ----------------------------------------------------
        # Dict format
        # ----------------------------------------------------

        if isinstance(info, dict):

            episodes = info.get(
                "episodes",
                [],
            )

            if not isinstance(episodes, list):
                episodes = [episodes]

            normalized_groups[role] = {
                "episodes": episodes,
                "short": info.get(
                    "short",
                    ROLE_SHORT_NAMES.get(
                        role,
                        role,
                    ),
                ),
            }

    return normalized_groups


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print()
    print("=" * 60)
    print(f"Logged in as {bot.user}")
    print("=" * 60)

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} slash commands."
        )

    except Exception as e:

        print(
            f"Command sync error: {e!r}"
        )


# ============================================================
# STAFF COMMAND
# ============================================================

@bot.tree.command(
    name="staff",
    description="Look up anime episode staff",
)
@app_commands.describe(
    anime="Anime name or shortcut",
    episode="Episode number, OP1, OP2, ED1, ED2, etc.",
)
async def staff(
    interaction: discord.Interaction,
    anime: str,
    episode: str,
):

    await interaction.response.defer()

    episode = episode.strip()

    if not episode:

        await interaction.followup.send(
            "❌ Please enter an episode number or OP/ED."
        )
        return

    if episode.isdigit():

        if int(episode) < 1:

            await interaction.followup.send(
                "❌ Episode must be 1 or higher."
            )
            return

    else:

        normalized_episode = normalize(episode)

        if not re.fullmatch(
            r"(op|ed)\s*\d+",
            normalized_episode,
        ):

            await interaction.followup.send(
                "❌ Invalid episode.\n"
                "Use `1`, `12`, `OP1`, `OP2`, `ED1`, etc."
            )
            return

    season = detect_season(anime)

    print()
    print("=" * 60)
    print("STAFF DISCORD COMMAND")
    print("=" * 60)
    print(f"Input:   {anime}")
    print(f"Season:  {season}")
    print(f"Episode: {episode}")
    print("=" * 60)

    try:

        data = get_staff(
            anime,
            season,
            episode,
        )

    except Exception as e:

        print(f"STAFF ERROR: {e!r}")

        await interaction.followup.send(
            "❌ Staff lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )
        return

    if not data:

        embed = discord.Embed(
            title="Episode Staff Credits",
            description=(
                f"**{anime}** — Season {season} "
                f"Episode {episode}\n\n"
                "**No relevant staff credits found.**"
            ),
            color=EMBED_COLOR,
        )

        embed.set_footer(
            text="Sakuga Staff"
        )

        await interaction.followup.send(
            embed=embed
        )
        return

    is_theme = episode.lower().startswith(("op", "ed"))

    if is_theme:
        title = (
            "Opening Staff"
            if episode.lower().startswith("op")
            else "Ending Staff"
        )
    else:
        title = "Episode Staff Credits"

    embed = discord.Embed(
        title=title,
        description=(
            f"**{anime}** — Season {season} "
            f"Episode {episode}"
        ),
        color=EMBED_COLOR,
    )

    add_staff_fields(
        embed,
        "🎬",
        "Storyboard",
        data.get("SB", []),
    )

    add_staff_fields(
        embed,
        "🎞️",
        "Episode Director",
        data.get("ED", []),
    )

    add_staff_fields(
        embed,
        "✏️",
        "Animation Director",
        data.get("AD", []),
    )

    add_staff_fields(
        embed,
        "🧩",
        "Assistant Animation Director",
        data.get("Ass. AD", []),
    )

    add_staff_fields(
        embed,
        "👑",
        "Chief Animation Director",
        data.get("CAD", []),
    )

    add_staff_fields(
        embed,
        "🎨",
        "Character Design",
        data.get("CD", []),
    )

    add_staff_fields(
        embed,
        "🔥",
        "Key Animation",
        data.get("KA", []),
    )

    second_ka = data.get("2KA", 0)

    if second_ka:

        embed.add_field(
            name="📝 2nd Key Animation",
            value=f"**{second_ka}**",
            inline=False,
        )

    add_staff_fields(
        embed,
        "🎵",
        "Artist",
        data.get("Artist", []),
    )

    embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    try:

        await interaction.followup.send(
            embed=embed
        )

    except discord.HTTPException:

        await interaction.followup.send(
            "❌ The staff list was too large."
        )


# ============================================================
# WORK COMMAND
# ============================================================

@bot.tree.command(
    name="work",
    description="Look up an animator's work in an anime",
)
@app_commands.describe(
    anime="Anime name or shortcut",
    animator="Animator name",
)
async def work(
    interaction: discord.Interaction,
    anime: str,
    animator: str,
):

    await interaction.response.defer()

    anime = anime.strip()
    animator = animator.strip()

    if not anime:

        await interaction.followup.send(
            "❌ Please enter an anime name."
        )
        return

    if not animator:

        await interaction.followup.send(
            "❌ Please enter an animator name."
        )
        return

    slug = get_anime_slug(anime)

    print()
    print("=" * 60)
    print("WORK DISCORD COMMAND")
    print("=" * 60)
    print(f"Anime:    {anime}")
    print(f"Slug:     {slug}")
    print(f"Animator: {animator}")
    print("=" * 60)

    try:

        works = await get_animator_works(
            animator,
            slug,
            anime_title=None,
        )

    except Exception as e:

        print(f"WORK ERROR: {e!r}")

        await interaction.followup.send(
            "❌ Work lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )
        return

    if not isinstance(works, dict):

        await interaction.followup.send(
            "❌ Work lookup returned invalid data."
        )
        return

    groups = normalize_work_groups(
        works.get("groups", {})
    )

    if not groups:

        anime_title = (
            works.get("anime")
            or anime
        )

        embed = discord.Embed(
            title=(
                f"{works.get('name') or animator} — "
                f"{anime_title}"
            ),
            description=(
                "No work found for this animator "
                "in this anime."
            ),
            color=EMBED_COLOR,
        )

        embed.set_footer(
            text="Sakuga Staff • KeyFrame / KFSL dataset"
        )

        await interaction.followup.send(
            embed=embed
        )
        return

    display_name = (
        works.get("name")
        or animator
    )

    anime_title = (
        works.get("anime")
        or anime
    )

    embed = discord.Embed(
        title=(
            f"{display_name} — "
            f"{anime_title}"
        ),
        color=EMBED_COLOR,
    )

    # ========================================================
    # MAIN STAFF
    # ========================================================

    if groups.get("Main Animator"):

        embed.add_field(
            name="📌 MAIN STAFF",
            value="**Main Animator:** Overview",
            inline=False,
        )

    # ========================================================
    # KEY ANIMATION
    # ========================================================

    key_animation = groups.get(
        "Key Animation"
    )

    if isinstance(
        key_animation,
        dict,
    ):

        key_episodes = key_animation.get(
            "episodes",
            [],
        )

    elif isinstance(
        key_animation,
        list,
    ):

        key_episodes = key_animation

    else:

        key_episodes = []

    key_text = format_work_episodes(
        key_episodes
    )

    if key_text:

        embed.add_field(
            name="🔥 KEY ANIMATION",
            value=(
                "**Key Animation**\n"
                f"KA: {key_text}"
            ),
            inline=False,
        )

    # ========================================================
    # OTHER STAFF
    #
    # KA is deliberately excluded.
    #
    # So:
    #
    # 🔥 KEY ANIMATION
    # Key Animation
    # KA: #17
    #
    # 🎬 OTHER STAFF
    # **Storyboard**
    # SB: #17, 17 (BD)
    #
    # ========================================================

    other_fields = []

    excluded_roles = {
        "Main Animator",
        "Key Animation",
    }

    for role, info in groups.items():

        if role in excluded_roles:
            continue

        # ----------------------------------------------------
        # Handle BOTH:
        #
        # list
        # dict
        # ----------------------------------------------------

        if isinstance(info, list):

            episodes = info

            role_short = ROLE_SHORT_NAMES.get(
                role,
                role,
            )

        elif isinstance(info, dict):

            episodes = info.get(
                "episodes",
                [],
            )

            role_short = info.get(
                "short",
                ROLE_SHORT_NAMES.get(
                    role,
                    role,
                ),
            )

        else:

            continue

        if not isinstance(
            episodes,
            list,
        ):

            episodes = [episodes]

        episode_text = format_work_episodes(
            episodes
        )

        if not episode_text:
            continue

        other_fields.append(
            (
                f"**{role}**\n"
                f"{role_short}: {episode_text}"
            )
        )

    # ========================================================
    # OTHER STAFF EMBED
    # ========================================================

    if other_fields:

        current = ""

        for field_text in other_fields:

            if (
                len(current)
                + len(field_text)
                + 2
                > 1024
            ):

                if current:

                    embed.add_field(
                        name="🎬 OTHER STAFF",
                        value=current,
                        inline=False,
                    )

                current = field_text

            else:

                if current:
                    current += (
                        "\n\n"
                        + field_text
                    )
                else:
                    current = field_text

        if current:

            embed.add_field(
                name="🎬 OTHER STAFF",
                value=current,
                inline=False,
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
            f"WORK EMBED ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ The work list was too large."
        )


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    print()
    print("=" * 60)
    print("SLASH COMMAND ERROR")
    print("=" * 60)
    print(repr(error))
    print("=" * 60)

    message = (
        "❌ Something went wrong while running "
        "that command."
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                message
            )

        else:

            await interaction.response.send_message(
                message
            )

    except Exception as e:

        print(
            f"ERROR HANDLER FAILED: {e!r}"
        )


# ============================================================
# RUN
# ============================================================

bot.run(TOKEN)
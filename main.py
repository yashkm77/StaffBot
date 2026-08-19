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

        # ----------------------------------------------------
        # Frieren
        # ----------------------------------------------------

        if alias_slug == "sousou-no-frieren-2nd-season":
            return 2

        # ----------------------------------------------------
        # My Hero Academia
        # ----------------------------------------------------

        for number in range(2, 8):

            if alias_slug == f"my-hero-academia-{number}":
                return number

        if alias_slug == "my-hero-academia-final-season":
            return 8

        # ----------------------------------------------------
        # Jujutsu Kaisen
        # ----------------------------------------------------

        if alias_slug == "jujutsu-kaisen":
            return 1

        if alias_slug == "jujutsu-kaisen-2nd-season":
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

        # ----------------------------------------------------
        # Bleach TYBW
        # ----------------------------------------------------

        if alias_slug == "bleach-thousand-year-blood-war":
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

        # ----------------------------------------------------
        # Mob Psycho 100
        # ----------------------------------------------------

        if alias_slug == "mob-psycho-100":
            return 1

        if alias_slug == "mob-psycho-100-ii":
            return 2

        if alias_slug == "mob-psycho-100-iii":
            return 3

        # ----------------------------------------------------
        # One Punch Man
        # ----------------------------------------------------

        if alias_slug == "one-punch-man":
            return 1

        if alias_slug == "one-punch-man-2":
            return 2

        if alias_slug == "one-punch-man-3":
            return 3

        # ----------------------------------------------------
        # Solo Leveling
        # ----------------------------------------------------

        if alias_slug == "solo-leveling":
            return 1

        if (
            alias_slug
            == "solo-leveling-season-2-arise-from-the-shadow"
        ):
            return 2

        # ----------------------------------------------------
        # Naruto
        # ----------------------------------------------------

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

    # If the user already entered a slug-like name,
    # convert spaces to hyphens.
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip("-")

    return slug


# ============================================================
# FORMAT NAMES
# ============================================================

def format_names(names):

    if not names:
        return None

    names = list(
        dict.fromkeys(names)
    )

    return ", ".join(
        str(name)
        for name in names
    )


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

    chunks = split_text(
        text,
        1024,
    )

    for index, chunk in enumerate(chunks):

        if index == 0:

            field_name = (
                f"{emoji} {title}"
            )

        else:

            field_name = (
                f"{emoji} {title} "
                "(continued)"
            )

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

    formatted = []

    seen = set()

    for episode in episodes:

        if episode is None:
            continue

        text = str(episode).strip()

        if not text:
            continue

        # ----------------------------------------------------
        # Opening / Ending
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

                formatted.append(
                    normalized
                )

                seen.add(normalized)

            continue

        # ----------------------------------------------------
        # Already formatted episode
        # ----------------------------------------------------

        if text.startswith("#"):

            if text not in seen:

                formatted.append(text)
                seen.add(text)

            continue

        # ----------------------------------------------------
        # Numeric episode
        # ----------------------------------------------------

        if text.isdigit():

            number = int(text)

            formatted_text = (
                f"#{number:02d}"
            )

            if formatted_text not in seen:

                formatted.append(
                    formatted_text
                )

                seen.add(formatted_text)

            continue

        # ----------------------------------------------------
        # Anything else
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

        # ----------------------------------------------------
        # Format 1:
        #
        # "Storyboard": [17]
        # ----------------------------------------------------

        if isinstance(info, list):

            episodes = info

            normalized_groups[role] = {
                "episodes": episodes,
                "short": ROLE_SHORT_NAMES.get(
                    role,
                    role,
                ),
            }

            continue

        # ----------------------------------------------------
        # Format 2:
        #
        # "Storyboard": {
        #     "episodes": [17],
        #     "short": "SB"
        # }
        # ----------------------------------------------------

        if isinstance(info, dict):

            episodes = info.get(
                "episodes",
                [],
            )

            short = info.get(
                "short",
                ROLE_SHORT_NAMES.get(
                    role,
                    role,
                ),
            )

            if not isinstance(
                episodes,
                list,
            ):

                episodes = [
                    episodes
                ]

            normalized_groups[role] = {
                "episodes": episodes,
                "short": short,
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

    # --------------------------------------------------------
    # EPISODE VALIDATION
    # --------------------------------------------------------

    episode = episode.strip()

    if not episode:

        await interaction.followup.send(
            "❌ Please enter an episode number or OP/ED.\n\n"
            "Examples:\n"
            "`1`\n"
            "`12`\n"
            "`op1`\n"
            "`op2`\n"
            "`ed1`\n"
            "`ed2`"
        )

        return

    if episode.isdigit():

        episode_number = int(episode)

        if episode_number < 1:

            await interaction.followup.send(
                "❌ Episode must be 1 or higher."
            )

            return

    else:

        normalized_episode = normalize(
            episode
        )

        if not re.fullmatch(
            r"(op|ed)\s*\d+",
            normalized_episode,
        ):

            await interaction.followup.send(
                "❌ Invalid episode.\n\n"
                "Use something like:\n"
                "`1`\n"
                "`12`\n"
                "`op1`\n"
                "`op2`\n"
                "`ed1`\n"
                "`ed2`"
            )

            return

    # --------------------------------------------------------
    # SEASON
    # --------------------------------------------------------

    season = detect_season(
        anime
    )

    print()
    print("=" * 60)
    print("STAFF DISCORD COMMAND")
    print("=" * 60)
    print(f"Input:   {anime}")
    print(f"Season:  {season}")
    print(f"Episode: {episode}")
    print("=" * 60)

    # --------------------------------------------------------
    # STAFF LOOKUP
    # --------------------------------------------------------

    try:

        data = get_staff(
            anime,
            season,
            episode,
        )

    except Exception as e:

        print(
            f"STAFF ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ Staff lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )

        return

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if not data:

        embed = discord.Embed(
            title="Episode Staff Credits",
            description=(
                f"**{anime}** — "
                f"Season {season} "
                f"Episode {episode}\n\n"
                "**No relevant staff credits "
                "found for this episode.**"
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

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    is_theme = (
        episode.lower().startswith(
            ("op", "ed")
        )
    )

    if is_theme:

        if episode.lower().startswith("op"):

            title = "Opening Staff"

        else:

            title = "Ending Staff"

    else:

        title = "Episode Staff Credits"

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    embed = discord.Embed(
        title=title,
        description=(
            f"**{anime}** — "
            f"Season {season} "
            f"Episode {episode}"
        ),
        color=EMBED_COLOR,
    )

    # --------------------------------------------------------
    # STORYBOARD
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🎬",
        "Storyboard",
        data.get(
            "SB",
            [],
        ),
    )

    # --------------------------------------------------------
    # EPISODE DIRECTOR
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🎞️",
        "Episode Director",
        data.get(
            "ED",
            [],
        ),
    )

    # --------------------------------------------------------
    # ANIMATION DIRECTOR
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "✏️",
        "Animation Director",
        data.get(
            "AD",
            [],
        ),
    )

    # --------------------------------------------------------
    # ASSISTANT ANIMATION DIRECTOR
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🧩",
        "Assistant Animation Director",
        data.get(
            "Ass. AD",
            [],
        ),
    )

    # --------------------------------------------------------
    # CHIEF ANIMATION DIRECTOR
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "👑",
        "Chief Animation Director",
        data.get(
            "CAD",
            [],
        ),
    )

    # --------------------------------------------------------
    # CHARACTER DESIGN
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🎨",
        "Character Design",
        data.get(
            "CD",
            [],
        ),
    )

    # --------------------------------------------------------
    # KEY ANIMATION
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🔥",
        "Key Animation",
        data.get(
            "KA",
            [],
        ),
    )

    # --------------------------------------------------------
    # 2ND KEY ANIMATION
    # --------------------------------------------------------

    second_ka = data.get(
        "2KA",
        0,
    )

    if second_ka:

        embed.add_field(
            name="📝 2nd Key Animation",
            value=f"**{second_ka}**",
            inline=False,
        )

    # --------------------------------------------------------
    # ARTIST
    # --------------------------------------------------------

    add_staff_fields(
        embed,
        "🎵",
        "Artist",
        data.get(
            "Artist",
            [],
        ),
    )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    try:

        await interaction.followup.send(
            embed=embed
        )

    except discord.HTTPException as e:

        print(
            f"EMBED ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ The staff list was too large "
            "to display in the embed."
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

    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GET SLUG
    # --------------------------------------------------------

    slug = get_anime_slug(
        anime
    )

    print()
    print("=" * 60)
    print("WORK DISCORD COMMAND")
    print("=" * 60)
    print(f"Anime:    {anime}")
    print(f"Slug:     {slug}")
    print(f"Animator: {animator}")
    print("=" * 60)

    # --------------------------------------------------------
    # WORK LOOKUP
    # --------------------------------------------------------

    try:

        works = await get_animator_works(
            animator,
            slug,
            anime_title=None,
        )

    except Exception as e:

        print(
            f"WORK ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ Work lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )

        return

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if not isinstance(
        works,
        dict,
    ):

        print(
            "WORK ERROR: get_animator_works "
            "returned invalid data."
        )

        await interaction.followup.send(
            "❌ Work lookup returned invalid data."
        )

        return

    # --------------------------------------------------------
    # GROUPS
    # --------------------------------------------------------

    groups = normalize_work_groups(
        works.get(
            "groups",
            {},
        )
    )

    # --------------------------------------------------------
    # NO WORK
    # --------------------------------------------------------

    if not groups:

        anime_title = (
            works.get(
                "anime"
            )
            or anime
        )

        embed = discord.Embed(
            title=(
                f"{animator} — "
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

    # --------------------------------------------------------
    # DISPLAY NAME
    # --------------------------------------------------------

    display_name = (
        works.get(
            "name"
        )
        or animator
    )

    anime_title = (
        works.get(
            "anime"
        )
        or anime
    )

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

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

    main_staff = groups.get(
        "Main Animator"
    )

    if main_staff:

        embed.add_field(
            name="📌 MAIN STAFF",
            value=(
                "**Main Animator:** "
                "Overview"
            ),
            inline=False,
        )

    # ========================================================
    # KEY ANIMATION
    # ========================================================

    key_animation = groups.get(
        "Key Animation"
    )

    if key_animation:

        key_episodes = key_animation.get(
            "episodes",
            [],
        )

        episode_text = format_work_episodes(
            key_episodes
        )

        if episode_text:

            embed.add_field(
                name="🔥 KEY ANIMATION",
                value=(
                    "**Key Animation**\n"
                    f"KA: {episode_text}"
                ),
                inline=False,
            )

    # ========================================================
    # OTHER STAFF
    # ========================================================

    other_fields = []

    for role, info in groups.items():

        # Already displayed
        if role in (
            "Main Animator",
            "Key Animation",
        ):
            continue

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Some versions of work_scraper return:
        #
        # "Storyboard": [17]
        #
        # Other versions return:
        #
        # "Storyboard": {
        #     "episodes": [17],
        #     "short": "SB"
        # }
        #
        # Handle BOTH.
        # ----------------------------------------------------

        if isinstance(
            info,
            list,
        ):

            episodes = info

            role_short = ROLE_SHORT_NAMES.get(
                role,
                role,
            )

        elif isinstance(
            info,
            dict,
        ):

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

        if not episodes:
            continue

        episode_text = format_work_episodes(
            episodes
        )

        if not episode_text:
            continue

        field_text = (
            f"**{role}**\n"
            f"{role_short}: {episode_text}"
        )

        other_fields.append(
            field_text
        )

    # ========================================================
    # ADD OTHER STAFF
    # ========================================================

    if other_fields:

        current = ""

        for field_text in other_fields:

            # ------------------------------------------------
            # Discord field value limit = 1024
            # ------------------------------------------------

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
            "❌ The work list was too large "
            "to display in the embed."
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

    # --------------------------------------------------------
    # Don't try to respond twice if Discord already received
    # a response.
    # --------------------------------------------------------

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
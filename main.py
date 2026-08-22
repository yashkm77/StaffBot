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

    normalized = normalize(
        anime
    )

    if normalized in ANIME_ALIASES:

        alias_slug = ANIME_ALIASES[
            normalized
        ]

        # Frieren
        if alias_slug == (
            "sousou-no-frieren-2nd-season"
        ):

            return 2

        # My Hero Academia
        for number in range(
            2,
            8,
        ):

            if alias_slug == (
                f"my-hero-academia-{number}"
            ):

                return number

        if alias_slug == (
            "my-hero-academia-final-season"
        ):

            return 8

        # Jujutsu Kaisen
        if alias_slug == "jujutsu-kaisen":

            return 1

        if alias_slug == (
            "jujutsu-kaisen-2nd-season"
        ):

            return 2

        if alias_slug == (
            "jujutsu-kaisen-3rd-season-culling-game-part-1"
        ):

            return 3

        if alias_slug == (
            "jujutsu-kaisen-4th-season-culling-game-part-2"
        ):

            return 4

        # Bleach TYBW
        if alias_slug == (
            "bleach-thousand-year-blood-war"
        ):

            return 1

        if alias_slug == (
            "bleach-thousand-year-blood-war-the-separation"
        ):

            return 2

        if alias_slug == (
            "bleach-thousand-year-blood-war-the-conflict"
        ):

            return 3

        if alias_slug == (
            "bleach-thousand-year-blood-war-the-calamity"
        ):

            return 4

        # Mob Psycho 100
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

        if alias_slug == (
            "solo-leveling-season-2-arise-from-the-shadow"
        ):

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

            return int(
                match.group(1)
            )

        except ValueError:

            pass

    return 1


# ============================================================
# GET ANIME SLUG
# ============================================================

def get_anime_slug(anime):

    normalized = normalize(
        anime
    )

    if normalized in ANIME_ALIASES:

        return ANIME_ALIASES[
            normalized
        ]

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip("-")

    return slug


# ============================================================
# GET ALL ANIME SEASONS
# ============================================================

def get_all_anime_seasons(anime):

    """
    If the user enters the base anime, return every known
    season.

    If the user enters a specific season, return only that
    season.

    Example:

        Jujutsu Kaisen
        -> all known JJK seasons

        Jujutsu Kaisen 2nd Season
        -> Season 2 only
    """

    normalized = normalize(
        anime
    )

    # ========================================================
    # JUJUTSU KAISEN
    # ========================================================

    if normalized in (
        "jujutsu kaisen",
        "jjk",
    ):

        return [
            (
                "Jujutsu Kaisen",
                "jujutsu-kaisen",
            ),

            (
                "Jujutsu Kaisen 2nd Season",
                "jujutsu-kaisen-2nd-season",
            ),

            (
                "Jujutsu Kaisen 3rd Season: Culling Game Part 1",
                "jujutsu-kaisen-3rd-season-culling-game-part-1",
            ),

            (
                "Jujutsu Kaisen 4th Season: Culling Game Part 2",
                "jujutsu-kaisen-4th-season-culling-game-part-2",
            ),
        ]

    # ========================================================
    # MY HERO ACADEMIA
    # ========================================================

    if normalized in (
        "my hero academia",
        "mha",
        "boku no hero academia",
    ):

        return [
            (
                "My Hero Academia",
                "my-hero-academia",
            ),

            (
                "My Hero Academia Season 2",
                "my-hero-academia-2",
            ),

            (
                "My Hero Academia Season 3",
                "my-hero-academia-3",
            ),

            (
                "My Hero Academia Season 4",
                "my-hero-academia-4",
            ),

            (
                "My Hero Academia Season 5",
                "my-hero-academia-5",
            ),

            (
                "My Hero Academia Season 6",
                "my-hero-academia-6",
            ),

            (
                "My Hero Academia Season 7",
                "my-hero-academia-7",
            ),

            (
                "My Hero Academia Final Season",
                "my-hero-academia-final-season",
            ),
        ]

    # ========================================================
    # BLEACH TYBW
    # ========================================================

    if normalized in (
        "bleach thousand year blood war",
        "bleach tybw",
        "tybw",
    ):

        return [
            (
                "Bleach: Thousand-Year Blood War",
                "bleach-thousand-year-blood-war",
            ),

            (
                "Bleach: Thousand-Year Blood War – The Separation",
                "bleach-thousand-year-blood-war-the-separation",
            ),

            (
                "Bleach: Thousand-Year Blood War – The Conflict",
                "bleach-thousand-year-blood-war-the-conflict",
            ),

            (
                "Bleach: Thousand-Year Blood War – The Calamity",
                "bleach-thousand-year-blood-war-the-calamity",
            ),
        ]

    # ========================================================
    # MOB PSYCHO 100
    # ========================================================

    if normalized in (
        "mob psycho 100",
        "mob psycho",
    ):

        return [
            (
                "Mob Psycho 100",
                "mob-psycho-100",
            ),

            (
                "Mob Psycho 100 II",
                "mob-psycho-100-ii",
            ),

            (
                "Mob Psycho 100 III",
                "mob-psycho-100-iii",
            ),
        ]

    # ========================================================
    # ONE PUNCH MAN
    # ========================================================

    if normalized in (
        "one punch man",
        "opm",
    ):

        return [
            (
                "One Punch Man",
                "one-punch-man",
            ),

            (
                "One Punch Man Season 2",
                "one-punch-man-2",
            ),

            (
                "One Punch Man Season 3",
                "one-punch-man-3",
            ),
        ]

    # ========================================================
    # SOLO LEVELING
    # ========================================================

    if normalized in (
        "solo leveling",
    ):

        return [
            (
                "Solo Leveling",
                "solo-leveling",
            ),

            (
                "Solo Leveling Season 2",
                "solo-leveling-season-2-arise-from-the-shadow",
            ),
        ]

    # ========================================================
    # DEFAULT
    #
    # Specific anime/season.
    # ========================================================

    return [
        (
            anime,
            get_anime_slug(
                anime
            ),
        )
    ]


# ============================================================
# FORMAT NAMES
# ============================================================

def format_names(names):

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
    limit=1024,
):

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

        elif (
            len(current)
            + len(piece)
            + 2
            <= limit
        ):

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
    names,
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
        1024,
    )

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

def format_work_episodes(
    episodes
):

    if not episodes:
        return ""

    formatted = []

    seen = set()

    for episode in episodes:

        if episode is None:
            continue

        text = str(
            episode
        ).strip()

        if not text:
            continue

        # OP / ED
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

                seen.add(
                    normalized
                )

            continue

        # Already formatted
        if text.startswith("#"):

            if text not in seen:

                formatted.append(
                    text
                )

                seen.add(
                    text
                )

            continue

        # Numeric episode
        if text.isdigit():

            number = int(
                text
            )

            formatted_text = (
                f"#{number:02d}"
            )

            if (
                formatted_text
                not in seen
            ):

                formatted.append(
                    formatted_text
                )

                seen.add(
                    formatted_text
                )

            continue

        # Anything else
        if text not in seen:

            formatted.append(
                text
            )

            seen.add(
                text
            )

    return ", ".join(
        formatted
    )


# ============================================================
# NORMALIZE WORK GROUPS
# ============================================================

def normalize_work_groups(
    groups
):

    if not isinstance(
        groups,
        dict,
    ):

        return {}

    normalized_groups = {}

    for role, info in groups.items():

        if not role:
            continue

        if isinstance(
            info,
            list,
        ):

            normalized_groups[role] = info

            continue

        if isinstance(
            info,
            dict,
        ):

            episodes = info.get(
                "episodes",
                [],
            )

            if not isinstance(
                episodes,
                list,
            ):

                episodes = [
                    episodes
                ]

            normalized_groups[role] = episodes

    return normalized_groups


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

        episode_number = int(
            episode
        )

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

    is_theme = episode.lower().startswith(
        ("op", "ed")
    )

    if is_theme:

        if episode.lower().startswith(
            "op"
        ):

            title = "Opening Staff"

        else:

            title = "Ending Staff"

    else:

        title = "Episode Staff Credits"

    embed = discord.Embed(
        title=title,
        description=(
            f"**{anime}** — "
            f"Season {season} "
            f"Episode {episode}"
        ),
        color=EMBED_COLOR,
    )

    add_staff_fields(
        embed,
        "🎬",
        "Storyboard",
        data.get(
            "SB",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "🎞️",
        "Episode Director",
        data.get(
            "ED",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "✏️",
        "Animation Director",
        data.get(
            "AD",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "🧩",
        "Assistant Animation Director",
        data.get(
            "Ass. AD",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "👑",
        "Chief Animation Director",
        data.get(
            "CAD",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "🎨",
        "Character Design",
        data.get(
            "CD",
            [],
        ),
    )

    add_staff_fields(
        embed,
        "🔥",
        "Key Animation",
        data.get(
            "KA",
            [],
        ),
    )

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

    add_staff_fields(
        embed,
        "🎵",
        "Artist",
        data.get(
            "Artist",
            [],
        ),
    )

    embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    try:

        await interaction.followup.send(
            embed=embed
        )

    except discord.HTTPException as e:

        print(
            f"EMBED ERROR: {e!r}"
        )


# ============================================================
# WORK COMMAND
# ============================================================

@bot.tree.command(
    name="work",
    description="Look up an animator's work in an anime",
)
@app_commands.describe(
    anime="Anime name, shortcut, or specific season",
    animator="Animator name",
)
async def work(
    interaction: discord.Interaction,
    anime: str,
    animator: str,
):

    # ========================================================
    # ACKNOWLEDGE IMMEDIATELY
    # ========================================================

    await interaction.response.defer()

    # ========================================================
    # CLEAN INPUT
    # ========================================================

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

    # ========================================================
    # GET SEASONS
    # ========================================================

    anime_seasons = get_all_anime_seasons(
        anime
    )

    print()

    print(
        "=" * 60
    )

    print(
        "WORK DISCORD COMMAND"
    )

    print(
        "=" * 60
    )

    print(
        f"Anime:    {anime}"
    )

    print(
        f"Animator: {animator}"
    )

    print(
        "Seasons:"
    )

    for season_title, season_slug in anime_seasons:

        print(
            f"  - {season_title}"
            f" -> {season_slug}"
        )

    print(
        "=" * 60
    )

    # ========================================================
    # SEARCH ALL SEASONS
    # ========================================================

    all_groups = {}

    display_name = animator

    try:

        for season_title, season_slug in anime_seasons:

            print()

            print(
                f"Searching: {season_title}"
            )

            season_works = await get_animator_works(
                animator,
                season_slug,
                anime_title=season_title,
            )

            if not isinstance(
                season_works,
                dict,
            ):

                continue

            if season_works.get(
                "found"
            ):

                display_name = (
                    season_works.get(
                        "name"
                    )
                    or display_name
                )

                groups = normalize_work_groups(
                    season_works.get(
                        "groups",
                        {},
                    )
                )

                if groups:

                    all_groups[
                        season_title
                    ] = groups

    except Exception as e:

        print(
            f"WORK ERROR: {e!r}"
        )

        await interaction.followup.send(
            "❌ Work lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )

        return

    # ========================================================
    # NO WORK
    # ========================================================

    if not all_groups:

        embed = discord.Embed(
            title=(
                f"{display_name} — "
                f"{anime}"
            ),
            description=(
                "No work found for this animator "
                "in the searched anime."
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

    # ========================================================
    # CREATE EMBED
    # ========================================================

    embed = discord.Embed(
        title=(
            f"{display_name} — "
            f"{anime}"
        ),
        color=EMBED_COLOR,
    )

    # ========================================================
    # DISPLAY EACH SEASON
    # ========================================================

    for season_title, groups in all_groups.items():

        season_lines = []

        # ----------------------------------------------------
        # MAIN ANIMATOR
        # ----------------------------------------------------

        main_staff = groups.get(
            "Main Animator"
        )

        if main_staff:

            season_lines.append(
                "**Main Animator:** Overview"
            )

        # ----------------------------------------------------
        # KEY ANIMATION
        # ----------------------------------------------------

        key_animation = groups.get(
            "Key Animation",
            [],
        )

        if key_animation:

            episode_text = format_work_episodes(
                key_animation
            )

            if episode_text:

                season_lines.append(
                    "**Key Animation**\n"
                    f"KA: {episode_text}"
                )

        # ----------------------------------------------------
        # STORYBOARD
        # ----------------------------------------------------

        storyboard = groups.get(
            "Storyboard",
            [],
        )

        if storyboard:

            episode_text = format_work_episodes(
                storyboard
            )

            if episode_text:

                season_lines.append(
                    "**Storyboard**\n"
                    f"SB: {episode_text}"
                )

        # ----------------------------------------------------
        # OTHER STAFF
        # ----------------------------------------------------

        OTHER_STAFF_ROLES = [

            "Episode Director",

            "Animation Director",

            "Assistant Animation Director",

            "Chief Animation Director",

            "2nd Key Animation",

            "Character Design",

            "Art Director",

            "Art Board",

            "Storyboard / Episode Director",

        ]

        for role in OTHER_STAFF_ROLES:

            info = groups.get(
                role
            )

            if not info:
                continue

            if isinstance(
                info,
                list,
            ):

                episodes = info

            elif isinstance(
                info,
                dict,
            ):

                episodes = info.get(
                    "episodes",
                    [],
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

            role_short = ROLE_SHORT_NAMES.get(
                role,
                role,
            )

            season_lines.append(
                f"**{role}**\n"
                f"{role_short}: {episode_text}"
            )

        # ----------------------------------------------------
        # ADD SEASON FIELD
        # ----------------------------------------------------

        if season_lines:

            value = "\n\n".join(
                season_lines
            )

            chunks = split_text(
                value,
                1024,
            )

            for index, chunk in enumerate(
                chunks
            ):

                if index == 0:

                    field_name = (
                        f"📺 {season_title}"
                    )

                else:

                    field_name = (
                        f"📺 {season_title} "
                        "(continued)"
                    )

                embed.add_field(
                    name=field_name,
                    value=chunk,
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


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    print()

    print(
        "=" * 60
    )

    print(
        "SLASH COMMAND ERROR"
    )

    print(
        "=" * 60
    )

    print(
        repr(error)
    )

    print(
        "=" * 60
    )

    message = (
        "❌ Something went wrong while running "
        "that command."
    )

    try:

        # ----------------------------------------------------
        # Interaction already acknowledged
        # ----------------------------------------------------

        if interaction.response.is_done():

            try:

                await interaction.followup.send(
                    message
                )

            except discord.HTTPException as followup_error:

                print(
                    f"FOLLOWUP ERROR: "
                    f"{followup_error!r}"
                )

        # ----------------------------------------------------
        # Interaction has NOT been acknowledged
        # ----------------------------------------------------

        else:

            try:

                await interaction.response.send_message(
                    message
                )

            except discord.HTTPException as response_error:

                print(
                    f"RESPONSE ERROR: "
                    f"{response_error!r}"
                )

    except Exception as e:

        print(
            f"ERROR HANDLER FAILED: {e!r}"
        )


# ============================================================
# RUN
# ============================================================

bot.run(
    TOKEN
)
import os
import re
import json 

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
    get_animator_works_all,
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
# ANIME INDEX
# ============================================================

ANIME_INDEX_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "anime_index.json",
)


def load_anime_index():

    if not os.path.exists(ANIME_INDEX_FILE):

        print(
            f"WARNING: {ANIME_INDEX_FILE} not found."
        )

        return {}

    try:

        with open(
            ANIME_INDEX_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):

            print(
                "WARNING: anime_index.json is not a dictionary."
            )

            return {}

        return data

    except Exception as e:

        print(
            f"ERROR loading anime_index.json: {e}"
        )

        return {}


ANIME_INDEX = load_anime_index()


# ============================================================
# ANIME INDEX NORMALIZED LOOKUP
# ============================================================

def build_anime_index_normalized():

    normalized_index = {}

    for name, slug in ANIME_INDEX.items():

        normalized_name = normalize(
            name
        )

        if not normalized_name:
            continue

        normalized_index.setdefault(
            normalized_name,
            set(),
        ).add(
            str(slug).strip()
        )

    return normalized_index


ANIME_INDEX_NORMALIZED = (
    build_anime_index_normalized()
)


# ============================================================
# GET ANIME SLUG
# ============================================================

def get_anime_slug(anime):

    normalized = normalize(
        anime
    )

    # --------------------------------------------------------
    # Exact anime_index.json match
    # --------------------------------------------------------

    if normalized in ANIME_INDEX_NORMALIZED:

        slugs = ANIME_INDEX_NORMALIZED[
            normalized
        ]

        if slugs:

            return sorted(
                slugs
            )[0]

    # --------------------------------------------------------
    # Existing manual aliases
    # --------------------------------------------------------

    if normalized in ANIME_ALIASES:

        return ANIME_ALIASES[
            normalized
        ]

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    return re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip("-")


# ============================================================
# FIND ALL ANIME ENTRIES
# ============================================================

def get_all_anime_seasons(
    anime
):

    """
    Find all KFSL anime slugs related to the user's input.

    anime_index.json is the primary source.

    Examples:

        mha
        my hero academia
        my hero academia 3

        jojo
        jojo part 3
        jojo stone ocean

        jjk
        jujutsu kaisen
    """

    normalized_input = normalize(
        anime
    )

    if not normalized_input:

        return []

    candidates = {}

    # ========================================================
    # 1. EXACT INDEX MATCH
    # ========================================================

    exact_matches = (
        ANIME_INDEX_NORMALIZED.get(
            normalized_input,
            set(),
        )
    )

    for slug in exact_matches:

        if slug:

            candidates[
                slug
            ] = normalized_input

    # ========================================================
    # 2. MANUAL ALIAS
    # ========================================================

    if normalized_input in ANIME_ALIASES:

        slug = ANIME_ALIASES[
            normalized_input
        ]

        if slug:

            candidates[
                slug
            ] = normalized_input

    # ========================================================
    # 3. PREFIX / CONTAINMENT SEARCH
    # ========================================================

    # Only do broader matching when there was no exact
    # result. This prevents "my hero academia 3" from
    # accidentally returning every MHA entry.

    if not candidates:

        for name, slug in ANIME_INDEX.items():

            normalized_name = normalize(
                name
            )

            if not normalized_name:
                continue

            # ------------------------------------------------
            # Exact word-based containment
            # ------------------------------------------------

            if (
                normalized_input
                in normalized_name
            ):

                candidates[
                    str(slug).strip()
                ] = normalized_name

                continue

            # ------------------------------------------------
            # Reverse containment
            # ------------------------------------------------

            if (
                normalized_name
                in normalized_input
            ):

                candidates[
                    str(slug).strip()
                ] = normalized_name

    # ========================================================
    # 4. SPECIAL FRANCHISE SHORTCUTS
    # ========================================================

    franchise_aliases = {

        "mha": [
            "my hero academia",
            "boku no hero academia",
        ],

        "bnha": [
            "my hero academia",
            "boku no hero academia",
        ],

        "jjk": [
            "jujutsu kaisen",
        ],

        "jojo": [
            "jojo",
            "jojo's bizarre adventure",
            "jojo s bizarre adventure",
            "jojo no kimyou na bouken",
        ],

    }

    if normalized_input in franchise_aliases:

        keywords = franchise_aliases[
            normalized_input
        ]

        for name, slug in ANIME_INDEX.items():

            normalized_name = normalize(
                name
            )

            for keyword in keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_keyword
                    in normalized_name
                ):

                    candidates[
                        str(slug).strip()
                    ] = normalized_name

                    break

    # ========================================================
    # 5. FALLBACK SLUG
    # ========================================================

    if not candidates:

        fallback = get_anime_slug(
            anime
        )

        if fallback:

            candidates[
                fallback
            ] = normalized_input

    # ========================================================
    # REMOVE EMPTY / DUPLICATES
    # ========================================================

    slugs = list(
        dict.fromkeys(
            slug
            for slug in candidates.keys()
            if slug
        )
    )

    # ========================================================
    # SORT
    # ========================================================

    def sort_key(slug):

        text = str(
            slug
        ).lower()

        # Numeric season

        match = re.search(
            r"-(\d+)(?:$|-)",
            text,
        )

        if match:

            try:

                return (
                    0,
                    int(
                        match.group(1)
                    ),
                    text,
                )

            except ValueError:

                pass

        # Ordinal season

        match = re.search(
            r"-(\d+)(?:st|nd|rd|th)-season",
            text,
        )

        if match:

            try:

                return (
                    0,
                    int(
                        match.group(1)
                    ),
                    text,
                )

            except ValueError:

                pass

        # Normal entry

        return (
            1,
            9999,
            text,
        )

    slugs.sort(
        key=sort_key
    )

    return slugs


# ============================================================
# DISPLAY TITLE
# ============================================================

def get_anime_display_title(
    slug
):

    # --------------------------------------------------------
    # Prefer a human-readable name from anime_index.json.
    # --------------------------------------------------------

    possible_names = []

    for name, indexed_slug in ANIME_INDEX.items():

        if str(indexed_slug).strip() != str(slug).strip():
            continue

        normalized_name = normalize(
            name
        )

        if not normalized_name:
            continue

        # Prefer English-looking names.

        if re.search(
            r"[a-z]",
            name,
            re.IGNORECASE,
        ):

            possible_names.append(
                name
            )

    if possible_names:

        # Prefer the shortest readable English name.

        possible_names.sort(
            key=lambda x: (
                len(x),
                x.lower(),
            )
        )

        return possible_names[0].strip()

    # --------------------------------------------------------
    # Existing known titles
    # --------------------------------------------------------

    known_titles = {

        "jujutsu-kaisen":
            "Jujutsu Kaisen",

        "jujutsu-kaisen-2nd-season":
            "Jujutsu Kaisen 2nd Season",

        "jujutsu-kaisen-3rd-season-culling-game-part-1":
            "Jujutsu Kaisen 3rd Season: Culling Game Part 1",

        "jujutsu-kaisen-4th-season-culling-game-part-2":
            "Jujutsu Kaisen 4th Season: Culling Game Part 2",

        "sousou-no-frieren-2nd-season":
            "Frieren: Beyond Journey's End 2nd Season",

        "my-hero-academia-final-season":
            "My Hero Academia Final Season",

        "bleach-thousand-year-blood-war":
            "Bleach: Thousand-Year Blood War",

        "bleach-thousand-year-blood-war-the-separation":
            "Bleach: Thousand-Year Blood War — The Separation",

        "bleach-thousand-year-blood-war-the-conflict":
            "Bleach: Thousand-Year Blood War — The Conflict",

        "bleach-thousand-year-blood-war-the-calamity":
            "Bleach: Thousand-Year Blood War — The Calamity",

    }

    if slug in known_titles:

        return known_titles[
            slug
        ]

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    return (
        str(slug)
        .replace(
            "-",
            " ",
        )
        .title()
    )


# ============================================================
# DISPLAY TITLE
# ============================================================

def get_anime_display_title(
    slug
):

    """
    Convert a slug into a readable title.

    Known aliases are preferred.
    """

    # --------------------------------------------------------
    # Special known titles.
    # --------------------------------------------------------

    known_titles = {

        "jujutsu-kaisen":
            "Jujutsu Kaisen",

        "jujutsu-kaisen-2nd-season":
            "Jujutsu Kaisen 2nd Season",

        "jujutsu-kaisen-3rd-season-culling-game-part-1":
            "Jujutsu Kaisen 3rd Season: Culling Game Part 1",

        "jujutsu-kaisen-4th-season-culling-game-part-2":
            "Jujutsu Kaisen 4th Season: Culling Game Part 2",

        "sousou-no-frieren-2nd-season":
            "Frieren: Beyond Journey's End 2nd Season",

        "my-hero-academia-final-season":
            "My Hero Academia Final Season",

        "bleach-thousand-year-blood-war":
            "Bleach: Thousand-Year Blood War",

        "bleach-thousand-year-blood-war-the-separation":
            "Bleach: Thousand-Year Blood War — The Separation",

        "bleach-thousand-year-blood-war-the-conflict":
            "Bleach: Thousand-Year Blood War — The Conflict",

        "bleach-thousand-year-blood-war-the-calamity":
            "Bleach: Thousand-Year Blood War — The Calamity",

    }

    if slug in known_titles:

        return known_titles[
            slug
        ]

    # --------------------------------------------------------
    # Generic fallback.
    # --------------------------------------------------------

    return (
        slug
        .replace(
            "-",
            " ",
        )
        .title()
    )


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

                formatted.append(
                    normalized
                )

                seen.add(
                    normalized
                )

            continue

        # ----------------------------------------------------
        # Already formatted
        # ----------------------------------------------------

        if text.startswith("#"):

            if text not in seen:

                formatted.append(
                    text
                )

                seen.add(
                    text
                )

            continue

        # ----------------------------------------------------
        # Numeric episode
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Anything else
        # ----------------------------------------------------

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
            "❌ Please enter an episode number or OP/ED."
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
                "Use something like `1`, `12`, `op1`, `op2`, `ed1`, `ed2`."
            )

            return

    try:

        # Existing staff command uses season detection
        # from the first/current season system.

        season = get_season_number(
            get_anime_slug(
                anime
            )
        )

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

    is_theme = episode.lower().startswith(
        ("op", "ed")
    )

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
            f"**{anime}** — "
            f"Season {season} "
            f"Episode {episode}"
        ),
        color=EMBED_COLOR,
    )

    # --------------------------------------------------------
    # STORYBOARD
    # --------------------------------------------------------

    if data.get("SB"):

        embed.add_field(
            name="🎬 Storyboard",
            value=format_names(
                data.get(
                    "SB",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # EPISODE DIRECTOR
    # --------------------------------------------------------

    if data.get("ED"):

        embed.add_field(
            name="🎞️ Episode Director",
            value=format_names(
                data.get(
                    "ED",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # AD
    # --------------------------------------------------------

    if data.get("AD"):

        embed.add_field(
            name="✏️ Animation Director",
            value=format_names(
                data.get(
                    "AD",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # ASS AD
    # --------------------------------------------------------

    if data.get("Ass. AD"):

        embed.add_field(
            name="🧩 Assistant Animation Director",
            value=format_names(
                data.get(
                    "Ass. AD",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # CAD
    # --------------------------------------------------------

    if data.get("CAD"):

        embed.add_field(
            name="👑 Chief Animation Director",
            value=format_names(
                data.get(
                    "CAD",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # CHARACTER DESIGN
    # --------------------------------------------------------

    if data.get("CD"):

        embed.add_field(
            name="🎨 Character Design",
            value=format_names(
                data.get(
                    "CD",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # KA
    # --------------------------------------------------------

    if data.get("KA"):

        embed.add_field(
            name="🔥 Key Animation",
            value=format_names(
                data.get(
                    "KA",
                    [],
                )
            ),
            inline=False,
        )

    # --------------------------------------------------------
    # 2KA
    # --------------------------------------------------------

    if data.get("2KA"):

        embed.add_field(
            name="📝 2nd Key Animation",
            value=f"**{data['2KA']}**",
            inline=False,
        )

    # --------------------------------------------------------
    # ARTIST
    # --------------------------------------------------------

    if data.get("Artist"):

        embed.add_field(
            name="🎵 Artist",
            value=format_names(
                data.get(
                    "Artist",
                    [],
                )
            ),
            inline=False,
        )

    embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    await interaction.followup.send(
        embed=embed
    )


# ============================================================
# WORK COMMAND
# ============================================================

@bot.tree.command(
    name="work",
    description="Look up an animator's work across an anime franchise",
)
@app_commands.describe(
    anime="Anime name, franchise, or shortcut",
    animator="Animator name",
)
async def work(
    interaction: discord.Interaction,
    anime: str,
    animator: str,
):

    # ========================================================
    # ACKNOWLEDGE ONCE
    # ========================================================

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

    # ========================================================
    # FIND ALL SEASONS
    # ========================================================

    season_slugs = get_all_anime_seasons(
        anime
    )

    if not season_slugs:

        await interaction.followup.send(
            "❌ I couldn't determine the anime franchise."
        )

        return

    anime_list = []

    for slug in season_slugs:

        anime_list.append({

            "slug": slug,

            "title": get_anime_display_title(
                slug
            ),

        })

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
        f"Input:    {anime}"
    )

    print(
        f"Animator: {animator}"
    )

    print(
        "Seasons:"
    )

    for item in anime_list:

        print(
            f"  - {item['title']}"
            f" -> {item['slug']}"
        )

    print(
        "=" * 60
    )

    # ========================================================
    # LOOK UP ALL SEASONS
    # ========================================================

    try:

        season_results = await get_animator_works_all(
            animator,
            anime_list,
        )

    except Exception as e:

        print(
            f"WORK ERROR: {e!r}"
        )

        # IMPORTANT:
        # We already deferred the interaction.
        # Therefore we ONLY use followup here.

        await interaction.followup.send(
            "❌ Work lookup encountered an error.\n"
            f"`{type(e).__name__}: {e}`"
        )

        return

    # ========================================================
    # NO RESULTS
    # ========================================================

    if not season_results:

        embed = discord.Embed(
            title=(
                f"{animator} — "
                f"{anime}"
            ),
            description=(
                "No work found for this animator "
                "in the detected anime seasons."
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
    # DISPLAY NAME
    # ========================================================

    display_name = (
        season_results[0].get(
            "name"
        )
        or animator
    )

    # ========================================================
    # CREATE EMBED
    # ========================================================

    embed = discord.Embed(
        title=display_name,
        description=(
            f"**{anime}**\n"
            "Animator work across all detected seasons"
        ),
        color=EMBED_COLOR,
    )

    # ========================================================
    # BUILD EACH SEASON
    # ========================================================

    for season_result in season_results:

        anime_title = (
            season_result.get(
                "anime"
            )
            or "Unknown Anime"
        )

        groups = season_result.get(
            "groups",
            {},
        )

        if not groups:
            continue

        # ----------------------------------------------------
        # SEASON HEADER
        # ----------------------------------------------------

        season_text_parts = []

        # ----------------------------------------------------
        # MAIN ANIMATOR
        # ----------------------------------------------------

        main_animator = groups.get(
            "Main Animator",
            [],
        )

        if main_animator:

            season_text_parts.append(
                "**Main Animator:** "
                "Overview"
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

                season_text_parts.append(
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

                season_text_parts.append(
                    "**Storyboard**\n"
                    f"SB: {episode_text}"
                )

        # ----------------------------------------------------
        # OTHER STAFF
        # ----------------------------------------------------

        other_staff_roles = [

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

        for role in other_staff_roles:

            episodes = groups.get(
                role
            )

            if not episodes:
                continue

            if not isinstance(
                episodes,
                list,
            ):

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

            season_text_parts.append(
                f"**{role}**\n"
                f"{role_short}: {episode_text}"
            )

        # ----------------------------------------------------
        # NOTHING TO DISPLAY
        # ----------------------------------------------------

        if not season_text_parts:
            continue

        # ----------------------------------------------------
        # ADD SEASON FIELD
        # ----------------------------------------------------

        season_text = "\n\n".join(
            season_text_parts
        )

        chunks = split_text(
            season_text,
            1024,
        )

        for index, chunk in enumerate(
            chunks
        ):

            if index == 0:

                field_name = (
                    f"📺 {anime_title}"
                )

            else:

                field_name = (
                    f"📺 {anime_title} "
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

        # Since the interaction was deferred,
        # use followup only.

        try:

            await interaction.followup.send(
                "❌ The work list was too large "
                "to display in the embed."
            )

        except Exception as followup_error:

            print(
                f"FOLLOWUP ERROR: "
                f"{followup_error!r}"
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
        # If interaction was already acknowledged/deferred,
        # NEVER call response.send_message().
        # ----------------------------------------------------

        if interaction.response.is_done():

            await interaction.followup.send(
                message
            )

        else:

            await interaction.response.send_message(
                message
            )

    except discord.HTTPException as e:

        print(
            f"ERROR HANDLER HTTP ERROR: {e!r}"
        )

    except Exception as e:

        print(
            f"ERROR HANDLER FAILED: {e!r}"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    bot.run(TOKEN)
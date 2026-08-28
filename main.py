import os
import re
import json
import glob

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
# NORMALIZED ANIME INDEX
# ============================================================

def build_anime_index_normalized():

    normalized_index = {}

    for name, slug in ANIME_INDEX.items():

        normalized_name = normalize(name)

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

    normalized = normalize(anime)

    if not normalized:
        return ""

    # --------------------------------------------------------
    # Exact anime_index match
    # --------------------------------------------------------

    if normalized in ANIME_INDEX_NORMALIZED:

        slugs = ANIME_INDEX_NORMALIZED[
            normalized
        ]

        if slugs:

            return sorted(slugs)[0]

    # --------------------------------------------------------
    # Manual aliases
    # --------------------------------------------------------

    if normalized in ANIME_ALIASES:

        alias = ANIME_ALIASES[
            normalized
        ]

        if isinstance(
            alias,
            (list, tuple, set)
        ):

            if alias:
                return str(
                    sorted(alias)[0]
                ).strip()

        elif alias:

            return str(alias).strip()

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    return re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip("-")


# ============================================================
# SEASON NUMBER HELPER
# ============================================================

def get_season_number(slug):

    if not slug:
        return 1

    text = normalize(
        str(slug)
    )

    # --------------------------------------------------------
    # 2nd / 3rd / 4th season
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d+)(?:st|nd|rd|th)\s+season\b",
        text,
    )

    if match:

        try:
            return int(
                match.group(1)
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # Numeric suffix such as:
    #
    # my hero academia 3
    # --------------------------------------------------------

    match = re.search(
        r"\s(\d+)$",
        text,
    )

    if match:

        try:
            return int(
                match.group(1)
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # Season X
    # --------------------------------------------------------

    match = re.search(
        r"\bseason\s+(\d+)\b",
        text,
    )

    if match:

        try:
            return int(
                match.group(1)
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # Original season
    # --------------------------------------------------------

    return 1


# ============================================================
# ANIME FILE HELPERS
# ============================================================

def get_local_anime_slugs():

    slugs = []

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    for filename in glob.glob(
        os.path.join(
            base_dir,
            "*.json",
        )
    ):

        basename = os.path.basename(
            filename
        )

        if basename in (
            "anime_index.json",
            "animator_index.json",
        ):
            continue

        if not basename.endswith(".json"):
            continue

        slug = basename[:-5].strip()

        if slug:
            slugs.append(slug)

    return slugs


# ============================================================
# FRANCHISE EXCLUSIONS
# ============================================================

def is_non_main_entry(slug):

    text = normalize(
        str(slug)
    )

    excluded_terms = [

        # Movies
        "movie",
        "film",

        # OVAs / specials
        "ova",
        "special",
        "specials",
        "ona",

        # Promotional material
        "pv",
        "promotion",
        "promotional",

        # Recaps / compilations
        "recap",
        "compilation",

        # Spin-offs
        "vigilantes",

        # MHA movies
        "heroes rising",
        "you re next",
        "ua battle heroes",

        # Other obvious side material
        "phantom parade",

    ]

    return any(
        term in text
        for term in excluded_terms
    )


# ============================================================
# FRANCHISE DEFINITIONS
# ============================================================

FRANCHISES = {

    "jjk": {
        "keywords": [
            "jujutsu kaisen",
            "jujutsu-kaisen",
            "呪術廻戦",
        ],
    },

    "jujutsu kaisen": {
        "keywords": [
            "jujutsu kaisen",
            "jujutsu-kaisen",
            "呪術廻戦",
        ],
    },

    "mha": {
        "keywords": [
            "my hero academia",
            "boku no hero academia",
        ],
    },

    "bnha": {
        "keywords": [
            "my hero academia",
            "boku no hero academia",
        ],
    },

    "my hero academia": {
        "keywords": [
            "my hero academia",
            "boku no hero academia",
        ],
    },

    "boku no hero academia": {
        "keywords": [
            "my hero academia",
            "boku no hero academia",
        ],
    },

    "jojo": {
        "keywords": [
            "jojo",
            "jojo's bizarre adventure",
            "jojo s bizarre adventure",
            "jojo no kimyou na bouken",
        ],
    },
}


# ============================================================
# MATCH FRANCHISE SLUG
# ============================================================

def slug_matches_franchise(
    slug,
    keywords,
):

    normalized_slug = normalize(
        str(slug)
    )

    if not normalized_slug:
        return False

    for keyword in keywords:

        normalized_keyword = normalize(
            keyword
        )

        if not normalized_keyword:
            continue

        if (
            normalized_keyword
            in normalized_slug
        ):

            return True

    return False


# ============================================================
# GET ALL ANIME SEASONS
# ============================================================

def get_all_anime_seasons(anime):
    """
    Find all relevant KFSL anime slugs.

    Examples:

        jjk
        jujutsu kaisen

        mha
        my hero academia

        my hero academia 3

        jjk 3
    """

    normalized_input = normalize(
        anime
    )

    if not normalized_input:
        return []

    candidates = {}

    # ========================================================
    # HELPER
    # ========================================================

    def add_candidate(slug):

        if not slug:
            return

        slug = str(
            slug
        ).strip()

        if not slug:
            return

        if is_non_main_entry(slug):
            return

        candidates[slug] = True

    # ========================================================
    # DETECT SPECIFIC SEASON NUMBER
    # ========================================================

    specific_match = re.search(
        r"\b(?:season|s|part|p)?\s*(\d+)\b",
        normalized_input,
    )

    requested_number = None

    if specific_match:

        requested_number = int(
            specific_match.group(1)
        )

    # ========================================================
    # DETECT FRANCHISE
    # ========================================================

    franchise = FRANCHISES.get(
        normalized_input
    )

    # ========================================================
    # SPECIFIC SEASON SEARCH
    # ========================================================

    if requested_number is not None:

        # ----------------------------------------------------
        # Remove season number from query.
        # ----------------------------------------------------

        query_without_number = re.sub(
            r"\b(?:season|s|part|p)?\s*\d+\b",
            "",
            normalized_input,
        ).strip()

        # ----------------------------------------------------
        # Exact index matches
        # ----------------------------------------------------

        exact_matches = (
            ANIME_INDEX_NORMALIZED.get(
                normalized_input,
                set(),
            )
        )

        for slug in exact_matches:

            add_candidate(slug)

        # ----------------------------------------------------
        # Search anime_index
        # ----------------------------------------------------

        for name, slug in ANIME_INDEX.items():

            normalized_name = normalize(
                name
            )

            normalized_slug = normalize(
                slug
            )

            if not normalized_name:
                continue

            # The base franchise must match.
            if query_without_number:

                base_matches = False

                # Franchise query
                if franchise:

                    for keyword in franchise["keywords"]:

                        normalized_keyword = normalize(
                            keyword
                        )

                        if (
                            normalized_keyword
                            in normalized_name
                            or normalized_keyword
                            in normalized_slug
                        ):

                            base_matches = True
                            break

                # Normal query
                else:

                    if (
                        query_without_number
                        in normalized_name
                        or query_without_number
                        in normalized_slug
                    ):

                        base_matches = True

                if not base_matches:
                    continue

            # ------------------------------------------------
            # Determine season number from slug/name.
            # ------------------------------------------------

            combined = (
                normalized_name
                + " "
                + normalized_slug
            )

            number_matches = [

                rf"\b{requested_number}(?:st|nd|rd|th)?\s+season\b",

                rf"\bseason\s+{requested_number}\b",

                rf"\b{requested_number}\s+season\b",

                rf"\b{requested_number}\b",

            ]

            if any(
                re.search(
                    pattern,
                    combined,
                )
                for pattern in number_matches
            ):

                # Avoid matching unrelated numbers.
                detected_season = get_season_number(
                    slug
                )

                if (
                    detected_season
                    == requested_number
                ):

                    add_candidate(slug)

        # ----------------------------------------------------
        # Search local JSON filenames.
        # ----------------------------------------------------

        for slug in get_local_anime_slugs():

            normalized_slug = normalize(
                slug
            )

            if franchise:

                if not slug_matches_franchise(
                    slug,
                    franchise["keywords"],
                ):
                    continue

            else:

                if (
                    query_without_number
                    not in normalized_slug
                ):
                    continue

            detected_season = get_season_number(
                slug
            )

            if (
                detected_season
                == requested_number
            ):

                add_candidate(slug)

        # ----------------------------------------------------
        # Specific query is done.
        # ----------------------------------------------------

        return sort_anime_slugs(
            list(candidates.keys())
        )

    # ========================================================
    # FRANCHISE SEARCH
    # ========================================================

    if franchise:

        keywords = franchise[
            "keywords"
        ]

        # ----------------------------------------------------
        # A. anime_index.json
        # ----------------------------------------------------

        for name, slug in ANIME_INDEX.items():

            normalized_name = normalize(
                name
            )

            normalized_slug = normalize(
                slug
            )

            if not normalized_name:
                continue

            matched = False

            for keyword in keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_keyword
                    in normalized_name
                    or normalized_keyword
                    in normalized_slug
                ):

                    matched = True
                    break

            if not matched:
                continue

            add_candidate(slug)

        # ----------------------------------------------------
        # B. Local KFSL JSON filenames
        # ----------------------------------------------------

        for slug in get_local_anime_slugs():

            if not slug_matches_franchise(
                slug,
                keywords,
            ):
                continue

            add_candidate(slug)

        # ----------------------------------------------------
        # C. IMPORTANT:
        #
        # For JJK and MHA, explicitly make sure canonical
        # seasons are recognized even if anime_index has
        # incomplete naming.
        # ----------------------------------------------------

        if normalized_input in (
            "jjk",
            "jujutsu kaisen",
        ):

            canonical_jjk = [

                "jujutsu-kaisen",

                "jujutsu-kaisen-2nd-season",

                "jujutsu-kaisen-3rd-season-culling-game-part-1",

                "jujutsu-kaisen-4th-season-culling-game-part-2",

            ]

            for slug in canonical_jjk:

                # Only add if the actual local JSON exists
                # OR the slug exists in anime_index.
                exists_in_index = any(
                    str(indexed_slug).strip()
                    == slug
                    for indexed_slug
                    in ANIME_INDEX.values()
                )

                exists_locally = (
                    slug
                    in get_local_anime_slugs()
                )

                if (
                    exists_in_index
                    or exists_locally
                ):

                    add_candidate(slug)

        elif normalized_input in (
            "mha",
            "bnha",
            "my hero academia",
            "boku no hero academia",
        ):

            canonical_mha = [

                "my-hero-academia",

                "my-hero-academia-2nd-season",

                "my-hero-academia-3",

                "my-hero-academia-4",

                "my-hero-academia-5",

                "my-hero-academia-6",

                "my-hero-academia-7",

                "my-hero-academia-final-season",

            ]

            for slug in canonical_mha:

                exists_in_index = any(
                    str(indexed_slug).strip()
                    == slug
                    for indexed_slug
                    in ANIME_INDEX.values()
                )

                exists_locally = (
                    slug
                    in get_local_anime_slugs()
                )

                if (
                    exists_in_index
                    or exists_locally
                ):

                    add_candidate(slug)

        # ----------------------------------------------------
        # Return franchise results.
        # ----------------------------------------------------

        return sort_anime_slugs(
            list(candidates.keys())
        )

    # ========================================================
    # NORMAL SEARCH
    # ========================================================

    # --------------------------------------------------------
    # Exact anime_index match
    # --------------------------------------------------------

    exact_matches = (
        ANIME_INDEX_NORMALIZED.get(
            normalized_input,
            set(),
        )
    )

    for slug in exact_matches:

        add_candidate(slug)

    # --------------------------------------------------------
    # Manual alias
    # --------------------------------------------------------

    if normalized_input in ANIME_ALIASES:

        alias = ANIME_ALIASES[
            normalized_input
        ]

        if isinstance(
            alias,
            (list, tuple, set)
        ):

            for slug in alias:

                add_candidate(slug)

        else:

            add_candidate(alias)

    # --------------------------------------------------------
    # Containment fallback
    # --------------------------------------------------------

    if not candidates:

        for name, slug in ANIME_INDEX.items():

            normalized_name = normalize(
                name
            )

            normalized_slug = normalize(
                slug
            )

            if not normalized_name:
                continue

            if (
                normalized_input
                in normalized_name
                or normalized_input
                in normalized_slug
                or normalized_name
                in normalized_input
            ):

                add_candidate(slug)

    # --------------------------------------------------------
    # Local filename fallback
    # --------------------------------------------------------

    if not candidates:

        for slug in get_local_anime_slugs():

            normalized_slug = normalize(
                slug
            )

            if (
                normalized_input
                in normalized_slug
                or normalized_slug
                in normalized_input
            ):

                add_candidate(slug)

    # ========================================================
    # FINAL FALLBACK
    # ========================================================

    if not candidates:

        fallback = get_anime_slug(
            anime
        )

        if fallback:

            add_candidate(
                fallback
            )

    return sort_anime_slugs(
        list(candidates.keys())
    )


# ============================================================
# SORT ANIME SLUGS
# ============================================================

def sort_anime_slugs(slugs):

    def sort_key(slug):

        text = normalize(
            str(slug)
        )

        # ----------------------------------------------------
        # Original series
        # ----------------------------------------------------

        if text in (
            "jujutsu kaisen",
            "my hero academia",
        ):

            return (
                0,
                1,
                text,
            )

        # ----------------------------------------------------
        # Explicit ordinal seasons
        # ----------------------------------------------------

        match = re.search(
            r"\b(\d+)(?:st|nd|rd|th)\s+season\b",
            text,
        )

        if match:

            return (
                0,
                int(match.group(1)),
                text,
            )

        # ----------------------------------------------------
        # Numeric MHA style
        # ----------------------------------------------------

        match = re.search(
            r"\s(\d+)$",
            text,
        )

        if match:

            return (
                0,
                int(match.group(1)),
                text,
            )

        # ----------------------------------------------------
        # Final season
        # ----------------------------------------------------

        if "final season" in text:

            return (
                0,
                999,
                text,
            )

        # ----------------------------------------------------
        # Everything else
        # ----------------------------------------------------

        return (
            1,
            9999,
            text,
        )

    return sorted(
        list(dict.fromkeys(slugs)),
        key=sort_key,
    )


# ============================================================
# DISPLAY TITLE
# ============================================================

def get_anime_display_title(slug):

    # --------------------------------------------------------
    # Known titles
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

        "my-hero-academia":
            "My Hero Academia",

        "my-hero-academia-2nd-season":
            "My Hero Academia 2nd Season",

        "my-hero-academia-3":
            "My Hero Academia 3rd Season",

        "my-hero-academia-4":
            "My Hero Academia 4th Season",

        "my-hero-academia-5":
            "My Hero Academia 5th Season",

        "my-hero-academia-6":
            "My Hero Academia 6th Season",

        "my-hero-academia-7":
            "My Hero Academia 7th Season",

        "my-hero-academia-final-season":
            "My Hero Academia Final Season",

        "sousou-no-frieren-2nd-season":
            "Frieren: Beyond Journey's End 2nd Season",

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
    # Try anime_index
    # --------------------------------------------------------

    possible_names = []

    for name, indexed_slug in ANIME_INDEX.items():

        if (
            str(indexed_slug).strip()
            != str(slug).strip()
        ):
            continue

        if re.search(
            r"[a-z]",
            name,
            re.IGNORECASE,
        ):

            possible_names.append(
                name
            )

    if possible_names:

        possible_names.sort(
            key=lambda x: (
                len(x),
                x.lower(),
            )
        )

        return possible_names[0].strip()

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

def format_work_episodes(episodes):

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

            if formatted_text not in seen:

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

    # ========================================================
    # ADD STAFF FIELDS SAFELY
    #
    # Discord limits:
    #   - Each field value: 1024 characters
    #   - Each embed: 25 fields
    #   - Total embed text: 6000 characters
    #
    # Large productions/movies can easily exceed the field limit,
    # so every role is split automatically.
    # ========================================================

    staff_fields = [
        ("🎬 Storyboard", data.get("SB", [])),
        ("🎞️ Episode Director", data.get("ED", [])),
        ("✏️ Animation Director", data.get("AD", [])),
        ("🧩 Assistant Animation Director", data.get("Ass. AD", [])),
        ("👑 Chief Animation Director", data.get("CAD", [])),
        ("🎨 Character Design", data.get("CD", [])),
        ("🔥 Key Animation", data.get("KA", [])),
        ("🎵 Artist", data.get("Artist", [])),
    ]

    # Build field entries first so they can be distributed across
    # multiple embeds when the whole staff list is very large.
    prepared_fields = []

    for field_name, names in staff_fields:

        if not names:
            continue

        value = format_names(names)

        if not value:
            continue

        chunks = split_text(value, 1024)

        for index, chunk in enumerate(chunks):

            if index == 0:
                current_name = field_name
            else:
                current_name = f"{field_name} (continued)"

            prepared_fields.append(
                (current_name, chunk)
            )

    if data.get("2KA"):

        prepared_fields.append(
            (
                "📝 2nd Key Animation",
                f"**{data['2KA']}**",
            )
        )

    # --------------------------------------------------------
    # Create one or more embeds.
    #
    # We keep both Discord limits safe:
    #   maximum 25 fields
    #   maximum 6000 characters
    # --------------------------------------------------------

    embeds = []
    current_embed = embed
    current_field_count = 0
    current_total_chars = len(embed.title or "") + len(embed.description or "")

    for field_name, value in prepared_fields:

        field_chars = len(field_name) + len(value)

        # Start a new embed if adding this field would exceed
        # either the 25-field limit or the 6000-character limit.
        if (
            current_field_count >= 25
            or current_total_chars + field_chars > 5900
        ):

            current_embed.set_footer(
                text="Sakuga Staff • KeyFrame / KFSL dataset"
            )

            embeds.append(current_embed)

            current_embed = discord.Embed(
                title=title,
                description=(
                    f"**{anime}** — "
                    f"Season {season} "
                    f"Episode {episode}"
                ),
                color=EMBED_COLOR,
            )

            current_field_count = 0
            current_total_chars = (
                len(current_embed.title or "")
                + len(current_embed.description or "")
            )

        current_embed.add_field(
            name=field_name[:256],
            value=value[:1024],
            inline=False,
        )

        current_field_count += 1
        current_total_chars += field_chars

    current_embed.set_footer(
        text="Sakuga Staff • KeyFrame / KFSL dataset"
    )

    embeds.append(current_embed)

    # --------------------------------------------------------
    # Send all pages.
    # --------------------------------------------------------

    for page_index, page_embed in enumerate(embeds):

        if len(embeds) > 1:
            page_embed.set_footer(
                text=(
                    "Sakuga Staff • KeyFrame / KFSL dataset"
                    f" • Page {page_index + 1}/{len(embeds)}"
                )
            )

        await interaction.followup.send(
            embed=page_embed
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

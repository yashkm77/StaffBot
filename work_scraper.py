import aiohttp
import asyncio
import json
import re
import html as html_module
import os


# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://keyframe-staff-list.com/staff"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# ROLE DISPLAY NAMES
# ============================================================

ROLE_NAMES = {
    "Chief Animation Director": "CAD",
    "Animation Director": "AD",
    "Assistant Animation Director": "Ass. AD",
    "Key Animation": "KA",
    "2nd Key Animation": "2KA",
    "Storyboard": "SB",
    "Episode Director": "ED",
    "Storyboard / Episode Director": "SB/ED",
    "Character Design": "Character Design",
    "Art Director": "Art Director",
    "Art Board": "Art Board",
    "Main Animator": "Main Animator",
}


# ============================================================
# NAME ALIASES
# ============================================================

NAME_ALIASES = {
    "keiichiro watanabe": "keiichirou watanabe",
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):
    """
    Normalize names / role names / menu names for matching.

    Examples:
        'Keiichiro Watanabe'
        -> 'keiichirou watanabe'

        '#17 (BD)'
        -> '17 bd'
    """

    if not text:
        return ""

    text = str(text).lower().strip()

    # Replace non-alphanumeric characters with spaces.
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    # Collapse repeated spaces.
    text = " ".join(
        text.split()
    )

    # Name spelling aliases.
    return NAME_ALIASES.get(
        text,
        text,
    )


# ============================================================
# LOAD LOCAL JSON
# ============================================================

def load_local_json(slug):
    """
    Load local KFSL JSON if available.

    Example:
        jujutsu-kaisen-2nd-season.json
    """

    path = os.path.join(
        BASE_DIR,
        f"{slug}.json",
    )

    if not os.path.exists(path):
        return None

    print(
        f"Local JSON found for {slug}"
    )

    print(
        f"Using local JSON: {slug}.json"
    )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except Exception as e:
        print(
            f"JSON error: {e}"
        )
        return None


# ============================================================
# PERSON NAMES
# ============================================================

def get_person_names(person):
    """
    Return every known name for a person.

    Checks:
        en
        ja
        pn.en
        pn.ja
    """

    names = set()

    if not isinstance(
        person,
        dict,
    ):
        return names

    # --------------------------------------------------------
    # Normal names
    # --------------------------------------------------------

    for key in (
        "en",
        "ja",
    ):
        value = person.get(
            key
        )

        if isinstance(
            value,
            str,
        ) and value.strip():

            names.add(
                normalize(value)
            )

    # --------------------------------------------------------
    # Pen name / alternate name
    # --------------------------------------------------------

    pn = person.get(
        "pn"
    )

    if isinstance(
        pn,
        dict,
    ):

        for key in (
            "en",
            "ja",
        ):

            value = pn.get(
                key
            )

            if isinstance(
                value,
                str,
            ) and value.strip():

                names.add(
                    normalize(value)
                )

    return names


# ============================================================
# GET MAIN NAME
# ============================================================

def get_main_name(person):
    """
    Prefer pen name English name if available.
    Otherwise use normal English name.
    """

    if not isinstance(
        person,
        dict,
    ):
        return ""

    pn = person.get(
        "pn"
    )

    if isinstance(
        pn,
        dict,
    ):

        value = pn.get(
            "en"
        )

        if isinstance(
            value,
            str,
        ) and value.strip():

            return value.strip()

    value = person.get(
        "en",
        "",
    )

    if isinstance(
        value,
        str,
    ):
        return value.strip()

    return ""


# ============================================================
# FIND PERSON ID
# ============================================================

def find_person_id(
    data,
    animator,
):
    """
    Recursively search KFSL data for an animator
    and return their ID.
    """

    target = normalize(
        animator
    )

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            if target in get_person_names(
                obj
            ):

                person_id = obj.get(
                    "id"
                )

                if person_id is not None:
                    return str(
                        person_id
                    )

            for value in obj.values():

                result = walk(
                    value
                )

                if result:
                    return result

        elif isinstance(
            obj,
            list,
        ):

            for value in obj:

                result = walk(
                    value
                )

                if result:
                    return result

        return None

    return walk(data)


# ============================================================
# EXTRACT STAFF LIST DATA
# ============================================================

def extract_staff_list_data(
    page_html,
):
    """
    Extract the JSON stored inside:

        <script id="staffListData">...</script>
    """

    if not page_html:
        return None

    pattern = re.compile(
        r'<script[^>]+id=["\']staffListData["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        re.DOTALL | re.IGNORECASE,
    )

    match = pattern.search(
        page_html
    )

    if not match:

        print(
            "staffListData was not found."
        )

        return None

    raw_json = match.group(
        1
    ).strip()

    raw_json = html_module.unescape(
        raw_json
    )

    try:

        return json.loads(
            raw_json
        )

    except json.JSONDecodeError as e:

        print(
            f"JSON decode error: {e}"
        )

        return None


# ============================================================
# GET WORK LABEL
# ============================================================

def get_work_label(menu_name):
    """
    Keep the original KFSL menu name.

    Examples:
        #17
        17
        #17 (BD)
        17 (BD)
        OP #1
        ED #2
    """

    if not menu_name:
        return ""

    return str(
        menu_name
    ).strip()


# ============================================================
# GET WORK TYPE
# ============================================================

def get_work_type(menu_name):
    """
    Determine whether KFSL menu is:

        OP
        EPISODE
        ED
        OTHER
    """

    if not menu_name:
        return "OTHER"

    text = str(
        menu_name
    ).strip()

    normalized = normalize(
        text
    )

    # --------------------------------------------------------
    # OPENING
    #
    # Matches:
    # OP 1
    # OP #1
    # OP 01
    # OP#1
    # --------------------------------------------------------

    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):
        return "OP"

    # --------------------------------------------------------
    # ENDING
    #
    # Matches:
    # ED 1
    # ED #1
    # ED 01
    # ED#1
    # --------------------------------------------------------

    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):
        return "ED"

    # --------------------------------------------------------
    # EPISODE
    #
    # Examples:
    # 1
    # #1
    # 17 (BD)
    # #17 (BD)
    # Episode 17
    # --------------------------------------------------------

    if re.search(
        r"\d+",
        normalized,
    ):
        return "EPISODE"

    return "OTHER"


# ============================================================
# GET EPISODE NUMBER
# ============================================================

def get_episode_number(menu_name):
    """
    Extract the numeric episode/work number.

    OP / ED return None.

    Examples:

        #17       -> 17
        17        -> 17
        #17 (BD)  -> 17
        OP #1     -> None
        ED #2     -> None
    """

    if not menu_name:
        return None

    text = str(
        menu_name
    ).strip()

    normalized = normalize(
        text
    )

    # --------------------------------------------------------
    # OP / ED must NOT become episode numbers.
    # --------------------------------------------------------

    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):
        return None

    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):
        return None

    # --------------------------------------------------------
    # Extract first number.
    # --------------------------------------------------------

    match = re.search(
        r"\d+",
        text,
    )

    if not match:
        return None

    try:

        return int(
            match.group(0)
        )

    except ValueError:

        return None


# ============================================================
# GET EPISODE DATA
# ============================================================

def get_episode_data(data):
    """
    Convert KFSL menus into a consistent internal structure.
    """

    episodes = []

    if not isinstance(
        data,
        dict,
    ):
        return episodes

    menus = data.get(
        "menus",
        [],
    )

    if not isinstance(
        menus,
        list,
    ):
        return episodes

    for menu in menus:

        if not isinstance(
            menu,
            dict,
        ):
            continue

        menu_name = str(
            menu.get(
                "name",
                "",
            )
        ).strip()

        if not menu_name:
            continue

        credits = menu.get(
            "credits"
        )

        if not isinstance(
            credits,
            list,
        ):
            continue

        work_type = get_work_type(
            menu_name
        )

        if work_type == "OTHER":
            continue

        episode_number = get_episode_number(
            menu_name
        )

        episodes.append({
            "episode": episode_number,

            # Original KFSL menu name.
            "name": menu_name,

            # Original work label.
            "work_name": get_work_label(
                menu_name
            ),

            "work_type": work_type,

            "credits": credits,
        })

    # ========================================================
    # SORT
    # ========================================================

    def sort_key(item):

        work_type = item.get(
            "work_type"
        )

        episode = item.get(
            "episode"
        )

        if work_type == "OP":
            priority = 0

        elif work_type == "EPISODE":
            priority = 1

        elif work_type == "ED":
            priority = 2

        else:
            priority = 3

        return (
            priority,

            episode
            if episode is not None
            else 9999,

            item.get(
                "work_name",
                "",
            ),
        )

    episodes.sort(
        key=sort_key
    )

    return episodes


# ============================================================
# NORMALIZE ROLE NAME
# ============================================================

def normalize_role_name(role_name):
    """
    Convert KFSL role variations into canonical names.

    IMPORTANT:
    This function does NOT convert to KA / AD / ED.
    Main.py can use ROLE_NAMES for display.
    """

    if not role_name:
        return ""

    text = str(
        role_name
    ).strip()

    normalized = normalize(
        text
    )

    # --------------------------------------------------------
    # Key Animation
    # --------------------------------------------------------

    if normalized in (
        "key animation",
        "key animator",
    ):
        return "Key Animation"

    # --------------------------------------------------------
    # 2nd Key Animation
    # --------------------------------------------------------

    if normalized in (
        "2nd key animation",
        "second key animation",
        "2nd key animator",
        "second key animator",
    ):
        return "2nd Key Animation"

    # --------------------------------------------------------
    # Storyboard
    # --------------------------------------------------------

    if normalized in (
        "storyboard",
        "story board",
    ):
        return "Storyboard"

    # --------------------------------------------------------
    # Episode Director
    # --------------------------------------------------------

    if normalized in (
        "episode director",
        "episode director ed",
    ):
        return "Episode Director"

    # --------------------------------------------------------
    # Storyboard / Episode Director
    # --------------------------------------------------------

    if normalized in (
        "storyboard episode director",
        "storyboard episode director ed",
        "storyboard episode director sb ed",
    ):
        return "Storyboard / Episode Director"

    # --------------------------------------------------------
    # Animation Director
    # --------------------------------------------------------

    if normalized in (
        "animation director",
        "animation director ad",
    ):
        return "Animation Director"

    # --------------------------------------------------------
    # Assistant Animation Director
    # --------------------------------------------------------

    if normalized in (
        "assistant animation director",
        "assistant animation director aad",
        "assistant animation director ass ad",
    ):
        return "Assistant Animation Director"

    # --------------------------------------------------------
    # Chief Animation Director
    # --------------------------------------------------------

    if normalized in (
        "chief animation director",
        "chief animation director cad",
    ):
        return "Chief Animation Director"

    # --------------------------------------------------------
    # Character Design
    # --------------------------------------------------------

    if normalized in (
        "character design",
        "character designer",
    ):
        return "Character Design"

    # --------------------------------------------------------
    # Art Director
    # --------------------------------------------------------

    if normalized in (
        "art director",
        "art director ad",
    ):
        return "Art Director"

    # --------------------------------------------------------
    # Art Board
    # --------------------------------------------------------

    if normalized in (
        "art board",
        "artboard",
    ):
        return "Art Board"

    # --------------------------------------------------------
    # Main Animator
    # --------------------------------------------------------

    if normalized in (
        "main animator",
        "main animation",
    ):
        return "Main Animator"

    # --------------------------------------------------------
    # Unknown role
    #
    # Keep the original KFSL role.
    # --------------------------------------------------------

    return text


# ============================================================
# GET ROLE DISPLAY NAME
# ============================================================

def get_role_display_name(role):
    """
    Convert canonical role into short display name.

    Example:
        Key Animation -> KA
        2nd Key Animation -> 2KA
    """

    canonical = normalize_role_name(
        role
    )

    return ROLE_NAMES.get(
        canonical,
        canonical,
    )


# ============================================================
# SEARCH ONE WORK
# ============================================================

def search_episode(
    episode,
    animator,
):
    """
    Search one KFSL work for the requested animator.
    """

    target = normalize(
        animator
    )

    results = []

    credits = episode.get(
        "credits",
        [],
    )

    if not isinstance(
        credits,
        list,
    ):
        return results

    for credit_group in credits:

        if not isinstance(
            credit_group,
            dict,
        ):
            continue

        roles = credit_group.get(
            "roles",
            [],
        )

        if not isinstance(
            roles,
            list,
        ):
            continue

        for role in roles:

            if not isinstance(
                role,
                dict,
            ):
                continue

            role_name = str(
                role.get(
                    "name",
                    "",
                )
            ).strip()

            if not role_name:
                continue

            # ------------------------------------------------
            # Canonical role.
            #
            # Do NOT change this to KA/AD/etc here.
            # ------------------------------------------------

            canonical_role = normalize_role_name(
                role_name
            )

            staff = role.get(
                "staff",
                [],
            )

            if not isinstance(
                staff,
                list,
            ):
                continue

            for person in staff:

                if not isinstance(
                    person,
                    dict,
                ):
                    continue

                # Ignore studios.
                if person.get(
                    "isStudio"
                ):
                    continue

                names = get_person_names(
                    person
                )

                if target not in names:
                    continue

                # ------------------------------------------------
                # Display English name.
                # ------------------------------------------------

                displayed_name = person.get(
                    "en",
                    "",
                )

                if not isinstance(
                    displayed_name,
                    str,
                ):
                    displayed_name = ""

                displayed_name = displayed_name.strip()

                # ------------------------------------------------
                # Save result.
                # ------------------------------------------------

                results.append({

                    "name": displayed_name,

                    "main_name": get_main_name(
                        person
                    ),

                    "id": person.get(
                        "id"
                    ),

                    "role": canonical_role,

                    "role_display": get_role_display_name(
                        canonical_role
                    ),

                    "episode": episode.get(
                        "episode"
                    ),

                    # Original KFSL work name.
                    "work_name": episode.get(
                        "work_name",
                        episode.get(
                            "name",
                            "",
                        ),
                    ),

                    "work_type": episode.get(
                        "work_type",
                        "EPISODE",
                    ),
                })

    return results


# ============================================================
# SEARCH LOCAL / RUNTIME JSON
# ============================================================

def search_local_json(
    data,
    anime_title,
    slug,
    animator,
):
    """
    Search either local JSON or freshly fetched KFSL JSON.
    """

    results = []

    episodes = get_episode_data(
        data
    )

    for episode in episodes:

        matches = search_episode(
            episode,
            animator,
        )

        for match in matches:

            results.append({

                "anime": anime_title,

                "slug": slug,

                "episode": match.get(
                    "episode"
                ),

                "work_name": match.get(
                    "work_name",
                    "",
                ),

                "work_type": match.get(
                    "work_type",
                    "EPISODE",
                ),

                "role": match.get(
                    "role",
                    "",
                ),

                "role_display": match.get(
                    "role_display",
                    "",
                ),

                "name": match.get(
                    "name",
                    "",
                ),

                "main_name": match.get(
                    "main_name",
                    "",
                ),

                "id": match.get(
                    "id"
                ),
            })

    return results


# ============================================================
# HTTP HEADERS
# ============================================================

def get_headers():
    """
    Browser-like headers for KFSL.
    """

    return {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) "
            "Version/26.0 Safari/605.1.15"
        ),

        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),

        "Accept-Language": (
            "en-US,en;q=0.9"
        ),

        "Cache-Control": "no-cache",

        "Pragma": "no-cache",
    }


# ============================================================
# GET ANIME PAGE
# ============================================================

async def get_anime_page(
    session,
    slug,
):
    """
    Fetch KFSL anime page.

    Does NOT save the response.
    """

    url = f"{BASE_URL}/{slug}"

    print(
        f"Opening: {url}"
    )

    try:

        async with session.get(
            url,
            allow_redirects=True,
        ) as response:

            print(
                f"HTTP: {response.status}"
            )

            if response.status != 200:

                print(
                    f"KFSL request failed: HTTP {response.status}"
                )

                return None

            return await response.text(
                encoding="utf-8",
                errors="ignore",
            )

    except asyncio.TimeoutError:

        print(
            "KFSL request timed out."
        )

        return None

    except aiohttp.ClientError as e:

        print(
            f"KFSL request error: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Unexpected request error: {e}"
        )

        return None


# ============================================================
# GET STAFF PROFILE
# ============================================================

async def get_staff_profile(
    session,
    person_id,
):
    """
    Try to locate the animator's actual KFSL profile URL.

    KFSL can use hashed profile paths, so we try the ID page
    and then inspect the returned HTML.
    """

    if person_id is None:
        return None

    person_id = str(
        person_id
    ).strip()

    if not person_id:
        return None

    possible_urls = [

        f"{BASE_URL}/{person_id}",

        f"{BASE_URL}?id={person_id}",
    ]

    for url in possible_urls:

        try:

            async with session.get(
                url,
                allow_redirects=True,
            ) as response:

                if response.status != 200:
                    continue

                text = await response.text(
                    encoding="utf-8",
                    errors="ignore",
                )

                # ------------------------------------------------
                # Find /staff/<hash>
                # ------------------------------------------------

                match = re.search(
                    r'href=["\'](/staff/[a-f0-9]{40,})["\']',
                    text,
                    re.IGNORECASE,
                )

                if match:

                    return (
                        "https://keyframe-staff-list.com"
                        + match.group(1)
                    )

                # ------------------------------------------------
                # Sometimes the current URL itself may be useful.
                # ------------------------------------------------

                final_url = str(
                    response.url
                )

                if (
                    final_url.startswith(
                        "https://keyframe-staff-list.com/staff/"
                    )
                    and final_url != url
                ):

                    return final_url

        except asyncio.TimeoutError:

            continue

        except aiohttp.ClientError:

            continue

        except Exception:

            continue

    return None


# ============================================================
# BUILD GROUPED WORKS
# ============================================================

def build_grouped_works(results):
    """
    Build:

        {
            "Key Animation": [
                "#01",
                "#05",
                "#17"
            ],
            "Animation Director": [
                "#12"
            ]
        }
    """

    grouped = {}

    # Used to prevent duplicates.
    seen = {}

    for result in results:

        role = result.get(
            "role",
            "",
        )

        if not role:
            continue

        # --------------------------------------------------------
        # Always normalize role again.
        # --------------------------------------------------------

        role = normalize_role_name(
            role
        )

        grouped.setdefault(
            role,
            [],
        )

        seen.setdefault(
            role,
            set(),
        )

        # --------------------------------------------------------
        # Keep original KFSL work name.
        # --------------------------------------------------------

        work_name = str(
            result.get(
                "work_name",
                "",
            )
        ).strip()

        if not work_name:

            episode = result.get(
                "episode"
            )

            if episode is not None:

                work_name = (
                    f"#{episode:02d}"
                )

            else:

                continue

        # --------------------------------------------------------
        # Prevent duplicates.
        # --------------------------------------------------------

        if work_name in seen[role]:
            continue

        seen[role].add(
            work_name
        )

        grouped[role].append(
            work_name
        )

    return grouped


# ============================================================
# SORT GROUPED WORKS
# ============================================================

def sort_work_names(work_names):
    """
    Sort work names numerically where possible.

    Example:
        #2
        #10
        #17
    """

    def key(value):

        text = str(
            value
        )

        match = re.search(
            r"\d+",
            text,
        )

        if match:

            return (
                0,
                int(
                    match.group(0)
                ),
                text.lower(),
            )

        return (
            1,
            999999,
            text.lower(),
        )

    return sorted(
        work_names,
        key=key,
    )


# ============================================================
# GET ANIMATOR WORKS
# ============================================================

async def get_animator_works(
    animator,
    anime_slug,
    anime_title=None,
):
    """
    Main function used by main.py.

    Priority:

        1. Local JSON
        2. Runtime KFSL fetch
        3. Failure -> empty result

    Runtime JSON is NEVER saved.
    """

    if not anime_title:

        anime_title = (
            anime_slug
            .replace(
                "-",
                " ",
            )
            .title()
        )

    # ========================================================
    # LOCAL JSON
    # ========================================================

    data = load_local_json(
        anime_slug
    )

    if data is not None:

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator,
        )

        if not results:

            return {
                "name": animator,
                "anime": anime_title,
                "slug": anime_slug,
                "profile_url": None,
                "groups": {},
                "found": False,
                "source": "local",
            }

        # ----------------------------------------------------
        # Find person ID.
        # ----------------------------------------------------

        person_id = results[0].get(
            "id"
        )

        headers = get_headers()

        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=20,
        )

        profile_url = None

        try:

            async with aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
            ) as session:

                if person_id:

                    profile_url = await get_staff_profile(
                        session,
                        person_id,
                    )

        except Exception as e:

            print(
                f"Profile lookup failed: {e}"
            )

        # ----------------------------------------------------
        # Group results.
        # ----------------------------------------------------

        grouped = build_grouped_works(
            results
        )

        # Sort each group.
        for role in grouped:

            grouped[role] = sort_work_names(
                grouped[role]
            )

        return {

            "name": (
                results[0].get(
                    "name"
                )
                or results[0].get(
                    "main_name"
                )
                or animator
            ),

            "anime": anime_title,

            "slug": anime_slug,

            "profile_url": profile_url,

            "groups": grouped,

            "found": True,

            "source": "local",
        }

    # ========================================================
    # NO LOCAL JSON
    # ========================================================

    print(
        f"No local JSON for {anime_slug}"
    )

    print(
        "Attempting runtime KFSL fetch..."
    )

    headers = get_headers()

    timeout = aiohttp.ClientTimeout(
        total=30,
        connect=10,
        sock_read=20,
    )

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
    ) as session:

        # ----------------------------------------------------
        # Fetch anime page.
        # ----------------------------------------------------

        page = await get_anime_page(
            session,
            anime_slug,
        )

        if not page:

            print(
                "KFSL anime page unavailable."
            )

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "unavailable",
            }

        # ----------------------------------------------------
        # Extract embedded JSON.
        # ----------------------------------------------------

        data = extract_staff_list_data(
            page
        )

        if not data:

            print(
                "Could not extract KFSL staffListData."
            )

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "unavailable",
            }

        # ----------------------------------------------------
        # Search animator.
        # ----------------------------------------------------

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator,
        )

        # ----------------------------------------------------
        # No animator found.
        # ----------------------------------------------------

        if not results:

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "runtime",
            }

        # ----------------------------------------------------
        # Group results.
        # ----------------------------------------------------

        grouped = build_grouped_works(
            results
        )

        # Sort each group.
        for role in grouped:

            grouped[role] = sort_work_names(
                grouped[role]
            )

        # ----------------------------------------------------
        # Profile.
        # ----------------------------------------------------

        person_id = results[0].get(
            "id"
        )

        profile_url = None

        if person_id:

            profile_url = await get_staff_profile(
                session,
                person_id,
            )

        return {

            "name": (
                results[0].get(
                    "name"
                )
                or results[0].get(
                    "main_name"
                )
                or animator
            ),

            "anime": anime_title,

            "slug": anime_slug,

            "profile_url": profile_url,

            "groups": grouped,

            "found": True,

            "source": "runtime",
        }


# ============================================================
# FORMAT RESULTS FOR MAIN.PY
# ============================================================

def format_groups(groups):
    """
    Optional helper for main.py.

    Converts canonical roles to display names.

    Example:

        Key Animation:
            #1, #2

    becomes:

        KA:
            #1, #2
    """

    formatted = {}

    for role, works in groups.items():

        display_role = get_role_display_name(
            role
        )

        formatted.setdefault(
            display_role,
            [],
        )

        formatted[display_role].extend(
            works
        )

    return formatted


# ============================================================
# TEST
# ============================================================

async def test():

    animator = "Keiichiro Watanabe"

    slug = "jujutsu-kaisen-2nd-season"

    anime_title = "Jujutsu Kaisen 2nd Season"

    print()

    print(
        "=" * 70
    )

    print(
        "Testing Staff Work Scraper"
    )

    print(
        "=" * 70
    )

    works = await get_animator_works(
        animator,
        slug,
        anime_title,
    )

    print(
        "=" * 70
    )

    print(
        f"Name: {works['name']}"
    )

    print(
        f"Anime: {works['anime']}"
    )

    print(
        f"Source: {works.get('source')}"
    )

    print(
        f"Found: {works.get('found')}"
    )

    print(
        f"Profile: {works['profile_url']}"
    )

    print()

    # --------------------------------------------------------
    # Canonical roles
    # --------------------------------------------------------

    for role, works_list in works[
        "groups"
    ].items():

        print(
            f"{role}: "
            + ", ".join(
                str(work)
                for work in works_list
            )
        )

    print()

    # --------------------------------------------------------
    # Display roles
    # --------------------------------------------------------

    print(
        "DISPLAY FORMAT"
    )

    print(
        "-" * 70
    )

    formatted = format_groups(
        works["groups"]
    )

    for role, works_list in formatted.items():

        print(
            f"{role}: "
            + ", ".join(
                str(work)
                for work in works_list
            )
        )

    print()

    print(
        "=" * 70
    )


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        test()
    )
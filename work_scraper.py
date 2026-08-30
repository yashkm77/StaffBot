import aiohttp
import asyncio
import json
import re
import html as html_module
import os
import unicodedata


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
    "keiichirou watanabe": "keiichirou watanabe",

    "kohei hirota": "kouhei hirota",
    "kouhei hirota": "kouhei hirota",

    # Chengxi Huang
    "chengxi huang": "chengxi huang",
    "huang chengxi": "chengxi huang",
    "cheng xi huang": "chengxi huang",
    "huang cheng xi": "chengxi huang",
}


# ============================================================
# EXTRA NAME ALIASES
# ============================================================

# Known alternate spellings / Chinese names.
#
# The important one here is Chengxi Huang:
#
#   Chengxi Huang
#   Huang Chengxi
#   黄成希
#
# If KFSL gives us the Chinese name, this allows the English
# search to match it as well.
#
# Add more names here later if necessary.

NAME_EQUIVALENTS = {
    "chengxi huang": {
        "chengxi huang",
        "huang chengxi",
        "cheng xi huang",
        "huang cheng xi",
        "黄成希",
    },

    "keiichirou watanabe": {
        "keiichirou watanabe",
        "keiichiro watanabe",
        "watanabe keiichirou",
        "watanabe keiichiro",
        "渡辺啓一郎",
    },

    "kouhei hirota": {
        "kouhei hirota",
        "kohei hirota",
        "hirota kouhei",
        "hirota kohei",
    },
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):
    """
    Normalize names / role names / menu names.

    Keeps Unicode characters.

    Examples:

        Chengxi Huang
        -> chengxi huang

        Huang Chengxi
        -> huang chengxi

        黄成希
        -> 黄成希
    """

    if text is None:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.lower()

    # Remove HTML if any
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Replace punctuation with spaces.
    text = re.sub(
        r"[^\w]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = " ".join(
        text.split()
    )

    # Apply aliases
    return NAME_ALIASES.get(
        text,
        text,
    )


# ============================================================
# BUILD NAME VARIANTS
# ============================================================

def get_name_variants(text):
    """
    Return all useful normalized variants of a name.

    This is important because databases can store names as:

        Chengxi Huang
        Huang Chengxi
        黄成希

    """

    normalized = normalize(
        text
    )

    if not normalized:
        return set()

    variants = {
        normalized
    }

    # Known equivalents
    if normalized in NAME_EQUIVALENTS:

        variants.update(
            normalize(x)
            for x in NAME_EQUIVALENTS[normalized]
        )

    # Reverse two-part names.
    parts = normalized.split()

    if len(parts) == 2:

        reversed_name = (
            f"{parts[1]} {parts[0]}"
        )

        variants.add(
            reversed_name
        )

        # Apply aliases to reversed version
        variants.add(
            NAME_ALIASES.get(
                reversed_name,
                reversed_name,
            )
        )

    return {
        x
        for x in variants
        if x
    }


# ============================================================
# NAME MATCHING
# ============================================================

def names_match(
    target,
    candidate_names,
):
    """
    Strong but flexible name matching.

    Handles:

        Chengxi Huang
        Huang Chengxi

    and known equivalents such as:

        Chengxi Huang
        黄成希
    """

    target_variants = get_name_variants(
        target
    )

    if not target_variants:
        return False

    candidate_variants = set()

    for candidate in candidate_names:

        candidate_variants.update(
            get_name_variants(
                candidate
            )
        )

    if not candidate_variants:
        return False

    # Exact normalized match
    if target_variants & candidate_variants:
        return True

    # --------------------------------------------------------
    # Compare two-part English names by components.
    # --------------------------------------------------------

    for target_name in target_variants:

        target_parts = target_name.split()

        if len(target_parts) != 2:
            continue

        target_first = target_parts[0]
        target_last = target_parts[1]

        for candidate_name in candidate_variants:

            candidate_parts = candidate_name.split()

            if len(candidate_parts) != 2:
                continue

            candidate_first = candidate_parts[0]
            candidate_last = candidate_parts[1]

            if (
                target_first == candidate_first
                and target_last == candidate_last
            ):
                return True

            if (
                target_first == candidate_last
                and target_last == candidate_first
            ):
                return True

    return False


# ============================================================
# LOAD LOCAL JSON
# ============================================================

def load_local_json(slug):

    path = os.path.join(
        BASE_DIR,
        f"{slug}.json",
    )

    if not os.path.isfile(path):

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

            return json.load(
                f
            )

    except json.JSONDecodeError as e:

        print(
            f"JSON decode error in "
            f"{slug}.json: {e}"
        )

        return None

    except OSError as e:

        print(
            f"Could not read "
            f"{slug}.json: {e}"
        )

        return None


# ============================================================
# PERSON NAMES
# ============================================================

def get_person_names(person):

    names = set()

    if not isinstance(
        person,
        dict,
    ):
        return names

    def add_name(value):

        if not isinstance(
            value,
            str,
        ):
            return

        value = value.strip()

        if not value:
            return

        normalized = normalize(
            value
        )

        if normalized:

            names.add(
                normalized
            )

    # --------------------------------------------------------
    # Direct fields
    # --------------------------------------------------------

    direct_fields = (
        "en",
        "ja",
        "jp",
        "zh",
        "zh_cn",
        "zh_tw",
        "name",
        "romanized",
        "romaji",
        "japanese",
        "chinese",
        "english",
    )

    for key in direct_fields:

        value = person.get(
            key
        )

        if isinstance(
            value,
            str,
        ):

            add_name(
                value
            )

        elif isinstance(
            value,
            dict,
        ):

            for subvalue in value.values():

                if isinstance(
                    subvalue,
                    str,
                ):

                    add_name(
                        subvalue
                    )

    # --------------------------------------------------------
    # pn container
    # --------------------------------------------------------

    pn = person.get(
        "pn"
    )

    if isinstance(
        pn,
        dict,
    ):

        for value in pn.values():

            if isinstance(
                value,
                str,
            ):

                add_name(
                    value
                )

            elif isinstance(
                value,
                dict,
            ):

                for subvalue in value.values():

                    if isinstance(
                        subvalue,
                        str,
                    ):

                        add_name(
                            subvalue
                        )

    # --------------------------------------------------------
    # names container
    # --------------------------------------------------------

    names_container = person.get(
        "names"
    )

    if isinstance(
        names_container,
        list,
    ):

        for value in names_container:

            if isinstance(
                value,
                str,
            ):

                add_name(
                    value
                )

            elif isinstance(
                value,
                dict,
            ):

                for subvalue in value.values():

                    if isinstance(
                        subvalue,
                        str,
                    ):

                        add_name(
                            subvalue
                        )

    elif isinstance(
        names_container,
        dict,
    ):

        for value in names_container.values():

            if isinstance(
                value,
                str,
            ):

                add_name(
                    value
                )

            elif isinstance(
                value,
                dict,
            ):

                for subvalue in value.values():

                    if isinstance(
                        subvalue,
                        str,
                    ):

                        add_name(
                            subvalue
                        )

    return names


# ============================================================
# GET MAIN NAME
# ============================================================

def get_main_name(person):

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

        for key in (
            "en",
            "english",
            "romanized",
            "romaji",
        ):

            value = pn.get(
                key
            )

            if (
                isinstance(
                    value,
                    str,
                )
                and value.strip()
            ):

                return value.strip()

    for key in (
        "en",
        "english",
        "romanized",
        "romaji",
        "name",
    ):

        value = person.get(
            key,
            "",
        )

        if (
            isinstance(
                value,
                str,
            )
            and value.strip()
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

    target = animator

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            candidate_names = get_person_names(
                obj
            )

            if names_match(
                target,
                candidate_names,
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

    return walk(
        data
    )


# ============================================================
# EXTRACT STAFF LIST DATA
# ============================================================

def extract_staff_list_data(
    page_html,
):

    if not page_html:
        return None

    pattern = re.compile(
        r'<script[^>]+'
        r'id=["\']staffListData["\']'
        r'[^>]*>'
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

    # Sometimes script data contains HTML whitespace.
    raw_json = raw_json.strip()

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

def get_work_label(
    menu_name,
):

    if not menu_name:
        return ""

    return str(
        menu_name
    ).strip()


# ============================================================
# GET WORK TYPE
# ============================================================

def get_work_type(
    menu_name,
):

    if not menu_name:

        return "OTHER"

    text = str(
        menu_name
    ).strip()

    normalized = normalize(
        text
    )

    # OP
    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "OP"

    # ED
    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "ED"

    # Episode / BD / special names containing a number
    if re.search(
        r"\d+",
        normalized,
    ):

        return "EPISODE"

    return "OTHER"


# ============================================================
# GET EPISODE NUMBER
# ============================================================

def get_episode_number(
    menu_name,
):

    if not menu_name:
        return None

    text = str(
        menu_name
    ).strip()

    normalized = normalize(
        text
    )

    # OP
    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):

        return None

    # ED
    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):

        return None

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

def get_episode_data(
    data,
):

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

            "name": menu_name,

            "work_name": get_work_label(
                menu_name
            ),

            "work_type": work_type,

            "credits": credits,

        })

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

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
            else 999999,
            str(
                item.get(
                    "work_name",
                    "",
                )
            ).lower(),
        )

    episodes.sort(
        key=sort_key
    )

    return episodes


# ============================================================
# NORMALIZE ROLE NAME
# ============================================================

def normalize_role_name(
    role_name,
):

    if not role_name:
        return ""

    text = str(
        role_name
    ).strip()

    normalized = normalize(
        text
    )

    role_aliases = {

        "key animation":
            "Key Animation",

        "key animator":
            "Key Animation",

        "2nd key animation":
            "2nd Key Animation",

        "second key animation":
            "2nd Key Animation",

        "2nd key animator":
            "2nd Key Animation",

        "second key animator":
            "2nd Key Animation",

        "storyboard":
            "Storyboard",

        "story board":
            "Storyboard",

        "episode director":
            "Episode Director",

        "episode director ed":
            "Episode Director",

        "storyboard episode director":
            "Storyboard / Episode Director",

        "storyboard episode director ed":
            "Storyboard / Episode Director",

        "storyboard episode director sb ed":
            "Storyboard / Episode Director",

        "animation director":
            "Animation Director",

        "animation director ad":
            "Animation Director",

        "assistant animation director":
            "Assistant Animation Director",

        "assistant animation director aad":
            "Assistant Animation Director",

        "assistant animation director ass ad":
            "Assistant Animation Director",

        "chief animation director":
            "Chief Animation Director",

        "chief animation director cad":
            "Chief Animation Director",

        "character design":
            "Character Design",

        "character designer":
            "Character Design",

        "art director":
            "Art Director",

        "art director ad":
            "Art Director",

        "art board":
            "Art Board",

        "artboard":
            "Art Board",

        "main animator":
            "Main Animator",

        "main animation":
            "Main Animator",
    }

    return role_aliases.get(
        normalized,
        text,
    )


# ============================================================
# GET ROLE DISPLAY NAME
# ============================================================

def get_role_display_name(
    role,
):

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

                # Ignore studios
                if person.get(
                    "isStudio"
                ):

                    continue

                names = get_person_names(
                    person
                )

                # ------------------------------------------------
                # IMPORTANT:
                # Flexible name matching.
                # ------------------------------------------------

                if not names_match(
                    animator,
                    names,
                ):

                    continue

                displayed_name = get_main_name(
                    person
                )

                if not displayed_name:

                    displayed_name = (
                        animator
                    )

                results.append({

                    "name": displayed_name,

                    "main_name": get_main_name(
                        person
                    ),

                    "id": person.get(
                        "id"
                    ),

                    "role": canonical_role,

                    "role_display":
                        get_role_display_name(
                            canonical_role
                        ),

                    "episode": episode.get(
                        "episode"
                    ),

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

        "Accept-Language":
            "en-US,en;q=0.9",

        "Cache-Control":
            "no-cache",

        "Pragma":
            "no-cache",

    }


# ============================================================
# GET ANIME PAGE
# ============================================================

async def get_anime_page(
    session,
    slug,
):

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
                    "KFSL request failed: "
                    f"HTTP {response.status}"
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
                # Standard KFSL staff profile slug
                # ------------------------------------------------

                match = re.search(
                    r'href=["\']'
                    r'(/staff/[a-f0-9]{40,})'
                    r'["\']',
                    text,
                    re.IGNORECASE,
                )

                if match:

                    return (
                        "https://keyframe-staff-list.com"
                        + match.group(1)
                    )

                # ------------------------------------------------
                # Check redirected URL
                # ------------------------------------------------

                final_url = str(
                    response.url
                )

                if final_url.startswith(
                    "https://keyframe-staff-list.com/staff/"
                ):

                    return final_url

        except (
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ):

            continue

        except Exception:

            continue

    return None


# ============================================================
# BUILD GROUPED WORKS
# ============================================================

def build_grouped_works(
    results,
):

    grouped = {}

    seen = {}

    for result in results:

        role = result.get(
            "role",
            "",
        )

        if not role:
            continue

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

        # Prevent duplicates
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
# SORT WORK NAMES
# ============================================================

def sort_work_names(
    work_names,
):

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
# LOOK UP ONE ANIME
# ============================================================

async def get_animator_works(
    animator,
    anime_slug,
    anime_title=None,
):

    if not anime_title:

        anime_title = (
            anime_slug
            .replace(
                "-",
                " ",
            )
            .title()
        )

    print()
    print(
        "-" * 70
    )
    print(
        f"Anime: {anime_title}"
    )
    print(
        f"Slug:  {anime_slug}"
    )
    print(
        f"Staff: {animator}"
    )
    print(
        "-" * 70
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

            print(
                f"No work found for "
                f"{animator} in {anime_title}"
            )

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "local",

            }

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

                    profile_url = (
                        await get_staff_profile(
                            session,
                            person_id,
                        )
                    )

        except Exception as e:

            print(
                f"Profile lookup failed: {e}"
            )

        grouped = build_grouped_works(
            results
        )

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
    # RUNTIME KFSL
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

        page = await get_anime_page(
            session,
            anime_slug,
        )

        if not page:

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "unavailable",

            }

        data = extract_staff_list_data(
            page
        )

        if not data:

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "unavailable",

            }

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator,
        )

        if not results:

            print(
                f"No work found for "
                f"{animator} in {anime_title}"
            )

            return {

                "name": animator,

                "anime": anime_title,

                "slug": anime_slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "runtime",

            }

        grouped = build_grouped_works(
            results
        )

        for role in grouped:

            grouped[role] = sort_work_names(
                grouped[role]
            )

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
# MULTI-SEASON LOOKUP
# ============================================================

async def get_animator_works_all(
    animator,
    anime_list,
):

    results = []

    if not anime_list:

        return results

    print()
    print(
        "=" * 70
    )
    print(
        f"SEARCHING: {animator}"
    )
    print(
        f"ANIME ENTRIES: {len(anime_list)}"
    )
    print(
        "=" * 70
    )

    for item in anime_list:

        if not isinstance(
            item,
            dict,
        ):

            continue

        slug = item.get(
            "slug"
        )

        title = item.get(
            "title"
        )

        if not slug:

            continue

        # ----------------------------------------------------
        # Important:
        # Strip accidental whitespace.
        # ----------------------------------------------------

        slug = str(
            slug
        ).strip()

        if title:

            title = str(
                title
            ).strip()

        try:

            result = await get_animator_works(
                animator,
                slug,
                anime_title=title,
            )

        except Exception as e:

            print(
                f"Season lookup failed: "
                f"{slug}: {e}"
            )

            result = {

                "name": animator,

                "anime": title or slug,

                "slug": slug,

                "profile_url": None,

                "groups": {},

                "found": False,

                "source": "unavailable",

            }

        if (
            result.get("found")
            and result.get("groups")
        ):

            results.append(
                result
            )

    print()
    print(
        "=" * 70
    )
    print(
        f"FOUND WORKS IN "
        f"{len(results)} ANIME ENTRIES"
    )
    print(
        "=" * 70
    )

    return results


# ============================================================
# FORMAT GROUPS
# ============================================================

def format_groups(
    groups,
):

    formatted = {}

    for role, works in groups.items():

        display_role = get_role_display_name(
            role
        )

        formatted.setdefault(
            display_role,
            [],
        )

        for work in works:

            if work not in formatted[
                display_role
            ]:

                formatted[
                    display_role
                ].append(
                    work
                )

    return formatted


# ============================================================
# DEBUG NAME TEST
# ============================================================

def debug_name_matching(
    animator,
    names,
):

    print()
    print(
        "=" * 70
    )
    print(
        "NAME MATCH DEBUG"
    )
    print(
        "=" * 70
    )

    print(
        f"Target: {animator}"
    )

    print(
        f"Target variants:"
    )

    for variant in sorted(
        get_name_variants(
            animator
        )
    ):

        print(
            f"  - {variant}"
        )

    print(
        "Candidate names:"
    )

    for name in sorted(
        names
    ):

        print(
            f"  - {name}"
        )

    print(
        f"RESULT: "
        f"{names_match(animator, names)}"
    )

    print(
        "=" * 70
    )


# ============================================================
# TEST
# ============================================================

async def test():

    # --------------------------------------------------------
    # Change this animator to test someone else.
    # --------------------------------------------------------

    animator = "Chengxi Huang"

    # --------------------------------------------------------
    # ATTACK ON TITAN
    #
    # Keep only the slugs that actually exist in your
    # downloaded KFSL JSON files.
    # --------------------------------------------------------

    anime_list = [

        {
            "slug":
                "shingeki-no-kyojin",
            "title":
                "Attack on Titan",
        },

        {
            "slug":
                "shingeki-no-kyojin-2",
            "title":
                "Attack on Titan Season 2",
        },

        {
            "slug":
                "shingeki-no-kyojin-3",
            "title":
                "Attack on Titan Season 3",
        },

        {
            "slug":
                "shingeki-no-kyojin-the-final-season",
            "title":
                "Attack on Titan The Final Season",
        },

        {
            "slug":
                "shingeki-no-kyojin-the-final-season-part-2",
            "title":
                "Attack on Titan The Final Season Part 2",
        },

        {
            "slug":
                "shingeki-no-kyojin-the-final-season-kanketsu-hen-zenpen",
            "title":
                "Attack on Titan The Final Season: The Final Chapters Part 1",
        },

        {
            "slug":
                "shingeki-no-kyojin-the-final-season-kanketsu-hen-kouhen",
            "title":
                "Attack on Titan The Final Season: The Final Chapters Part 2",
        },

        {
            "slug":
                "shingeki-no-kyojin-ova",
            "title":
                "Attack on Titan OVA",
        },

    ]

    print()
    print(
        "=" * 70
    )

    print(
        "TESTING MULTI-SEASON STAFF SCRAPER"
    )

    print(
        "=" * 70
    )

    results = await get_animator_works_all(
        animator,
        anime_list,
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    if not results:

        print()
        print(
            f"No work found for {animator}"
        )

        print(
            "Checked the supplied anime seasons, "
            "movies, OVAs, and specials."
        )

        return

    for result in results:

        print()
        print(
            f"📺 {result['anime']}"
        )

        formatted = format_groups(
            result["groups"]
        )

        for role, works in formatted.items():

            print(
                f"{role}: "
                + ", ".join(
                    str(x)
                    for x in works
                )
            )

        if result.get(
            "profile_url"
        ):

            print(
                f"Profile: "
                f"{result['profile_url']}"
            )

    print()
    print(
        "=" * 70
    )

    print(
        "DONE"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        test()
    )

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
    # Existing aliases
    "keiichiro watanabe": "keiichirou watanabe",
    "kohei hirota": "kouhei hirota",

    # Chengxi Huang
    "chengxi huang": "chengxi huang",
    "huang chengxi": "chengxi huang",
    "黄成希": "chengxi huang",
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):
    """
    Normalize names / role names / menu names.

    Preserves Unicode characters such as:
        黄成希

    Examples:
        Chengxi Huang -> chengxi huang
        Huang Chengxi -> chengxi huang
        Keiichiro Watanabe -> keiichirou watanabe
        #17 (BD) -> 17 bd
        黄成希 -> chengxi huang
    """

    if not text:
        return ""

    text = str(text).lower().strip()

    # Preserve Unicode letters/numbers.
    text = re.sub(
        r"[^\w]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = " ".join(
        text.split()
    )

    return NAME_ALIASES.get(
        text,
        text,
    )


# ============================================================
# ADD NAME TO NAME SET
# ============================================================

def add_person_name(
    names,
    value,
):
    """
    Add a staff name and useful variants.

    Handles:
        Chengxi Huang
        Huang Chengxi
        黄成希

    without assuming that every name is Western-style.
    """

    if not isinstance(
        value,
        str,
    ):
        return

    value = value.strip()

    if not value:
        return

    # --------------------------------------------------------
    # Original normalized name
    # --------------------------------------------------------

    normalized = normalize(
        value
    )

    if not normalized:
        return

    names.add(
        normalized
    )

    # --------------------------------------------------------
    # Add reversed two-part name
    #
    # Example:
    #
    # Chengxi Huang
    # Huang Chengxi
    # --------------------------------------------------------

    parts = normalized.split()

    if len(parts) == 2:

        reversed_name = (
            f"{parts[1]} {parts[0]}"
        )

        names.add(
            reversed_name
        )


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

    # --------------------------------------------------------
    # Recursive value extractor
    # --------------------------------------------------------

    def collect_values(value):

        if isinstance(
            value,
            str,
        ):

            add_person_name(
                names,
                value,
            )

        elif isinstance(
            value,
            dict,
        ):

            for subvalue in value.values():

                collect_values(
                    subvalue
                )

        elif isinstance(
            value,
            list,
        ):

            for item in value:

                collect_values(
                    item
                )

    # --------------------------------------------------------
    # Direct name fields
    # --------------------------------------------------------

    for key in (
        "en",
        "ja",
        "jp",
        "zh",
        "name",
        "romanized",
        "romaji",
        "japanese",
        "chinese",
    ):

        if key in person:

            collect_values(
                person.get(key)
            )

    # --------------------------------------------------------
    # pn container
    # --------------------------------------------------------

    if "pn" in person:

        collect_values(
            person.get("pn")
        )

    # --------------------------------------------------------
    # names container
    # --------------------------------------------------------

    if "names" in person:

        collect_values(
            person.get("names")
        )

    # --------------------------------------------------------
    # Chengxi Huang explicit variants
    #
    # KFSL can represent the same person using:
    #
    #   黄成希
    #   Huang Chengxi
    #   Chengxi Huang
    #
    # --------------------------------------------------------

    if (
        "黄成希" in names
        or "huang chengxi" in names
        or "chengxi huang" in names
    ):

        names.add(
            "chengxi huang"
        )

        names.add(
            "huang chengxi"
        )

        names.add(
            "黄成希"
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
# PERSON MATCHER
# ============================================================

def person_matches(
    person,
    animator,
):
    """
    Check whether a KFSL person matches the requested animator.

    Supports:

        Chengxi Huang
        Huang Chengxi
        黄成希

    and automatically handles reversed two-part names.
    """

    if not isinstance(
        person,
        dict,
    ):
        return False

    target = normalize(
        animator
    )

    if not target:
        return False

    names = get_person_names(
        person
    )

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if target in names:
        return True

    # --------------------------------------------------------
    # Reversed target
    #
    # Chengxi Huang
    # Huang Chengxi
    # --------------------------------------------------------

    target_parts = target.split()

    if len(target_parts) == 2:

        reversed_target = (
            f"{target_parts[1]} {target_parts[0]}"
        )

        if reversed_target in names:
            return True

    # --------------------------------------------------------
    # Explicit Chengxi Huang handling
    # --------------------------------------------------------

    if target == "chengxi huang":

        if "黄成希" in names:
            return True

        if "huang chengxi" in names:
            return True

        if "chengxi huang" in names:
            return True

    return False


# ============================================================
# FIND PERSON ID
# ============================================================

def find_person_id(
    data,
    animator,
):

    target = normalize(
        animator
    )

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            if person_matches(
                obj,
                target,
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
# LOAD LOCAL JSON
# ============================================================

def load_local_json(slug):
    """
    Load local KFSL JSON if available.
    """

    path = os.path.join(
        BASE_DIR,
        f"{slug}.json",
    )

    if not os.path.exists(
        path
    ):
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

    except Exception as e:

        print(
            f"JSON error: {e}"
        )

        return None


# ============================================================
# EXTRACT STAFF LIST DATA
# ============================================================

def extract_staff_list_data(
    page_html,
):

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

    if not menu_name:
        return ""

    return str(
        menu_name
    ).strip()


# ============================================================
# GET WORK TYPE
# ============================================================

def get_work_type(menu_name):

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

    # Episode
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

    if not menu_name:
        return None

    text = str(
        menu_name
    ).strip()

    normalized = normalize(
        text
    )

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

    if not role_name:
        return ""

    text = str(
        role_name
    ).strip()

    normalized = normalize(
        text
    )

    if normalized in (
        "key animation",
        "key animator",
    ):

        return "Key Animation"

    if normalized in (
        "2nd key animation",
        "second key animation",
        "2nd key animator",
        "second key animator",
    ):

        return "2nd Key Animation"

    if normalized in (
        "storyboard",
        "story board",
    ):

        return "Storyboard"

    if normalized in (
        "episode director",
        "episode director ed",
    ):

        return "Episode Director"

    if normalized in (
        "storyboard episode director",
        "storyboard episode director ed",
        "storyboard episode director sb ed",
    ):

        return "Storyboard / Episode Director"

    if normalized in (
        "animation director",
        "animation director ad",
    ):

        return "Animation Director"

    if normalized in (
        "assistant animation director",
        "assistant animation director aad",
        "assistant animation director ass ad",
    ):

        return "Assistant Animation Director"

    if normalized in (
        "chief animation director",
        "chief animation director cad",
    ):

        return "Chief Animation Director"

    if normalized in (
        "character design",
        "character designer",
    ):

        return "Character Design"

    if normalized in (
        "art director",
        "art director ad",
    ):

        return "Art Director"

    if normalized in (
        "art board",
        "artboard",
    ):

        return "Art Board"

    if normalized in (
        "main animator",
        "main animation",
    ):

        return "Main Animator"

    return text


# ============================================================
# GET ROLE DISPLAY NAME
# ============================================================

def get_role_display_name(role):

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

                # ------------------------------------------------
                # Ignore studios
                # ------------------------------------------------

                if person.get(
                    "isStudio"
                ):
                    continue

                # ------------------------------------------------
                # MATCH PERSON
                # ------------------------------------------------

                if not person_matches(
                    person,
                    animator,
                ):
                    continue

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
                    f"KFSL request failed: "
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

def build_grouped_works(results):

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

def sort_work_names(work_names):

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

    """
    Check multiple anime/season slugs.

    anime_list format:

        [
            {
                "slug": "jujutsu-kaisen",
                "title": "Jujutsu Kaisen"
            },
            {
                "slug": "jujutsu-kaisen-2nd-season",
                "title": "Jujutsu Kaisen 2nd Season"
            }
        ]
    """

    results = []

    if not anime_list:
        return results

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

        print()

        print(
            "=" * 60
        )

        print(
            f"Checking season: {title}"
        )

        print(
            f"Slug: {slug}"
        )

        print(
            "=" * 60
        )

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

        if result.get(
            "found"
        ) and result.get(
            "groups"
        ):

            results.append(
                result
            )

    return results


# ============================================================
# FORMAT GROUPS
# ============================================================

def format_groups(groups):

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

    # --------------------------------------------------------
    # CHANGE THIS TO TEST ANOTHER ANIMATOR
    # --------------------------------------------------------

    animator = "Chengxi Huang"

    anime_list = [

        {
            "slug": "attack-on-titan",
            "title": "Attack on Titan",
        },

    ]

    print()

    print(
        "=" * 70
    )

    print(
        "TESTING MULTI-SEASON STAFF WORK SCRAPER"
    )

    print(
        "=" * 70
    )

    print(
        f"Animator: {animator}"
    )

    results = await get_animator_works_all(
        animator,
        anime_list,
    )

    if not results:

        print()

        print(
            "No work found for this animator."
        )

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

    print()

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


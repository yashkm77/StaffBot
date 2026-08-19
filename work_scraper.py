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
# NORMALIZE
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = " ".join(
        text.split()
    )

    # --------------------------------------------------------
    # Name spelling aliases
    # --------------------------------------------------------

    return NAME_ALIASES.get(
        text,
        text,
    )


# ============================================================
# LOAD LOCAL JSON
# ============================================================

def load_local_json(slug):

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

    menu_name = str(
        menu_name
    ).strip()

    # --------------------------------------------------------
    # OP / ED
    # --------------------------------------------------------

    normalized = normalize(
        menu_name
    )

    if re.fullmatch(
        r"op\s*\d+",
        normalized,
    ):

        return menu_name

    if re.fullmatch(
        r"ed\s*\d+",
        normalized,
    ):

        return menu_name

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Keep the ORIGINAL KFSL menu name.
    #
    # Examples:
    #
    # 17
    # #17
    # 17 (BD)
    # #17 (BD)
    # --------------------------------------------------------

    return menu_name


# ============================================================
# GET WORK TYPE
# ============================================================

def get_work_type(menu_name):

    normalized = normalize(
        menu_name
    )

    if re.fullmatch(
        r"op\s*\d+",
        normalized,
    ):

        return "OP"

    if re.fullmatch(
        r"ed\s*\d+",
        normalized,
    ):

        return "ED"

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

    normalized = normalize(
        menu_name
    )

    # OP / ED must not become episode 1
    if re.fullmatch(
        r"(op|ed)\s*\d+",
        normalized,
    ):

        return None

    match = re.search(
        r"#?\s*(\d+)",
        str(menu_name),
    )

    if not match:
        return None

    try:

        return int(
            match.group(1)
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

            # Original KFSL menu
            "name": menu_name,

            # Original work label
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

    # --------------------------------------------------------
    # Key Animation
    # --------------------------------------------------------

    if normalized in (
        "key animation",
        "key animator",
        "key animation原画",
    ):

        return "Key Animation"

    # --------------------------------------------------------
    # Storyboard
    # --------------------------------------------------------

    if normalized == "storyboard":

        return "Storyboard"

    # --------------------------------------------------------
    # Episode Director
    # --------------------------------------------------------

    if normalized == "episode director":

        return "Episode Director"

    # --------------------------------------------------------
    # Animation Director
    # --------------------------------------------------------

    if normalized == "animation director":

        return "Animation Director"

    # --------------------------------------------------------
    # Assistant Animation Director
    # --------------------------------------------------------

    if normalized in (
        "assistant animation director",
        "assistant animation director aad",
    ):

        return "Assistant Animation Director"

    # --------------------------------------------------------
    # Chief Animation Director
    # --------------------------------------------------------

    if normalized == "chief animation director":

        return "Chief Animation Director"

    # --------------------------------------------------------
    # 2nd Key Animation
    # --------------------------------------------------------

    if normalized in (
        "2nd key animation",
        "second key animation",
    ):

        return "2nd Key Animation"

    # --------------------------------------------------------
    # Storyboard / Episode Director
    # --------------------------------------------------------

    if normalized in (
        "storyboard episode director",
        "storyboard episode director ed",
    ):

        return "Storyboard / Episode Director"

    # --------------------------------------------------------
    # Character Design
    # --------------------------------------------------------

    if normalized == "character design":

        return "Character Design"

    # --------------------------------------------------------
    # Art Director
    # --------------------------------------------------------

    if normalized == "art director":

        return "Art Director"

    # --------------------------------------------------------
    # Art Board
    # --------------------------------------------------------

    if normalized == "art board":

        return "Art Board"

    # --------------------------------------------------------
    # Main Animator
    # --------------------------------------------------------

    if normalized == "main animator":

        return "Main Animator"

    # --------------------------------------------------------
    # Unknown role
    #
    # Keep original role.
    # --------------------------------------------------------

    return text


# ============================================================
# SEARCH ONE WORK
# ============================================================

def search_episode(
    episode,
    animator,
):

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

            # =================================================
            # IMPORTANT
            #
            # NEVER change "Key Animation" to "KA" here.
            #
            # Main.py needs the canonical name.
            # =================================================

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

                if person.get(
                    "isStudio"
                ):
                    continue

                names = get_person_names(
                    person
                )

                if target not in names:
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

                    # Canonical role
                    "role": canonical_role,

                    # Numeric episode
                    "episode": episode.get(
                        "episode"
                    ),

                    # ORIGINAL KFSL work name
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
# SEARCH LOCAL JSON
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
            animator
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
            url
        ) as response:

            print(
                f"HTTP: {response.status}"
            )

            if response.status != 200:
                return None

            return await response.text()

    except Exception as e:

        print(
            f"Request error: {e}"
        )

        return None


# ============================================================
# GET STAFF PROFILE
# ============================================================

async def get_staff_profile(
    session,
    person_id,
):

    possible_urls = [

        f"https://keyframe-staff-list.com/staff/{person_id}",

        f"https://keyframe-staff-list.com/staff?id={person_id}",

    ]

    for url in possible_urls:

        try:

            async with session.get(
                url
            ) as response:

                if response.status != 200:
                    continue

                text = await response.text()

                match = re.search(
                    r'href=["\'](/staff/[a-f0-9]{40,})',
                    text,
                    re.IGNORECASE,
                )

                if match:

                    return (
                        "https://keyframe-staff-list.com"
                        + match.group(1)
                    )

        except Exception:
            continue

    return None


# ============================================================
# BUILD GROUPED WORKS
# ============================================================

def build_grouped_works(results):

    grouped = {}

    for result in results:

        role = result.get(
            "role",
            "",
        )

        if not role:
            continue

        # =====================================================
        # ALWAYS NORMALIZE ROLE AGAIN
        #
        # This protects us from old/cached scraper data.
        # =====================================================

        role = normalize_role_name(
            role
        )

        grouped.setdefault(
            role,
            [],
        )

        # =====================================================
        # KEEP ORIGINAL KFSL WORK NAME
        # =====================================================

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

        if work_name not in grouped[role]:

            grouped[role].append(
                work_name
            )

    return grouped


# ============================================================
# GET ANIMATOR WORKS
# ============================================================

async def get_animator_works(
    animator,
    anime_slug,
    anime_title=None,
):

    if not anime_title:

        anime_title = anime_slug.replace(
            "-",
            " ",
        ).title()

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

            }

        person_id = results[0].get(
            "id"
        )

        headers = {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) "
                "Version/26.0 Safari/605.1.15"
            ),

            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),

            "Accept-Language": (
                "en-US,en;q=0.9"
            ),

        }

        timeout = aiohttp.ClientTimeout(
            total=30
        )

        async with aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
        ) as session:

            profile_url = None

            if person_id:

                profile_url = await get_staff_profile(
                    session,
                    person_id,
                )

        grouped = build_grouped_works(
            results
        )

        return {

            "name": (
                results[0]["name"]
                or animator
            ),

            "anime": anime_title,

            "slug": anime_slug,

            "profile_url": profile_url,

            "groups": grouped,

        }

    # ========================================================
    # NO LOCAL JSON
    # ========================================================

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) "
            "Version/26.0 Safari/605.1.15"
        ),

    }

    timeout = aiohttp.ClientTimeout(
        total=30
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

            }

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator,
        )

        grouped = build_grouped_works(
            results
        )

        person_id = (
            results[0]["id"]
            if results
            else None
        )

        profile_url = None

        if person_id:

            profile_url = await get_staff_profile(
                session,
                person_id,
            )

        return {

            "name": (
                results[0]["name"]
                if results
                else animator
            ),

            "anime": anime_title,

            "slug": anime_slug,

            "profile_url": profile_url,

            "groups": grouped,

        }


# ============================================================
# TEST
# ============================================================

async def test():

    animator = "Keiichiro Watanabe"

    slug = "jujutsu-kaisen-2nd-season"

    anime_title = "Jujutsu Kaisen 2nd Season"

    print()
    print("=" * 70)

    works = await get_animator_works(
        animator,
        slug,
        anime_title,
    )

    print("=" * 70)

    print(
        f"Name: {works['name']}"
    )

    print(
        f"Anime: {works['anime']}"
    )

    print(
        f"Profile: {works['profile_url']}"
    )

    print()

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
    print("=" * 70)


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        test()
    )
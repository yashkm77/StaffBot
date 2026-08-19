import aiohttp
import asyncio
import json
import re
import html as html_module
import os


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
    # Keiichirou Watanabe
    "keiichiro watanabe": "keiichirou watanabe",
    "keiichiro watanabe": "keiichirou watanabe",
    "K1R0": "keiichirou watanabe",

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
        text
    )

    text = " ".join(
        text.split()
    )

    # Resolve common name spelling variants
    text = NAME_ALIASES.get(
        text,
        text
    )

    return text
# ============================================================
# LOAD LOCAL JSON
# ============================================================

def load_local_json(slug):

    path = os.path.join(
        BASE_DIR,
        f"{slug}.json"
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
            encoding="utf-8"
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

    for key in (
        "en",
        "ja"
    ):

        value = person.get(key)

        if (
            isinstance(value, str)
            and value.strip()
        ):

            names.add(
                normalize(value)
            )

    pn = person.get("pn")

    if isinstance(pn, dict):

        for key in (
            "en",
            "ja"
        ):

            value = pn.get(key)

            if (
                isinstance(value, str)
                and value.strip()
            ):

                names.add(
                    normalize(value)
                )

    return names


# ============================================================
# MAIN / PEN NAME
# ============================================================

def get_main_name(person):

    pn = person.get("pn")

    if isinstance(pn, dict):

        value = pn.get("en")

        if (
            isinstance(value, str)
            and value.strip()
        ):

            return value.strip()

    value = person.get(
        "en",
        ""
    )

    if isinstance(value, str):
        return value.strip()

    return ""


# ============================================================
# FIND PERSON ID
# ============================================================

def find_person_id(
    data,
    animator
):

    target = normalize(
        animator
    )

    def walk(obj):

        if isinstance(obj, dict):

            if target in get_person_names(obj):

                person_id = obj.get(
                    "id"
                )

                if person_id is not None:

                    return str(
                        person_id
                    )

            for value in obj.values():

                result = walk(value)

                if result:
                    return result

        elif isinstance(obj, list):

            for value in obj:

                result = walk(value)

                if result:
                    return result

        return None

    return walk(data)


# ============================================================
# EXTRACT STAFF LIST DATA
# ============================================================

def extract_staff_list_data(
    page_html
):

    pattern = re.compile(
        r'<script[^>]+id=["\']staffListData["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        re.DOTALL | re.IGNORECASE
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
# EPISODES
# ============================================================

def get_episode_data(data):

    episodes = []

    if not isinstance(
        data,
        dict
    ):

        return episodes

    menus = data.get(
        "menus",
        []
    )

    if not isinstance(
        menus,
        list
    ):

        return episodes

    for menu in menus:

        if not isinstance(
            menu,
            dict
        ):

            continue

        menu_name = str(
            menu.get(
                "name",
                ""
            )
        )

        match = re.search(
            r"#?(\d+)",
            menu_name
        )

        if not match:
            continue

        episode_number = int(
            match.group(1)
        )

        credits = menu.get(
            "credits"
        )

        if not isinstance(
            credits,
            list
        ):

            continue

        episodes.append({
            "episode": episode_number,
            "name": menu_name,
            "credits": credits
        })

    episodes.sort(
        key=lambda x: x["episode"]
    )

    return episodes


# ============================================================
# SEARCH ONE EPISODE
# ============================================================

def search_episode(
    episode,
    animator
):

    target = normalize(
        animator
    )

    results = []

    credits = episode.get(
        "credits",
        []
    )

    for credit_group in credits:

        if not isinstance(
            credit_group,
            dict
        ):

            continue

        roles = credit_group.get(
            "roles",
            []
        )

        if not isinstance(
            roles,
            list
        ):

            continue

        for role in roles:

            if not isinstance(
                role,
                dict
            ):

                continue

            role_name = str(
                role.get(
                    "name",
                    ""
                )
            ).strip()

            if not role_name:
                continue

            role_short = ROLE_NAMES.get(
                role_name,
                role_name
            )

            staff = role.get(
                "staff",
                []
            )

            if not isinstance(
                staff,
                list
            ):

                continue

            for person in staff:

                if not isinstance(
                    person,
                    dict
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
                    ""
                )

                if not isinstance(
                    displayed_name,
                    str
                ):

                    displayed_name = ""

                displayed_name = displayed_name.strip()

                results.append({
                    "name": displayed_name,
                    "main_name": get_main_name(person),
                    "id": person.get("id"),

                    # Full role name
                    "role": role_name,

                    # Short role name
                    "role_short": role_short
                })

    return results


# ============================================================
# SEARCH LOCAL JSON
# ============================================================

def search_local_json(
    data,
    anime_title,
    slug,
    animator
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
                "episode": episode["episode"],
                "role": match["role"],
                "role_short": match["role_short"],
                "name": match["name"],
                "main_name": match["main_name"],
                "id": match["id"]
            })

    return results


# ============================================================
# GET ANIME PAGE
# ============================================================

async def get_anime_page(
    session,
    slug
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
# STAFF PROFILE
# ============================================================

async def get_staff_profile(
    session,
    person_id
):

    possible_urls = [
        f"{BASE_URL}/{person_id}",
        f"{BASE_URL}?id={person_id}",
    ]

    for url in possible_urls:

        try:

            async with session.get(
                url
            ) as response:

                if response.status != 200:
                    continue

                text = await response.text()

                # We don't need clickable profile URLs
                # for /work.
                #
                # This function is kept only for compatibility.

                return None

        except Exception:
            continue

    return None


# ============================================================
# BUILD GROUPED WORKS
# ============================================================

def build_grouped_works(results):

    grouped = {}

    for result in results:

        role = result["role"]

        role_short = result.get(
            "role_short",
            role
        )

        episode = result["episode"]

        if role not in grouped:

            grouped[role] = {
                "short": role_short,
                "episodes": []
            }

        if episode not in grouped[role]["episodes"]:

            grouped[role]["episodes"].append(
                episode
            )

    # Sort episodes
    for role in grouped:

        grouped[role]["episodes"].sort()

    return grouped


# ============================================================
# GET ANIMATOR WORKS
# ============================================================

async def get_animator_works(
    animator,
    anime_slug,
    anime_title=None
):

    if not anime_title:

        anime_title = anime_slug.replace(
            "-",
            " "
        ).title()

    # --------------------------------------------------------
    # LOCAL JSON FIRST
    # --------------------------------------------------------

    data = load_local_json(
        anime_slug
    )

    if data is not None:

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator
        )

        if not results:

            return {
                "name": animator,
                "anime": anime_title,
                "slug": anime_slug,
                "profile_url": None,
                "groups": {}
            }

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
            "profile_url": None,
            "groups": grouped
        }

    # --------------------------------------------------------
    # NO LOCAL JSON
    # --------------------------------------------------------

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
        )
    }

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:

        page = await get_anime_page(
            session,
            anime_slug
        )

        if not page:

            return {
                "name": animator,
                "anime": anime_title,
                "slug": anime_slug,
                "profile_url": None,
                "groups": {}
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
                "groups": {}
            }

        results = search_local_json(
            data,
            anime_title,
            anime_slug,
            animator
        )

        grouped = build_grouped_works(
            results
        )

        return {
            "name": (
                results[0]["name"]
                if results
                else animator
            ),
            "anime": anime_title,
            "slug": anime_slug,
            "profile_url": None,
            "groups": grouped
        }


# ============================================================
# TEST
# ============================================================

async def test():

    animator = "Keiichirou Watanabe"

    slug = "jujutsu-kaisen-2nd-season"

    anime_title = "Jujutsu Kaisen 2nd Season"

    print()
    print("=" * 70)

    works = await get_animator_works(
        animator,
        slug,
        anime_title
    )

    print("=" * 70)

    print(
        f"Name: {works['name']}"
    )

    print(
        f"Anime: {works['anime']}"
    )

    print()

    for role, info in works["groups"].items():

        print(role)

        print(
            f"{info['short']}: "
            + ", ".join(
                f"#{episode:02d}"
                for episode in info["episodes"]
            )
        )

        print()

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())
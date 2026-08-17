import aiohttp
import asyncio
import json
import re
import html as html_module


BASE_URL = "https://keyframe-staff-list.com/staff"


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
}


# ============================================================
# NORMALIZE NAME
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

    return " ".join(
        text.split()
    )


# ============================================================
# EXTRACT KEYFRAME STAFF JSON
# ============================================================

def extract_staff_list_data(page_html):

    pattern = re.compile(
        r'<script[^>]+id=["\']staffListData["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        re.DOTALL | re.IGNORECASE
    )

    match = pattern.search(page_html)

    if not match:

        print(
            "staffListData was not found."
        )

        return None

    raw_json = match.group(1).strip()

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
# GET ALL POSSIBLE NAMES FOR A PERSON
#
# This supports:
#
# - English name
# - Japanese name
# - Pen name
# - Main name
# - Real name
# - Alternate name
# ============================================================

def get_person_names(person):

    names = set()

    # English name
    en_name = person.get("en")

    if en_name:

        names.add(
            normalize(en_name)
        )

    # Japanese name
    ja_name = person.get("ja")

    if ja_name:

        names.add(
            normalize(ja_name)
        )

    # Pen name object
    pn = person.get("pn")

    if isinstance(pn, dict):

        pn_en = pn.get("en")

        if pn_en:

            names.add(
                normalize(pn_en)
            )

        pn_ja = pn.get("ja")

        if pn_ja:

            names.add(
                normalize(pn_ja)
            )

    # Other possible main/real name fields
    for key in (
        "main",
        "mainName",
        "main_name",
        "realName",
        "real_name",
        "alternate",
        "alternative"
    ):

        value = person.get(key)

        if isinstance(value, str):

            if value.strip():

                names.add(
                    normalize(value)
                )

        elif isinstance(value, dict):

            for subvalue in value.values():

                if isinstance(
                    subvalue,
                    str
                ):

                    names.add(
                        normalize(subvalue)
                    )

    return names


# ============================================================
# GET MAIN / PEN NAME
# ============================================================

def get_main_name(person):

    pn = person.get("pn")

    if isinstance(pn, dict):

        pn_en = pn.get("en")

        if pn_en:

            return pn_en.strip()

    for key in (
        "main",
        "mainName",
        "main_name",
        "realName",
        "real_name"
    ):

        value = person.get(key)

        if isinstance(value, str):

            if value.strip():

                return value.strip()

    return (
        person.get(
            "en",
            ""
        ).strip()
    )


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

            display_role = ROLE_NAMES.get(
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

                # ------------------------------------------------
                # IMPORTANT:
                # Match both displayed and main/pen names.
                # ------------------------------------------------

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

                displayed_name = (
                    displayed_name.strip()
                )

                main_name = get_main_name(
                    person
                )

                results.append({

                    "name":
                        displayed_name,

                    "main_name":
                        main_name,

                    "id":
                        person.get(
                            "id"
                        ),

                    "role":
                        display_role

                })

    return results


# ============================================================
# GET EPISODES FROM KEYFRAME PAGE
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

        # ----------------------------------------------------
        # Extract episode number
        #
        # Examples:
        # #01
        # #1
        # Episode 01
        # ----------------------------------------------------

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

            "episode":
                episode_number,

            "name":
                menu_name,

            "credits":
                credits

        })

    # Newest episode first
    episodes.sort(
        key=lambda x: x["episode"],
        reverse=True
    )

    return episodes


# ============================================================
# DOWNLOAD ANIME PAGE
# ============================================================

async def get_anime_page(
    session,
    slug
):

    url = (
        f"{BASE_URL}/{slug}"
    )

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
# SEARCH ANIME FOR ANIMATOR
# ============================================================

async def search_anime(
    session,
    slug,
    anime_title,
    animator
):

    page = await get_anime_page(
        session,
        slug
    )

    if not page:

        return []

    print(
        f"HTML length: {len(page)}"
    )

    data = extract_staff_list_data(
        page
    )

    if not data:

        return []

    print(
        f"Page title: {data.get('title')}"
    )

    episodes = get_episode_data(
        data
    )

    print(
        f"Episodes found: {len(episodes)}"
    )

    results = []

    for episode in episodes:

        matches = search_episode(
            episode,
            animator
        )

        for match in matches:

            results.append({

                "anime":
                    anime_title,

                "slug":
                    slug,

                "episode":
                    episode["episode"],

                "role":
                    match["role"],

                "name":
                    match["name"],

                "main_name":
                    match["main_name"],

                "id":
                    match["id"]

            })

    return results


# ============================================================
# PUBLIC FUNCTION USED BY MAIN.PY
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

    headers = {

        "User-Agent":
            (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) "
                "Version/26.0 Safari/605.1.15"
            ),

        "Accept":
            (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),

        "Accept-Language":
            "en-US,en;q=0.9"

    }

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:

        results = await search_anime(
            session,
            anime_slug,
            anime_title,
            animator
        )

    return results


# ============================================================
# TEST
# ============================================================

async def test():

    animator = "Hachidai Takayama"

    slug = "my-hero-academia"

    anime_title = "My Hero Academia"

    print()

    print(
        "=" * 70
    )

    print(
        f"Animator: {animator}"
    )

    print(
        f"Anime: {anime_title}"
    )

    print(
        f"Slug: {slug}"
    )

    print(
        "=" * 70
    )

    print()

    results = await get_animator_works(
        animator,
        slug,
        anime_title
    )

    print()

    print(
        "=" * 70
    )

    print(
        f"FOUND {len(results)} CREDIT(S)"
    )

    print(
        "=" * 70
    )

    print()

    if not results:

        print(
            "No credits found."
        )

        return

    for work in results:

        print(
            f"Episode: #{work['episode']:02d}"
        )

        print(
            f"Role: {work['role']}"
        )

        print(
            f"Displayed name: {work['name']}"
        )

        print(
            f"Main/Pen name: {work['main_name']}"
        )

        print(
            f"ID: {work['id']}"
        )

        print(
            "-" * 70
        )


# ============================================================
# START SCRIPT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        test()
    )
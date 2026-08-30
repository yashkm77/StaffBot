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
BASE_DOMAIN = "https://keyframe-staff-list.com"
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
#
# These are applied to the SEARCH QUERY.
#
# Example:
#
# Chengxi Huang
#     ->
# chengxi huang
#
# and we also explicitly know:
#
# Chengxi Huang <-> 黄成希
#
# ============================================================

NAME_ALIASES = {

    # Existing aliases
    "keiichiro watanabe": "keiichirou watanabe",
    "kohei hirota": "kouhei hirota",

    # Chengxi Huang
    "chengxi huang": "chengxi huang",
    "huang chengxi": "chengxi huang",
    "黄成希": "chengxi huang",
    "成希 黄": "chengxi huang",
    "黄 成希": "chengxi huang",
}


# ============================================================
# MULTI-NAME ALIASES
# ============================================================
#
# This is more powerful than NAME_ALIASES.
#
# A search for one name can match ANY of these names.
#
# ============================================================

PERSON_NAME_ALIASES = {

    "chengxi huang": {
        "chengxi huang",
        "huang chengxi",
        "黄成希",
    },

    "keiichirou watanabe": {
        "keiichirou watanabe",
        "keiichiro watanabe",
    },

    "kouhei hirota": {
        "kouhei hirota",
        "kohei hirota",
    },
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):
    """
    Normalize names / roles / menu names.

    Unicode is preserved.

    Examples:

        Chengxi Huang
            -> chengxi huang

        黄成希
            -> 黄成希

        #17 (BD)
            -> 17 bd

        Storyboard / Episode Director
            -> storyboard episode director
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

    # Replace punctuation while preserving Unicode letters/numbers
    text = re.sub(
        r"[^\w]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = " ".join(
        text.split()
    )

    return text


# ============================================================
# NORMALIZE SEARCH NAME
# ============================================================

def normalize_search_name(name):
    """
    Normalize the user's animator query.

    Applies aliases such as:

        Kohei Hirota
            -> kouhei hirota

        黄成希
            -> chengxi huang

    """

    normalized = normalize(name)

    if not normalized:
        return ""

    return NAME_ALIASES.get(
        normalized,
        normalized,
    )


# ============================================================
# GET SEARCH ALIASES
# ============================================================

def get_search_aliases(name):
    """
    Return every known form of a person's name.

    Chengxi Huang returns:

        chengxi huang
        huang chengxi
        黄成希
    """

    normalized = normalize(name)

    canonical = NAME_ALIASES.get(
        normalized,
        normalized,
    )

    aliases = set()

    if normalized:
        aliases.add(normalized)

    if canonical:
        aliases.add(canonical)

    aliases.update(
        PERSON_NAME_ALIASES.get(
            canonical,
            set(),
        )
    )

    return {
        normalize(x)
        for x in aliases
        if normalize(x)
    }


# ============================================================
# NAME MATCH
# ============================================================

def names_match(
    target_name,
    person_names,
):
    """
    Determine whether a target animator matches
    any name belonging to a KFSL person.

    This is the important fix for:

        Chengxi Huang
            <->

        黄成希
    """

    target_aliases = get_search_aliases(
        target_name
    )

    if not target_aliases:
        return False

    normalized_person_names = {
        normalize(x)
        for x in person_names
        if normalize(x)
    }

    # Direct match
    if target_aliases & normalized_person_names:
        return True

    # --------------------------------------------------------
    # Extra Chinese / Japanese safety
    # --------------------------------------------------------
    #
    # If the target is romanized but the JSON only contains
    # a CJK name, our explicit aliases above handle known
    # people.
    #
    # Do NOT perform fuzzy matching on CJK names because
    # that can create false positives.
    #

    return False


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
            f"JSON error for {slug}: {e}"
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
    # Direct name fields
    # --------------------------------------------------------

    direct_fields = (
        "en",
        "ja",
        "jp",
        "zh",
        "name",
        "romanized",
        "romaji",
        "japanese",
        "chinese",
        "english",
        "native",
    )

    for key in direct_fields:

        value = person.get(
            key
        )

        if isinstance(
            value,
            str,
        ):

            add_name(value)

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

        for key, value in pn.items():

            if isinstance(
                value,
                str,
            ):

                add_name(value)

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

                add_name(value)

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

                add_name(value)

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
            "romanized",
            "romaji",
        ):

            value = pn.get(
                key
            )

            if isinstance(
                value,
                str,
            ) and value.strip():

                return value.strip()

    for key in (
        "en",
        "name",
        "romanized",
        "romaji",
    ):

        value = person.get(
            key,
            "",
        )

        if isinstance(
            value,
            str,
        ) and value.strip():

            return value.strip()

    return ""


# ============================================================
# FIND PERSON ID
# ============================================================

def find_person_id(
    data,
    animator,
):

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            names = get_person_names(
                obj
            )

            if names_match(
                animator,
                names,
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

    # --------------------------------------------------------
    # OP
    # --------------------------------------------------------

    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "OP"

    # --------------------------------------------------------
    # ED
    # --------------------------------------------------------

    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "ED"

    # --------------------------------------------------------
    # Episode
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
        "assistant animation director ass aad",
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

                names = get_person_names(
                    person
                )

                # ------------------------------------------------
                # IMPORTANT:
                #
                # Use alias-aware matching instead of:
                #
                # target in names
                #
                # ------------------------------------------------

                if not names_match(
                    animator,
                    names,
                ):

                    continue

                displayed_name = ""

                for key in (
                    "en",
                    "name",
                    "romanized",
                    "romaji",
                ):

                    value = person.get(
                        key,
                        "",
                    )

                    if isinstance(
                        value,
                        str,
                    ) and value.strip():

                        displayed_name = value.strip()
                        break

                # If no English name exists, use main name
                if not displayed_name:

                    displayed_name = get_main_name(
                        person
                    )

                # If still empty, use the query
                if not displayed_name:

                    displayed_name = animator

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
# REMOVE DUPLICATE RESULTS
# ============================================================

def deduplicate_results(results):

    unique = []

    seen = set()

    for result in results:

        key = (

            result.get(
                "anime",
                "",
            ),

            result.get(
                "slug",
                "",
            ),

            result.get(
                "episode",
            ),

            result.get(
                "work_name",
                "",
            ),

            result.get(
                "role",
                "",
            ),

            result.get(
                "id",
            ),

        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            result
        )

    return unique


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

        "Referer": BASE_DOMAIN + "/",

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

                # ------------------------------------------------
                # Standard staff profile URL
                # ------------------------------------------------

                match = re.search(
                    r'href=["\'](/staff/[a-f0-9]{40,})["\']',
                    text,
                    re.IGNORECASE,
                )

                if match:

                    return (
                        BASE_DOMAIN
                        + match.group(1)
                    )

                # ------------------------------------------------
                # Redirected profile
                # ------------------------------------------------

                final_url = str(
                    response.url
                )

                if final_url.startswith(
                    BASE_DOMAIN + "/staff/"
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

        # --------------------------------------------------------
        # Prevent duplicate work under the same role
        # --------------------------------------------------------

        work_key = normalize(
            work_name
        )

        if work_key in seen[role]:
            continue

        seen[role].add(
            work_key
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

    print()
    print(
        f"Checking season: {anime_title}"
    )
    print(
        f"Slug: {anime_slug}"
    )
    print(
        f"Staff: {animator}"
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

        results = deduplicate_results(
            results
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

        person_id = None

        for result in results:

            if result.get(
                "id"
            ) is not None:

                person_id = result.get(
                    "id"
                )

                break

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

    try:

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

            results = deduplicate_results(
                results
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

            person_id = None

            for result in results:

                if result.get(
                    "id"
                ) is not None:

                    person_id = result.get(
                        "id"
                    )

                    break

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

    except asyncio.TimeoutError:

        print(
            f"Runtime KFSL timeout: {anime_slug}"
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

    except aiohttp.ClientError as e:

        print(
            f"Runtime KFSL error: {e}"
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


# ============================================================
# MULTI-SEASON LOOKUP
# ============================================================

async def get_animator_works_all(
    animator,
    anime_list,
):

    """
    Check multiple anime/season slugs.

    Duplicate slugs are automatically removed.

    Example:

        [
            {
                "slug": "shingeki-no-kyojin",
                "title": "Attack on Titan"
            },
            {
                "slug": "shingeki-no-kyojin-season-2",
                "title": "Attack on Titan Season 2"
            }
        ]
    """

    results = []

    if not anime_list:
        return results

    # ========================================================
    # REMOVE DUPLICATE SLUGS
    # ========================================================

    unique_anime = []

    seen_slugs = set()

    for item in anime_list:

        if not isinstance(
            item,
            dict,
        ):
            continue

        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        if not slug:
            continue

        slug_key = normalize(
            slug
        )

        if slug_key in seen_slugs:

            print(
                f"Skipping duplicate slug: {slug}"
            )

            continue

        seen_slugs.add(
            slug_key
        )

        unique_anime.append(
            item
        )

    # ========================================================
    # CHECK
    # ========================================================

    for item in unique_anime:

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

        if (
            result.get("found")
            and result.get("groups")
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

    # --------------------------------------------------------
    # Remove duplicate works after formatting
    # --------------------------------------------------------

    for role in formatted:

        formatted[role] = list(
            dict.fromkeys(
                formatted[role]
            )
        )

        formatted[role] = sort_work_names(
            formatted[role]
        )

    return formatted


# ============================================================
# DEBUG PERSON SEARCH
# ============================================================

def debug_person_search(
    data,
    animator,
):
    """
    Useful when an animator still isn't found.

    Shows people whose names contain part of the query.
    """

    target_aliases = get_search_aliases(
        animator
    )

    print()
    print(
        "=" * 70
    )
    print(
        f"DEBUG NAME SEARCH: {animator}"
    )
    print(
        f"Search aliases: {sorted(target_aliases)}"
    )
    print(
        "=" * 70
    )

    matches = []

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            names = get_person_names(
                obj
            )

            if names:

                for target in target_aliases:

                    for name in names:

                        if (
                            target in name
                            or name in target
                        ):

                            person_id = obj.get(
                                "id"
                            )

                            matches.append({

                                "id": person_id,

                                "names": sorted(
                                    names
                                ),

                            })

                            break

            for value in obj.values():

                walk(value)

        elif isinstance(
            obj,
            list,
        ):

            for value in obj:

                walk(value)

    walk(data)

    # Remove duplicates
    unique = []

    seen = set()

    for item in matches:

        key = (
            item.get("id"),
            tuple(
                item.get(
                    "names",
                    []
                )
            ),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    for item in unique:

        print(
            f"ID: {item['id']}"
        )

        print(
            "Names:"
        )

        for name in item["names"]:

            print(
                f"  - {name}"
            )

        print(
            "-" * 50
        )

    print(
        f"DEBUG MATCHES: {len(unique)}"
    )

    print(
        "=" * 70
    )

    return unique


# ============================================================
# TEST
# ============================================================

async def test():

    # --------------------------------------------------------
    # TEST CHENGXI HUANG
    # --------------------------------------------------------

    animator = "Chengxi Huang"

    anime_list = [

        {
            "slug": "shingeki-no-kyojin",
            "title": "Shingeki No Kyojin",
        },

        {
            "slug": "shingeki-no-kyojin-season-2",
            "title": "Shingeki No Kyojin Season 2",
        },

        {
            "slug": "shingeki-no-kyojin-season-3",
            "title": "Shingeki No Kyojin Season 3",
        },

        {
            "slug": "shingeki-no-kyojin-season-3-part-2",
            "title": "Shingeki No Kyojin Season 3 Part 2",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season",
            "title": "Shingeki No Kyojin The Final Season",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-part-2",
            "title": "Shingeki No Kyojin The Final Season Part 2",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-kanketsu-hen-zenpen",
            "title": "Shingeki No Kyojin The Final Season Kanketsu Hen Zenpen",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-kanketsu-hen-kouhen",
            "title": "Shingeki No Kyojin The Final Season Kanketsu Hen Kouhen",
        },

        {
            "slug": "shingeki-no-kyojin-lost-girls",
            "title": "Shingeki No Kyojin Lost Girls",
        },

        {
            "slug": "shingeki-no-kyojin-ova",
            "title": "Shingeki No Kyojin OVA",
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
        f"SEARCHING: {animator}"
    )

    print(
        f"SEARCH ALIASES: "
        f"{sorted(get_search_aliases(animator))}"
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

    print()
    print(
        "=" * 70
    )

    print(
        f"FOUND WORKS IN {len(results)} ANIME ENTRIES"
    )

    print(
        "=" * 70
    )

    for result in results:

        print()

        print(
            f"📺 {result['anime']}"
        )

        print(
            f"Slug: {result['slug']}"
        )

        print(
            f"Source: {result['source']}"
        )

        if result.get(
            "profile_url"
        ):

            print(
                f"Profile: {result['profile_url']}"
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

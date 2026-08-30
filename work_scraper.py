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
#
# Important:
# Chengxi Huang is 黄成希.
#
# KFSL may use:
#   Chengxi Huang
#   Huang Chengxi
#   黄成希
#
# All of these are treated as the same person.
# ============================================================

NAME_ALIASES = {

    # --------------------------------------------------------
    # Chengxi Huang
    # --------------------------------------------------------

    "chengxi huang": "chengxi huang",
    "huang chengxi": "chengxi huang",
    "黄成希": "chengxi huang",

    # --------------------------------------------------------
    # Other known aliases
    # --------------------------------------------------------

    "keiichiro watanabe": "keiichirou watanabe",
    "keiichirou watanabe": "keiichirou watanabe",

    "kohei hirota": "kouhei hirota",
    "kouhei hirota": "kouhei hirota",
}


# ============================================================
# EXTRA NAME ALIASES
#
# Used when searching.
#
# This is intentionally separate from NAME_ALIASES so one
# normalized person can have several accepted spellings.
# ============================================================

PERSON_SEARCH_ALIASES = {

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

    if text is None:
        return ""

    text = str(text).strip().lower()

    if not text:
        return ""

    # Preserve Unicode letters such as:
    #
    # 黄成希
    # 進撃の巨人
    #
    text = re.sub(
        r"[^\w]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = " ".join(text.split())

    return NAME_ALIASES.get(
        text,
        text,
    )


# ============================================================
# GET SEARCH NAMES
# ============================================================

def get_search_names(animator):

    normalized = normalize(animator)

    names = set()

    if normalized:
        names.add(normalized)

    aliases = PERSON_SEARCH_ALIASES.get(
        normalized
    )

    if aliases:
        for alias in aliases:
            names.add(
                normalize(alias)
            )

    return names


# ============================================================
# PERSON NAME MATCH
# ============================================================

def person_matches(person, animator):

    target_names = get_search_names(
        animator
    )

    if not target_names:
        return False

    person_names = get_person_names(
        person
    )

    if not person_names:
        return False

    return bool(
        target_names.intersection(
            person_names
        )
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
    # Direct fields
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
        "original",
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
        "english",
        "romanized",
        "romaji",
        "name",
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

            if person_matches(
                obj,
                animator,
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

    # OP1 / OP 1 / OP#1
    if re.fullmatch(
        r"op\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "OP"

    # ED1 / ED 1 / ED#1
    if re.fullmatch(
        r"ed\s*(?:#\s*)?\d+",
        normalized,
    ):

        return "ED"

    # Anything containing a number is treated
    # as an episode/work entry.
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

    # --------------------------------------------------------
    # Some KFSL JSON variants may use another container.
    # --------------------------------------------------------

    if not isinstance(
        menus,
        list,
    ):

        menus = data.get(
            "menu",
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
                menu.get(
                    "title",
                    "",
                ),
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

            credits = menu.get(
                "credit",
                [],
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
    # Remove duplicate menu entries
    # --------------------------------------------------------

    unique = {}

    for episode in episodes:

        key = (
            episode.get("work_name"),
            episode.get("work_type"),
        )

        unique[key] = episode

    episodes = list(
        unique.values()
    )

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
        "key animation artist",
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
        "2nd key animation artist",
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
        "assistant animation director aad",
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
# EXTRACT PEOPLE FROM CREDIT
#
# Handles:
#
# staff: [...]
# staff: {...}
# person: {...}
# people: [...]
#
# This makes the parser less dependent on one exact KFSL
# JSON shape.
# ============================================================

def extract_people(value):

    people = []

    if isinstance(
        value,
        list,
    ):

        for item in value:

            if isinstance(
                item,
                dict,
            ):

                people.append(
                    item
                )

            elif isinstance(
                item,
                list,
            ):

                people.extend(
                    extract_people(item)
                )

    elif isinstance(
        value,
        dict,
    ):

        # ----------------------------------------------------
        # A direct person object
        # ----------------------------------------------------

        if (
            "en" in value
            or "ja" in value
            or "zh" in value
            or "name" in value
            or "pn" in value
            or "names" in value
            or "id" in value
        ):

            people.append(
                value
            )

        # ----------------------------------------------------
        # Otherwise search nested containers
        # ----------------------------------------------------

        for key in (
            "staff",
            "people",
            "persons",
            "person",
            "members",
            "artists",
        ):

            nested = value.get(
                key
            )

            if nested is not None:

                people.extend(
                    extract_people(nested)
                )

    return people


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

        # ----------------------------------------------------
        # Normal KFSL structure:
        #
        # {
        #   "roles": [...]
        # }
        # ----------------------------------------------------

        roles = credit_group.get(
            "roles"
        )

        if not isinstance(
            roles,
            list,
        ):

            # Some structures may have one role directly.
            if (
                "name" in credit_group
                and (
                    "staff" in credit_group
                    or "people" in credit_group
                    or "person" in credit_group
                )
            ):

                roles = [
                    credit_group
                ]

            else:

                roles = []

        for role in roles:

            if not isinstance(
                role,
                dict,
            ):
                continue

            role_name = str(
                role.get(
                    "name",
                    role.get(
                        "role",
                        "",
                    ),
                )
            ).strip()

            if not role_name:
                continue

            canonical_role = normalize_role_name(
                role_name
            )

            # ------------------------------------------------
            # Extract staff from every common field
            # ------------------------------------------------

            people = []

            for field in (
                "staff",
                "people",
                "persons",
                "person",
                "members",
                "artists",
            ):

                value = role.get(
                    field
                )

                if value is not None:

                    people.extend(
                        extract_people(
                            value
                        )
                    )

            # ------------------------------------------------
            # Remove duplicate person objects
            # ------------------------------------------------

            unique_people = []

            seen_persons = set()

            for person in people:

                person_id = person.get(
                    "id"
                )

                if person_id is not None:

                    person_key = (
                        "id",
                        str(person_id),
                    )

                else:

                    person_key = (
                        "names",
                        tuple(
                            sorted(
                                get_person_names(
                                    person
                                )
                            )
                        ),
                    )

                if person_key in seen_persons:
                    continue

                seen_persons.add(
                    person_key
                )

                unique_people.append(
                    person
                )

            # ------------------------------------------------
            # Search people
            # ------------------------------------------------

            for person in unique_people:

                # Ignore studios
                if person.get(
                    "isStudio"
                ):
                    continue

                if person.get(
                    "is_studio"
                ):
                    continue

                # ------------------------------------------------
                # THIS IS THE IMPORTANT FIX
                #
                # Search all accepted names:
                #
                # Chengxi Huang
                # Huang Chengxi
                # 黄成希
                # ------------------------------------------------

                if not person_matches(
                    person,
                    animator,
                ):
                    continue

                displayed_name = ""

                # Prefer English name
                for key in (
                    "en",
                    "english",
                    "romanized",
                    "romaji",
                    "name",
                ):

                    value = person.get(
                        key
                    )

                    if isinstance(
                        value,
                        str,
                    ) and value.strip():

                        displayed_name = value.strip()
                        break

                if not displayed_name:

                    displayed_name = get_main_name(
                        person
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

        normalized = normalize(
            text
        )

        # OP before normal episode
        op_match = re.fullmatch(
            r"op\s*(?:#\s*)?(\d+)",
            normalized,
        )

        if op_match:

            return (
                0,
                int(
                    op_match.group(1)
                ),
                text.lower(),
            )

        # ED
        ed_match = re.fullmatch(
            r"ed\s*(?:#\s*)?(\d+)",
            normalized,
        )

        if ed_match:

            return (
                2,
                int(
                    ed_match.group(1)
                ),
                text.lower(),
            )

        # Normal episode
        match = re.search(
            r"\d+",
            text,
        )

        if match:

            return (
                1,
                int(
                    match.group(0)
                ),
                text.lower(),
            )

        return (
            3,
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

        print(
            f"Matches found: {len(results)}"
        )

        if not results:

            # ------------------------------------------------
            # DEBUG NAME SEARCH
            #
            # This tells you what names were actually present
            # if Chengxi Huang still fails.
            # ------------------------------------------------

            if normalize(animator) == "chengxi huang":

                print(
                    "DEBUG: Chengxi Huang was not found "
                    "in the staff credits."
                )

                print(
                    "Accepted names:"
                )

                for name in sorted(
                    get_search_names(animator)
                ):

                    print(
                        f"  - {name}"
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
# REMOVE DUPLICATE ANIME ENTRIES
# ============================================================

def deduplicate_anime_list(anime_list):

    unique = {}

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

        # Keep first occurrence
        if slug not in unique:

            unique[slug] = {

                "slug": slug,

                "title": item.get(
                    "title"
                ) or slug,

            }

    return list(
        unique.values()
    )


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

    anime_list = deduplicate_anime_list(
        anime_list
    )

    print(
        f"Unique anime entries: {len(anime_list)}"
    )

    for item in anime_list:

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

        for work in works:

            if work not in formatted[display_role]:

                formatted[
                    display_role
                ].append(
                    work
                )

    for role in formatted:

        formatted[role] = sort_work_names(
            formatted[role]
        )

    return formatted


# ============================================================
# DEBUG ONE JSON
#
# Useful if Chengxi Huang still returns nothing.
# It prints every matching name containing:
#
# cheng
# huang
# 黄
#
# ============================================================

def debug_animator_in_json(
    data,
    animator,
):

    target_names = get_search_names(
        animator
    )

    print()
    print(
        "=" * 70
    )
    print(
        f"DEBUG SEARCH: {animator}"
    )
    print(
        f"Accepted normalized names: {sorted(target_names)}"
    )
    print(
        "=" * 70
    )

    found_people = []

    def walk(obj):

        if isinstance(
            obj,
            dict,
        ):

            names = get_person_names(
                obj
            )

            if names:

                # Exact match
                if names.intersection(
                    target_names
                ):

                    found_people.append(
                        obj
                    )

                # Partial debug match
                elif any(
                    (
                        "chengxi" in name
                        or "huang" in name
                        or "黄" in name
                        or "成希" in name
                    )
                    for name in names
                ):

                    print(
                        "Possible person:",
                        sorted(names)
                    )

            for value in obj.values():

                walk(value)

        elif isinstance(
            obj,
            list,
        ):

            for value in obj:

                walk(value)

    walk(data)

    print()
    print(
        f"EXACT PEOPLE FOUND: {len(found_people)}"
    )

    for person in found_people:

        print(
            "Names:",
            sorted(
                get_person_names(
                    person
                )
            )
        )

        print(
            "ID:",
            person.get(
                "id"
            )
        )

    print(
        "=" * 70
    )


# ============================================================
# TEST
# ============================================================

async def test():

    # --------------------------------------------------------
    # CHANGE THIS TO TEST ANIMATOR
    # --------------------------------------------------------

    animator = "Chengxi Huang"

    anime_list = [

        {
            "slug": "shingeki-no-kyojin",
            "title": "Attack on Titan",
        },

        {
            "slug": "shingeki-no-kyojin-season-2",
            "title": "Attack on Titan Season 2",
        },

        {
            "slug": "shingeki-no-kyojin-season-3",
            "title": "Attack on Titan Season 3",
        },

        {
            "slug": "shingeki-no-kyojin-season-3-part-2",
            "title": "Attack on Titan Season 3 Part 2",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season",
            "title": "Attack on Titan The Final Season",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-part-2",
            "title": "Attack on Titan The Final Season Part 2",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-kanketsu-hen-zenpen",
            "title": "Attack on Titan The Final Season Kanketsu Hen Zenpen",
        },

        {
            "slug": "shingeki-no-kyojin-the-final-season-kanketsu-hen-kouhen",
            "title": "Attack on Titan The Final Season Kanketsu Hen Kouhen",
        },

        {
            "slug": "shingeki-no-kyojin-lost-girls",
            "title": "Attack on Titan Lost Girls",
        },

        {
            "slug": "shingeki-no-kyojin-ova",
            "title": "Attack on Titan OVA",
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
        f"SEARCHING: {animator}"
    )

    print(
        "=" * 70
    )

    results = await get_animator_works_all(
        animator,
        anime_list,
    )

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


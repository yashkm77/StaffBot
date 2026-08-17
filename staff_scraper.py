import json
import os
import re


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# ANIME ALIASES
# ============================================================

ANIME_ALIASES = {

    # --------------------------------------------------------
    # Jujutsu Kaisen
    # --------------------------------------------------------

    "jjk": "jujutsu-kaisen",
    "jujutsu kaisen": "jujutsu-kaisen",

    "jjk s1": "jujutsu-kaisen-0",
    "jjk 0": "jujutsu-kaisen-0",

    "jjk s2": "jujutsu-kaisen-2nd-season",
    "jujutsu kaisen s2": "jujutsu-kaisen-2nd-season",

    "jjk s3": "jujutsu-kaisen-3rd-season-culling-game-part-1",
    "jujutsu kaisen s3": "jujutsu-kaisen-3rd-season-culling-game-part-1",

    "jjk s4": "jujutsu-kaisen-4th-season-culling-game-part-2",
    "jujutsu kaisen s4": "jujutsu-kaisen-4th-season-culling-game-part-2",


    # --------------------------------------------------------
    # Chainsaw Man
    # --------------------------------------------------------

    "csm": "chainsaw-man",
    "chainsaw man": "chainsaw-man",

    "csm s1": "chainsaw-man",
    "chainsaw man s1": "chainsaw-man",

    "csm reze": "chainsaw-man-the-movie-reze-arc",
    "csm reze arc": "chainsaw-man-the-movie-reze-arc",
    "chainsaw man reze": "chainsaw-man-the-movie-reze-arc",
    "chainsaw man reze arc": "chainsaw-man-the-movie-reze-arc",


    # --------------------------------------------------------
    # My Hero Academia
    # --------------------------------------------------------

    "mha": "my-hero-academia",
    "my hero academia": "my-hero-academia",

    "mha s1": "my-hero-academia",
    "mha s2": "my-hero-academia-2",
    "mha s3": "my-hero-academia-3",
    "mha s4": "my-hero-academia-4",
    "mha s5": "my-hero-academia-5",
    "mha s6": "my-hero-academia-6",
    "mha s7": "my-hero-academia-7",

    "mha final": "my-hero-academia-final-season",
    "mha final season": "my-hero-academia-final-season",


    # --------------------------------------------------------
    # One Piece
    # --------------------------------------------------------

    "one piece": "one-piece",
    "op": "one-piece",

    "one piece fan letter": "one-piece-fan-letter",
    "op fan letter": "one-piece-fan-letter",


    # --------------------------------------------------------
    # Bleach
    # --------------------------------------------------------

    "bleach": "bleach",

    "bleach tybw": "bleach-thousand-year-blood-war",
    "tybw": "bleach-thousand-year-blood-war",

    "bleach tybw s1": "bleach-thousand-year-blood-war",
    "tybw s1": "bleach-thousand-year-blood-war",

    "bleach tybw s2":
        "bleach-thousand-year-blood-war-the-separation",

    "tybw s2":
        "bleach-thousand-year-blood-war-the-separation",

    "bleach tybw s3":
        "bleach-thousand-year-blood-war-the-conflict",

    "tybw s3":
        "bleach-thousand-year-blood-war-the-conflict",

    "bleach tybw s4":
        "bleach-thousand-year-blood-war-the-calamity",

    "tybw s4":
        "bleach-thousand-year-blood-war-the-calamity",


    # --------------------------------------------------------
    # JoJo
    # --------------------------------------------------------

    "jojo": "jojo-s-bizarre-adventure-tv",

    "jojo s1":
        "jojo-s-bizarre-adventure-tv",

    "jojo part 1":
        "jojo-s-bizarre-adventure-tv",

    "jojo s2":
        "jojo-s-bizarre-adventure-tv",

    "jojo part 2":
        "jojo-s-bizarre-adventure-tv",

    "jojo s3":
        "jojo-s-bizarre-adventure-part-3-stardust-crusaders",

    "jojo part 3":
        "jojo-s-bizarre-adventure-part-3-stardust-crusaders",

    "jojo s3.4":
        "jojo-s-bizarre-adventure-part-3-stardust-crusaders-battle-in-egypt",

    "jojo part 3.4":
        "jojo-s-bizarre-adventure-part-3-stardust-crusaders-battle-in-egypt",

    "jojo s4":
        "jojo-s-bizarre-adventure-part-4-diamond-is-unbreakable",

    "jojo part 4":
        "jojo-s-bizarre-adventure-part-4-diamond-is-unbreakable",

    "jojo s5":
        "jojo-s-bizarre-adventure-part-5-golden-wind",

    "jojo part 5":
        "jojo-s-bizarre-adventure-part-5-golden-wind",

    "jojo s6":
        "jojo-s-bizarre-adventure-part-6-stone-ocean",

    "jojo part 6":
        "jojo-s-bizarre-adventure-part-6-stone-ocean",

    "jojo s6 part 2":
        "jojo-s-bizarre-adventure-part-6-stone-ocean-part-2",

    "jojo part 6 part 2":
        "jojo-s-bizarre-adventure-part-6-stone-ocean-part-2",

    "jojo s7":
        "jojo-s-bizarre-adventure-part-7-steel-ball-run-1st-stage",

    "jojo part 7":
        "jojo-s-bizarre-adventure-part-7-steel-ball-run-1st-stage",

    "jojo bizarre adventure":
        "jojo-s-bizarre-adventure",


    # --------------------------------------------------------
    # Mob Psycho
    # --------------------------------------------------------

    "mob": "mob-psycho-100",
    "mob psycho": "mob-psycho-100",

    "mob s1": "mob-psycho-100",
    "mob s2": "mob-psycho-100-ii",
    "mob s3": "mob-psycho-100-iii",


    # --------------------------------------------------------
    # One Punch Man
    # --------------------------------------------------------

    "opm": "one-punch-man",
    "one punch man": "one-punch-man",

    "opm s1": "one-punch-man",
    "opm s2": "one-punch-man-2",
    "opm s3": "one-punch-man-3",


    # --------------------------------------------------------
    # Naruto
    # --------------------------------------------------------

    "naruto": "naruto",
    "naruto shippuden": "naruto-shippuuden",
    "shippuden": "naruto-shippuuden",


    # --------------------------------------------------------
    # Boruto
    # --------------------------------------------------------

    "boruto": "boruto-naruto-next-generations",
    "boruto naruto": "boruto-naruto-next-generations",


    # --------------------------------------------------------
    # Dragon Ball
    # --------------------------------------------------------

    "dbs": "dragon-ball-super",
    "dragon ball super": "dragon-ball-super",

    "dbs broly": "dragon-ball-super-broly",
    "dragon ball broly": "dragon-ball-super-broly",


    # --------------------------------------------------------
    # Frieren
    # --------------------------------------------------------

    "frieren": "sousou-no-frieren",
    "sousou no frieren": "sousou-no-frieren",

    "frieren s1": "sousou-no-frieren",
    "frieren s2": "sousou-no-frieren-2nd-season",

    "frieren season 2":
        "sousou-no-frieren-2nd-season",

    "sousou no frieren s2":
        "sousou-no-frieren-2nd-season",


    # --------------------------------------------------------
    # Yomi no Tsugai
    # --------------------------------------------------------

    "yomi": "yomi-no-tsugai",
    "yomi no tsugai": "yomi-no-tsugai",
    "yomi no tsugai s1": "yomi-no-tsugai",


    # --------------------------------------------------------
    # Solo Leveling
    # --------------------------------------------------------

    "solo": "solo-leveling",
    "solo leveling": "solo-leveling",

    "solo leveling s1": "solo-leveling",

    "solo leveling s2":
        "solo-leveling-season-2-arise-from-the-shadow",


    # --------------------------------------------------------
    # Precure
    # --------------------------------------------------------

    "futari wa precure": "futari-wa-precure",
    "precure": "futari-wa-precure",

    "futari wa precure max heart":
        "futari-wa-precure-max-heart",

    "precure max heart":
        "futari-wa-precure-max-heart",

    "max heart":
        "futari-wa-precure-max-heart",

    "futari wa precure splash star":
        "futari-wa-precure-splash-star",

    "precure splash star":
        "futari-wa-precure-splash-star",

    "splash star":
        "futari-wa-precure-splash-star",

    "fresh precure":
        "fresh-precure!",

    "fresh":
        "fresh-precure!",

    "heartcatch precure":
        "heartcatch-precure!",

    "heartcatch":
        "heartcatch-precure!",

    "happiness charge precure":
        "happiness-charge-precure!",

    "happiness charge":
        "happiness-charge-precure!",

    "go princess precure":
        "go!-princess-precure",

    "go princess":
        "go!-princess-precure",

    "mahoutsukai precure":
        "mahoutsukai-precure!",

    "mahoutsukai":
        "mahoutsukai-precure!",

    "doki doki precure":
        "doki-doki!-precure!",

    "doki doki":
        "doki-doki!-precure!",


    # --------------------------------------------------------
    # Precure Movies
    # --------------------------------------------------------

    "precure max heart movie":
        "eiga-futari-wa-precure-max-heart",

    "max heart movie":
        "eiga-futari-wa-precure-max-heart",

    "precure max heart 2":
        "eiga-futari-wa-precure-max-heart-2-yukizora-no-tomodachi",

    "max heart 2":
        "eiga-futari-wa-precure-max-heart-2-yukizora-no-tomodachi",

    "precure max heart 2 movie":
        "eiga-futari-wa-precure-max-heart-2-yukizora-no-tomodachi",


    # --------------------------------------------------------
    # Little Witch Academia
    # --------------------------------------------------------

    "little witch academia":
        "little-witch-academia",

    "lwa":
        "little-witch-academia",

    "little witch academia tv":
        "little-witch-academia-tv",

    "lwa tv":
        "little-witch-academia-tv",

    "little witch academia enchanted parade":
        "little-witch-academia-the-enchanted-parade",

    "lwa enchanted parade":
        "little-witch-academia-the-enchanted-parade",


    # --------------------------------------------------------
    # Other
    # --------------------------------------------------------

    "witch hat atelier":
        "witch-hat-atelier",

    "ousama ranking":
        "ousama-ranking",

    "ranking of kings":
        "ousama-ranking",

    "ousama ranking treasure box":
        "ousama-ranking-yuuki-no-takarabako",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    text = text.replace("_", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# ALIAS
# ============================================================

def resolve_alias(anime):

    anime_normalized = normalize(
        anime
    )

    if anime_normalized in ANIME_ALIASES:

        return ANIME_ALIASES[
            anime_normalized
        ]

    return anime_normalized.replace(
        " ",
        "-"
    )


# ============================================================
# JSON
# ============================================================

def load_json(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            f"Could not read JSON: "
            f"{os.path.basename(path)}"
        )

        print(
            f"Reason: {e}"
        )

        return None


# ============================================================
# STAFF NAME
# ============================================================

def get_staff_name(person):

    if not isinstance(
        person,
        dict
    ):
        return None

    pn = person.get(
        "pn"
    )

    if isinstance(
        pn,
        dict
    ):

        pn_en = pn.get(
            "en"
        )

        if pn_en and str(
            pn_en
        ).strip():

            return str(
                pn_en
            ).strip()

        pn_ja = pn.get(
            "ja"
        )

        if pn_ja and str(
            pn_ja
        ).strip():

            return str(
                pn_ja
            ).strip()

    en = person.get(
        "en"
    )

    if en and str(
        en
    ).strip():

        return str(
            en
        ).strip()

    ja = person.get(
        "ja"
    )

    if ja and str(
        ja
    ).strip():

        return str(
            ja
        ).strip()

    name = person.get(
        "name"
    )

    if name and str(
        name
    ).strip():

        return str(
            name
        ).strip()

    return None


# ============================================================
# ROLE MATCHING
# ============================================================

ROLE_ALIASES = {

    "sb": [
        "storyboard",
        "story board",
        "storyboards",
        "storyboard / episode director",
        "storyboard / unit director",
        "絵コンテ",
    ],

    "ed": [
        "episode director",
        "episode direction",
        "episode direction cooperation",
        "演出",
    ],

    "ad": [
        "animation director",
        "作画監督",
    ],

    "ass_ad": [
        "assistant animation director",
        "assistant animation director(s)",
        "assistant ad",
        "作画監督補佐",
    ],

    "ka": [
        "key animation",
        "key animator",
        "原画",
    ],

    "2ka": [
        "2nd key animation",
        "2nd key animator",
        "second key animation",
        "second key animator",
        "第二原画",
    ],

    "cad": [
        "chief animation director",
        "chief animation director(s)",
        "総作画監督",
    ],

    "cd": [
        "character design",
        "character designer",
        "キャラクターデザイン",
    ],

    "artist": [
        "song",
        "artist",
        "歌",
    ],
}


def role_matches(
    role_name,
    wanted
):

    if not role_name:
        return False

    role = normalize(
        role_name
    )

    if role == wanted:
        return True

    for alias in ROLE_ALIASES.get(
        wanted,
        []
    ):

        if role == normalize(
            alias
        ):
            return True

    return False


# ============================================================
# GET STAFF FROM ROLE
# ============================================================

def get_staff_from_role(
    role
):

    if not isinstance(
        role,
        dict
    ):
        return []

    staff = role.get(
        "staff"
    )

    if isinstance(
        staff,
        int
    ):

        return [
            str(staff)
        ]

    if not isinstance(
        staff,
        list
    ):
        return []

    results = []

    for person in staff:

        name = get_staff_name(
            person
        )

        if name:

            results.append(
                name
            )

    return results


# ============================================================
# FIND EPISODE MENU
# ============================================================

def find_episode_menu(
    data,
    episode
):

    if not isinstance(
        data,
        dict
    ):
        return None

    menus = data.get(
        "menus",
        []
    )

    if not isinstance(
        menus,
        list
    ):
        return None

    # --------------------------------------------------------
    # OP / ED
    #
    # episode can be:
    #
    # op1
    # op2
    # ed1
    # ed2
    # --------------------------------------------------------

    if isinstance(
        episode,
        str
    ):

        value = normalize(
            episode
        )

        match = re.fullmatch(
            r"(op|opening|ed|ending)[\s\-]*(\d+)",
            value
        )

        if match:

            kind = match.group(
                1
            )

            number = int(
                match.group(2)
            )

            if kind in (
                "op",
                "opening"
            ):

                wanted_names = [
                    f"op{number}",
                    f"op {number}",
                    f"opening {number}",
                    f"opening{number}",
                ]

            else:

                wanted_names = [
                    f"ed{number}",
                    f"ed {number}",
                    f"ending {number}",
                    f"ending{number}",
                ]

            wanted_names = [
                normalize(x)
                for x in wanted_names
            ]

            for menu in menus:

                if not isinstance(
                    menu,
                    dict
                ):
                    continue

                name = normalize(
                    menu.get(
                        "name",
                        ""
                    )
                )

                if name in wanted_names:

                    return menu

            # ------------------------------------------------
            # More flexible OP / ED fallback
            # ------------------------------------------------

            for menu in menus:

                if not isinstance(
                    menu,
                    dict
                ):
                    continue

                name = normalize(
                    menu.get(
                        "name",
                        ""
                    )
                )

                if kind in (
                    "op",
                    "opening"
                ):

                    if (
                        "op" in name
                        or "opening" in name
                    ):

                        numbers = re.findall(
                            r"\d+",
                            name
                        )

                        if numbers and int(
                            numbers[-1]
                        ) == number:

                            return menu

                else:

                    if (
                        "ed" in name
                        or "ending" in name
                    ):

                        numbers = re.findall(
                            r"\d+",
                            name
                        )

                        if numbers and int(
                            numbers[-1]
                        ) == number:

                            return menu

            return None

    # --------------------------------------------------------
    # NORMAL EPISODE
    # --------------------------------------------------------

    try:

        episode_number = int(
            episode
        )

    except (
        ValueError,
        TypeError
    ):

        return None

    possible = {
        f"#{episode_number:02d}",
        f"#{episode_number}",
        f"{episode_number:02d}",
        f"{episode_number}",
        f"episode {episode_number}",
        f"episode {episode_number:02d}",
        f"ep {episode_number}",
        f"ep {episode_number:02d}",
    }

    # --------------------------------------------------------
    # Normal episode menu
    # --------------------------------------------------------

    for menu in menus:

        if not isinstance(
            menu,
            dict
        ):
            continue

        name = normalize(
            menu.get(
                "name",
                ""
            )
        )

        if name in possible:

            return menu

    # --------------------------------------------------------
    # Numeric fallback
    # --------------------------------------------------------

    for menu in menus:

        if not isinstance(
            menu,
            dict
        ):
            continue

        name = str(
            menu.get(
                "name",
                ""
            )
        ).strip()

        match = re.search(
            r"#?\s*(\d+)",
            name
        )

        if match:

            try:

                if int(
                    match.group(1)
                ) == episode_number:

                    return menu

            except ValueError:

                pass

    # --------------------------------------------------------
    # MOVIE FALLBACK
    # --------------------------------------------------------

    if episode_number == 1:

        for menu in menus:

            if not isinstance(
                menu,
                dict
            ):
                continue

            name = normalize(
                menu.get(
                    "name",
                    ""
                )
            )

            if name == "movie":

                return menu

    return None


# ============================================================
# FIND ROLE
# ============================================================

def find_roles(
    menu,
    wanted
):

    if not isinstance(
        menu,
        dict
    ):
        return []

    credits = menu.get(
        "credits",
        []
    )

    if not isinstance(
        credits,
        list
    ):
        return []

    results = []

    for credit in credits:

        if not isinstance(
            credit,
            dict
        ):
            continue

        roles = credit.get(
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

            role_name = role.get(
                "name",
                ""
            )

            if not role_matches(
                role_name,
                wanted
            ):
                continue

            results.extend(
                get_staff_from_role(
                    role
                )
            )

    return list(
        dict.fromkeys(
            results
        )
    )


# ============================================================
# 2KA COUNT
# ============================================================

def get_2ka_count(
    menu
):

    if not isinstance(
        menu,
        dict
    ):
        return 0

    credits = menu.get(
        "credits",
        []
    )

    if not isinstance(
        credits,
        list
    ):
        return 0

    total = 0

    for credit in credits:

        if not isinstance(
            credit,
            dict
        ):
            continue

        roles = credit.get(
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

            role_name = role.get(
                "name",
                ""
            )

            if not role_matches(
                role_name,
                "2ka"
            ):
                continue

            staff = role.get(
                "staff"
            )

            if isinstance(
                staff,
                int
            ):

                total += staff

            elif isinstance(
                staff,
                list
            ):

                total += len(
                    staff
                )

    return total


# ============================================================
# EXTRACT STAFF
# ============================================================

def extract_episode_staff(
    data,
    episode
):

    menu = find_episode_menu(
        data,
        episode
    )

    if menu is None:

        print(
            "No matching episode/OP/ED "
            "data in this file."
        )

        return None

    # ========================================================
    # NORMAL STAFF
    # ========================================================

    result = {

        "SB": find_roles(
            menu,
            "sb"
        ),

        "ED": find_roles(
            menu,
            "ed"
        ),

        "AD": find_roles(
            menu,
            "ad"
        ),

        "Ass. AD": find_roles(
            menu,
            "ass_ad"
        ),

        "CAD": find_roles(
            menu,
            "cad"
        ),

        "CD": find_roles(
            menu,
            "cd"
        ),

        "KA": find_roles(
            menu,
            "ka"
        ),

        "2KA": get_2ka_count(
            menu
        ),
    }

    # ========================================================
    # STORYBOARD / EPISODE DIRECTOR COMBINED ROLE
    # ========================================================

    credits = menu.get(
        "credits",
        []
    )

    if isinstance(
        credits,
        list
    ):

        for credit in credits:

            if not isinstance(
                credit,
                dict
            ):
                continue

            roles = credit.get(
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

                role_name = normalize(
                    role.get(
                        "name",
                        ""
                    )
                )

                if (
                    "storyboard"
                    in role_name
                    and
                    "episode director"
                    in role_name
                ):

                    names = get_staff_from_role(
                        role
                    )

                    result["SB"].extend(
                        names
                    )

                    result["ED"].extend(
                        names
                    )

    # ========================================================
    # OP / ED ARTIST
    # ========================================================

    # Only show Artist for OP/ED.
    #
    # Example:
    #
    # Song -> King Gnu
    #
    # Result:
    #
    # Artist
    # - King Gnu
    #
    # We deliberately DO NOT include:
    # Lyrics
    # Composition
    # Arrangement
    # Label
    # Theme Song Cooperation
    #

    if isinstance(
        episode,
        str
    ):

        value = normalize(
            episode
        )

        is_op_ed = re.fullmatch(
            r"(op|opening|ed|ending)[\s\-]*\d+",
            value
        )

        if is_op_ed:

            result["Artist"] = find_roles(
                menu,
                "artist"
            )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    for key in [
        "SB",
        "ED",
        "AD",
        "Ass. AD",
        "CAD",
        "CD",
        "KA",
        "Artist",
    ]:

        if key in result:

            result[key] = list(
                dict.fromkeys(
                    result[key]
                )
            )

    # ========================================================
    # CHECK IF USEFUL
    # ========================================================

    useful = any(
        result[key]
        for key in [
            "SB",
            "ED",
            "AD",
            "Ass. AD",
            "CAD",
            "CD",
            "KA",
            "Artist",
        ]
    )

    if result["2KA"] > 0:

        useful = True

    if not useful:

        return None

    return result


# ============================================================
# EXACT FILE
# ============================================================

def get_exact_file(
    anime_slug
):

    filename = (
        anime_slug
        + ".json"
    )

    path = os.path.join(
        BASE_DIR,
        filename
    )

    if os.path.isfile(
        path
    ):

        return filename

    return None


# ============================================================
# FALLBACK FILE SEARCH
# ============================================================

def find_matching_files(
    anime_slug
):

    exact = get_exact_file(
        anime_slug
    )

    if exact:

        return [
            (
                10000,
                exact
            )
        ]

    matches = []

    for filename in os.listdir(
        BASE_DIR
    ):

        if not filename.endswith(
            ".json"
        ):
            continue

        if filename == "anime_index.json":

            continue

        base = filename[
            :-5
        ].lower()

        if base == anime_slug:

            matches.append(
                (
                    10000,
                    filename
                )
            )

        elif anime_slug in base:

            matches.append(
                (
                    3000,
                    filename
                )
            )

    matches.sort(
        key=lambda x: (
            -x[0],
            x[1]
        )
    )

    return matches


# ============================================================
# MAIN get_staff
# ============================================================

def get_staff(
    anime,
    season=1,
    episode=1
):

    anime_input = normalize(
        anime
    )

    anime_slug = resolve_alias(
        anime_input
    )

    print()
    print(
        "=" * 60
    )
    print(
        "STAFF LOOKUP"
    )
    print(
        "=" * 60
    )

    print(
        f"Input: {anime}"
    )

    print(
        f"Anime: {anime_slug}"
    )

    print(
        f"Season: {season}"
    )

    print(
        f"Episode: {episode}"
    )

    print()

    print(
        "Searching local staff files..."
    )

    matches = find_matching_files(
        anime_slug
    )

    if not matches:

        print()

        print(
            "No matching JSON files found."
        )

        return None

    print()

    print(
        "Matching staff files:"
    )

    for score, filename in matches:

        print(
            f" - {filename} | "
            f"score={score}"
        )

    # ========================================================
    # TRY MATCHING FILES
    # ========================================================

    for score, filename in matches:

        path = os.path.join(
            BASE_DIR,
            filename
        )

        print()

        print(
            f"Trying: {filename}"
        )

        data = load_json(
            path
        )

        if data is None:

            continue

        staff = extract_episode_staff(
            data,
            episode
        )

        if staff is None:

            continue

        print()

        print(
            f"Selected: {filename}"
        )

        title = data.get(
            "title",
            ""
        )

        slug = data.get(
            "slug",
            ""
        )

        if title:

            print(
                f"Title: {title}"
            )

        if slug:

            print(
                f"Slug: {slug}"
            )

        return staff

    # ========================================================
    # ERROR
    # ========================================================

    print()

    print(
        "=" * 60
    )

    print(
        "ERROR"
    )

    print(
        "=" * 60
    )

    print(
        f"No episode/OP/ED staff data "
        f"was found for {anime} "
        f"Season {season} "
        f"Episode {episode}."
    )

    return None


# ============================================================
# TERMINAL TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "Staff Scraper Test"
    )

    print(
        "------------------"
    )

    anime = input(
        "Anime: "
    ).strip()

    try:

        season = int(
            input(
                "Season: "
            ).strip()
        )

    except ValueError:

        print(
            "Invalid season. "
            "Using Season 1."
        )

        season = 1

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # DO NOT convert episode directly to int.
    #
    # This allows:
    #
    # 1
    # 2
    # op1
    # op2
    # ed1
    # ed2
    # --------------------------------------------------------

    episode = input(
        "Episode / OP / ED "
        "(e.g. 1, op1, op2, ed1): "
    ).strip()

    if not episode:

        episode = "1"

    result = get_staff(
        anime,
        season,
        episode
    )

    print()

    if not result:

        print(
            "No staff found."
        )

    else:

        print(
            "=" * 40
        )

        print(
            "STAFF"
        )

        print(
            "=" * 40
        )

        for role, names in result.items():

            if not names:

                continue

            print()

            print(
                role
            )

            if role == "2KA":

                print(
                    names
                )

            else:

                for name in names:

                    print(
                        f"- {name}"
                    )
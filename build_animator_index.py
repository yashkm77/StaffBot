import json
import os
import glob
import re
from collections import defaultdict


OUTPUT_FILE = "animator_index.json"


def normalize(text):
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()

    # Replace punctuation/separators with spaces
    text = re.sub(r"[_\-./]+", " ", text)

    # Remove remaining punctuation
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def add_name(person_names, value):
    if not isinstance(value, str):
        return

    value = value.strip()

    if not value:
        return

    normalized = normalize(value)

    if not normalized:
        return

    person_names.add(value)


def extract_person_names(person):
    """
    Extract all useful name variants from one KFSL staff object.
    """

    names = set()

    # English
    add_name(
        names,
        person.get("en")
    )

    # Japanese
    add_name(
        names,
        person.get("ja")
    )

    # Person-name variants
    pn = person.get("pn")

    if isinstance(pn, dict):

        add_name(
            names,
            pn.get("en")
        )

        add_name(
            names,
            pn.get("ja")
        )

    return names


def process_json_file(path, database):

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

    except Exception as e:
        print(
            f"[SKIP] {os.path.basename(path)}: {e}"
        )
        return 0

    count = 0

    menus = data.get(
        "menus",
        []
    )

    if not isinstance(menus, list):
        return 0

    anime_title = data.get(
        "title",
        os.path.basename(path)
    )

    for menu in menus:

        if not isinstance(menu, dict):
            continue

        credits = menu.get(
            "credits",
            []
        )

        if not isinstance(credits, list):
            continue

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

                role_name = role.get(
                    "name",
                    ""
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

                    # Never put studios in animator index
                    if person.get(
                        "isStudio"
                    ):
                        continue

                    person_id = person.get(
                        "id"
                    )

                    if person_id is None:
                        continue

                    names = extract_person_names(
                        person
                    )

                    if not names:
                        continue

                    person_key = str(
                        person_id
                    )

                    if person_key not in database:

                        database[person_key] = {
                            "id": person_id,
                            "names": [],
                            "works": []
                        }

                    entry = database[
                        person_key
                    ]

                    # Add names
                    existing_names = set(
                        entry.get(
                            "names",
                            []
                        )
                    )

                    existing_names.update(
                        names
                    )

                    entry["names"] = sorted(
                        existing_names
                    )

                    # Add work information
                    work = {
                        "anime": anime_title,
                        "file": os.path.basename(
                            path
                        ),
                        "role": role_name
                    }

                    if work not in entry["works"]:
                        entry["works"].append(
                            work
                        )

                    count += 1

    return count


def main():

    database = {}

    files = sorted(
        glob.glob("*.json")
    )

    # Never treat the generated index as an input
    files = [
        f
        for f in files
        if os.path.basename(f)
        != OUTPUT_FILE
    ]

    print(
        f"Found {len(files)} JSON files."
    )

    total_people = 0

    for path in files:

        before = len(database)

        process_json_file(
            path,
            database
        )

        added = len(database) - before

        if added:
            print(
                f"[OK] {path}: +{added} people"
            )

    # ------------------------------------------------------------
    # Build searchable name index
    # ------------------------------------------------------------

    name_index = defaultdict(list)

    for person_id, person in database.items():

        for name in person.get(
            "names",
            []
        ):

            normalized = normalize(
                name
            )

            if not normalized:
                continue

            if person_id not in name_index[
                normalized
            ]:
                name_index[
                    normalized
                ].append(
                    person_id
                )

            # Also index reversed western names:
            #
            # Kohei Hirota
            # Hirota Kohei
            #
            parts = normalized.split()

            if len(parts) == 2:

                reversed_name = (
                    parts[1]
                    + " "
                    + parts[0]
                )

                if person_id not in name_index[
                    reversed_name
                ]:
                    name_index[
                        reversed_name
                    ].append(
                        person_id
                    )

    output = {
        "version": 1,
        "people": database,
        "name_index": dict(
            name_index
        )
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 60)
    print(
        f"People found: {len(database):,}"
    )
    print(
        f"Search names: {len(name_index):,}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
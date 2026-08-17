import json
from pathlib import Path


INPUT_FILE = "my_hero_academia_staff.json"
OUTPUT_FILE = "my_hero_academia_staff_clean.json"


def load_staff_data(filename):
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_episode(data, episode_number):
    episode_name = f"#{episode_number:02d}"

    for menu in data.get("menus", []):
        if menu.get("name") == episode_name:
            return menu

    return None


def get_episode_staff(data, episode_number):
    episode = get_episode(data, episode_number)

    if not episode:
        return None

    result = []

    for credit in episode.get("credits", []):
        credit_name = credit.get("name", "").strip()

        for role in credit.get("roles", []):
            role_name = role.get("name", "").strip()
            original_role = role.get("original", "").strip()

            for staff in role.get("staff", []):

                english_name = (staff.get("en") or "").strip()
                japanese_name = (staff.get("ja") or "").strip()
                staff_id = staff.get("id")

                # Ignore completely empty entries
                if not english_name and not japanese_name:
                    continue

                result.append({
                    "credit": credit_name,
                    "role": role_name,
                    "original_role": original_role,
                    "name": english_name or japanese_name,
                    "name_ja": japanese_name,
                    "id": staff_id
                })

    return result


def print_episode_staff(data, episode_number):
    episode = get_episode(data, episode_number)

    if not episode:
        print(f"Episode #{episode_number:02d} not found.")
        return

    staff = get_episode_staff(data, episode_number)

    print()
    print("=" * 80)
    print(f"EPISODE: {episode.get('name')}")
    print("=" * 80)

    current_credit = None

    for person in staff:

        if person["credit"] != current_credit:
            current_credit = person["credit"]

            print()
            print(f"CREDIT: {current_credit}")
            print("-" * 60)

        print(
            f"  {person['role']}: "
            f"{person['name']} "
            f"| {person['name_ja']} "
            f"| ID: {person['id']}"
        )


def save_clean_data(data, filename):
    cleaned_data = {
        "title": data.get("title"),
        "slug": data.get("slug"),
        "anilistId": data.get("anilistId"),
        "status": data.get("status"),
        "uuid": data.get("uuid"),
        "menus": []
    }

    for menu in data.get("menus", []):

        cleaned_menu = {
            "name": menu.get("name"),
            "credits": []
        }

        for credit in menu.get("credits", []):

            cleaned_credit = {
                "name": credit.get("name"),
                "roles": []
            }

            for role in credit.get("roles", []):

                cleaned_staff = []

                for staff in role.get("staff", []):

                    english_name = (staff.get("en") or "").strip()
                    japanese_name = (staff.get("ja") or "").strip()

                    # Skip blank staff entries
                    if not english_name and not japanese_name:
                        continue

                    cleaned_staff.append({
                        "en": english_name,
                        "ja": japanese_name,
                        "id": staff.get("id")
                    })

                # Only save roles that actually contain staff
                if cleaned_staff:
                    cleaned_credit["roles"].append({
                        "name": role.get("name"),
                        "original": role.get("original"),
                        "staff": cleaned_staff
                    })

            # Only save credits containing roles
            if cleaned_credit["roles"]:
                cleaned_menu["credits"].append(cleaned_credit)

        # Only save menus containing credits
        if cleaned_menu["credits"]:
            cleaned_data["menus"].append(cleaned_menu)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            cleaned_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(f"Saved cleaned data to: {filename}")


def main():

    print(f"Loading: {INPUT_FILE}")

    data = load_staff_data(INPUT_FILE)

    print()
    print("TITLE:", data.get("title"))
    print("SLUG:", data.get("slug"))
    print("MENUS:", len(data.get("menus", [])))

    # Test Episode 1
    episode_number = 1

    print_episode_staff(data, episode_number)

    # Save cleaned version
    save_clean_data(
        data,
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
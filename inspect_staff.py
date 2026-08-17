import aiohttp
import asyncio
import json
import sys


BASE_URL = "https://keyframe-staff-list.com/staff"


def extract_episode(html, episode_name):
    search = f'"name":"{episode_name}"'
    start = html.find(search)

    if start == -1:
        return None

    # Find the beginning of the episode object
    start = html.rfind("{", 0, start)

    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(html)):
        char = html[i]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                episode_json = html[start:i + 1]

                try:
                    return json.loads(episode_json)
                except json.JSONDecodeError:
                    return None

    return None


def process_episode(episode):

    roles_output = {
        "SB": [],
        "ED": [],
        "CAD": [],
        "AD": [],
        "AAD": [],
        "KA": [],
        "2KA": None,
    }

    credits = episode.get("credits", [])

    for credit_group in credits:

        for role in credit_group.get("roles", []):

            role_name = role.get("name")

            staff_names = []

            for person in role.get("staff", []):

                # Ignore studios
                if person.get("isStudio"):
                    continue

                name = person.get("en", "").strip()

                if name:
                    staff_names.append(name)

            if not staff_names:
                continue

            # -----------------------------
            # Storyboard
            # -----------------------------
            if role_name == "Storyboard":

                roles_output["SB"].extend(staff_names)

            # -----------------------------
            # Episode Director
            # -----------------------------
            elif role_name == "Episode Director":

                roles_output["ED"].extend(staff_names)

            # -----------------------------
            # Storyboard + Episode Director
            # -----------------------------
            elif role_name == "Storyboard / Episode Director":

                roles_output["SB"].extend(staff_names)
                roles_output["ED"].extend(staff_names)

            # -----------------------------
            # Chief Animation Director
            # -----------------------------
            elif role_name == "Chief Animation Director":

                roles_output["CAD"].extend(staff_names)

            # -----------------------------
            # Animation Director
            # -----------------------------
            elif role_name == "Animation Director":

                roles_output["AD"].extend(staff_names)

            # -----------------------------
            # Assistant Animation Director
            # -----------------------------
            elif role_name == "Assistant Animation Director":

                roles_output["AAD"].extend(staff_names)

            # -----------------------------
            # Key Animation
            # -----------------------------
            elif role_name == "Key Animation":

                roles_output["KA"].extend(staff_names)

            # -----------------------------
            # 2nd Key Animation
            # -----------------------------
            elif role_name == "2nd Key Animation":

                roles_output["2KA"] = len(staff_names)

    # --------------------------------
    # Remove duplicate names
    # --------------------------------

    for role in ["SB", "ED", "CAD", "AD", "AAD", "KA"]:

        roles_output[role] = list(
            dict.fromkeys(roles_output[role])
        )

    return roles_output


def print_results(episode_number, roles):

    print(f"Episode {episode_number}")
    print()

    # Desired order
    for role in ["SB", "ED", "CAD", "AD", "AAD", "KA"]:

        if roles[role]:

            print(
                f"{role}: "
                f"{', '.join(roles[role])}"
            )

    # 2KA is displayed as a number
    if roles["2KA"] is not None:

        print(
            f"2KA: "
            f"{roles['2KA']}"
        )


async def main():

    # --------------------------------
    # Check command-line arguments
    # --------------------------------

    if len(sys.argv) < 3:

        print("Usage:")
        print(
            'python inspect_staff.py '
            '"anime-slug" "#04"'
        )

        return

    anime_slug = sys.argv[1]
    episode_number = sys.argv[2]

    # Make sure episode starts with #
    if not episode_number.startswith("#"):

        episode_number = f"#{episode_number}"

    # --------------------------------
    # Build URL
    # --------------------------------

    url = f"{BASE_URL}/{anime_slug}"

    print(f"Fetching: {url}")
    print()

    # --------------------------------
    # Fetch webpage
    # --------------------------------

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            if response.status != 200:

                print(
                    f"Failed to fetch page. "
                    f"HTTP status: {response.status}"
                )

                return

            html = await response.text()

    # --------------------------------
    # Extract episode
    # --------------------------------

    episode = extract_episode(
        html,
        episode_number
    )

    if not episode:

        print(
            f"Could not find Episode "
            f"{episode_number}."
        )

        return

    print(
        f"Found Episode "
        f"{episode_number}!"
    )

    print()

    # --------------------------------
    # Process staff
    # --------------------------------

    roles = process_episode(episode)

    # --------------------------------
    # Print results
    # --------------------------------

    print_results(
        episode_number,
        roles
    )


if __name__ == "__main__":
    asyncio.run(main())
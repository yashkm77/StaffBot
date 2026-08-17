import aiohttp
import asyncio
import json
import re


BASE_URL = "https://keyframe-staff-list.com/staff"

ANIME_SLUG = "my-hero-academia"


def extract_episode(html, episode_name):

    search = f'"name":"{episode_name}"'

    start = html.find(search)

    if start == -1:
        return None

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

                try:
                    return json.loads(
                        html[start:i + 1]
                    )

                except json.JSONDecodeError:
                    return None

    return None


async def main():

    url = f"{BASE_URL}/{ANIME_SLUG}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/26.0 Safari/605.1.15"
        )
    }

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        async with session.get(url) as response:

            print("HTTP:", response.status)

            html = await response.text()

    print("HTML length:", len(html))

    episodes = sorted(
        set(
            re.findall(
                r'"name":"#(\d+)"',
                html
            )
        ),
        key=int
    )

    print(
        f"Episodes found: {len(episodes)}"
    )

    print()
    print("=" * 70)
    print("PEOPLE WITH PEN NAMES")
    print("=" * 70)

    found = set()

    for number in episodes:

        episode_name = f"#{int(number):02d}"

        episode = extract_episode(
            html,
            episode_name
        )

        if not episode:
            continue

        for credit_group in episode.get(
            "credits",
            []
        ):

            for role in credit_group.get(
                "roles",
                []
            ):

                for person in role.get(
                    "staff",
                    []
                ):

                    if person.get("isStudio"):
                        continue

                    pn = person.get("pn")

                    if not pn:
                        continue

                    name = person.get(
                        "en",
                        ""
                    ).strip()

                    pn_en = pn.get(
                        "en",
                        ""
                    ).strip()

                    key = (
                        name.lower(),
                        pn_en.lower()
                    )

                    if key in found:
                        continue

                    found.add(key)

                    print()

                    print(
                        f"Episode: {episode_name}"
                    )

                    print(
                        f"Role: {role.get('name')}"
                    )

                    print(
                        f"Displayed name: {name}"
                    )

                    print(
                        f"Main/Pen name: {pn_en}"
                    )

                    print(
                        f"ID: {person.get('id')}"
                    )

    print()
    print("=" * 70)

    print(
        f"Total unique pen-name entries: {len(found)}"
    )


asyncio.run(main())
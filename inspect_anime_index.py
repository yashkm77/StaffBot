import aiohttp
import asyncio
import re


URL = "https://keyframe-staff-list.com/staff/ousama-ranking"


async def main():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/26.0 Safari/605.1.15"
        )
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(
            URL,
            headers=headers
        ) as response:

            print("HTTP:", response.status)

            html = await response.text()

    print()
    print("HTML length:", len(html))
    print()

    # -------------------------------------------------
    # Page title
    # -------------------------------------------------

    title = re.findall(
        r"<title>(.*?)</title>",
        html,
        re.IGNORECASE | re.DOTALL
    )

    print("TITLE:")
    print(title[:5])

    print()

    # -------------------------------------------------
    # OpenGraph title
    # -------------------------------------------------

    og_titles = re.findall(
        r'<meta[^>]+'
        r'(?:property|name)=["\']og:title["\'][^>]+'
        r'content=["\'](.*?)["\']',
        html,
        re.IGNORECASE | re.DOTALL
    )

    print("OG TITLE:")
    print(og_titles[:5])

    print()

    # -------------------------------------------------
    # Search for useful title words
    # -------------------------------------------------

    for search in [
        "Ousama",
        "Ranking",
        "王様",
        "anime",
        "title",
        "slug",
        "alternate",
        "alternative",
    ]:

        print(
            f"{search}:",
            html.lower().find(
                search.lower()
            )
        )

    print()

    # -------------------------------------------------
    # Print lines containing title-related information
    # -------------------------------------------------

    print("POSSIBLE TITLE DATA:")
    print()

    for line in html.splitlines():

        lower = line.lower()

        if (
            "ousama" in lower
            or "ranking" in lower
            or "王様" in line
            or "title" in lower
        ):

            print(
                line[:1000]
            )


asyncio.run(main())
import json
import os
import re
import sys
import time
import unicodedata

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.safari.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
)


BASE_URL = "https://keyframe-staff-list.com/staff"

OUTPUT_DIR = "."


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKC",
        str(text)
    )

    text = text.lower()

    text = re.sub(
        r"[^\w\s-]",
        " ",
        text,
        flags=re.UNICODE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# MAKE SLUG
# ============================================================

def make_slug(text):

    text = normalize(text)

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    return slug.strip("-")


# ============================================================
# CREATE SAFARI DRIVER
# ============================================================

def create_driver():

    print()
    print("=" * 60)
    print("Starting Safari...")
    print("=" * 60)
    print()

    options = Options()

    driver = webdriver.Safari(
        options=options
    )

    driver.set_page_load_timeout(
        60
    )

    return driver


# ============================================================
# EXTRACT STAFF JSON
# ============================================================

def extract_staff_json(driver):

    try:

        element = driver.find_element(
            By.ID,
            "staffListData"
        )

    except NoSuchElementException:

        return None

    # Selenium gives us the text/content
    # inside the script element.

    text = driver.execute_script(
        """
        const element = document.getElementById(
            'staffListData'
        );

        if (!element) {
            return null;
        }

        return element.textContent;
        """
    )

    if not text:

        return None

    text = text.strip()

    try:

        data = json.loads(
            text
        )

    except json.JSONDecodeError as e:

        print()
        print(
            "❌ staffListData was found, "
            "but it is not valid JSON."
        )

        print(
            "JSON error:",
            e
        )

        return None

    if not isinstance(
        data,
        dict
    ):

        print(
            "❌ staffListData is not a JSON object."
        )

        return None

    return data


# ============================================================
# CHECK STAFF DATA
# ============================================================

def validate_staff_data(data):

    if not isinstance(
        data,
        dict
    ):

        return False

    if "menus" not in data:

        return False

    if not isinstance(
        data["menus"],
        list
    ):

        return False

    return True


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    data,
    slug
):

    filename = os.path.join(
        OUTPUT_DIR,
        f"{slug}.json"
    )

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    except OSError as e:

        print()
        print(
            "❌ Could not save file:"
        )

        print(
            e
        )

        return None

    return filename


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(data):

    title = data.get(
        "title",
        "Unknown"
    )

    menus = data.get(
        "menus",
        []
    )

    print()
    print("=" * 60)
    print("STAFF DATA FOUND")
    print("=" * 60)

    print()
    print(
        "Title:",
        title
    )

    print(
        "Menus:",
        len(menus)
    )

    episode_count = 0

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
        )

        if re.search(
            r"#\s*\d+",
            name
        ):

            episode_count += 1

    print(
        "Episode menus:",
        episode_count
    )

    print()

    if menus:

        print(
            "First menus:"
        )

        for menu in menus[:10]:

            if isinstance(
                menu,
                dict
            ):

                print(
                    "  -",
                    menu.get(
                        "name",
                        ""
                    )
                )


# ============================================================
# DOWNLOAD ANIME
# ============================================================

def download_anime(
    driver,
    anime,
    slug=None
):

    if not slug:

        slug = make_slug(
            anime
        )

    if not slug:

        print(
            "❌ Could not create a slug."
        )

        return False

    url = (
        f"{BASE_URL}/{slug}"
    )

    print()
    print("=" * 60)

    print(
        "Anime:",
        anime
    )

    print(
        "Slug:",
        slug
    )

    print(
        "URL:",
        url
    )

    print("=" * 60)
    print()

    print(
        "Opening page in Safari..."
    )

    try:

        driver.get(
            url
        )

    except WebDriverException as e:

        print()
        print(
            "❌ Safari failed to load the page."
        )

        print(
            e
        )

        return False

    # Give the page a moment to finish loading.

    time.sleep(
        3
    )

    print(
        "Page loaded."
    )

    print(
        "Looking for staffListData..."
    )

    data = extract_staff_json(
        driver
    )

    if data is None:

        print()
        print(
            "❌ staffListData was not found."
        )

        print()
        print(
            "Possible reasons:"
        )

        print(
            "1. Cloudflare is still checking Safari."
        )

        print(
            "2. The page has not finished loading."
        )

        print(
            "3. The slug is incorrect."
        )

        print()
        print(
            "Current Safari URL:"
        )

        print(
            driver.current_url
        )

        return False

    if not validate_staff_data(
        data
    ):

        print()
        print(
            "❌ Staff data format is unexpected."
        )

        return False

    print_summary(
        data
    )

    filename = save_json(
        data,
        slug
    )

    if not filename:

        return False

    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)

    print()
    print(
        "Saved:",
        filename
    )

    print()

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("KeyFrame Staff List - Safari Downloader")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Get anime from command line
    # --------------------------------------------------------

    if len(sys.argv) > 1:

        anime = " ".join(
            sys.argv[1:]
        )

    else:

        anime = input(
            "Enter anime name: "
        ).strip()

    if not anime:

        print(
            "❌ No anime name provided."
        )

        return

    # --------------------------------------------------------
    # Optional manual slug
    # --------------------------------------------------------

    print()

    slug_input = input(
        "Enter KeyFrame slug "
        "(press Enter to generate automatically): "
    ).strip()

    if slug_input:

        slug = slug_input

    else:

        slug = make_slug(
            anime
        )

    # --------------------------------------------------------
    # Start Safari
    # --------------------------------------------------------

    driver = None

    try:

        driver = create_driver()

        success = download_anime(
            driver,
            anime,
            slug
        )

        if not success:

            print()
            print(
                "Download failed."
            )

    except KeyboardInterrupt:

        print()
        print(
            "Stopped."
        )

    except Exception as e:

        print()
        print(
            "❌ Unexpected error:"
        )

        print(
            repr(e)
        )

    finally:

        if driver:

            print()
            print(
                "Closing Safari..."
            )

            driver.quit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
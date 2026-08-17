from urllib.parse import urlparse

from downloader import run_download
from report import get_last_run


def main_menu():

    while True:

        print()
        print("=" * 60)
        print("          SOCIAL MEDIA DOWNLOADER")
        print("=" * 60)
        print()

        print("1. Facebook")
        print("2. Instagram")
        print("3. Settings")
        print("4. Download History")
        print("5. Exit")

        print()

        choice = input(
            "Select an option: "
        ).strip()

        if choice == "1":

            facebook_workflow()

        elif choice == "2":

            instagram_workflow()

        elif choice == "3":

            settings_menu()

        elif choice == "4":

            history_menu()

        elif choice == "5":

            print()
            print("Goodbye.")
            break

        else:

            print()
            print(
                "Invalid option."
            )


# ============================================================
# FACEBOOK
# ============================================================

def facebook_workflow():

    print()
    print("=" * 60)
    print("                    FACEBOOK")
    print("=" * 60)

    print()

    url = get_url(
        "Facebook page URL"
    )

    if not url:
        return

    content = facebook_content_menu()

    if not content:
        return

    date_range = date_range_menu()

    if not date_range:
        return

    download_confirmation(
        "Facebook",
        url,
        content,
        date_range
    )


def facebook_content_menu():

    while True:

        print()
        print("-" * 60)
        print("FACEBOOK CONTENT")
        print("-" * 60)
        print()

        print("1. Photos")
        print("2. Videos")
        print("3. Photos + Videos")
        print("4. Back")

        print()

        choice = input(
            "Select content type: "
        ).strip()

        options = {
            "1": "Photos",
            "2": "Videos",
            "3": "Photos + Videos"
        }

        if choice in options:

            return options[choice]

        if choice == "4":

            return None

        print(
            "\nInvalid option."
        )


# ============================================================
# INSTAGRAM
# ============================================================

def instagram_workflow():

    print()
    print("=" * 60)
    print("                   INSTAGRAM")
    print("=" * 60)

    print()

    url = get_url(
        "Instagram profile URL"
    )

    if not url:
        return

    content = instagram_content_menu()

    if not content:
        return

    date_range = date_range_menu()

    if not date_range:
        return

    download_confirmation(
        "Instagram",
        url,
        content,
        date_range
    )


def instagram_content_menu():

    while True:

        print()
        print("-" * 60)
        print("INSTAGRAM CONTENT")
        print("-" * 60)
        print()

        print("1. Photos")
        print("2. Posts")
        print("3. Reels")
        print("4. Videos")
        print("5. Posts + Reels")
        print("6. Everything")
        print("7. Back")

        print()

        choice = input(
            "Select content type: "
        ).strip()

        options = {
            "1": "Photos",
            "2": "Posts",
            "3": "Reels",
            "4": "Videos",
            "5": "Posts + Reels",
            "6": "Everything"
        }

        if choice in options:

            return options[choice]

        if choice == "7":

            return None

        print(
            "\nInvalid option."
        )


# ============================================================
# DATE RANGE
# ============================================================

def date_range_menu():

    while True:

        print()
        print("-" * 60)
        print("DOWNLOAD RANGE")
        print("-" * 60)
        print()

        print("1. Last 7 days")
        print("2. Last 30 days")
        print("3. Last N months")
        print("4. Specific year")
        print("5. Custom date range")
        print("6. Everything")
        print("7. New since last download")
        print("8. Latest N media items")
        print("9. Back")

        print()

        choice = input(
            "Select range: "
        ).strip()

        if choice == "1":

            return {
                "type": "last_days",
                "days": 7,
                "label": "Last 7 days"
            }

        if choice == "2":

            return {
                "type": "last_days",
                "days": 30,
                "label": "Last 30 days"
            }

        if choice == "3":

            return get_n_months()

        if choice == "4":

            return get_specific_year()

        if choice == "5":

            return get_custom_range()

        if choice == "6":

            return {
                "type": "all",
                "label": "Everything"
            }

        if choice == "7":

            return {
                "type": "new_since_last",
                "label": "New since last download"
            }

        if choice == "8":

            return get_latest_n()

        if choice == "9":

            return None

        print(
            "\nInvalid option."
        )


# ============================================================
# N MONTHS
# ============================================================

def get_n_months():

    while True:

        value = input(
            "\nHow many months? "
        ).strip()

        try:

            months = int(value)

            if months <= 0:
                raise ValueError

            return {
                "type": "last_months",
                "months": months,
                "label": (
                    f"Last {months} months"
                )
            }

        except ValueError:

            print(
                "Enter a positive number."
            )


# ============================================================
# YEAR
# ============================================================

def get_specific_year():

    while True:

        value = input(
            "\nEnter year (e.g. 2025): "
        ).strip()

        try:

            year = int(value)

            if year < 2000 or year > 2100:
                raise ValueError

            return {
                "type": "year",
                "year": year,
                "label": f"Year {year}"
            }

        except ValueError:

            print(
                "Enter a valid year."
            )


# ============================================================
# CUSTOM RANGE
# ============================================================

def get_custom_range():

    while True:

        print()
        print(
            "Date format: YYYY-MM-DD"
        )
        print()

        start = input(
            "Start date: "
        ).strip()

        end = input(
            "End date: "
        ).strip()

        if not valid_date(start):

            print(
                "Invalid start date."
            )

            continue

        if not valid_date(end):

            print(
                "Invalid end date."
            )

            continue

        if start > end:

            print(
                "Start date cannot be after end date."
            )

            continue

        return {
            "type": "custom",
            "start": start,
            "end": end,
            "label": (
                f"{start} to {end}"
            )
        }


# ============================================================
# LATEST N
# ============================================================

def get_latest_n():

    while True:

        value = input(
            "\nHow many media items? "
        ).strip()

        try:

            count = int(value)

            if count <= 0:
                raise ValueError

            return {
                "type": "latest_n",
                "count": count,
                "label": (
                    f"Latest {count} media items"
                )
            }

        except ValueError:

            print(
                "Enter a positive number."
            )


# ============================================================
# URL
# ============================================================

def get_url(label):

    while True:

        url = input(
            f"{label}: "
        ).strip()

        if not url:

            print(
                "No URL entered."
            )

            return None

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):

            print(
                "URL must start with "
                "http:// or https://"
            )

            continue

        parsed = urlparse(url)

        if not parsed.netloc:

            print(
                "Invalid URL."
            )

            continue

        return url


# ============================================================
# DATE VALIDATION
# ============================================================

def valid_date(value):

    from datetime import datetime

    try:

        datetime.strptime(
            value,
            "%Y-%m-%d"
        )

        return True

    except ValueError:

        return False


# ============================================================
# CONFIRMATION
# ============================================================

def download_confirmation(
    platform,
    url,
    content,
    date_range
):

    print()
    print("=" * 60)
    print("                 DOWNLOAD PLAN")
    print("=" * 60)
    print()

    print(
        f"Platform       : {platform}"
    )

    print(
        f"URL            : {url}"
    )

    print(
        f"Content        : {content}"
    )

    print(
        f"Date range     : "
        f"{date_range['label']}"
    )

    print(
        "Quality        : Highest available"
    )

    print(
        "Archive        : Enabled"
    )

    print(
        "Duplicates     : Skip"
    )

    print(
        "Rate protection: Enabled"
    )

    print()

    answer = input(
        "Start download? [Y/N]: "
    ).strip().lower()

    if answer not in (
        "y",
        "yes"
    ):

        print()
        print(
            "Download cancelled."
        )

        return

    print()

    run_download(
        platform=platform,
        url=url,
        content=content,
        date_selection=date_range
    )

    input(
        "\nPress Enter to return "
        "to the main menu..."
    )


# ============================================================
# SETTINGS
# ============================================================

def settings_menu():

    print()
    print("=" * 60)
    print("                    SETTINGS")
    print("=" * 60)
    print()

    print(
        "Current default quality:"
        " Highest available"
    )

    print(
        "Instagram rate protection:"
        " 6-12 seconds"
    )

    print(
        "Archive:"
        " Enabled"
    )

    print()

    input(
        "Press Enter to return..."
    )


# ============================================================
# HISTORY
# ============================================================

def history_menu():

    print()
    print("=" * 60)
    print("                DOWNLOAD HISTORY")
    print("=" * 60)
    print()

    print(
        "History is stored in:"
    )

    print(
        "logs/state.json"
    )

    print()

    input(
        "Press Enter to return..."
    )
import json
import subprocess
import sys
import time
from collections import Counter

from date_range import create_filter
from filters import (
    content_filter,
    instagram_include
)
from paths import (
    PROJECT_ROOT,
    ensure_directories
)
from report import (
    create_report,
    save_state
)


CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "gallery-dl.json"
)


VIDEO_EXTENSIONS = {
    "mp4",
    "m4v",
    "mov",
    "webm",
    "mkv",
    "avi",
    "3gp"
}


IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "avif"
}


# ============================================================
# COMMAND BUILDER
# ============================================================

def build_command(
    platform,
    url,
    content,
    date_selection
):
    command = [
        sys.executable,
        "-m",
        "gallery_dl",

        "-c",
        str(CONFIG_FILE),

        "--quiet"
    ]

    # --------------------------------------------------------
    # INSTAGRAM CONTENT
    # --------------------------------------------------------

    if platform == "Instagram":

        include = instagram_include(
            content
        )

        command.extend([
            "-o",
            f"extractor.instagram.include={include}"
        ])

    # --------------------------------------------------------
    # CONTENT FILTER
    # --------------------------------------------------------

    media_filter = content_filter(
        platform,
        content
    )

    date_filter = create_filter(
        date_selection
    )

    combined_filter = combine_filters(
        media_filter,
        date_filter
    )

    if combined_filter:

        command.extend([
            "--filter",
            combined_filter
        ])

    # --------------------------------------------------------
    # LATEST N
    # --------------------------------------------------------

    if date_selection["type"] == "latest_n":

        count = date_selection["count"]

        command.extend([
            "--range",
            f"1-{count}"
        ])

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    command.append(url)

    return command


def combine_filters(
    media_filter,
    date_filter
):
    if media_filter and date_filter:

        return (
            f"({media_filter}) and "
            f"({date_filter})"
        )

    if media_filter:
        return media_filter

    if date_filter:
        return date_filter

    return None


# ============================================================
# PRE-DOWNLOAD SCANNER
# ============================================================

def scan_download(
    platform,
    url,
    content,
    date_selection
):

    print()
    print("=" * 60)
    print("              SCANNING MEDIA")
    print("=" * 60)
    print()

    print(
        "This may take some time for a large profile."
    )

    print(
        "Nothing will be downloaded during this scan."
    )

    print()

    command = build_command(
        platform,
        url,
        content,
        date_selection
    )

    # Dump JSON instead of downloading
    command.insert(
        -1,
        "--dump-json"
    )

    command.insert(
        -1,
        "--no-download"
    )

    try:

        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    except Exception as error:

        print()
        print(
            f"Scanner error: {error}"
        )

        return None

    records = []

    for line in result.stdout.splitlines():

        line = line.strip()

        if not line:
            continue

        try:

            data = json.loads(line)

            if isinstance(data, dict):
                records.append(data)

        except json.JSONDecodeError:
            continue

    if result.returncode != 0 and not records:

        print()
        print(
            "Unable to scan the profile."
        )

        if result.stderr:

            print()
            print(
                result.stderr[-3000:]
            )

        return None

    return analyze_records(
        platform,
        content,
        records
    )


# ============================================================
# ANALYZE RESULTS
# ============================================================

def analyze_records(
    platform,
    content,
    records
):

    stats = Counter()

    stats["total"] = len(records)

    for item in records:

        extension = str(
            item.get(
                "extension",
                ""
            )
        ).lower()

        item_type = str(
            item.get(
                "type",
                ""
            )
        ).lower()

        subcategory = str(
            item.get(
                "subcategory",
                ""
            )
        ).lower()

        if extension in IMAGE_EXTENSIONS:

            stats["photos"] += 1

        elif extension in VIDEO_EXTENSIONS:

            stats["videos"] += 1

        # Instagram reel detection
        if (
            platform == "Instagram"
            and (
                subcategory == "reels"
                or item_type == "reel"
            )
        ):

            stats["reels"] += 1

    return {
        "records": records,
        "total": stats["total"],
        "photos": stats["photos"],
        "videos": stats["videos"],
        "reels": stats["reels"]
    }


# ============================================================
# DISPLAY PREVIEW
# ============================================================

def show_scan_result(
    platform,
    content,
    date_selection,
    result
):

    print()
    print("=" * 60)
    print("             DOWNLOAD PREVIEW")
    print("=" * 60)

    print()

    print(
        f"Platform        : {platform}"
    )

    print(
        f"Content         : {content}"
    )

    print(
        f"Date range      : "
        f"{date_selection['label']}"
    )

    print()

    print("-" * 60)

    print(
        f"Total media     : "
        f"{result['total']}"
    )

    print(
        f"Photos          : "
        f"{result['photos']}"
    )

    print(
        f"Videos          : "
        f"{result['videos']}"
    )

    if platform == "Instagram":

        print(
            f"Reels           : "
            f"{result['reels']}"
        )

    print("-" * 60)

    print()

    return result["total"]


# ============================================================
# REAL DOWNLOAD
# ============================================================

def run_download(
    platform,
    url,
    content,
    date_selection
):

    ensure_directories()

    # --------------------------------------------------------
    # FIRST SCAN
    # --------------------------------------------------------

    scan_result = scan_download(
        platform,
        url,
        content,
        date_selection
    )

    if scan_result is None:

        return 1

    # --------------------------------------------------------
    # DISPLAY COUNT
    # --------------------------------------------------------

    show_scan_result(
        platform,
        content,
        date_selection,
        scan_result
    )

    total = scan_result["total"]

    if total == 0:

        print()
        print(
            "No matching media found."
        )

        return 0

    # --------------------------------------------------------
    # CONFIRM
    # --------------------------------------------------------

    print()

    answer = input(
        f"Download these {total} media items? [Y/N]: "
    ).strip().lower()

    if answer not in (
        "y",
        "yes"
    ):

        print()
        print(
            "Download cancelled."
        )

        return 0

    # --------------------------------------------------------
    # START DOWNLOAD
    # --------------------------------------------------------

    command = build_command(
        platform,
        url,
        content,
        date_selection
    )

    # Remove quiet so user can see progress
    if "--quiet" in command:

        command.remove(
            "--quiet"
        )

    print()
    print("=" * 60)
    print("              DOWNLOADING")
    print("=" * 60)

    print()

    start_time = time.time()

    return_code = 1

    try:

        process = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT)
        )

        return_code = (
            process.returncode
        )

    except KeyboardInterrupt:

        print()
        print(
            "Download interrupted."
        )

        return_code = 130

    except Exception as error:

        print()
        print(
            f"Downloader error: {error}"
        )

        return_code = 1

    duration = (
        time.time()
        - start_time
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print("=" * 60)

    if return_code == 0:

        print(
            "DOWNLOAD COMPLETED"
        )

    elif return_code == 130:

        print(
            "DOWNLOAD INTERRUPTED"
        )

    else:

        print(
            f"DOWNLOAD FINISHED "
            f"WITH ERROR "
            f"(code {return_code})"
        )

    print("=" * 60)

    print(
        f"Duration: "
        f"{duration:.1f} seconds"
    )

    report_file = create_report(
        platform=platform,
        url=url,
        content=content,
        date_range=date_selection["label"],
        command=command,
        return_code=return_code,
        duration=duration
    )

    if return_code == 0:

        save_state(
            platform,
            url
        )

    print()

    print(
        f"Report: {report_file}"
    )

    return return_code
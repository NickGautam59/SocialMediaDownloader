import json
from datetime import datetime
from pathlib import Path

from paths import LOGS_DIR, STATE_FILE


def save_state(platform, url):
    state = load_state()

    key = f"{platform}:{url}"

    state[key] = {
        "last_run": datetime.now().isoformat()
    }

    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with STATE_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            indent=4
        )


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {}


def get_last_run(platform, url):
    state = load_state()

    key = f"{platform}:{url}"

    item = state.get(key)

    if not item:
        return None

    return item.get("last_run")


def create_report(
    platform,
    url,
    content,
    date_range,
    command,
    return_code,
    duration
):
    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    report_file = (
        LOGS_DIR
        / f"report_{timestamp}.txt"
    )

    lines = [
        "=" * 60,
        "SOCIAL MEDIA DOWNLOADER REPORT",
        "=" * 60,
        "",
        f"Platform       : {platform}",
        f"URL            : {url}",
        f"Content        : {content}",
        f"Date Range     : {date_range}",
        f"Return Code    : {return_code}",
        f"Duration       : {duration:.1f} seconds",
        "",
        "Command:",
        " ".join(command),
        "",
        "=" * 60
    ]

    report_file.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    return report_file
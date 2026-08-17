from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
ARCHIVE_DIR = PROJECT_ROOT / "archive"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

STATE_FILE = LOGS_DIR / "state.json"


def ensure_directories():
    DOWNLOADS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    LOGS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def platform_directory(platform, username):
    path = (
        DOWNLOADS_DIR
        / platform
        / sanitize(username)
    )

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path


def sanitize(value):
    invalid = '<>:"/\\|?*'

    result = str(value)

    for character in invalid:
        result = result.replace(
            character,
            "_"
        )

    return result.strip()
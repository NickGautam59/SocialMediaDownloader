from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
from contextlib import contextmanager
from urllib.parse import urlparse

from gallery_dl import config, job
from gallery_dl.extractor.common import Message
import gallery_dl


@dataclass(frozen=True)
class MediaItem:
    shortcode: str
    post_url: str
    date: datetime | None
    media_id: str
    extension: str = "jpg"


@dataclass
class ProfileInfo:
    username: str
    posts: int
    authenticated: bool


@dataclass
class DownloadStats:
    scanned: int = 0
    candidates: int = 0
    media_total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class GalleryDLInstagramEngine:
    """Instagram V2 engine using gallery-dl directly as a Python library."""

    def __init__(self):
        self.root = Path(__file__).resolve().parents[2]
        self.download_root = self.root / "downloads" / "Instagram"
        self.data_root = self.root / "data"
        self.archive_file = self.data_root / "instagram_gallery_archive.txt"
        self.state_file = self.data_root / "instagram_state.json"
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.auth_mode = None
        self.gallery_version = gallery_dl.__version__

    @staticmethod
    def normalize_profile(value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Instagram profile is required.")
        if "instagram.com" not in value.lower():
            username = value.lstrip("@").lower()
        else:
            parsed = urlparse(value if "://" in value else "https://" + value)
            parts = [p for p in parsed.path.split("/") if p]
            if not parts:
                raise ValueError("Invalid Instagram profile URL.")
            username = parts[0].lstrip("@").lower()
        if username in {"p", "reel", "reels", "tv", "stories", "explore"}:
            raise ValueError("That URL is not an Instagram profile URL.")
        if not re.fullmatch(r"[a-z0-9._]+", username):
            raise ValueError("Invalid Instagram username.")
        return username

    @staticmethod
    def _parse_datetime(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

    @contextmanager
    def _config(self, browser=None):
        config.clear()
        config.set((), "base-directory", str(self.download_root))
        config.set((), "directory", ("{username}", "Posts"))
        config.set((), "filename", "{post_date:%Y-%m-%d_%H-%M-%S}_{post_shortcode}_{num}.{extension}")
        config.set((), "archive", str(self.archive_file))
        config.set((), "skip", True)
        config.set((), "retries", 5)
        config.set((), "sleep-retries", "2-8")
        config.set((), "sleep", "1-2")
        config.set(("extractor", "instagram"), "videos", False)
        config.set(("extractor", "instagram"), "audio", False)
        config.set(("extractor", "instagram"), "previews", False)
        if browser:
            name, profile = browser
            config.set((), "cookies", (name, profile, None, None, None))
        try:
            yield
        finally:
            config.clear()

    def _browser_variants(self):
        variants = [("brave", None), ("chrome", None), ("edge", None), ("firefox", None)]
        if os.name == "nt":
            local = os.environ.get("LOCALAPPDATA", "")
            beta = Path(local) / "BraveSoftware" / "Brave-Browser-Beta" / "User Data" / "Default"
            if beta.exists():
                variants.insert(1, ("brave", str(beta)))
        return variants

    def _is_auth_error(self, exc) -> bool:
        text = str(exc).lower()
        return any(x in text for x in (
            "login", "unauthorized", "401", "challenge", "checkpoint",
            "private", "sessionid", "please wait a few minutes"
        ))

    def _run_data(self, url: str):
        with self._config():
            data_job = job.DataJob(url, file=None, resolve=0)
            status = data_job.run()
            return status, data_job.data

    def _run_data_with_auth(self, url: str):
        try:
            status, data = self._run_data(url)
            self.auth_mode = "anonymous"
            return status, data
        except Exception as first:
            if not self._is_auth_error(first):
                raise
            last = first
            for browser in self._browser_variants():
                try:
                    with self._config(browser):
                        data_job = job.DataJob(url, file=None, resolve=0)
                        status = data_job.run()
                        self.auth_mode = f"browser:{browser[0]}"
                        return status, data_job.data
                except Exception as exc:
                    last = exc
            raise RuntimeError(
                "Instagram needs access that could not be obtained anonymously or "
                "from an existing browser session. No Instagram password was requested."
            ) from last

    @staticmethod
    def _records(data):
        for entry in data or []:
            if not isinstance(entry, tuple) or len(entry) < 3:
                continue
            message, url, metadata = entry[:3]
            if message != Message.Url or not isinstance(metadata, dict):
                continue
            yield metadata

    def _scan(self, profile_url):
        status, data = self._run_data_with_auth(profile_url)
        records = list(self._records(data))
        if not records and status:
            raise RuntimeError("gallery-dl could not extract the Instagram profile.")
        return records

    def _archive_text(self):
        try:
            return self.archive_file.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            return ""

    def _archived(self, media_id):
        return str(media_id) in self._archive_text()

    def _state(self, username, posts, media):
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            state = {}
        state[username] = {
            "last_scan_utc": datetime.now(timezone.utc).isoformat(),
            "last_scanned_posts": posts,
            "last_scanned_media": media,
            "access": self.auth_mode,
            "gallery_dl": self.gallery_version,
        }
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_file)

    def preview(self, value, start=None, end=None, latest_n=None, quick_update=False):
        username = self.normalize_profile(value)
        records = self._scan(f"https://www.instagram.com/{username}/")
        grouped = {}

        for record in records:
            media_id = str(record.get("media_id") or record.get("id") or "")
            shortcode = str(record.get("post_shortcode") or record.get("shortcode") or "")
            if not media_id or not shortcode:
                continue
            extension = str(record.get("extension") or "jpg").lower()
            if extension in {"mp4", "mov", "m4v", "webm"} or record.get("video_url"):
                continue
            dt = self._parse_datetime(record.get("post_date") or record.get("date"))
            if start and dt and dt < start:
                continue
            if end and dt and dt > end:
                continue
            if self._archived(media_id):
                continue
            item = MediaItem(
                shortcode=shortcode,
                post_url=str(record.get("post_url") or f"https://www.instagram.com/p/{shortcode}/"),
                date=dt,
                media_id=media_id,
                extension=extension,
            )
            grouped.setdefault(shortcode, []).append(item)

        posts = [items[0] for items in grouped.values()]
        posts.sort(key=lambda x: x.date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        if latest_n is not None:
            posts = posts[:latest_n]
        if quick_update:
            posts = [p for p in posts if not self._archived(p.media_id)]

        selected = {p.shortcode for p in posts}
        media_total = sum(len(items) for code, items in grouped.items() if code in selected)
        self._state(username, len(posts), media_total)
        return username, posts, media_total

    def download_images(self, username, posts, media_total):
        stats = DownloadStats(len(posts), len(posts), media_total)
        total = len(posts)

        for index, post in enumerate(posts, 1):
            before = set(self.download_root.joinpath(username, "Posts").glob("*"))
            try:
                with self._config():
                    config.set((), "filter", "not video_url")
                    status = job.DownloadJob(post.post_url).run()
                after = set(self.download_root.joinpath(username, "Posts").glob("*"))
                created = [p for p in after - before if p.is_file()]
                if status:
                    stats.failed += 1
                    stats.errors.append(f"{post.shortcode}: gallery-dl status {status}")
                    print(f"  [{index}/{total}] FAILED {post.shortcode} | remaining={total-index}")
                else:
                    stats.downloaded += len(created)
                    print(f"  [{index}/{total}] {post.shortcode} | media={len(created)} | remaining={total-index}")
            except Exception as exc:
                stats.failed += 1
                stats.errors.append(f"{post.shortcode}: {exc}")
                print(f"  [{index}/{total}] FAILED {post.shortcode} | remaining={total-index}")

        stats.skipped = max(0, media_total - stats.downloaded)
        return stats

    def download_single_image(self, url):
        if not re.search(r"instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+", url, re.I):
            raise ValueError("Unsupported Instagram post URL.")
        stats = DownloadStats(scanned=1, candidates=1)
        try:
            with self._config():
                config.set((), "filter", "not video_url")
                status = job.DownloadJob(url).run()
            if status:
                stats.failed = 1
                stats.errors.append(f"gallery-dl status {status}")
            else:
                stats.downloaded = 1
        except Exception as exc:
            stats.failed = 1
            stats.errors.append(str(exc))
        return stats

    def inspect_profile(self, value):
        username = self.normalize_profile(value)
        records = self._scan(f"https://www.instagram.com/{username}/")
        posts = {
            str(r.get("post_shortcode") or r.get("shortcode"))
            for r in records
            if r.get("post_shortcode") or r.get("shortcode")
        }
        return ProfileInfo(username, len(posts), self.auth_mode != "anonymous")

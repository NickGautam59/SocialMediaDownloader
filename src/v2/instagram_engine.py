from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class MediaItem:
    shortcode: str
    post_url: str
    date: datetime | None
    media_id: str
    extension: str = "jpg"
    path: str | None = None


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
    """Instagram V2 engine built around the maintained gallery-dl extractor.

    The application never asks for an Instagram password. Public profiles are
    attempted anonymously first. If Instagram requires authentication,
    gallery-dl is allowed to read an existing browser session without storing
    the password or exporting cookies into this project.
    """

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.download_root = self.root / "downloads" / "Instagram"
        self.data_root = self.root / "data"
        self.archive_file = self.data_root / "instagram_gallery_archive.txt"
        self.state_file = self.data_root / "instagram_state.json"
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.auth_mode: str | None = None
        self._gallery_version: str | None = None
        self._ensure_gallery_dl()

    def _ensure_gallery_dl(self) -> None:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "gallery_dl", "--version"],
                capture_output=True, text=True, timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(
                "gallery-dl is not installed. Run: py -m pip install -r "
                "requirements-instagram-v2.txt"
            ) from exc
        if result.returncode != 0:
            raise RuntimeError(
                "gallery-dl is not available. Run: py -m pip install -r "
                "requirements-instagram-v2.txt"
            )
        self._gallery_version = (result.stdout or result.stderr).strip().splitlines()[0]

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

    def _profile_url(self, username: str) -> str:
        return f"https://www.instagram.com/{username}/"

    def _browser_auth_variants(self) -> list[str]:
        variants = ["brave", "chrome", "edge", "firefox"]
        if os.name == "nt":
            local = os.environ.get("LOCALAPPDATA", "")
            beta = Path(local) / "BraveSoftware" / "Brave-Browser-Beta" / "User Data" / "Default"
            if beta.exists():
                variants.insert(1, f"brave:{beta}")
        return variants

    def _base_args(self) -> list[str]:
        return [
            sys.executable, "-m", "gallery_dl",
            "--no-input",
            "--no-colors",
            "-o", "extractor.instagram.videos=false",
            "-o", "extractor.instagram.audio=false",
            "-o", "extractor.instagram.previews=false",
            "-o", "extractor.instagram.base-directory=" + str(self.download_root),
            "-o", 'extractor.instagram.directory=["{username}","Posts"]',
            "-o", 'extractor.instagram.filename="{post_date:%Y-%m-%d_%H-%M-%S}_{post_shortcode}_{num}.{extension}"',
            "--restrict-filenames", "windows",
        ]

    def _run(self, args: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    @staticmethod
    def _looks_auth_related(output: str) -> bool:
        text = output.lower()
        markers = (
            "redirect to login",
            "login page",
            "login required",
            "401",
            "unauthorized",
            "challenge",
            "checkpoint",
            "please wait a few minutes",
            "private profile",
            "sessionid",
        )
        return any(marker in text for marker in markers)

    def _execute_with_auth_fallback(
        self, args_without_auth: list[str], timeout: int = 900
    ) -> subprocess.CompletedProcess[str]:
        first = self._run(args_without_auth, timeout)
        if first.returncode == 0:
            self.auth_mode = "anonymous"
            return first

        combined = (first.stdout or "") + "\n" + (first.stderr or "")
        if not self._looks_auth_related(combined):
            return first

        last = first
        for browser in self._browser_auth_variants():
            args = list(args_without_auth)
            insert_at = args.index("--no-input") + 1
            args[insert_at:insert_at] = ["--cookies-from-browser", browser]
            try:
                result = self._run(args, timeout)
            except subprocess.SubprocessError as exc:
                continue
            last = result
            if result.returncode == 0:
                self.auth_mode = f"browser:{browser}"
                return result

        return last

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _json_records(stdout: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                records.append(value)
        return records

    def _scan_records(self, profile_url: str) -> list[dict[str, Any]]:
        args = self._base_args() + ["-j", profile_url]
        result = self._execute_with_auth_fallback(args, timeout=1200)
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise RuntimeError(
                "Instagram scan failed.\n"
                + (details[-3000:] if details else "gallery-dl returned an unknown error.")
            )
        return self._json_records(result.stdout)

    @staticmethod
    def _record_to_media(record: dict[str, Any]) -> MediaItem | None:
        shortcode = str(
            record.get("post_shortcode")
            or record.get("shortcode")
            or ""
        )
        media_id = str(record.get("media_id") or record.get("id") or "")
        post_url = str(record.get("post_url") or "")
        if not shortcode or not media_id:
            return None
        if not post_url:
            post_url = f"https://www.instagram.com/p/{shortcode}/"
        extension = str(record.get("extension") or "jpg").lower()
        return MediaItem(
            shortcode=shortcode,
            post_url=post_url,
            date=GalleryDLInstagramEngine._parse_datetime(
                record.get("post_date") or record.get("date")
            ),
            media_id=media_id,
            extension=extension,
        )

    def _archive_text(self) -> str:
        try:
            return self.archive_file.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            return ""

    def _archive_has(self, media_id: str) -> bool:
        return media_id in self._archive_text()

    def _save_state(self, username: str, posts: int, media: int) -> None:
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            state = {}
        state[username] = {
            "last_scan_utc": datetime.now(timezone.utc).isoformat(),
            "last_scanned_posts": posts,
            "last_scanned_media": media,
            "auth_mode": self.auth_mode,
            "gallery_dl": self._gallery_version,
        }
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_file)

    def preview(
        self,
        value: str,
        start: datetime | None = None,
        end: datetime | None = None,
        latest_n: int | None = None,
        quick_update: bool = False,
    ) -> tuple[str, list[MediaItem], int]:
        username = self.normalize_profile(value)
        records = self._scan_records(self._profile_url(username))

        grouped: dict[str, list[MediaItem]] = {}
        for record in records:
            item = self._record_to_media(record)
            if item is None:
                continue
            if item.extension in {"mp4", "mov", "m4v", "webm"}:
                continue
            if start and item.date and item.date < start:
                continue
            if end and item.date and item.date > end:
                continue
            if self._archive_has(item.media_id):
                continue
            grouped.setdefault(item.shortcode, []).append(item)

        posts: list[MediaItem] = []
        for shortcode, items in grouped.items():
            items.sort(key=lambda x: x.media_id)
            posts.append(items[0])

        posts.sort(
            key=lambda x: x.date or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        if quick_update:
            # Archive filtering already removes downloaded media. This is an
            # additional safety rule for a partial/interrupted previous run.
            posts = [p for p in posts if not self._archive_has(p.media_id)]
        if latest_n is not None:
            posts = posts[:latest_n]

        selected_codes = {p.shortcode for p in posts}
        media_items = [
            item
            for code, items in grouped.items()
            if code in selected_codes
            for item in items
        ]
        media_items.sort(
            key=lambda x: x.date or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        self._save_state(username, len(selected_codes), len(media_items))
        return username, posts, len(media_items)

    def _write_input_file(self, urls: list[str]) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt",
            prefix="instagram_v2_", delete=False
        )
        path = Path(handle.name)
        with handle:
            for url in urls:
                handle.write(url + "\n")
        return path

    def download_images(
        self, username: str, posts: list[MediaItem], media_total: int
    ) -> DownloadStats:
        stats = DownloadStats(
            scanned=len(posts),
            candidates=len(posts),
            media_total=media_total,
        )
        if not posts:
            return stats

        input_file = self._write_input_file([p.post_url for p in posts])
        args = self._base_args() + [
            "--download-archive", str(self.archive_file),
            "--filter", "not video_url",
            "--sleep", "1-2",
            "--retries", "5",
            "--sleep-retries", "2-8",
            "--Print", "file:{_path}",
            "-i", str(input_file),
        ]
        try:
            result = self._execute_with_auth_fallback(args, timeout=7200)
            printed_files = [
                line.strip()[5:]
                for line in result.stdout.splitlines()
                if line.strip().startswith("file:")
            ]
            for index, path in enumerate(printed_files, 1):
                print(
                    f"  [{index}/{media_total}] downloaded | "
                    f"{Path(path).name}"
                )
            if result.returncode != 0:
                details = (result.stderr or result.stdout).strip()
                stats.failed = max(1, len(posts))
                stats.errors.append(details[-3000:] if details else "gallery-dl failed")
                return stats

            stats.downloaded = len(printed_files)
            stats.skipped = max(0, media_total - stats.downloaded)
            return stats
        finally:
            try:
                input_file.unlink(missing_ok=True)
            except OSError:
                pass

    def download_single_image(self, url: str) -> DownloadStats:
        if not re.search(r"instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+", url, re.I):
            raise ValueError("Unsupported Instagram post URL.")

        stats = DownloadStats(scanned=1, candidates=1)
        args = self._base_args() + [
            "--download-archive", str(self.archive_file),
            "--filter", "not video_url",
            "--retries", "5",
            "--sleep-retries", "2-8",
            "--Print", "file:{_path}",
            url,
        ]
        result = self._execute_with_auth_fallback(args, timeout=1800)
        files = [
            line.strip()[5:]
            for line in result.stdout.splitlines()
            if line.strip().startswith("file:")
        ]
        stats.media_total = len(files)
        stats.downloaded = len(files)
        if result.returncode != 0:
            stats.failed = 1
            stats.errors.append((result.stderr or result.stdout).strip()[-3000:])
        return stats

    def inspect_profile(self, value: str) -> ProfileInfo:
        username = self.normalize_profile(value)
        records = self._scan_records(self._profile_url(username))
        posts = {
            str(r.get("post_shortcode") or r.get("shortcode"))
            for r in records
            if r.get("post_shortcode") or r.get("shortcode")
        }
        return ProfileInfo(
            username=username,
            posts=len(posts),
            authenticated=self.auth_mode != "anonymous",
        )

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from .instagram_engine import GalleryDLInstagramEngine


@dataclass(frozen=True)
class RangeSpec:
    label: str
    start: datetime | None = None
    end: datetime | None = None
    latest_n: int | None = None


class InstagramApp:
    def __init__(self):
        self.engine = GalleryDLInstagramEngine()
        self.default_profile = "hustinderofficial"

    def run(self):
        while True:
            print("\n=== Instagram Downloader V2 ===")
            print("1. Download profile images")
            print("2. Quick update")
            print("3. Download single post")
            print("4. Check Instagram profile")
            print("5. Exit")
            c = input("Choose: ").strip()
            try:
                if c == "1":
                    p = input("Profile URL/username: ").strip()
                    if p:
                        self.run_download(p, self.choose_range())
                elif c == "2":
                    p = input("Profile URL/username: ").strip()
                    if p:
                        self.run_download(p, RangeSpec("Quick update"))
                elif c == "3":
                    self.run_single(input("Instagram post URL: ").strip())
                elif c == "4":
                    self.check_profile()
                elif c == "5":
                    return
                else:
                    print("Invalid choice.")
            except KeyboardInterrupt:
                print("\nCancelled.")
            except Exception as exc:
                print("ERROR:", exc)

    def choose_range(self):
        print("\n1. Last 7 days\n2. Last 1 month\n3. Last 3 months\n4. Last 6 months\n5. Last 1 year\n6. Everything available\n7. Custom dates\n8. Latest N image posts")
        c = input("Choose: ").strip()
        now = datetime.now(timezone.utc)
        days = {"1": 7, "2": 30, "3": 90, "4": 180, "5": 365}
        if c in days:
            d = days[c]
            return RangeSpec(f"Last {d} days", now - timedelta(days=d), now)
        if c == "6":
            return RangeSpec("Everything available")
        if c == "7":
            s = datetime.strptime(input("Start YYYY-MM-DD: ").strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            e = datetime.strptime(input("End YYYY-MM-DD: ").strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            if e < s:
                raise ValueError("End date must be on or after start date.")
            return RangeSpec("Custom", s, e)
        if c == "8":
            n = int(input("N: ").strip())
            if n < 1:
                raise ValueError("N must be at least 1.")
            return RangeSpec("Latest N image posts", latest_n=n)
        return RangeSpec("Last 7 days", now - timedelta(days=7), now)

    def check_profile(self):
        p = input(f"Profile URL/username [{self.default_profile}]: ").strip() or self.default_profile
        info = self.engine.inspect_profile(p)
        mode = "existing browser session" if info.authenticated else "anonymous public access"
        print(f"OK: @{info.username} | scanned posts={info.posts} | access={mode}")

    def run_download(self, profile, rng):
        username, posts, media_total = self.engine.preview(profile, rng.start, rng.end, rng.latest_n, rng.label == "Quick update")
        print("\nDOWNLOAD PREVIEW")
        print(f"  Profile: @{username}")
        print(f"  Range: {rng.label}")
        print(f"  New image posts: {len(posts)}")
        print(f"  Image media items expected: {media_total}")
        print(f"  Access: {self.engine.auth_mode or 'unknown'}")
        if not posts:
            print("  Nothing new to download.")
            return
        answer = input("Start download? [Y/n]: ").strip().lower()
        if answer not in ("", "y", "yes"):
            print("Cancelled.")
            return
        print("\nDOWNLOADING")
        stats = self.engine.download_images(username, posts, media_total)
        print(f"\nDONE | media downloaded={stats.downloaded} | skipped={stats.skipped} | failed={stats.failed}")
        if stats.errors:
            print("First error:", stats.errors[0])

    def run_single(self, url):
        stats = self.engine.download_single_image(url)
        print(f"Done | media downloaded={stats.downloaded} | skipped={stats.skipped} | failed={stats.failed}")
        if stats.errors:
            print("Error:", stats.errors[0])

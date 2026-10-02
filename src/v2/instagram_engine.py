from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json, re
from urllib.parse import urlparse
import browser_cookie3
import instaloader

@dataclass
class ProfileInfo:
    username: str
    mediacount: int
    is_private: bool

@dataclass
class DownloadStats:
    scanned: int = 0
    candidates: int = 0
    media_total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

class InstagramEngine:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[2]
        self.download_root = self.root / 'downloads' / 'Instagram'
        self.state_file = self.root / 'data' / 'instagram_state.json'
        self.session_dir = self.root / 'data' / 'sessions'
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state = self._load()
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_root / '{target}'),
            filename_pattern='{date_utc:%Y-%m-%d_%H-%M-%S}_{shortcode}',
            download_pictures=True, download_videos=False,
            download_video_thumbnails=False, download_comments=False,
            save_metadata=True, compress_json=False,
            post_metadata_txt_pattern=None, storyitem_metadata_txt_pattern=None,
            max_connection_attempts=3, request_timeout=120, iphone_support=True,
        )
        self._authenticate()

    def _load(self):
        try: return json.loads(self.state_file.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def _save(self):
        tmp = self.state_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, indent=2, sort_keys=True), encoding='utf-8')
        tmp.replace(self.state_file)

    def _session_file(self, username):
        return self.session_dir / f'{username}.session'

    def _authenticate(self):
        # Instagram currently restricts anonymous profile enumeration; use an existing
        # local Instaloader session first, then import the logged-in browser session.
        for session in sorted(self.session_dir.glob('*.session')):
            user = session.stem
            try:
                self.loader.load_session_from_file(user, str(session))
                if self.loader.test_login():
                    self.authenticated_as = user
                    return
            except Exception:
                continue
        for name, getter in [('Chrome', browser_cookie3.chrome), ('Edge', browser_cookie3.edge), ('Firefox', browser_cookie3.firefox)]:
            try:
                cookies = getter(domain_name='instagram.com')
                if not cookies: continue
                self.loader.context._session.cookies.update(cookies)
                user = self.loader.test_login()
                if user:
                    self.authenticated_as = user
                    self.loader.save_session_to_file(str(self._session_file(user)))
                    return
            except Exception:
                continue
        self.authenticated_as = None

    @staticmethod
    def normalize_profile(v):
        v = v.strip()
        if 'instagram.com' not in v: return v.lstrip('@').lower()
        parts = [p for p in urlparse(v if '://' in v else 'https://' + v).path.split('/') if p]
        if not parts: raise ValueError('Invalid Instagram URL.')
        u = parts[0].lstrip('@').lower()
        if u in {'p','reel','reels','tv'}: raise ValueError('Use a profile URL here.')
        if not re.fullmatch(r'[A-Za-z0-9._]+', u): raise ValueError('Invalid Instagram username.')
        return u

    def inspect_profile(self, v):
        if not self.authenticated_as:
            raise RuntimeError('Instagram now requires an authenticated session for profile enumeration. Log into Instagram in Chrome/Edge/Firefox, close the browser, then run this again.')
        u = self.normalize_profile(v)
        p = instaloader.Profile.from_username(self.loader.context, u)
        return ProfileInfo(p.username, p.mediacount, p.is_private)

    def _done(self, u): return set(self.state.get(u, {}).get('downloaded', []))
    def _target(self, u):
        p = self.download_root / u / 'Posts'; p.mkdir(parents=True, exist_ok=True); return p
    def _mark(self, u, code):
        r = self.state.setdefault(u, {})
        r['downloaded'] = sorted(self._done(u) | {code})
        r['last_success_utc'] = datetime.now(timezone.utc).isoformat()
        self._save()

    def preview(self, v, start=None, end=None, latest_n=None, quick_update=False):
        u = self.normalize_profile(v)
        p = instaloader.Profile.from_username(self.loader.context, u)
        posts = []
        done = self._done(u)
        for post in p.get_posts():
            dt = post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc.tzinfo is None else post.date_utc
            if start and dt < start: break
            if end and dt > end: continue
            if quick_update and post.shortcode in done: break
            if post.is_video: continue
            if post.shortcode in done: continue
            posts.append(post)
            if latest_n is not None and len(posts) >= latest_n: break
        media_total = sum(max(1, getattr(post, 'mediacount', 1)) for post in posts)
        return u, posts, media_total

    def download_images(self, username, posts, media_total):
        stats = DownloadStats(scanned=len(posts), candidates=len(posts), media_total=media_total)
        total = len(posts)
        for index, post in enumerate(posts, 1):
            try:
                changed = self.loader.download_post(post, target=str(self._target(username)))
                if changed:
                    self._mark(username, post.shortcode); stats.downloaded += 1
                else:
                    stats.skipped += 1
                remaining = total - index
                print(f'  [{index}/{total}] @{username}  {post.shortcode}  | downloaded={stats.downloaded} | remaining={remaining}')
            except Exception as e:
                stats.failed += 1
                stats.errors.append(post.shortcode + ': ' + str(e))
                print(f'  [{index}/{total}] FAILED {post.shortcode} | remaining={total-index}')
        return stats

    def download_single_image(self, url):
        if not self.authenticated_as:
            raise RuntimeError('An Instagram browser session is required. Log into Instagram in Chrome/Edge/Firefox first.')
        m = re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)', url)
        if not m: raise ValueError('Unsupported Instagram post URL.')
        post = instaloader.Post.from_shortcode(self.loader.context, m.group(1))
        if post.is_video: raise ValueError('Selected item is a video/reel; this build downloads images only.')
        u = post.owner_username; s = DownloadStats(scanned=1, candidates=1, media_total=max(1, post.mediacount))
        print(f'Downloading 1 post / {s.media_total} image media...')
        try:
            if self.loader.download_post(post, target=str(self._target(u))):
                self._mark(u, post.shortcode); s.downloaded = 1
            else: s.skipped = 1
        except Exception as e: s.failed = 1; s.errors.append(post.shortcode + ': ' + str(e))
        return s
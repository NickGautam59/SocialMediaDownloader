from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json, re, time, os
from urllib.parse import urlparse
import browser_cookie3
import instaloader

HEADERS = {
    'X-IG-App-ID': '936619743392459',
    'X-ASBD-ID': '198387',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

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
            download_pictures=True, download_videos=False, download_video_thumbnails=False,
            download_comments=False, save_metadata=True, compress_json=False,
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

    def _session_file(self, username): return self.session_dir / f'{username}.session'

    def _authenticate(self):
        # Reuse a previously imported Instaloader session first.
        for session in sorted(self.session_dir.glob('*.session')):
            try:
                user = session.stem
                self.loader.load_session_from_file(user, str(session))
                if self.loader.test_login():
                    self.authenticated_as = user
                    return
            except Exception:
                pass

        # Import cookies using the same mechanism as current Instaloader.
        # Brave is explicitly supported, including a common Brave Beta profile path.
        browsers = [
            ('Brave', browser_cookie3.brave, self._brave_cookie_files()),
            ('Chrome', browser_cookie3.chrome, [None]),
            ('Edge', browser_cookie3.edge, [None]),
            ('Firefox', browser_cookie3.firefox, [None]),
        ]

        for name, getter, cookie_files in browsers:
            for cookie_file in cookie_files:
                try:
                    kwargs = {'cookie_file': cookie_file} if cookie_file else {}
                    browser_cookies = list(getter(**kwargs))
                    cookies = {
                        cookie.name: cookie.value
                        for cookie in browser_cookies
                        if 'instagram' in cookie.domain
                    }
                    if not cookies:
                        continue

                    self.loader.context.update_cookies(cookies)
                    user = self.loader.test_login()
                    if user:
                        self.authenticated_as = user
                        self.loader.save_session_to_file(str(self._session_file(user)))
                        return
                except Exception:
                    continue

        self.authenticated_as = None

    @staticmethod
    def _brave_cookie_files():
        if os.name != 'nt':
            return [None]
        local = os.environ.get('LOCALAPPDATA', '')
        if not local:
            return [None]
        candidates = [
            Path(local) / 'BraveSoftware' / 'Brave-Browser-Beta' / 'User Data' / 'Default' / 'Network' / 'Cookies',
            Path(local) / 'BraveSoftware' / 'Brave-Browser' / 'User Data' / 'Default' / 'Network' / 'Cookies',
            Path(local) / 'BraveSoftware' / 'Brave-Browser-Beta' / 'User Data' / 'Default' / 'Cookies',
            Path(local) / 'BraveSoftware' / 'Brave-Browser' / 'User Data' / 'Default' / 'Cookies',
        ]
        existing = [str(p) for p in candidates if p.exists()]
        return existing or [None]

    @staticmethod
    def normalize_profile(v):
        v=v.strip()
        if 'instagram.com' not in v: return v.lstrip('@').lower()
        parts=[p for p in urlparse(v if '://' in v else 'https://'+v).path.split('/') if p]
        if not parts: raise ValueError('Invalid Instagram URL.')
        u=parts[0].lstrip('@').lower()
        if u in {'p','reel','reels','tv'}: raise ValueError('Use a profile URL here.')
        if not re.fullmatch(r'[A-Za-z0-9._]+',u): raise ValueError('Invalid Instagram username.')
        return u

    def _require_auth(self):
        if not self.authenticated_as:
            raise RuntimeError('Instagram profile access currently requires a logged-in browser session. Log into Instagram in Brave Beta (recommended), Chrome, Edge, or Firefox, fully close the browser, then run this program again.')

    def _resolve_user_id(self, username):
        # Fast path: Instaloader's current profile resolver.
        try:
            p=instaloader.Profile.from_username(self.loader.context, username)
            return int(p.userid), p
        except Exception:
            pass
        # Resilient fallback: read the profile page with the logged-in browser session.
        url=f'https://www.instagram.com/{username}/'
        headers={**HEADERS, 'Referer': url}
        resp=self.loader.context._session.get(url, headers=headers, timeout=self.loader.context.request_timeout)
        if resp.status_code >= 400: resp.raise_for_status()
        html=resp.text
        patterns=[
            r'profilePage_(\d+)',
            rf'"id"\s*:\s*"(\d+)"[^{{}}]{{0,250}}"username"\s*:\s*"{re.escape(username)}"',
            rf'"username"\s*:\s*"{re.escape(username)}"[^{{}}]{{0,250}}"(?:pk|id)"\s*:\s*"?(\d+)',
        ]
        for pattern in patterns:
            m=re.search(pattern,html,re.I)
            if m: return int(m.group(1)), None
        raise RuntimeError('Could not resolve the Instagram profile ID. Instagram changed the profile page format; no download was attempted.')

    def inspect_profile(self,v):
        self._require_auth(); u=self.normalize_profile(v)
        uid,p=self._resolve_user_id(u)
        return ProfileInfo(p.username if p else u, p.mediacount if p else 0, p.is_private if p else False)

    def _iter_profile_posts(self, username, user_id):
        url=f'https://www.instagram.com/api/v1/feed/user/{user_id}/'
        headers={**HEADERS, 'Referer': f'https://www.instagram.com/{username}/'}
        max_id=None
        while True:
            params={'count':12}
            if max_id: params['max_id']=max_id
            resp=self.loader.context._session.get(url, headers=headers, params=params, timeout=self.loader.context.request_timeout)
            resp.raise_for_status()
            data=resp.json()
            for item in data.get('items') or []:
                try: yield instaloader.Post.from_iphone_struct(self.loader.context,item)
                except Exception: continue
            if not data.get('more_available'): break
            max_id=data.get('next_max_id')
            if not max_id: break
            time.sleep(2)

    def _done(self,u): return set(self.state.get(u,{}).get('downloaded',[]))
    def _target(self,u):
        p=self.download_root/u/'Posts'; p.mkdir(parents=True,exist_ok=True); return p
    def _mark(self,u,code):
        r=self.state.setdefault(u,{})
        r['downloaded']=sorted(self._done(u)|{code})
        r['last_success_utc']=datetime.now(timezone.utc).isoformat()
        self._save()

    def preview(self,v,start=None,end=None,latest_n=None,quick_update=False):
        self._require_auth(); u=self.normalize_profile(v); uid,_=self._resolve_user_id(u)
        posts=[]; done=self._done(u)
        for post in self._iter_profile_posts(u,uid):
            dt=post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc.tzinfo is None else post.date_utc
            if start and dt<start: break
            if end and dt>end: continue
            if quick_update and post.shortcode in done: break
            if post.is_video or post.shortcode in done: continue
            posts.append(post)
            if latest_n is not None and len(posts)>=latest_n: break
        media_total=sum(max(1,getattr(post,'mediacount',1)) for post in posts)
        return u,posts,media_total

    def download_images(self,username,posts,media_total):
        stats=DownloadStats(scanned=len(posts),candidates=len(posts),media_total=media_total); total=len(posts)
        for index,post in enumerate(posts,1):
            try:
                changed=self.loader.download_post(post,target=str(self._target(username)))
                if changed: self._mark(username,post.shortcode); stats.downloaded+=1
                else: stats.skipped+=1
                print(f'  [{index}/{total}] {post.shortcode} | downloaded={stats.downloaded} | remaining={total-index}')
            except Exception as e:
                stats.failed+=1; stats.errors.append(post.shortcode+': '+str(e))
                print(f'  [{index}/{total}] FAILED {post.shortcode} | remaining={total-index}')
        return stats

    def download_single_image(self,url):
        self._require_auth()
        m=re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)',url)
        if not m: raise ValueError('Unsupported Instagram post URL.')
        post=instaloader.Post.from_shortcode(self.loader.context,m.group(1))
        if post.is_video: raise ValueError('Selected item is a video/reel; this build downloads images only.')
        u=post.owner_username; s=DownloadStats(scanned=1,candidates=1,media_total=max(1,post.mediacount))
        try:
            if self.loader.download_post(post,target=str(self._target(u))): self._mark(u,post.shortcode); s.downloaded=1
            else: s.skipped=1
        except Exception as e: s.failed=1; s.errors.append(post.shortcode+': '+str(e))
        return s
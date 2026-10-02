from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json, re
from urllib.parse import urlparse
import instaloader

@dataclass
class ProfileInfo:
    username: str
    mediacount: int
    is_private: bool

@dataclass
class DownloadStats:
    scanned: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

class InstagramEngine:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[2]
        self.download_root = self.root / 'downloads' / 'Instagram'
        self.state_file = self.root / 'data' / 'instagram_state.json'
        self.download_root.mkdir(parents=True, exist_ok=True); self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()
        self.loader = instaloader.Instaloader(dirname_pattern=str(self.download_root / '{target}'), filename_pattern='{date_utc:%Y-%m-%d_%H-%M-%S}_{shortcode}', download_comments=False, save_metadata=True, compress_json=False, post_metadata_txt_pattern=None)
        self.loader.context.max_connection_attempts = 3; self.loader.context.request_timeout = 60.0

    def _load(self):
        try: return json.loads(self.state_file.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError): return {}
    def _save(self):
        tmp=self.state_file.with_suffix('.tmp'); tmp.write_text(json.dumps(self.state,indent=2,sort_keys=True),encoding='utf-8'); tmp.replace(self.state_file)
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
    def inspect_profile(self,v):
        u=self.normalize_profile(v); p=instaloader.Profile.from_username(self.loader.context,u); return ProfileInfo(p.username,p.mediacount,p.is_private)
    def _done(self,u): return set(self.state.get(u,{}).get('downloaded',[]))
    def _target(self,u):
        p=self.download_root/u/'Posts'; p.mkdir(parents=True,exist_ok=True); return p
    def _mark(self,u,code):
        r=self.state.setdefault(u,{}); r['downloaded']=sorted(self._done(u)|{code}); r['last_success_utc']=datetime.now(timezone.utc).isoformat(); self._save()
    def _download(self,u,post,s):
        if post.shortcode in self._done(u): s.skipped+=1; return
        try:
            changed=self.loader.download_post(post,target=str(self._target(u)))
            if changed: self._mark(u,post.shortcode); s.downloaded+=1
            else: s.skipped+=1
        except Exception as e: s.failed+=1; s.errors.append(post.shortcode+': '+str(e))
    def download_images(self,u,start=None,end=None,latest_n=None,quick_update=False):
        u=self.normalize_profile(u); p=instaloader.Profile.from_username(self.loader.context,u)
        if p.is_private: raise PermissionError('Private profiles are not supported in this public-profile build.')
        s=DownloadStats(); done=self._done(u)
        for post in p.get_posts():
            s.scanned+=1; dt=post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc.tzinfo is None else post.date_utc
            if start and dt<start: break
            if end and dt>end: continue
            if quick_update and post.shortcode in done: break
            if post.is_video: continue
            self._download(u,post,s)
            if latest_n is not None and s.downloaded+s.skipped>=latest_n: break
        return s
    def download_single_image(self,url):
        m=re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)',url)
        if not m: raise ValueError('Unsupported Instagram post URL.')
        post=instaloader.Post.from_shortcode(self.loader.context,m.group(1))
        if post.is_video: raise ValueError('Selected item is a video/reel; image-only build skips videos.')
        s=DownloadStats(scanned=1); self._download(post.owner_username,post,s); return s
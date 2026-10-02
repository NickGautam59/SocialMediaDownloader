from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from .instagram_engine import InstagramEngine

@dataclass(frozen=True)
class RangeSpec:
    label: str
    start: datetime | None = None
    end: datetime | None = None
    latest_n: int | None = None

class InstagramApp:
    def __init__(self):
        self.engine = InstagramEngine()
        self.default_profile = 'hustinderofficial'

    def run(self):
        while True:
            print('\n=== Instagram Downloader V2 ===')
            print('1. Download profile images')
            print('2. Quick update')
            print('3. Download single post')
            print('4. Check Instagram session/profile')
            print('5. Exit')
            c = input('Choose: ').strip()
            if c == '1':
                p = input('Profile URL/username: ').strip()
                if not p: print('Profile is required.'); continue
                self.run_download(p, self.choose_range())
            elif c == '2':
                p = input('Profile URL/username: ').strip()
                if not p: print('Profile is required.'); continue
                self.run_download(p, RangeSpec('Quick update'))
            elif c == '3': self.run_single(input('Instagram post URL: ').strip())
            elif c == '4': self.check_profile()
            elif c == '5': return
            else: print('Invalid choice.')

    def choose_range(self):
        print('\n1. Last 7 days\n2. Last 1 month\n3. Last 3 months\n4. Last 6 months\n5. Last 1 year\n6. Everything available\n7. Custom dates\n8. Latest N image posts')
        c = input('Choose: ').strip(); now = datetime.now(timezone.utc)
        days = {'1':7,'2':30,'3':90,'4':180,'5':365}
        if c in days: return RangeSpec(f'Last {days[c]} days', now-timedelta(days=days[c]), now)
        if c == '6': return RangeSpec('Everything')
        if c == '7':
            s = datetime.strptime(input('Start YYYY-MM-DD: ').strip(), '%Y-%m-%d').replace(tzinfo=timezone.utc)
            e = datetime.strptime(input('End YYYY-MM-DD: ').strip(), '%Y-%m-%d').replace(hour=23,minute=59,second=59,tzinfo=timezone.utc)
            return RangeSpec('Custom', s, e)
        if c == '8': return RangeSpec('Latest N', latest_n=int(input('N: ').strip()))
        return RangeSpec('Last 7 days', now-timedelta(days=7), now)

    def check_profile(self):
        try:
            p = self.engine.inspect_profile(input('Profile URL/username: ').strip() or self.default_profile)
            print(f'OK: @{p.username} | posts={p.mediacount} | private={p.is_private} | session={self.engine.authenticated_as}')
        except Exception as e: print('ERROR:', e)

    def run_download(self, profile, rng):
        try:
            p = self.engine.inspect_profile(profile)
            print(f'\nProfile: @{p.username} | total posts reported: {p.mediacount}')
            print('Scanning matching image posts before download...')
            username, posts, media_total = self.engine.preview(p.username, rng.start, rng.end, rng.latest_n, rng.label == 'Quick update')
            print('\nDOWNLOAD PREVIEW')
            print(f'  Profile: @{username}')
            print(f'  Range: {rng.label}')
            print(f'  Image posts to download: {len(posts)}')
            print(f'  Image media items expected: {media_total}')
            if not posts:
                print('  Nothing new to download.')
                return
            answer = input('Start download? [Y/n]: ').strip().lower()
            if answer not in ('', 'y', 'yes'): print('Cancelled.'); return
            print('\nDOWNLOADING')
            s = self.engine.download_images(username, posts, media_total)
            print(f'\nDONE | posts downloaded={s.downloaded} | skipped={s.skipped} | failed={s.failed} | remaining=0')
            if s.errors: print('First error:', s.errors[0])
        except Exception as e: print('ERROR:', e)

    def run_single(self, url):
        try:
            s = self.engine.download_single_image(url)
            print(f'Done | downloaded={s.downloaded} | skipped={s.skipped} | failed={s.failed}')
        except Exception as e: print('ERROR:', e)
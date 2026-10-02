from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
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
            print('1. Download public profile images')
            print('2. Quick update')
            print('3. Download single post')
            print('4. Test profile')
            print('5. Exit')
            c = input('Choose: ').strip()
            if c == '1':
                p = input('Profile URL/username [' + self.default_profile + ']: ').strip() or self.default_profile
                self.run_download(p, self.choose_range())
            elif c == '2':
                p = input('Profile URL/username [' + self.default_profile + ']: ').strip() or self.default_profile
                self.run_download(p, RangeSpec('Quick update'))
            elif c == '3': self.run_single(input('Instagram post URL: ').strip())
            elif c == '4':
                try:
                    p = self.engine.inspect_profile(input('Profile [' + self.default_profile + ']: ').strip() or self.default_profile)
                    print('OK: @%s | posts=%s | private=%s' % (p.username, p.mediacount, p.is_private))
                except Exception as e: print('ERROR:', e)
            elif c == '5': return
            else: print('Invalid choice.')

    def choose_range(self):
        print('\n1 Last 7 days\n2 Last 1 month\n3 Last 3 months\n4 Last 6 months\n5 Last 1 year\n6 Everything\n7 Custom dates\n8 Latest N image posts')
        c = input('Choose: ').strip(); now = datetime.now(timezone.utc)
        days = {'1':7,'2':30,'3':90,'4':180,'5':365}
        if c in days: return RangeSpec('range', now-timedelta(days=days[c]), now)
        if c == '6': return RangeSpec('everything')
        if c == '7':
            s = datetime.strptime(input('Start YYYY-MM-DD: ').strip(), '%Y-%m-%d').replace(tzinfo=timezone.utc)
            e = datetime.strptime(input('End YYYY-MM-DD: ').strip(), '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            return RangeSpec('custom', s, e)
        if c == '8': return RangeSpec('latest', latest_n=int(input('N: ').strip()))
        return RangeSpec('range', now-timedelta(days=7), now)

    def run_download(self, profile, rng):
        try:
            p = self.engine.inspect_profile(profile)
            print('@%s: posts=%s, private=%s' % (p.username, p.mediacount, p.is_private))
            s = self.engine.download_images(p.username, rng.start, rng.end, rng.latest_n, rng.label == 'Quick update')
            print('Done: downloaded=%s skipped=%s failed=%s scanned=%s' % (s.downloaded,s.skipped,s.failed,s.scanned))
            if s.errors: print('First error:', s.errors[0])
        except Exception as e: print('ERROR:', e)

    def run_single(self, url):
        try:
            s = self.engine.download_single_image(url)
            print('Done: downloaded=%s skipped=%s failed=%s' % (s.downloaded,s.skipped,s.failed))
        except Exception as e: print('ERROR:', e)
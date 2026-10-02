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
            print('1. Set up Instagram session')
            print('2. Download profile images')
            print('3. Quick update')
            print('4. Download single post')
            print('5. Check Instagram session/profile')
            print('6. Exit')
            c=input('Choose: ').strip()
            if c=='1': self.setup_session()
            elif c=='2':
                p=input('Profile URL/username: ').strip()
                if p: self.run_download(p,self.choose_range())
                else: print('Profile is required.')
            elif c=='3':
                p=input('Profile URL/username: ').strip()
                if p: self.run_download(p,RangeSpec('Quick update'))
                else: print('Profile is required.')
            elif c=='4': self.run_single(input('Instagram post URL: ').strip())
            elif c=='5': self.check_profile()
            elif c=='6': return
            else: print('Invalid choice.')

    def setup_session(self):
        username=input('Instagram username: ').strip().lstrip('@')
        if not username:
            print('Username is required.')
            return
        try:
            print('\nInstagram will handle the login interactively.')
            print('Your password is entered directly into the Instaloader prompt and is not stored in this project.')
            self.engine.loader.interactive_login(username)
            if not self.engine.loader.test_login():
                raise RuntimeError('Instagram login did not produce a valid session.')
            self.engine.authenticated_as=username
            session_file=self.engine._session_file(username)
            self.engine.loader.save_session_to_file(str(session_file))
            print(f'\nSESSION READY: @{username}')
            print(f'Saved session: {session_file}')
            print('You can now use Download profile images.')
        except Exception as e:
            print('LOGIN ERROR:', e)

    def choose_range(self):
        print('\n1. Last 7 days\n2. Last 1 month\n3. Last 3 months\n4. Last 6 months\n5. Last 1 year\n6. Everything available\n7. Custom dates\n8. Latest N image posts')
        c=input('Choose: ').strip(); now=datetime.now(timezone.utc)
        days={'1':7,'2':30,'3':90,'4':180,'5':365}
        if c in days: return RangeSpec(f'Last {days[c]} days',now-timedelta(days=days[c]),now)
        if c=='6': return RangeSpec('Everything available')
        if c=='7':
            s=datetime.strptime(input('Start YYYY-MM-DD: ').strip(),'%Y-%m-%d').replace(tzinfo=timezone.utc)
            e=datetime.strptime(input('End YYYY-MM-DD: ').strip(),'%Y-%m-%d').replace(hour=23,minute=59,second=59,tzinfo=timezone.utc)
            if e<s: raise ValueError('End date must be on or after start date.')
            return RangeSpec('Custom',s,e)
        if c=='8': return RangeSpec('Latest N',latest_n=int(input('N: ').strip()))
        return RangeSpec('Last 7 days',now-timedelta(days=7),now)

    def check_profile(self):
        try:
            p=self.engine.inspect_profile(input('Profile URL/username: ').strip() or self.default_profile)
            print(f'OK: @{p.username} | reported posts={p.mediacount} | private={p.is_private} | session={self.engine.authenticated_as}')
        except Exception as e: print('ERROR:',e)

    def run_download(self,profile,rng):
        try:
            username,posts,media_total=self.engine.preview(profile,rng.start,rng.end,rng.latest_n,rng.label=='Quick update')
            print('\nDOWNLOAD PREVIEW')
            print(f'  Profile: @{username}')
            print(f'  Range: {rng.label}')
            print(f'  New image posts: {len(posts)}')
            print(f'  Image media items expected: {media_total}')
            if not posts: print('  Nothing new to download.'); return
            answer=input('Start download? [Y/n]: ').strip().lower()
            if answer not in ('','y','yes'): print('Cancelled.'); return
            print('\nDOWNLOADING')
            s=self.engine.download_images(username,posts,media_total)
            print(f'\nDONE | posts downloaded={s.downloaded} | skipped={s.skipped} | failed={s.failed} | remaining=0')
            if s.errors: print('First error:',s.errors[0])
        except Exception as e: print('ERROR:',e)

    def run_single(self,url):
        try:
            s=self.engine.download_single_image(url)
            print(f'Done | downloaded={s.downloaded} | skipped={s.skipped} | failed={s.failed}')
        except Exception as e: print('ERROR:',e)
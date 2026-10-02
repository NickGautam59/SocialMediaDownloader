# Instagram V2

Separate Instagram branch for public-profile image downloading. Existing Facebook implementation is not changed.

## Run

Install: `py -m pip install -r requirements-instagram-v2.txt`

Launch: `py run_v2.py`

Do not launch `src/v2/main.py` directly.

## Test profile

https://www.instagram.com/hustinderofficial?stkn=ZnFza3NkMzF5NzFr

The query string is ignored for profile extraction.

## Current scope

- Public profile posts
- Images and carousels/sidecars through Instaloader
- Last 7 days, 1/3/6 months, 1 year
- Everything available
- Custom date range
- Latest N image posts
- Quick update
- Single image-post URL
- Local duplicate state
- No comments download
- No profile-picture download

Video posts and Reels are skipped by this image-focused build.
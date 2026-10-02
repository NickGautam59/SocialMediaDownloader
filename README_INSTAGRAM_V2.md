# Instagram Downloader V2

Instagram V2 uses the maintained **gallery-dl** Instagram extractor. Facebook/V1 is untouched.

## Workflow

1. Enter only an Instagram profile URL or username.
2. Choose 7 days, 1/3/6 months, 1 year, everything, custom dates, or latest N image posts.
3. V2 scans first and shows new image posts plus expected image media items.
4. Confirm with Y.
5. Images download without intentional resizing or recompression.
6. Quick update later picks up media not already archived.

## Authentication

V2 never asks for an Instagram password. It tries public extraction first. If Instagram requires a logged-in session, gallery-dl can try an existing Brave, Chrome, Edge, or Firefox browser session. Browser cookies are read directly by gallery-dl and are not exported into this project. Brave Beta's detected Default profile is also tried on Windows.

## Images

- Image posts and image slides from carousels
- Videos/Reels excluded
- Highest practical image URL selected by gallery-dl
- No intentional resizing or recompression
- Download archive for duplicate protection
- Retry handling
- Per-post progress

## Output

`downloads/Instagram/<username>/Posts/`

Local state is kept in `data/instagram_gallery_archive.txt` and `data/instagram_state.json`; both are ignored by git.

## Install

```powershell
py -m pip install -r requirements-instagram-v2.txt
py run_v2.py
```

Pinned engine: gallery-dl 1.32.14.

Example profile:
`https://www.instagram.com/hustinderofficial/`

The old Instaloader/browser-cookie3/password-login path has been removed from Instagram V2.
# Instagram Downloader V2

Instagram V2 uses the maintained **gallery-dl** Instagram extractor. Facebook/V1 is untouched.

## Workflow

1. Enter only an Instagram profile URL or username.
2. Choose 7 days, 1/3/6 months, 1 year, everything, custom dates, or latest N image posts.
3. V2 scans the profile first.
4. It shows new image posts and expected image media items.
5. Confirm with Y.
6. Images download without intentional resizing or recompression.
7. Run Quick update later for new media.

## Authentication

V2 never asks for an Instagram password.

It tries public/anonymous extraction first. If Instagram requires a logged-in session, gallery-dl can try an existing Brave, Chrome, Edge, or Firefox browser session. Browser cookies are read directly by gallery-dl and are not exported into the project.

For Brave Beta on Windows, V2 also tries the detected Default profile directory.

## Images

- Image posts
- Image slides from carousels
- Videos/Reels excluded
- Highest practical image URL selected by gallery-dl
- No intentional resizing or recompression
- Download archive for duplicate protection
- Retry handling
- Per-post progress

## Output

downloads/Instagram/<username>/Posts/

Local state:
- data/instagram_gallery_archive.txt
- data/instagram_state.json

These are ignored by git.

## Install

```powershell
py -m pip install -r requirements-instagram-v2.txt
py run_v2.py
```

Pinned engine: gallery-dl 1.32.14.

## Example

```
https://www.instagram.com/hustinderofficial/
```

The old Instaloader/browser-cookie3/password-login implementation has been removed from the Instagram V2 path.

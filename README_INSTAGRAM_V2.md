# Instagram V2

Instagram-only V2 branch for public profile image archiving. Facebook code is not modified.

## Why browser login is used

Instagram currently restricts anonymous profile enumeration. Instaloader 4.15.3 can return 401/429 from profile endpoints even on a first request. Current Instaloader reports also document retired GraphQL profile-post endpoints. This build therefore imports an existing Instagram session from Chrome, Edge, or Firefox automatically and uses the current `/api/v1/feed/user/<id>/` pagination path as the profile-post fallback. citeturn6search4turn8search0

**No Instagram password is stored in this project.** The program reads the existing browser session and stores only an Instaloader session file under the ignored local `data/sessions/` directory.

## Run

```text
py -m pip install -r requirements-instagram-v2.txt
py run_v2.py
```

Use `run_v2.py` as the only launcher.

## Workflow

1. Enter any public Instagram profile URL.
2. Choose 7 days, 1/3/6 months, 1 year, everything, custom dates, or latest N.
3. The program scans the matching posts first.
4. It shows the number of new image posts and expected image media items.
5. You confirm with Y.
6. Downloads run with `[current/total]`, downloaded count, and remaining count.

## Quality

Post pictures are downloaded through Instaloader with picture downloads enabled and iPhone/high-resolution support left enabled. The program does not intentionally resize, recompress, or choose a lower-quality derivative.

## Content

- Image posts
- Carousels / sidecars
- Date filtering
- Quick update
- Duplicate protection
- Resume through Instaloader's normal download handling
- Metadata JSON
- Single image-post URL

Video posts and Reels are intentionally excluded from this image-focused build.

## Example

https://www.instagram.com/hustinderofficial?stkn=ZnFza3NkMzF5NzFr

The tracking query string is ignored.
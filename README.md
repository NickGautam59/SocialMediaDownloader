# 🚀 Social Media Downloader

> **A powerful, privacy-friendly command-line downloader for Facebook & Instagram — powered by [gallery-dl](https://github.com/mikf/gallery-dl).**

<p align="center">

**Facebook • Instagram • Photos • Videos • Posts • Reels • Date Ranges • Archive Protection**

</p>

---

## ✨ Overview

**Social Media Downloader** is a lightweight Python application that provides a simple menu-driven interface around `gallery-dl`.

Instead of remembering complex `gallery-dl` commands, you choose what you want from a clean interactive menu:

```text
Platform
   ↓
Content Type
   ↓
Date / Range
   ↓
Download
```

The project is designed to be:

- ⚡ Fast and lightweight
- 🧩 Modular and easy to maintain
- 🛡️ Safer for repeated downloads through archive protection
- 📁 Automatically organized
- 🔁 Suitable for repeated/incremental downloads
- 🐍 Built with Python
- 🆓 Free and open-source friendly
- 🖥️ Easy to run from Windows + VS Code

---

# 🎯 Features

## 📘 Facebook

Supports:

- 📸 Photos
- 🎥 Videos
- 📸🎥 Photos + Videos

Example:

```text
Facebook
   ↓
Photos
   ↓
Last 30 days
   ↓
Download
```

---

## 📸 Instagram

Supports:

- 📷 Photos
- 📝 Posts
- 🎬 Reels
- 🎥 Videos
- 📷🎬 Posts + Reels
- 📦 Everything

Example:

```text
Instagram
   ↓
Posts + Reels
   ↓
Last 6 months
   ↓
Download
```

---

# 📅 Flexible Date Selection

Choose exactly what you want to download.

```text
1. Last 7 days
2. Last 30 days
3. Last N months
4. Specific year
5. Custom date range
6. Everything
7. New since last download
8. Latest N media items
```

### Examples

### Last 7 Days

```text
Today
  ↓
7 days backwards
  ↓
Download matching media
```

### Last N Months

```text
Enter: 6

Today
  ↓
6 months backwards
  ↓
Download matching media
```

### Specific Year

```text
Enter: 2025

2025-01-01
     ↓
2025-12-31
```

### Custom Range

```text
Start: 2025-01-01
End:   2025-06-30
```

---

# 🛡️ Archive & Duplicate Protection

The downloader uses gallery-dl's archive functionality to prevent previously processed media from being downloaded repeatedly.

Conceptually:

```text
             Download Request
                    │
                    ▼
              Gallery-dl
                    │
                    ▼
              Archive Check
               /          \
          Already?         New?
             │               │
            YES              YES
             │               │
            Skip          Download
```

This makes repeated downloads much more practical.

For example:

```text
First run
─────────
1,000 media discovered
1,000 processed


Second run
──────────
1,000 old
   +
  20 new

→ Only new media needs processing
```

---

# 📁 Project Structure

```text
SOCIALMEDIADOWNLOADER/
│
├── config/
│   └── gallery-dl.json
│
├── downloads/
│
├── archive/
│
├── logs/
│
├── src/
│   ├── main.py
│   ├── menu.py
│   ├── downloader.py
│   ├── date_range.py
│   ├── filters.py
│   ├── paths.py
│   └── report.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

### Components

| File | Purpose |
|---|---|
| `main.py` | Application entry point |
| `menu.py` | Interactive user interface |
| `downloader.py` | Gallery-dl execution engine |
| `date_range.py` | Date/range calculations |
| `filters.py` | Content filtering |
| `paths.py` | Project directories |
| `report.py` | State and download reports |
| `gallery-dl.json` | Gallery-dl configuration |

---

# 🖥️ Application Interface

The application starts with:

```text
============================================================
          SOCIAL MEDIA DOWNLOADER
============================================================

1. Facebook
2. Instagram
3. Settings
4. Download History
5. Exit

Select an option:
```

### Facebook

```text
============================================================
                    FACEBOOK
============================================================

1. Photos
2. Videos
3. Photos + Videos
4. Back
```

### Instagram

```text
============================================================
                   INSTAGRAM
============================================================

1. Photos
2. Posts
3. Reels
4. Videos
5. Posts + Reels
6. Everything
7. Back
```

---

# ⚙️ Requirements

## Operating System

Primarily developed and tested on:

- Windows 10/11

The underlying gallery-dl project supports multiple platforms, but this project currently focuses on a straightforward Windows + Python workflow.

## Software

You need:

- Python 3.10+
- `pip`
- `gallery-dl`
- Git (optional, for GitHub)
- VS Code (recommended)

---

# 🚀 Installation

## 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/SocialMediaDownloader.git
cd SocialMediaDownloader
```

Or download the repository ZIP and extract it.

---

## 2. Install dependencies

Run:

```powershell
py -m pip install -r requirements.txt
```

Or install gallery-dl directly:

```powershell
py -m pip install -U gallery-dl
```

Verify:

```powershell
py -m gallery_dl --version
```

---

# ▶️ Run the Application

From the project root:

```powershell
py src/main.py
```

You should see:

```text
============================================================
          SOCIAL MEDIA DOWNLOADER
============================================================

1. Facebook
2. Instagram
3. Settings
4. Download History
5. Exit
```

---

# 📥 Basic Usage

## Facebook Example

Choose:

```text
1. Facebook
```

Enter the page URL:

```text
https://www.facebook.com/61585184752261/
```

Then select:

```text
Photos
```

and choose a date range.

---

## Instagram Example

Choose:

```text
2. Instagram
```

Enter:

```text
https://www.instagram.com/whospri__/
```

Then select:

```text
Posts + Reels
```

and choose the desired date range.

---

# 🔗 URL Examples

### Facebook

```text
https://www.facebook.com/PAGE
```

or a numeric Facebook page URL:

```text
https://www.facebook.com/61585184752261/
```

### Instagram

```text
https://www.instagram.com/USERNAME/
```

Sharing parameters such as:

```text
?igsh=...
```

can normally be removed from the URL.

For example:

```text
https://www.instagram.com/whospri__/?igsh=abc123
```

can be entered as:

```text
https://www.instagram.com/whospri__/
```

---

# 📦 Download Configuration

The project uses:

```text
config/gallery-dl.json
```

The configuration includes:

- Download base directory
- SQLite archive
- Retry handling
- Timeout
- Facebook video support
- Instagram video/audio support
- Instagram cursor pagination
- Post ordering
- Request-delay protection

Example:

```json
{
    "extractor": {
        "base-directory": "./downloads",
        "archive": "./archive/downloads.sqlite3",
        "retries": 4,
        "timeout": 30,

        "facebook": {
            "videos": true
        },

        "instagram": {
            "videos": true,
            "audio": true,
            "cursor": true,
            "previews": false,
            "order-posts": "desc",
            "order-files": "asc",
            "user-cache": "disk",
            "sleep-request": "6.0-12.0"
        }
    }
}
```

---

# 🧠 How It Works

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │   Main Menu     │
                  └────────┬────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
            FACEBOOK             INSTAGRAM
                 │                   │
                 ▼                   ▼
          Content Type        Content Type
                 │                   │
                 └─────────┬─────────┘
                           ▼
                     Date Range
                           │
                           ▼
                    Filter Builder
                           │
                           ▼
                    Gallery-dl
                           │
                           ▼
                    Archive Check
                           │
                           ▼
                      Download
                           │
                           ▼
                      Report
```

---

# 📊 Download Reports

After a download, the application creates a report inside:

```text
logs/
```

Reports contain information such as:

- Platform
- URL
- Content selection
- Date range
- Command used
- Return code
- Duration

Example:

```text
============================================================
SOCIAL MEDIA DOWNLOADER REPORT
============================================================

Platform       : Instagram
URL            : https://www.instagram.com/example/
Content        : Posts + Reels
Date Range     : Last 30 days
Return Code    : 0
Duration       : 125.4 seconds

Command:
...

============================================================
```

---

# 🗂️ Download Storage

Downloads are stored separately from the application source.

```text
SOCIALMEDIADOWNLOADER/
│
├── downloads/
│
├── archive/
│
└── logs/
```

This separation is intentional.

It allows you to:

- Update the program without mixing source files with media
- Keep the Git repository lightweight
- Preserve the download archive
- Keep logs separate

---

# 🔐 Privacy & Security

## Never commit these to GitHub

Do **not** upload:

```text
downloads/
archive/
logs/
gallery-dl/
.env
cookies
sessions
authentication files
```

The included `.gitignore` is intended to help prevent accidental commits.

### Never put passwords or access tokens directly into:

```text
gallery-dl.json
```

or Python source files.

---

# 🌐 GitHub

This project can be maintained in either:

### Private repository

Recommended while developing:

```text
GitHub
   ↓
Private repository
   ↓
Development
   ↓
Testing
   ↓
Release
```

### Public repository

Once the project is stable, you can publish it for others to use.

Before making it public, review:

- `.gitignore`
- authentication handling
- documentation
- third-party licenses
- example configuration
- personal data
- downloaded media
- logs

---

# 🧰 Useful Commands

### Check Python

```powershell
py --version
```

### Check gallery-dl

```powershell
py -m gallery_dl --version
```

### Update gallery-dl

```powershell
py -m pip install -U gallery-dl
```

### Run application

```powershell
py src/main.py
```

### Check Git

```powershell
git status
```

### Add files

```powershell
git add .
```

### Commit

```powershell
git commit -m "Update downloader"
```

### Push

```powershell
git push
```

---

# 🐛 Troubleshooting

## `ModuleNotFoundError`

Run:

```powershell
py -m pip install -r requirements.txt
```

---

## `gallery-dl` command not found

Use:

```powershell
py -m gallery_dl
```

instead of:

```powershell
gallery-dl
```

---

## Instagram returns no results

First test gallery-dl directly:

```powershell
py -m gallery_dl --verbose -K "https://www.instagram.com/USERNAME/"
```

If metadata is returned, the extractor is working and the issue is likely in the application's filtering/configuration.

---

## Facebook returns `KeyError: 'set_id'`

Facebook's web response can change over time.

Test:

```powershell
py -m gallery_dl --verbose -K "FACEBOOK_URL"
```

If `set_id` is missing from the extractor response, check the current gallery-dl version and upstream issue tracker before changing application code.

---

## Download was interrupted

Run the same selection again.

The archive is intended to prevent previously processed items from being downloaded repeatedly.

---

# ⚠️ Responsible Use

This software is intended for downloading content that you are permitted to download.

Before downloading or redistributing content:

- Respect copyright.
- Respect the creator's rights.
- Respect platform terms and applicable laws.
- Do not use the software to bypass access controls.
- Do not redistribute private or restricted content without permission.
- Do not commit authentication credentials or private data to GitHub.

The user is responsible for how this software is used.

---

# 🛣️ Roadmap

Planned improvements:

- [ ] Better download progress display
- [ ] Accurate pre-download media estimation
- [ ] Exact "new media" count
- [ ] Better post/reel classification
- [ ] True latest-N-post selection
- [ ] Improved folder organization
- [ ] Quality selection
- [ ] Configuration wizard
- [ ] GUI
- [ ] Scheduled downloads
- [ ] Multi-account support
- [ ] More social platforms
- [ ] Automatic update checker
- [ ] Portable Windows release
- [ ] One-click installer
- [ ] Docker support
- [ ] Automated tests
- [ ] GitHub Actions

---

# 🤝 Contributing

Contributions are welcome.

Recommended workflow:

```text
Fork
  ↓
Create branch
  ↓
Make change
  ↓
Test
  ↓
Commit
  ↓
Pull Request
```

Before submitting a change:

1. Test Facebook.
2. Test Instagram.
3. Test at least one date range.
4. Test duplicate/archive behavior.
5. Make sure no credentials or downloaded media are included.

---

# ⭐ Project Philosophy

The goal is simple:

> **Complex downloading should feel simple to the user.**

Instead of remembering commands like:

```powershell
py -m gallery_dl ...
```

the user should be able to think:

```text
"I want Instagram reels from the last 3 months."
```

and select:

```text
Instagram
   ↓
Reels
   ↓
Last N months
   ↓
3
   ↓
Download
```

The application handles the underlying gallery-dl configuration.

---

# 📜 License

This project is a wrapper/application around third-party software.

Before choosing a license for this repository, review the licenses of all dependencies and decide how you want to license your own code.

The project relies on:

- Python
- gallery-dl

See the respective projects for their licensing terms.

---

# 💙 Acknowledgements

Special thanks to the maintainers and contributors of:

### gallery-dl

A command-line program for downloading image galleries and collections from various websites.

🔗 https://github.com/mikf/gallery-dl

---

# 👑 Social Media Downloader

**Facebook + Instagram**

**Simple interface. Powerful backend.**

```text
Choose → Filter → Download
```

---

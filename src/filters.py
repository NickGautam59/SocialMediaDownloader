VIDEO_EXTENSIONS = {
    "mp4",
    "m4v",
    "mov",
    "webm",
    "mkv",
    "avi",
    "3gp"
}


IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "avif"
}


def content_filter(platform, content):
    """
    Returns a gallery-dl filter expression.

    This is intentionally conservative.
    The extractor itself decides which media exists.
    """

    if platform == "Facebook":

        if content == "Photos":
            return (
                "extension.lower() "
                "not in "
                f"{sorted(VIDEO_EXTENSIONS)!r}"
            )

        if content == "Videos":
            return (
                "extension.lower() "
                "in "
                f"{sorted(VIDEO_EXTENSIONS)!r}"
            )

        return None

    if platform == "Instagram":

        if content == "Photos":
            return (
                "extension.lower() "
                "in "
                f"{sorted(IMAGE_EXTENSIONS)!r}"
            )

        if content == "Videos":
            return (
                "extension.lower() "
                "in "
                f"{sorted(VIDEO_EXTENSIONS)!r}"
            )

        return None

    return None


def instagram_include(content):
    """
    Determines which Instagram extractor
    categories should be requested.
    """

    if content == "Reels":
        return "reels"

    if content == "Posts":
        return "posts"

    if content == "Posts + Reels":
        return "posts,reels"

    if content == "Everything":
        return "posts,reels"

    if content == "Photos":
        return "posts"

    if content == "Videos":
        return "posts"

    return "posts"
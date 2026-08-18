"""Supabase Storage-backed cookie manager for yt-dlp.

Cookie files are stored in a private Supabase Storage bucket named 'cookies'.
On each invocation, the needed cookie file is downloaded to /tmp (the only
writable directory in serverless environments) and cleaned up afterwards.

On a traditional server the files would persist, but /tmp cleanup is
still harmless.
"""
import os
import tempfile
import logging

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

# In-memory cache: {cookie_name: absolute_path}
_cookie_cache: dict[str, str] = {}

STORAGE_BUCKET = "cookies"

# Mapping of cookie names used by platform modules to their storage filenames.
_COOKIE_FILENAMES: dict[str, str] = {
    "youtube": "youtube.txt",
    "instagram": "insta.txt",
    "tiktok": "insta.txt",
    "twitter": "x.txt",
    "facebook": "facebook.txt",
    "twitch": "twitch.txt",
    "rumble": "rumble.txt",
    "vimeo": "vimeo_cookies.txt",
    "fallback": "fallback_cookies.txt",
}

TEMP_DIR = tempfile.gettempdir()


def _storage_available() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def get_cookie_path(platform: str) -> str | None:
    """Return the local temp path for a platform's cookie file.

    Downloads from Supabase Storage on first call, then caches.
    Returns None if the cookie file doesn't exist in Storage or
    Supabase is not configured.
    """
    if not _storage_available():
        return None

    cookie_name = _COOKIE_FILENAMES.get(platform, f"{platform}.txt")

    if cookie_name in _cookie_cache:
        cached = _cookie_cache[cookie_name]
        if os.path.isfile(cached):
            return cached
        _cookie_cache.pop(cookie_name, None)

    tmp_path = os.path.join(TEMP_DIR, f"ytcookies_{cookie_name}")

    if os.path.isfile(tmp_path):
        _cookie_cache[cookie_name] = tmp_path
        return tmp_path

    storage_path = cookie_name
    download_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"

    try:
        import requests as _requests

        resp = _requests.get(
            download_url,
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            },
            timeout=10,
        )
        if resp.status_code == 200 and resp.content:
            with open(tmp_path, "wb") as f:
                f.write(resp.content)
            _cookie_cache[cookie_name] = tmp_path
            logger.info("Downloaded cookie '%s' -> %s", cookie_name, tmp_path)
            return tmp_path
        else:
            logger.debug(
                "Cookie '%s' not found in Storage (HTTP %s)",
                cookie_name,
                resp.status_code,
            )
            return None
    except Exception as exc:
        logger.warning("Failed to download cookie '%s': %s", cookie_name, exc)
        return None


def cleanup_tmp_cookies() -> None:
    """Remove all cached cookie files from temp dir."""
    for cookie_name, path in list(_cookie_cache.items()):
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    _cookie_cache.clear()

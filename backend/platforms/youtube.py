import re
import logging
from urllib.parse import urlparse, parse_qs
from backend.platforms.base import BASE_CONFIG
from backend.errors import unsupported_url_type

logger = logging.getLogger(__name__)

DOMAINS = ['youtube.com', 'youtu.be', 'm.youtube.com']

# YouTube URL path segments that indicate non-video resources
_UNSUPPORTED_PATHS = {
    'playables': 'a YouTube Playable game',
    'channel': 'a YouTube channel page',
    'channels': 'a YouTube channels listing',
    'user': 'a legacy YouTube user page',
    'results': 'YouTube search results',
    'playlist': 'a YouTube playlist',
    'shorts': 'a YouTube Short',
    'live': 'a live stream',
    'gaming': 'YouTube Gaming',
    'music.youtube.com': 'YouTube Music',
    'podcasts': 'a YouTube Podcast',
    'feed': 'a YouTube feed page',
}

# Regex patterns for YouTube URLs that should be rejected
_CHANNEL_PATTERNS = [
    re.compile(r'youtube\.com/(@[\w.-]+)(?:/.*)?$', re.IGNORECASE),     # /@handle
    re.compile(r'youtube\.com/channel/[\w-]+(?:/.*)?$', re.IGNORECASE),  # /channel/ID
    re.compile(r'youtube\.com/c/[\w.-]+(?:/.*)?$', re.IGNORECASE),       # /custom/Name
    re.compile(r'youtube\.com/user/[\w.-]+(?:/.*)?$', re.IGNORECASE),    # /user/Name
]

_SEARCH_PATTERNS = [
    re.compile(r'youtube\.com/results\?.*search_query=', re.IGNORECASE),
]


def validate_youtube_url(url: str) -> None:
    """Validate that a YouTube URL points to an actual downloadable video.
    
    Raises AppError if the URL is not a supported video resource.
    """
    if not url:
        return
    
    parsed = urlparse(url if '://' in url else 'https://' + url)
    hostname = (parsed.hostname or '').lower()
    path = (parsed.path or '').strip('/')
    
    # Check for youtu.be short URLs — always valid (they're direct video links)
    if hostname == 'youtu.be':
        return
    
    # Check for YouTube Music
    if 'music.youtube.com' in hostname:
        raise unsupported_url_type('YouTube Music', 'YouTube')
    
    # Extract the first path segment
    path_segments = [s for s in path.split('/') if s]
    first_segment = path_segments[0].lower() if path_segments else ''
    
    # Check against known unsupported path segments
    if first_segment in _UNSUPPORTED_PATHS:
        raise unsupported_url_type(_UNSUPPORTED_PATHS[first_segment], 'YouTube')
    
    # Check for /shorts/ anywhere in the path
    if 'shorts' in path.lower():
        raise unsupported_url_type('a YouTube Short', 'YouTube')
    
    # Check for channel-like URL patterns
    for pattern in _CHANNEL_PATTERNS:
        if pattern.search(url):
            raise unsupported_url_type('a YouTube channel', 'YouTube')
    
    # Check for search URLs
    for pattern in _SEARCH_PATTERNS:
        if pattern.search(url):
            raise unsupported_url_type('YouTube search results', 'YouTube')
    
    # Check for bare hostname with no meaningful path
    if hostname in ('youtube.com', 'm.youtube.com', 'www.youtube.com') and not path_segments:
        raise unsupported_url_type('the YouTube homepage', 'YouTube')
    
    # Check for YouTube embedded player URLs (not downloadable)
    if '/embed/' in path.lower():
        raise unsupported_url_type('an embedded YouTube player', 'YouTube')


def validate_extracted_metadata(info: dict, url: str) -> None:
    """Validate that extracted metadata is trustworthy, not a fake/partial result.
    
    Raises AppError if the metadata indicates the resource is not a valid video.
    """
    if not info:
        raise unsupported_url_type('this URL', 'YouTube')
    
    extractor = (info.get('_type') or '').lower()
    title = (info.get('title') or '').strip()
    duration = info.get('duration') or 0
    webpage_url = (info.get('webpage_url') or '').lower()
    entries = info.get('entries')
    
    # If it's a playlist/series type and we asked for noplaylist, reject
    if extractor in ('playlist', 'multi_video'):
        # Check if it has entries — if so, it's a playlist, not a single video
        if entries and hasattr(entries, '__iter__'):
            count = sum(1 for _ in entries) if not isinstance(entries, list) else len(entries)
            if count > 0:
                raise unsupported_url_type('a YouTube playlist', 'YouTube')
    
    # Reject if title is empty or just a URL slug with no real content
    if not title or title.lower() in ('untitled', 'no title'):
        raise unsupported_url_type('this URL', 'YouTube')
    
    # Reject YouTube Music links that somehow passed hostname check
    if 'music.youtube.com' in webpage_url:
        raise unsupported_url_type('YouTube Music', 'YouTube')
    
    # Warn (but don't fail) if duration is 0 — could be a live stream or error
    if duration == 0 and extractor not in ('playlist',):
        logger.warning("YouTube metadata has 0 duration for %s — possible live stream or extraction issue", url)


def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        'writesubtitles': True,
        'writeautomaticsub': True,
    }

def post_process_metadata(info, metadata):
    metadata['tags'] = info.get('tags', []) or []
    metadata['resource_type'] = info.get('_type', 'video')
    return metadata

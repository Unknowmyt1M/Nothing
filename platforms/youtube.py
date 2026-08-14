from platforms.base import BASE_CONFIG

DOMAINS = ['youtube.com', 'youtu.be', 'm.youtube.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'cookiefile': 'cookies/youtube.txt',
    }

def post_process_metadata(info, metadata):
    # YouTube has built-in tags in yt-dlp metadata
    metadata['tags'] = info.get('tags', []) or []
    return metadata

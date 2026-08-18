from backend.platforms.base import BASE_CONFIG

DOMAINS = ['rumble.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=1440][ext=mp4]/best[height>=1080][ext=mp4]/best[height>=720][ext=mp4]/best[ext=mp4]/best',
        'writesubtitles': True,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'extractor_retries': 5,
        'http_chunk_size': 10485760,
        'hls_use_mpegts': False,
        'extract_flat': False,
    }

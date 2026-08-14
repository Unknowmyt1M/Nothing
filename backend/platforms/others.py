from backend.platforms.base import BASE_CONFIG

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
        'extractor_retries': 5,
        'http_chunk_size': 10485760,
    }

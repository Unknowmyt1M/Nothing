from backend.platforms.base import BASE_CONFIG

DOMAINS = ['reddit.com', 'redd.it', 'old.reddit.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
    }

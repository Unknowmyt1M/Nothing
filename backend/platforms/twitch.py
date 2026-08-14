from backend.platforms.base import BASE_CONFIG

DOMAINS = ['twitch.tv', 'clips.twitch.tv', 'm.twitch.tv']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        'cookiefile': 'cookies/twitch.txt',
    }

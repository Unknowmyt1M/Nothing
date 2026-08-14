import re
from backend.platforms.base import BASE_CONFIG

DOMAINS = ['facebook.com', 'fb.com', 'm.facebook.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        'cookiefile': 'cookies/facebook.txt',
    }

def post_process_metadata(info, metadata):
    desc = metadata.get('description', '')
    title = metadata.get('title', '')
    hashtags = re.findall(r'#(\w+)', str(desc) + ' ' + str(title))
    metadata['tags'] = hashtags[:8]
    return metadata

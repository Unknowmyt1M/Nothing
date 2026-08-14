import re
from backend.platforms.base import BASE_CONFIG

DOMAINS = ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        'cookiefile': 'cookies/insta.txt',  # uses instagram cookies as fallback
    }

def post_process_metadata(info, metadata):
    desc = metadata.get('description', '')
    hashtags = re.findall(r'#(\w+)', str(desc))
    metadata['tags'] = hashtags[:10]
    return metadata

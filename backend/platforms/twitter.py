import re
from backend.platforms.base import BASE_CONFIG

DOMAINS = ['twitter.com', 'x.com', 't.co']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
    }

def post_process_metadata(info, metadata):
    desc = metadata.get('description', '')
    title = metadata.get('title', '')
    hashtags = re.findall(r'#(\w+)', str(desc) + ' ' + str(title))
    metadata['tags'] = hashtags[:10]
    return metadata

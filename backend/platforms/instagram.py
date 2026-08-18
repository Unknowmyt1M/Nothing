import re
from backend.platforms.base import BASE_CONFIG

DOMAINS = ['instagram.com', 'instagr.am']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
    }

def post_process_metadata(info, metadata):
    # Extract hashtags from description
    desc = metadata.get('description', '')
    hashtags = re.findall(r'#(\w+)', str(desc))
    metadata['tags'] = hashtags[:10]
    return metadata

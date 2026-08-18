from backend.platforms.base import BASE_CONFIG, extract_tags_from_text

DOMAINS = ['vimeo.com']

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
    }

def post_process_metadata(info, metadata):
    # Vimeo tags sometimes come from info, fallback to text parsing
    tags = info.get('tags', [])
    if not tags:
        text = metadata.get('title', '') + ' ' + metadata.get('description', '')
        tags = extract_tags_from_text(text)
    metadata['tags'] = tags
    return metadata

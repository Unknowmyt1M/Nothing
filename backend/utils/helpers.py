import os
import re
import tempfile

# In serverless (Vercel, AWS Lambda, etc.) only /tmp is writable.
_IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
_TEMP_DIR = tempfile.gettempdir()


def get_temp_dir(subdir: str = "downloads") -> str:
    """Return a writable directory for temporary files.

    On serverless platforms ``/tmp/<subdir>`` is returned (and created if
    missing).  On a traditional server the project-local ``downloads/``
    directory is used instead.
    """
    if _IS_SERVERLESS:
        path = os.path.join(_TEMP_DIR, subdir)
    else:
        path = os.path.join(os.getcwd(), subdir)
    os.makedirs(path, exist_ok=True)
    return path

def format_bytes(bytes_value):
    """Format bytes to human readable string"""
    if not bytes_value:
        return "0 B"
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PiB"

def format_time(seconds):
    """Format seconds to human readable time string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_duration(duration):
    """Format duration from seconds to HH:MM:SS"""
    if not duration:
        return "0:00"
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def format_number(number):
    """Format large numbers with K, M, B suffixes"""
    if not number:
        return "0"
    try:
        num = float(number)
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            if num.is_integer():
                return str(int(num))
            else:
                return f"{num:.1f}"
    except (ValueError, TypeError):
        return "0"

def clean_string_for_json(text):
    """Clean string for safe JSON serialization"""
    if not text:
        return ''
    try:
        if not isinstance(text, str):
            text = str(text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = text.replace('\\', '').replace('\r', '').replace('\n', ' ')
        if len(text) > 5000:
            text = text[:5000] + '...'
        return text.strip()
    except Exception:
        return 'Content unavailable'

def clean_description_from_technical_details(raw_description):
    """Clean description by removing technical details"""
    if not raw_description:
        return "No description available"
    technical_patterns = [
        r'--- \*\*Technical Details\*\* ---.*?(?=\n\n|\Z)',
        r'\*\*Technical Details\*\*.*?(?=\n\n|\Z)',
        r'\*\*Resolution:\*\*.*?(?=\n|\Z)',
        r'\*\*Format:\*\*.*?(?=\n|\Z)',
        r'\*\*Video Codec:\*\*.*?(?=\n|\Z)',
        r'\*\*Audio Codec:\*\*.*?(?=\n|\Z)',
        r'\*\*Bitrate:\*\*.*?(?=\n|\Z)',
        r'\*\*FPS:\*\*.*?(?=\n|\Z)',
        r'\*\*File Size:\*\*.*?(?=\n|\Z)',
    ]
    clean_desc = raw_description
    for pattern in technical_patterns:
        clean_desc = re.sub(pattern, '', clean_desc, flags=re.IGNORECASE | re.DOTALL)
    return clean_desc.strip()

def extract_tags_from_text(text):
    """Extract potential tags from title and description"""
    if not text:
        return []
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
    
    common_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'so', 'than'
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [word for word in words if word not in common_words]
    
    all_tags = list(set(hashtags + keywords[:10]))
    return all_tags[:15]

import os
import re
import json
import logging
import subprocess

BASE_CONFIG = {
    'format': 'best[height>=1440][ext=mp4]/best[height>=1080][ext=mp4]/best[height>=720][ext=mp4]/best[ext=mp4]/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'writeinfojson': True,
    'writedescription': True,
    'writesubtitles': False,
    'writeautomaticsub': False,
    'ignoreerrors': False,
    'no_warnings': False,
    'extractaudio': False,
    'audioformat': 'mp3',
    'embed_subs': False,
    'embed_thumbnail': False,
    'retries': 5,
    'file_access_retries': 5,
    'fragment_retries': 5,
    'http_chunk_size': 10485760,  # 10MB chunks for stability
    'merge_output_format': 'mp4',
    'noplaylist': True,
}

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
    """Extract potential tags from text"""
    if not text:
        return []
    common_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'so', 'than'
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    tags = []
    for word in words:
        if word not in common_words and len(tags) < 10:
            if word not in tags:
                tags.append(word)
    return tags

def get_advanced_video_metadata(file_path_or_url):
    """Extract detailed video metadata using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path_or_url
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"FFprobe failed: {result.stderr}")
            
        probe_data = json.loads(result.stdout)
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        video_stream = None
        audio_stream = None
        for stream in streams:
            if stream.get('codec_type') == 'video' and not video_stream:
                video_stream = stream
            elif stream.get('codec_type') == 'audio' and not audio_stream:
                audio_stream = stream
                
        metadata = {}
        metadata['file_size'] = int(format_info.get('size', 0))
        metadata['file_size_mb'] = round(metadata['file_size'] / (1024 * 1024), 2) if metadata['file_size'] > 0 else 0
        metadata['duration'] = float(format_info.get('duration', 0))
        metadata['bitrate'] = int(format_info.get('bit_rate', 0))
        metadata['format_name'] = format_info.get('format_name', 'Unknown')
        
        if video_stream:
            metadata['width'] = int(video_stream.get('width', 0))
            metadata['height'] = int(video_stream.get('height', 0))
            metadata['video_codec'] = video_stream.get('codec_name', 'Unknown')
            metadata['video_bitrate'] = int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0
            metadata['fps'] = video_stream.get('r_frame_rate', '0/1')
            if '/' in str(metadata['fps']):
                try:
                    num, den = map(int, str(metadata['fps']).split('/'))
                    metadata['fps'] = round(num / den, 2) if den > 0 else 0
                except:
                    metadata['fps'] = 0
                    
        if audio_stream:
            metadata['audio_codec'] = audio_stream.get('codec_name', 'Unknown')
            metadata['audio_bitrate'] = int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0
            metadata['sample_rate'] = int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else 0
            metadata['channels'] = int(audio_stream.get('channels', 0)) if audio_stream.get('channels') else 0
            
        return metadata
    except subprocess.TimeoutExpired:
        raise Exception("Video analysis timed out")
    except Exception as e:
        raise Exception(f"Advanced metadata extraction failed: {str(e)}")

def is_direct_download_url(url):
    """
    Check if a URL is a direct download link (e.g. points to an mp4 file).
    First checks by URL path extension, then does a quick HEAD request to verify.
    """
    if not url:
        return False
    
    # 1. Quick extension check to avoid making network requests for common social media URLs
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Exclude social media domains early to save network calls
    domain = parsed.netloc.lower()
    social_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'twitter.com', 'x.com', 'tiktok.com', 'vimeo.com', 'twitch.tv', 'rumble.com']
    if any(sd in domain for sd in social_domains):
        return False
        
    direct_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mp3', '.wav', '.mov', '.flv', '.ogg', '.m4a']
    if any(path.endswith(ext) for ext in direct_extensions):
        return True
        
    # 2. Network HEAD request to check content-type
    try:
        import requests
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '').lower()
        if content_type.startswith('video/') or content_type.startswith('audio/') or 'mpegurl' in content_type:
            return True
    except Exception:
        # If head request fails, check GET with stream=True and close immediately
        try:
            import requests
            response = requests.get(url, stream=True, timeout=5, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            response.close()
            if content_type.startswith('video/') or content_type.startswith('audio/') or 'mpegurl' in content_type:
                return True
        except:
            pass
            
    return False


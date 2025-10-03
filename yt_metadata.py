import yt_dlp
import logging
import re
import os

def extract_metadata(url, cookies_file=None):
    """Extract metadata from YouTube video URL"""
    # Use fallback cookies if no specific cookies provided
    if not cookies_file and os.path.exists("cookies/fallback_cookies.txt"):
        cookies_file = "cookies/fallback_cookies.txt"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'cookiefile': cookies_file,
        'extractor_retries': 3,
        'format': 'best[ext=mp4]/best[ext=webm]/best',  # Check highest quality for metadata
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Failed to extract video information")
            
            # Clean and format data
            title = info.get('title', 'No title')
            description = info.get('description', 'No description')
            uploader = info.get('uploader', 'Unknown')
            duration = info.get('duration', 0)
            view_count = info.get('view_count', 0)
            thumbnail = info.get('thumbnail', '')
            
            # Extract tags from description and title
            tags = extract_tags_from_text(title + ' ' + description)
            
            # Format duration
            duration_str = format_duration(duration)
            
            # Format view count
            view_count_str = format_number(view_count)
            
            return {
                'title': title,
                'description': description,
                'uploader': uploader,
                'duration': duration_str,
                'view_count': view_count_str,
                'thumbnail': thumbnail,
                'tags': tags,
                'url': url
            }
            
    except Exception as e:
        logging.error(f"Error extracting metadata: {e}")
        raise Exception(f"Failed to extract metadata: {str(e)}")

def extract_tags_from_text(text):
    """Extract potential tags from title and description"""
    # Common tag patterns
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
    
    # Common keywords that might be tags
    keywords = []
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an'}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [word for word in words if word not in common_words]
    
    # Combine hashtags and important keywords (limit to top 10)
    all_tags = list(set(hashtags + keywords[:10]))
    return all_tags[:15]  # Limit to 15 tags

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_number(number):
    """Format large numbers with suffixes"""
    if not number:
        return "0"
    
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)

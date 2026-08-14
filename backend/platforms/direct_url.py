import urllib.parse
from urllib.parse import urlparse
import requests
import yt_dlp
import logging
from backend.platforms.base import (
    BASE_CONFIG,
    clean_string_for_json,
    format_duration,
    get_advanced_video_metadata
)

DOMAINS = [] # Handled dynamically by is_direct_download_url

def get_config():
    return {
        **BASE_CONFIG,
        'format': 'best', # Download as-is
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writeinfojson': False,
        'writedescription': False,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'http_chunk_size': 10485760,
        'retries': 10,
        'file_access_retries': 10,
        'fragment_retries': 10,
    }

def extract_direct_url_metadata(url):
    """Extract metadata from direct video links"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        content_type = response.headers.get('content-type', '').lower()
        if not (content_type.startswith('video') or 'mpegurl' in content_type):
            raise Exception("URL does not point to a direct video file")
            
        file_size = response.headers.get('content-length')
        content_disposition = response.headers.get('content-disposition', '')
        
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1] if parsed_url.path else 'direct_video'
        
        if content_disposition and 'filename=' in content_disposition:
            try:
                filename = content_disposition.split('filename=')[1].strip('"').strip("'")
            except:
                pass
                
        if '.' in filename:
            title = filename.rsplit('.', 1)[0]
            file_ext = filename.rsplit('.', 1)[1].upper()
        else:
            title = filename
            if 'mp4' in content_type:
                file_ext = 'MP4'
            elif 'webm' in content_type:
                file_ext = 'WEBM'
            else:
                file_ext = 'VIDEO'
                
        title = title.replace('_', ' ').replace('-', ' ').replace('%20', ' ')
        
        # Call ffprobe
        advanced_metadata = {}
        try:
            advanced_metadata = get_advanced_video_metadata(url)
        except Exception as probe_error:
            logging.warning(f"FFprobe analysis failed: {probe_error}")
            
        # Call yt-dlp metadata
        ydl_metadata = {}
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    ydl_metadata = {
                        'duration': info.get('duration', 0),
                        'width': info.get('width', 0),
                        'height': info.get('height', 0),
                        'filesize': info.get('filesize', 0) or info.get('filesize_approx', 0),
                        'thumbnails': info.get('thumbnails', [])[:10]
                    }
        except Exception as ydl_error:
            logging.warning(f"yt-dlp metadata extraction failed: {ydl_error}")
            
        duration = advanced_metadata.get('duration', 0) or ydl_metadata.get('duration', 0)
        duration_str = format_duration(int(duration)) if duration else 'Unknown'
        
        filesize = advanced_metadata.get('file_size', 0) or ydl_metadata.get('filesize', 0)
        if not filesize and file_size:
            try:
                filesize = int(file_size)
            except:
                filesize = 0
                
        file_size_mb = round(filesize / (1024 * 1024), 2) if filesize > 0 else 0
        width = advanced_metadata.get('width', 0) or ydl_metadata.get('width', 0)
        height = advanced_metadata.get('height', 0) or ydl_metadata.get('height', 0)
        quality = f"{width}x{height}" if width and height else 'Unknown'
        
        desc_parts = [
            f"**Filename:** {filename}",
            f"**File Size:** {file_size_mb} MB" if file_size_mb > 0 else "**File Size:** Unknown",
            f"**Format:** {file_ext}",
            f"**Resolution:** {quality}" if quality != 'Unknown' else ""
        ]
        if advanced_metadata.get('video_codec'):
            desc_parts.append(f"**Video Codec:** {advanced_metadata['video_codec'].upper()}")
        if advanced_metadata.get('audio_codec'):
            desc_parts.append(f"**Audio Codec:** {advanced_metadata['audio_codec'].upper()}")
            
        description = "\n".join([p for p in desc_parts if p])
        thumbnails = ydl_metadata.get('thumbnails', [])
        thumb_url = thumbnails[0].get('url', '') if thumbnails else ''
        
        return {
            'title': clean_string_for_json(title) if title else filename,
            'description': clean_string_for_json(description),
            'duration': duration_str,
            'thumbnail': thumb_url,
            'file_size': f"{file_size_mb} MB" if file_size_mb > 0 else 'Unknown',
            'quality': quality,
            'format': file_ext,
            'url': url,
            'platform': 'direct_url',
            'upload_date': '',
            'video_codec': advanced_metadata.get('video_codec', 'Unknown'),
            'audio_codec': advanced_metadata.get('audio_codec', 'Unknown'),
            'fps': f"{advanced_metadata.get('fps') or 0} FPS" if (advanced_metadata.get('fps') or 0) > 0 else 'Unknown',
            'uploader': None,
            'view_count': None,
            'tags': []
        }
    except Exception as e:
        # fallback
        return {
            'title': 'Direct Video Link',
            'description': f"Direct video streaming file from:\n{url}\n\nAnalysis error: {str(e)}",
            'duration': 'Unknown',
            'thumbnail': '',
            'file_size': 'Unknown',
            'quality': 'Unknown',
            'format': 'Unknown',
            'url': url,
            'platform': 'direct_url',
            'upload_date': '',
            'video_codec': 'Unknown',
            'audio_codec': 'Unknown',
            'fps': 'Unknown',
            'uploader': None,
            'view_count': None,
            'tags': []
        }

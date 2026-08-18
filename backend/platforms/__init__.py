import os
import importlib
import logging
import yt_dlp
import time
from backend.errors import (
    AppError,
    extraction_error,
    content_unavailable,
    parse_ytdl_error,
)
from backend.platforms.base import (
    BASE_CONFIG,
    _is_safe_url,
    is_direct_download_url,
    format_bytes,
    format_time,
    format_duration,
    format_number,
    clean_string_for_json,
    clean_description_from_technical_details,
    extract_tags_from_text
)

logger = logging.getLogger(__name__)

# Registry mapping platform identifiers to their modules
PLATFORM_MODULES = {
    'youtube': 'backend.platforms.youtube',
    'instagram': 'backend.platforms.instagram',
    'facebook': 'backend.platforms.facebook',
    'twitter': 'backend.platforms.twitter',
    'tiktok': 'backend.platforms.tiktok',
    'vimeo': 'backend.platforms.vimeo',
    'reddit': 'backend.platforms.reddit',
    'twitch': 'backend.platforms.twitch',
    'rumble': 'backend.platforms.rumble',
    'direct_url': 'backend.platforms.direct_url',
    'deadtoons': 'backend.platforms.others',
    'cybervynx': 'backend.platforms.others',
    'voe': 'backend.platforms.others',
    'filemoon': 'backend.platforms.others',
    'newerstream': 'backend.platforms.others',
    'shortic': 'backend.platforms.others',
    'smoothpre': 'backend.platforms.others',
}

def get_platform_module(platform):
    """Dynamically import and return the platform module"""
    module_path = PLATFORM_MODULES.get(platform)
    if module_path:
        try:
            return importlib.import_module(module_path)
        except Exception as e:
            logging.error(f"Error importing platform module {module_path}: {e}")
    return None

def get_platform_from_url(url):
    """Detect platform from URL"""
    from urllib.parse import urlparse
    hostname = (urlparse(url if '://' in url else 'http://' + url).hostname or '').lower()
    
    exact_domains = {
        'youtube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
        'instagram': ['instagram.com', 'instagr.am'],
        'facebook': ['facebook.com', 'fb.com', 'm.facebook.com'],
        'twitter': ['twitter.com', 'x.com', 't.co'],
        'dailymotion': ['dailymotion.com', 'dai.ly'],
        'vimeo': ['vimeo.com'],
        'pinterest': ['pinterest.com', 'pin.it'],
        'reddit': ['reddit.com', 'redd.it', 'old.reddit.com'],
        'tiktok': ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'],
        'snapchat': ['snapchat.com', 'snap.com'],
        'twitch': ['twitch.tv', 'clips.twitch.tv', 'm.twitch.tv'],
        'rumble': ['rumble.com'],
        'deadtoons': ['deadtoons.upns.ink'],
        'cybervynx': ['cybervynx.com'],
        'voe': ['voe.sx'],
        'filemoon': ['filemoon.nl'],
        'newerstream': ['newer.stream'],
        'shortic': ['short.icu'],
        'smoothpre': ['smoothpre.com']
    }
    
    # First check exact domain matches (proper hostname boundary, not substring)
    for platform, domains in exact_domains.items():
        for domain in domains:
            if hostname == domain or hostname.endswith('.' + domain):
                return platform
            
    # Then check for direct download URLs using HTTP headers
    if is_direct_download_url(url):
        return 'direct_url'
        
    return 'unknown'

def get_platform_config(platform):
    """Retrieve custom yt-dlp config for the given platform.

    Automatically resolves cookie files from Supabase Storage when available,
    placing them in /tmp for the duration of the request.
    """
    module = get_platform_module(platform)
    if module and hasattr(module, 'get_config'):
        config = dict(module.get_config())
    else:
        config = dict(BASE_CONFIG)
    # Ensure runtime tooling (ffmpeg, JS runtime) applies to every platform
    if BASE_CONFIG.get('ffmpeg_location'):
        config.setdefault('ffmpeg_location', BASE_CONFIG['ffmpeg_location'])
    if BASE_CONFIG.get('js_runtimes'):
        config.setdefault('js_runtimes', BASE_CONFIG['js_runtimes'])

    # Resolve cookie file from Supabase Storage if not already set
    if 'cookiefile' not in config:
        try:
            from backend.services.cookie_manager import get_cookie_path
            cookie_path = get_cookie_path(platform)
            if cookie_path:
                config['cookiefile'] = cookie_path
        except Exception:
            pass  # cookie manager unavailable — proceed without cookies

    return config

def get_supported_platforms():
    """Return a list of all supported platforms"""
    return list(PLATFORM_MODULES.keys())

def is_platform_supported(url):
    """Check if URL platform is supported"""
    platform = get_platform_from_url(url)
    return platform in get_supported_platforms()

def get_platform_display_name(platform):
    """Get display name for a platform"""
    display_names = {
        'youtube': 'YouTube',
        'instagram': 'Instagram', 
        'facebook': 'Facebook',
        'twitter': 'Twitter/X',
        'dailymotion': 'Dailymotion',
        'vimeo': 'Vimeo',
        'pinterest': 'Pinterest',
        'reddit': 'Reddit',
        'tiktok': 'TikTok',
        'snapchat': 'Snapchat',
        'twitch': 'Twitch',
        'rumble': 'Rumble',
        'deadtoons': 'DeadToons',
        'cybervynx': 'CyberVynx',
        'voe': 'VOE',
        'filemoon': 'FileMoon',
        'newerstream': 'NewerStream',
        'shortic': 'Short.icu',
        'smoothpre': 'SmoothPre',
        'direct_url': 'Direct URL'
    }
    return display_names.get(platform, platform.title())

def get_available_formats_list(url):
    """Retrieve list of available video formats for a URL"""
    try:
        platform = get_platform_from_url(url)
        
        # Validate YouTube URLs before listing formats
        if platform == 'youtube':
            from backend.platforms.youtube import validate_youtube_url
            validate_youtube_url(url)
        
        config = get_platform_config(platform)
        
        list_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'no_check_certificate': True,
            'noplaylist': True,
            'retries': 3,
            'socket_timeout': 15,
        }
        
        # Merge runtime tooling (ffmpeg, JS runtime) so format extraction is complete
        if BASE_CONFIG.get('ffmpeg_location'):
            list_opts['ffmpeg_location'] = BASE_CONFIG['ffmpeg_location']
        if BASE_CONFIG.get('js_runtimes'):
            list_opts['js_runtimes'] = BASE_CONFIG['js_runtimes']
        
        # Merge cookies config if present
        if 'cookiefile' in config:
            list_opts['cookiefile'] = config['cookiefile']
            
        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'formats' in info:
                formats = info['formats']
                for fmt in formats:
                    if not fmt.get('duration') and info.get('duration'):
                        fmt['duration'] = info['duration']
                    if not fmt.get('format_id'):
                        fmt['format_id'] = f"{fmt.get('height', 'unknown')}p_{fmt.get('ext', 'mp4')}"
                return formats
        return []
    except Exception as e:
        logger.error("Error fetching formats list: %s", e)
        return []

def get_best_available_format(url):
    """Resolve the highest quality format ID that exists"""
    try:
        formats = get_available_formats_list(url)
        if not formats:
            return 'best'
            
        video_formats = [f for f in formats if f.get('height') and f.get('vcodec') != 'none']
        if video_formats:
            video_formats.sort(key=lambda x: (x.get('height') or 0, x.get('filesize') or x.get('filesize_approx') or 0), reverse=True)
            return video_formats[0]['format_id']
        return 'best'
    except Exception as e:
        logging.error(f"Error finding best format: {e}")
        return 'best'

def extract_platform_metadata(url, platform=None):
    """Extract and post-process metadata from URL"""
    # SSRF protection: refuse to fetch metadata from private/internal IPs
    if not _is_safe_url(url):
        raise extraction_error("URL resolves to a private or internal address — SSRF blocked")

    if not platform:
        platform = get_platform_from_url(url)
        
    # Pre-extraction URL validation for YouTube
    if platform == 'youtube':
        from backend.platforms.youtube import validate_youtube_url
        validate_youtube_url(url)
        
    # Delegate direct URLs to direct_url module
    if platform == 'direct_url':
        module = get_platform_module(platform)
        if module and hasattr(module, 'extract_direct_url_metadata'):
            return module.extract_direct_url_metadata(url)
            
    config = get_platform_config(platform)
    
    js_runtimes = BASE_CONFIG.get('js_runtimes', {})
    ffmpeg_loc = BASE_CONFIG.get('ffmpeg_location')
    logger.info("yt-dlp extraction for %s | js_runtimes=%s ffmpeg=%s", platform, bool(js_runtimes), ffmpeg_loc)

    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'retries': 2,
        'socket_timeout': 10,
        'ignoreerrors': True,
        'noplaylist': True,
    }
    
    if ffmpeg_loc:
        opts['ffmpeg_location'] = ffmpeg_loc
    if js_runtimes:
        opts['js_runtimes'] = js_runtimes
    
    if 'cookiefile' in config:
        opts['cookiefile'] = config['cookiefile']
        
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            if platform in ['instagram', 'facebook', 'tiktok', 'twitter']:
                time.sleep(0.5)  # brief delay to prevent bot blocking
                
            info = ydl.extract_info(url, download=False)
            if not info:
                logger.error("yt-dlp returned None for %s (js_runtimes=%s)", url, bool(js_runtimes))
                raise extraction_error(
                    "yt-dlp returned no video information. "
                    + ("No JS runtime available — YouTube extraction may require Node.js or Deno."
                       if not js_runtimes else
                       "The video may be private, age-restricted, or temporarily unavailable.")
                )
                
            # Populate standard values
            title = clean_string_for_json(info.get('title', 'No title'))
            description = clean_string_for_json(clean_description_from_technical_details(info.get('description', '')))
            uploader = clean_string_for_json(info.get('uploader', 'Unknown'))
            
            duration_val = info.get('duration', 0)
            duration_str = format_duration(int(duration_val) if duration_val else 0)
            
            view_count_val = info.get('view_count', 0)
            view_count_str = format_number(int(view_count_val) if view_count_val else 0)
            
            thumbnail = info.get('thumbnail', '')
            upload_date = info.get('upload_date', '')
            
            # Technical details
            advanced_info = {}
            formats = info.get('formats', [])
            if formats:
                # Find the best format
                video_formats = [f for f in formats if f.get('height') and f.get('vcodec') != 'none']
                if video_formats:
                    # Sort by height descending, then size descending
                    video_formats.sort(key=lambda x: (x.get('height') or 0, x.get('filesize') or x.get('filesize_approx') or 0), reverse=True)
                    best_fmt = video_formats[0]
                else:
                    best_fmt = max(formats, key=lambda x: (x.get('height') or 0, x.get('width') or 0))
                
                advanced_info.update({
                    'quality': f"{best_fmt.get('width', 0)}x{best_fmt.get('height', 0)}" if best_fmt.get('width') and best_fmt.get('height') else None,
                    'video_codec': best_fmt.get('vcodec', 'Unknown') if best_fmt.get('vcodec') != 'none' else None,
                    'audio_codec': best_fmt.get('acodec', 'Unknown') if best_fmt.get('acodec') != 'none' else None,
                    'fps': best_fmt.get('fps') or 'Unknown',
                    'file_size': f"{round((best_fmt.get('filesize') or best_fmt.get('filesize_approx') or 0) / (1024 * 1024), 2)} MB" if (best_fmt.get('filesize') or best_fmt.get('filesize_approx')) else None,
                    'format': best_fmt.get('ext', 'Unknown').upper() if best_fmt.get('ext') else None
                })
                
            metadata = {
                'title': title,
                'description': description,
                'uploader': uploader,
                'duration': duration_str,
                'view_count': view_count_str,
                'thumbnail': thumbnail,
                'url': url,
                'platform': platform,
                'upload_date': upload_date,
                'tags': []
            }
            
            metadata.update(advanced_info)
            
            # Run custom platform post-processor if available
            module = get_platform_module(platform)
            if module and hasattr(module, 'post_process_metadata'):
                metadata = module.post_process_metadata(info, metadata)
            else:
                # Default tag extraction fallback
                metadata['tags'] = extract_tags_from_text(title + ' ' + description)
            
            # Post-extraction metadata validation for YouTube
            if platform == 'youtube':
                from backend.platforms.youtube import validate_extracted_metadata
                validate_extracted_metadata(info, url)
                
            return metadata
            
    except AppError:
        raise
    except Exception as e:
        logger.error("Metadata extraction error for %s: %s", platform, e)
        raise parse_ytdl_error(str(e))


def download_from_platform(url, output_path='downloads', platform=None, progress_callback=None, quality=None, cancel_event=None):
    """Download video from platform using custom settings and progress hooks.
    
    Args:
        cancel_event: threading.Event – if set, download is cancelled.
    """
    if not platform:
        platform = get_platform_from_url(url)
    
    # Pre-download URL validation for YouTube
    if platform == 'youtube':
        from backend.platforms.youtube import validate_youtube_url
        validate_youtube_url(url)
        
    os.makedirs(output_path, exist_ok=True)
    
    # Custom downloader for direct url to avoid yt-dlp page download issues (e.g. 403 Forbidden)
    if platform == 'direct_url':
        try:
            import requests as _requests
            from backend.platforms.direct_url import extract_direct_url_metadata
            
            metadata = extract_direct_url_metadata(url)
            title = metadata.get('title', 'Direct_Video')
            ext = metadata.get('format', 'mp4').lower()
            
            # Sanitize filename
            filename = "".join([c for c in title if c.isalnum() or c in ' ._-']).strip()
            if not filename.endswith(f".{ext}"):
                filename = f"{filename}.{ext}"
                
            dest_file = os.path.join(output_path, filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = _requests.get(url, stream=True, headers=headers, timeout=60)
            response.raise_for_status()
            
            total_bytes = int(response.headers.get('content-length') or 0)
            downloaded_bytes = 0
            
            start_time = time.time()
            with open(dest_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if cancel_event and cancel_event.is_set():
                        # Cleanup partial file
                        f.close()
                        try:
                            os.remove(dest_file)
                        except OSError:
                            pass
                        from backend.errors import download_cancelled
                        raise download_cancelled()
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        if progress_callback:
                            elapsed = time.time() - start_time
                            speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                            eta = (total_bytes - downloaded_bytes) / speed if speed > 0 and total_bytes > downloaded_bytes else 0
                            
                            progress_callback({
                                'status': 'downloading',
                                'downloaded_bytes': downloaded_bytes,
                                'total_bytes': total_bytes,
                                'speed': speed,
                                'eta': int(eta)
                            })
            return dest_file
        except AppError:
            raise
        except Exception as e:
            logger.error("Error downloading direct URL: %s", e)
            raise parse_ytdl_error(str(e))

    config = get_platform_config(platform)
    
    # Use the requested quality when provided. Video-only formats (e.g. 137, 134)
    # get merged with the best audio so the file is not silent.
    if quality:
        config['format'] = f"{quality}+bestaudio/best"
    else:
        config['format'] = BASE_CONFIG['format']
    
    # Configure output template
    config['outtmpl'] = os.path.join(output_path, '%(title).200s.%(ext)s')
    config['restrictfilenames'] = True
    
    def progress_hook(d):
        if cancel_event and cancel_event.is_set():
            raise _CancelException()
        if progress_callback and d['status'] == 'downloading':
            progress_callback(d)
            
    config['progress_hooks'] = [progress_hook]
    
    try:
        with yt_dlp.YoutubeDL(config) as ydl:
            ydl.download([url])
            # Get the filename from the last hook call or prepare_filename
            # No need for a second extract_info call — use the info from the download
            info = ydl.extract_info(url, download=False)
            return ydl.prepare_filename(info)
    except _CancelException:
        # Cleanup temp files created by yt-dlp
        _cleanup_partial_files(output_path)
        _cleanup_cookies()
        from backend.errors import download_cancelled
        raise download_cancelled()
    except AppError:
        _cleanup_cookies()
        raise
    except Exception as e:
        logger.error("Error downloading video: %s", e)
        _cleanup_cookies()
        raise parse_ytdl_error(str(e))
    finally:
        # Always attempt cookie cleanup after download completes or fails
        _cleanup_cookies()


class _CancelException(Exception):
    """Raised inside yt-dlp progress hooks to abort download."""
    pass


def _cleanup_partial_files(directory: str) -> None:
    """Remove .part and .ytdl temp files left behind by yt-dlp."""
    import glob as _glob
    for pattern in ['*.part', '*.ytdl', '*.temp']:
        for f in _glob.glob(os.path.join(directory, pattern)):
            try:
                os.remove(f)
                logger.info("Cleaned up partial file: %s", f)
            except OSError:
                pass


def _cleanup_cookies() -> None:
    """Remove temporary cookie files downloaded from Supabase Storage."""
    try:
        from backend.services.cookie_manager import cleanup_tmp_cookies
        cleanup_tmp_cookies()
    except Exception:
        pass


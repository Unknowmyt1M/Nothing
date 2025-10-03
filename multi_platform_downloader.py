import os
import json
import yt_dlp
import logging
import requests
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import threading
from urllib.parse import urlparse, parse_qs
import re
import subprocess

def is_direct_download_url(url):
    """Check if URL is a direct video download using HTTP headers"""
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        content_type = r.headers.get("Content-Type", "")
        if content_type.startswith("video") or "mpegurl" in content_type.lower():
            return True
    except Exception:
        pass
    return False

def get_platform_from_url(url):
    """Detect platform from URL"""
    url_lower = url.lower()
    
    # Check for exact domain matches first (more specific)
    exact_domains = {
        'youtube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
        'instagram': ['instagram.com', 'instagr.am'],
        'facebook': ['facebook.com', 'fb.com', 'm.facebook.com'],
        'twitter': ['twitter.com', 'x.com'],
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
    
    # Check for direct video URLs using HTTP headers - after platform check
    if is_direct_download_url(url):
        return 'direct_url'
    
    # First check exact domain matches
    for platform, domains in exact_domains.items():
        if any(domain in url_lower for domain in domains):
            return platform
    
    # Then check for specific URL patterns (less specific)
    pattern_matches = {
        'twitter': ['t.co'],  # Twitter shortlinks only
        'pinterest': ['pinterest.'],  # Pinterest subdomains
    }
    
    for platform, patterns in pattern_matches.items():
        if any(pattern in url_lower for pattern in patterns):
            return platform
    
    return 'unknown'

def get_platform_config(platform):
    """Get yt-dlp configuration for specific platform"""
    # Ultra high quality base config - prefer highest available quality
    base_config = {
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
    }
    
    platform_configs = {
        'youtube': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
            'writesubtitles': True,
            'writeautomaticsub': True,
            'cookiefile': 'cookies/cookies.txt',  # YouTube authentication cookies - tested working
        },
        'instagram': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
            'cookiefile': 'cookies/instagram_cookies.txt',  # Instagram authentication cookies
        },
        'facebook': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
            'cookiefile': 'cookies/instagram_cookies.txt',  # Use Instagram cookies for Facebook as fallback
        },
        'twitter': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'dailymotion': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'vimeo': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
            'cookiefile': 'cookies/vimeo_cookies.txt',
        },
        'pinterest': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'reddit': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'tiktok': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
            'cookiefile': 'cookies/instagram_cookies.txt',  # Use Instagram cookies for TikTok as fallback
        },
        'snapchat': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'twitch': {
            **base_config,
            'format': 'best[height>=720][height<=1080][ext=mp4]/best[height>=720][ext=mp4]/best[height>=720]/best[ext=mp4]/best',
        },
        'rumble': {
            **base_config,
            'format': 'best[height>=1440][ext=mp4]/best[height>=1080][ext=mp4]/best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'writesubtitles': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'extractor_retries': 5,
            'http_chunk_size': 10485760,  # 10MB chunks for better stability
            'hls_use_mpegts': False,
            'extract_flat': False,
        },
        'direct_url': {
            **base_config,
            'format': 'best',  # Download the file as-is for direct URLs
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
            'http_chunk_size': 10485760,  # 10MB chunks for stability
            'retries': 10,  # More retries for direct downloads
            'file_access_retries': 10,
            'fragment_retries': 10,
        },
        'deadtoons': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'cybervynx': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'voe': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'filemoon': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'newerstream': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'shortic': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        },
        'smoothpre': {
            **base_config,
            'format': 'best[height>=720][ext=mp4]/best[ext=mp4]/best',
            'extractor_retries': 5,
            'http_chunk_size': 10485760,
        }
    }
    
    return platform_configs.get(platform, base_config)

def get_available_formats_list(url):
    """Get list of all available formats for a video with complete information"""
    try:
        platform = get_platform_from_url(url)
        
        # Config to get complete format information (not just list)
        list_config = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'no_check_certificate': True,
        }
        
        # Add cookies for specific platforms
        if platform == 'youtube':
            list_config['cookiefile'] = 'cookies/cookies.txt'
        elif platform == 'instagram':
            list_config['cookiefile'] = 'cookies/instagram_cookies.txt'
        elif platform == 'vimeo':
            list_config['cookiefile'] = 'cookies/vimeo_cookies.txt'
        elif platform == 'facebook':
            list_config['cookiefile'] = 'cookies/instagram_cookies.txt'  # Use Instagram cookies as fallback
        elif platform == 'tiktok':
            list_config['cookiefile'] = 'cookies/instagram_cookies.txt'  # Use Instagram cookies as fallback
        
        with yt_dlp.YoutubeDL(list_config) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'formats' in info:
                # Ensure all formats have complete data
                formats = info['formats']
                for fmt in formats:
                    # Add missing information if available from main info
                    if not fmt.get('duration') and info.get('duration'):
                        fmt['duration'] = info['duration']
                    
                    # Ensure format_id exists
                    if not fmt.get('format_id'):
                        fmt['format_id'] = f"{fmt.get('height', 'unknown')}p_{fmt.get('ext', 'mp4')}"
                
                return formats
        return []
    except Exception as e:
        logging.error(f"Error listing formats: {e}")
        return []

def get_best_available_format(url):
    """Get the best available format ID that actually exists"""
    try:
        formats = get_available_formats_list(url)
        if not formats:
            return 'best'  # Fallback to generic best
        
        # Filter video formats and sort by quality
        video_formats = [f for f in formats if f.get('height') and f.get('vcodec') != 'none']
        if video_formats:
            # Sort by height (quality) descending, then by filesize descending
            video_formats.sort(key=lambda x: (x.get('height', 0), x.get('filesize', 0)), reverse=True)
            return video_formats[0]['format_id']
        
        return 'best'
    except Exception as e:
        logging.error(f"Error getting best format: {e}")
        return 'best'

def extract_platform_metadata(url, platform=None):
    """Extract metadata from any supported platform URL"""
    if not platform:
        platform = get_platform_from_url(url)
    
    # Handle direct URLs differently
    if platform == 'direct_url':
        return extract_direct_url_metadata(url)
    
    # Get safe format that actually exists
    safe_format = get_best_available_format(url)
    
    # Create safe config for metadata extraction
    config = {
        'format': safe_format,  # Use available format instead of specific requirements
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'writeinfojson': False,
        'writedescription': False,
        'retries': 2,
        'socket_timeout': 10,
        'ignoreerrors': True,
    }
    
    # Add cookies for authentication
    if platform == 'youtube':
        config['cookiefile'] = 'cookies/cookies.txt'
    elif platform == 'instagram':
        config['cookiefile'] = 'cookies/instagram_cookies.txt'
    elif platform == 'vimeo':
        config['cookiefile'] = 'cookies/vimeo_cookies.txt'
    
    try:
        with yt_dlp.YoutubeDL(config) as ydl:
            # Add minimal delay for social media platforms to avoid overwhelming servers
            if platform in ['instagram', 'facebook', 'tiktok', 'twitter']:
                import time
                time.sleep(0.5)  # Reduced to 0.5 second delay
            
            # Extract info without downloading
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Failed to extract video information")
            
            # Clean and format data with comprehensive error handling
            try:
                title = clean_string_for_json(info.get('title', 'No title'))
            except Exception:
                title = 'No title'
            
            try:
                raw_description = info.get('description', '')
                # Clean description - remove technical details that shouldn't be in user-facing description
                description = clean_description_from_technical_details(raw_description)
                description = clean_string_for_json(description)
            except Exception:
                description = 'No description'
            
            try:
                uploader = clean_string_for_json(info.get('uploader', 'Unknown'))
            except Exception:
                uploader = 'Unknown'
            
            try:
                duration = int(info.get('duration', 0)) if info.get('duration') else 0
            except (ValueError, TypeError):
                duration = 0
            
            try:
                view_count = info.get('view_count', 0)
                if view_count is None:
                    view_count = 0
                # Convert to int if it's a float
                if isinstance(view_count, float):
                    view_count = int(view_count)
            except (ValueError, TypeError):
                view_count = 0
            
            try:
                thumbnail = str(info.get('thumbnail', ''))
            except Exception:
                thumbnail = ''
            
            try:
                upload_date = str(info.get('upload_date', ''))
            except Exception:
                upload_date = ''
            
            # Platform-specific metadata extraction with error handling
            tags = []
            try:
                if platform == 'youtube':
                    tags = info.get('tags', []) or []
                elif platform == 'instagram':
                    # Extract hashtags from description
                    hashtags = re.findall(r'#(\w+)', str(description))
                    tags = hashtags[:10]  # Limit to 10 tags
                elif platform == 'twitter':
                    # Extract hashtags and mentions
                    hashtags = re.findall(r'#(\w+)', str(description) + ' ' + str(title))
                    tags = hashtags[:10]
                elif platform == 'facebook':
                    # Facebook-specific tag extraction
                    hashtags = re.findall(r'#(\w+)', str(description) + ' ' + str(title))
                    tags = hashtags[:8]  # Limit to 8 tags for Facebook
                else:
                    # Extract tags from description and title for other platforms
                    tags = extract_tags_from_text(str(title) + ' ' + str(description))
            except Exception as tag_error:
                logging.warning(f"Tag extraction failed for {platform}: {tag_error}")
                tags = []
            
            # Format duration
            duration_str = format_duration(duration)
            
            # Format view count with error handling
            try:
                view_count_str = format_number(view_count) if view_count is not None else "0"
            except Exception:
                view_count_str = "0"
            
            # Extract advanced technical information if available
            advanced_info = {}
            try:
                # Get video stream information
                formats = info.get('formats', [])
                if formats:
                    # Find best quality format for technical details
                    best_format = max(formats, key=lambda x: (x.get('height', 0), x.get('width', 0)))
                    
                    advanced_info.update({
                        'quality': f"{best_format.get('width', 0)}x{best_format.get('height', 0)}" if best_format.get('width') and best_format.get('height') else None,
                        'video_codec': best_format.get('vcodec', 'Unknown') if best_format.get('vcodec') != 'none' else None,
                        'audio_codec': best_format.get('acodec', 'Unknown') if best_format.get('acodec') != 'none' else None,
                        'fps': f"{best_format.get('fps', 0)} FPS" if best_format.get('fps') else None,
                        'file_size': f"{round(best_format.get('filesize', 0) / (1024 * 1024), 2)} MB" if best_format.get('filesize') and best_format.get('filesize') > 0 else None,
                        'format': best_format.get('ext', 'Unknown').upper() if best_format.get('ext') else None
                    })
                
                # Additional video info from main info object
                if info.get('width') and info.get('height'):
                    advanced_info['quality'] = f"{info.get('width')}x{info.get('height')}"
                if info.get('fps'):
                    advanced_info['fps'] = f"{info.get('fps')} FPS"
                if info.get('filesize') or info.get('filesize_approx'):
                    filesize = info.get('filesize') or info.get('filesize_approx')
                    if filesize and filesize > 0:
                        advanced_info['file_size'] = f"{round(filesize / (1024 * 1024), 2)} MB"
                
            except Exception as tech_error:
                logging.warning(f"Advanced technical info extraction failed: {tech_error}")
            
            # Build enhanced description for platforms with technical details
            enhanced_description = clean_string_for_json(description)
            if advanced_info and platform in ['rumble', 'vimeo', 'dailymotion']:
                tech_details = []
                if advanced_info.get('quality'):
                    tech_details.append(f"**Resolution:** {advanced_info['quality']}")
                if advanced_info.get('file_size'):
                    tech_details.append(f"**File Size:** {advanced_info['file_size']}")
                if advanced_info.get('format'):
                    tech_details.append(f"**Format:** {advanced_info['format']}")
                if advanced_info.get('fps'):
                    tech_details.append(f"**Frame Rate:** {advanced_info['fps']}")
                if advanced_info.get('video_codec'):
                    tech_details.append(f"**Video Codec:** {advanced_info['video_codec']}")
                if advanced_info.get('audio_codec'):
                    tech_details.append(f"**Audio Codec:** {advanced_info['audio_codec']}")
                
                if tech_details:
                    enhanced_description += f"\n\n--- **Technical Details** ---\n" + "\n".join(tech_details)
            
            # Ensure all strings are properly cleaned for JSON serialization
            result = {
                'title': clean_string_for_json(title),
                'description': enhanced_description,
                'uploader': clean_string_for_json(uploader),
                'duration': duration_str,
                'view_count': view_count_str,
                'thumbnail': thumbnail or '',
                'tags': [clean_string_for_json(tag) for tag in tags],
                'url': url,
                'platform': platform,
                'upload_date': upload_date
            }
            
            # Add advanced technical info to result
            result.update(advanced_info)
            
            return result
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error extracting metadata from {platform}: {error_msg}")
        
        # Handle specific error types
        if "429" in error_msg or "Too Many Requests" in error_msg:
            raise Exception(f"Rate limited by {platform}. Please wait a few minutes and try again.")
        elif "Restricted Video" in error_msg or "This video is not available" in error_msg:
            raise Exception(f"Video is not accessible (may be private, restricted, or require authentication)")
        elif "Sign in to confirm you’re not a bot" in error_msg:
            raise Exception(f"Platform {platform} requires authentication or is blocking automated access")
        else:
            raise Exception(f"Failed to extract metadata from {platform}: {clean_string_for_json(error_msg)}")

def download_from_platform(url, output_path='downloads', platform=None, progress_callback=None):
    """Download video from any supported platform"""
    if not platform:
        platform = get_platform_from_url(url)
    
    # Create downloads directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    config = get_platform_config(platform)
    config['outtmpl'] = os.path.join(output_path, '%(title)s.%(ext)s')
    
    # Progress hook
    def progress_hook(d):
        if progress_callback and d['status'] == 'downloading':
            progress_callback(d)
    
    config['progress_hooks'] = [progress_hook]
    
    try:
        with yt_dlp.YoutubeDL(config) as ydl:
            # Download the video
            ydl.download([url])
            
            # Get the downloaded file path
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            return filename
            
    except Exception as e:
        logging.error(f"Error downloading from {platform}: {e}")
        raise Exception(f"Failed to download from {platform}: {str(e)}")

def download_and_upload_multi_platform(url, access_token, user_id, title, description, tags, privacy, upload_id, progress_data):
    """Download from any platform and upload to YouTube"""
    try:
        # Detect platform
        platform = get_platform_from_url(url)
        logging.info(f"Detected platform: {platform}")
        
        progress_data[upload_id]['platform'] = platform
        progress_data[upload_id]['status'] = 'extracting_metadata'
        
        # Extract metadata first
        try:
            metadata = extract_platform_metadata(url, platform)
            progress_data[upload_id]['metadata'] = metadata
        except Exception as e:
            logging.warning(f"Could not extract metadata: {e}")
            # Continue with download even if metadata extraction fails
        
        progress_data[upload_id]['status'] = 'downloading'
        progress_data[upload_id]['progress'] = 0
        
        # Progress callback for download
        def download_progress(d):
            if d['status'] == 'downloading':
                try:
                    if 'total_bytes' in d and d['total_bytes']:
                        progress = (d['downloaded_bytes'] / d['total_bytes']) * 50  # Download is first 50%
                        progress_data[upload_id]['progress'] = progress
                        progress_data[upload_id]['downloaded'] = format_bytes(d['downloaded_bytes'])
                        progress_data[upload_id]['total'] = format_bytes(d['total_bytes'])
                        
                        if 'speed' in d and d['speed']:
                            progress_data[upload_id]['speed'] = format_bytes(d['speed']) + '/s'
                    elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                        progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 50
                        progress_data[upload_id]['progress'] = progress
                        progress_data[upload_id]['downloaded'] = format_bytes(d['downloaded_bytes'])
                        progress_data[upload_id]['total'] = format_bytes(d['total_bytes_estimate']) + ' (est)'
                        
                        if 'speed' in d and d['speed']:
                            progress_data[upload_id]['speed'] = format_bytes(d['speed']) + '/s'
                except Exception as e:
                    logging.error(f"Progress update error: {e}")
            
            elif d['status'] == 'finished':
                progress_data[upload_id]['status'] = 'download_complete'
                progress_data[upload_id]['progress'] = 50
        
        # Download the video
        downloaded_file = download_from_platform(url, 'downloads', platform, download_progress)
        
        if not os.path.exists(downloaded_file):
            raise Exception("Downloaded file not found")
        
        progress_data[upload_id]['status'] = 'uploading'
        progress_data[upload_id]['local_file'] = downloaded_file
        
        # Upload to YouTube
        result = upload_to_youtube(downloaded_file, access_token, title, description, tags, privacy, upload_id, progress_data)
        
        # Clean up downloaded file
        try:
            os.remove(downloaded_file)
            # Also remove info and description files if they exist
            info_file = downloaded_file + '.info.json'
            desc_file = downloaded_file + '.description'
            if os.path.exists(info_file):
                os.remove(info_file)
            if os.path.exists(desc_file):
                os.remove(desc_file)
        except Exception as e:
            logging.warning(f"Could not clean up files: {e}")
        
        progress_data[upload_id]['status'] = 'completed'
        progress_data[upload_id]['progress'] = 100
        
        return result
        
    except Exception as e:
        progress_data[upload_id]['status'] = 'error'
        progress_data[upload_id]['error'] = str(e)
        logging.error(f"Multi-platform download/upload error: {e}")
        raise

def upload_to_youtube(video_file, access_token, title, description, tags, privacy, upload_id, progress_data):
    """Upload video file to YouTube"""
    try:
        # Create credentials from access token
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        
        # Build credentials from access token
        credentials = Credentials(token=access_token)
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Set up the request body
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': privacy
            }
        }
        
        # Create media upload object
        media = MediaFileUpload(
            video_file,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        # Use the proper YouTube API upload method
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        # Execute the upload with progress tracking
        file_size = os.path.getsize(video_file)
        progress_data[upload_id]['total_upload'] = format_bytes(file_size)
        upload_start_time = time.time()
        
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                logging.info(f"Uploading video to YouTube, attempt {retry + 1}")
                status, response = insert_request.next_chunk()
                
                if status:
                    progress = 50 + (status.progress() * 50)  # Upload is second 50%
                    uploaded_bytes = status.resumable_progress
                    elapsed_time = time.time() - upload_start_time
                    
                    # Calculate upload speed
                    if elapsed_time > 0:
                        upload_speed = uploaded_bytes / elapsed_time
                        progress_data[upload_id]['upload_speed'] = format_bytes(upload_speed) + '/s'
                        
                        # Calculate ETA for upload
                        remaining_bytes = file_size - uploaded_bytes
                        if upload_speed > 0:
                            eta_seconds = remaining_bytes / upload_speed
                            progress_data[upload_id]['upload_eta'] = format_time(eta_seconds)
                    
                    progress_data[upload_id]['progress'] = progress
                    progress_data[upload_id]['uploaded'] = format_bytes(uploaded_bytes)
                    
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                    retry += 1
                    if retry > 5:
                        raise Exception(f"Upload failed after 5 retries: {error}")
                    time.sleep(2 ** retry)
                else:
                    raise Exception(f"HTTP error {e.resp.status}: {e.content}")
        
        if response:
            video_id = response.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            return {
                'success': True,
                'video_id': video_id,
                'video_url': video_url,
                'title': title
            }
        else:
            raise Exception("Upload completed but no response received")
            
    except Exception as e:
        logging.error(f"YouTube upload error: {e}")
        raise

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

            # Force integer conversion to avoid float format error
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)

            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
 

def format_number(number):
    """Format large numbers with appropriate suffixes"""
    if not number:
        return "0"
    
    try:
        # Convert to float first to handle any numeric type
        num = float(number)
        
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            # Return as integer if it's a whole number, otherwise as float
            if num.is_integer():
                return str(int(num))
            else:
                return f"{num:.1f}"
    except (ValueError, TypeError):
        return "0"

def extract_tags_from_text(text):
    """Extract potential tags from text"""
    if not text:
        return []
    
    # Remove common words and extract meaningful keywords
    common_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'so', 'than'
    }
    
    # Extract words that could be tags
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    tags = []
    
    for word in words:
        if word not in common_words and len(tags) < 10:
            if word not in tags:  # Avoid duplicates
                tags.append(word)
    
    return tags

def get_supported_platforms():
    """Get list of supported platforms"""
    return [
        'youtube',
        'instagram', 
        'facebook',
        'twitter',
        'dailymotion',
        'vimeo', 
        'pinterest',
        'reddit',
        'tiktok',
        'snapchat',
        'twitch',
        'rumble',
        'deadtoons',
        'cybervynx',
        'voe',
        'filemoon',
        'newerstream',
        'shortic',
        'smoothpre',
        'direct_url'
    ]

def is_platform_supported(url):
    """Check if URL platform is supported"""
    platform = get_platform_from_url(url)
    return platform in get_supported_platforms()

def clean_string_for_json(text):
    """Clean string for safe JSON serialization"""
    if not text:
        return ''
    
    try:
        # Convert to string and handle encoding issues
        if not isinstance(text, str):
            text = str(text)
        
        # Remove non-printable characters and clean up
        import re
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove or replace problematic characters for JSON
        text = text.replace('\\', '').replace('\r', '').replace('\n', ' ')
        
        # Limit length to prevent huge JSON responses
        if len(text) > 5000:
            text = text[:5000] + '...'
        
        return text.strip()
    except Exception:
        return 'Content unavailable'

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
        
        # Extract format information
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        # Find video stream
        video_stream = None
        audio_stream = None
        
        for stream in streams:
            if stream.get('codec_type') == 'video' and not video_stream:
                video_stream = stream
            elif stream.get('codec_type') == 'audio' and not audio_stream:
                audio_stream = stream
        
        # Extract comprehensive metadata
        metadata = {}
        
        # File information
        metadata['file_size'] = int(format_info.get('size', 0))
        metadata['file_size_mb'] = round(metadata['file_size'] / (1024 * 1024), 2) if metadata['file_size'] > 0 else 0
        metadata['duration'] = float(format_info.get('duration', 0))
        metadata['bitrate'] = int(format_info.get('bit_rate', 0))
        metadata['format_name'] = format_info.get('format_name', 'Unknown')
        
        # Video stream information
        if video_stream:
            metadata['width'] = int(video_stream.get('width', 0))
            metadata['height'] = int(video_stream.get('height', 0))
            metadata['video_codec'] = video_stream.get('codec_name', 'Unknown')
            metadata['video_bitrate'] = int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0
            metadata['fps'] = video_stream.get('r_frame_rate', '0/1')
            
            # Calculate FPS from fraction
            if '/' in str(metadata['fps']):
                try:
                    num, den = map(int, str(metadata['fps']).split('/'))
                    metadata['fps'] = round(num / den, 2) if den > 0 else 0
                except:
                    metadata['fps'] = 0
        
        # Audio stream information
        if audio_stream:
            metadata['audio_codec'] = audio_stream.get('codec_name', 'Unknown')
            metadata['audio_bitrate'] = int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0
            metadata['sample_rate'] = int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else 0
            metadata['channels'] = int(audio_stream.get('channels', 0)) if audio_stream.get('channels') else 0
        
        return metadata
        
    except subprocess.TimeoutExpired:
        raise Exception("Video analysis timed out (file too large or slow connection)")
    except json.JSONDecodeError:
        raise Exception("Invalid response from ffprobe")
    except Exception as e:
        raise Exception(f"Advanced metadata extraction failed: {str(e)}")

def extract_direct_url_metadata(url):
    """Extract metadata from direct video URLs with comprehensive analysis"""
    import urllib.parse
    from urllib.parse import urlparse
    import requests
    import yt_dlp
    
    try:
        # First verify this is actually a direct video URL
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            
            if not (content_type.startswith('video') or 'mpegurl' in content_type):
                raise Exception("URL does not point to a direct video file")
                
            # Get file info from headers
            file_size = response.headers.get('content-length')
            content_disposition = response.headers.get('content-disposition', '')
            
        except Exception as e:
            raise Exception(f"Failed to verify direct video URL: {str(e)}")
        
        # Parse URL to get filename
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1] if parsed_url.path else 'direct_video'
        
        # Try to get filename from Content-Disposition header
        if content_disposition and 'filename=' in content_disposition:
            try:
                filename = content_disposition.split('filename=')[1].strip('"').strip("'")
            except:
                pass
        
        # Use filename as title (without extension)
        if '.' in filename:
            title = filename.rsplit('.', 1)[0]
            file_ext = filename.rsplit('.', 1)[1].upper()
        else:
            title = filename
            # Get format from content-type if extension not available
            if 'mp4' in content_type:
                file_ext = 'MP4'
            elif 'webm' in content_type:
                file_ext = 'WEBM'
            elif 'mkv' in content_type:
                file_ext = 'MKV'
            elif 'avi' in content_type:
                file_ext = 'AVI'
            else:
                file_ext = 'VIDEO'
        
        # Clean up title
        title = title.replace('_', ' ').replace('-', ' ').replace('%20', ' ')
        
        # Get advanced metadata using ffprobe
        advanced_metadata = {}
        try:
            advanced_metadata = get_advanced_video_metadata(url)
        except Exception as probe_error:
            logging.warning(f"FFprobe analysis failed: {probe_error}")
        
        # Try to get detailed video information using yt-dlp
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
        
        # Combine metadata from all sources (ffprobe takes priority)
        duration = advanced_metadata.get('duration', 0) or ydl_metadata.get('duration', 0)
        duration_str = format_duration(int(duration)) if duration else 'Unknown'
        
        # File size (ffprobe > yt-dlp > HTTP headers)
        filesize = advanced_metadata.get('file_size', 0) or ydl_metadata.get('filesize', 0)
        if not filesize and file_size:
            try:
                filesize = int(file_size)
            except:
                filesize = 0
        
        file_size_mb = round(filesize / (1024 * 1024), 2) if filesize > 0 else 0
        
        # Video quality (ffprobe > yt-dlp)
        width = advanced_metadata.get('width', 0) or ydl_metadata.get('width', 0)
        height = advanced_metadata.get('height', 0) or ydl_metadata.get('height', 0)
        quality = f"{width}x{height}" if width and height else 'Unknown'
        
        # Build comprehensive description with all available info
        description_parts = []
        
        # Basic file info (always show)
        description_parts.append(f"**Filename:** {filename}")
        if file_size_mb > 0:
            description_parts.append(f"**File Size:** {file_size_mb} MB")
        if file_ext != 'Unknown':
            description_parts.append(f"**Format:** {file_ext}")
        
        # Video technical details (from ffprobe)
        if quality != 'Unknown':
            description_parts.append(f"**Resolution:** {quality}")
        if advanced_metadata.get('video_codec'):
            description_parts.append(f"**Video Codec:** {advanced_metadata['video_codec'].upper()}")
        if (advanced_metadata.get('video_bitrate') or 0) > 0:
            video_bitrate_kbps = round(advanced_metadata['video_bitrate'] / 1000)
            description_parts.append(f"**Video Bitrate:** {video_bitrate_kbps} kbps")
        if (advanced_metadata.get('fps') or 0) > 0:
            description_parts.append(f"**Frame Rate:** {advanced_metadata['fps']} FPS")
        
        # Audio technical details (from ffprobe)
        if advanced_metadata.get('audio_codec'):
            description_parts.append(f"**Audio Codec:** {advanced_metadata['audio_codec'].upper()}")
        if (advanced_metadata.get('audio_bitrate') or 0) > 0:
            audio_bitrate_kbps = round(advanced_metadata['audio_bitrate'] / 1000)
            description_parts.append(f"**Audio Bitrate:** {audio_bitrate_kbps} kbps")
        if (advanced_metadata.get('sample_rate') or 0) > 0:
            description_parts.append(f"**Sample Rate:** {advanced_metadata['sample_rate']} Hz")
        if (advanced_metadata.get('channels') or 0) > 0:
            channel_text = "Stereo" if advanced_metadata['channels'] == 2 else f"{advanced_metadata['channels']} Channel"
            description_parts.append(f"**Audio:** {channel_text}")
        
        # Overall bitrate
        if (advanced_metadata.get('bitrate') or 0) > 0:
            total_bitrate_kbps = round(advanced_metadata['bitrate'] / 1000)
            description_parts.append(f"**Total Bitrate:** {total_bitrate_kbps} kbps")
        
        description = "\n".join(description_parts) if description_parts else "Direct video file"
        
        # Get thumbnails
        thumbnails = ydl_metadata.get('thumbnails', [])
        thumbnail_urls = [thumb.get('url', '') for thumb in thumbnails if thumb.get('url')]
        
        return {
            'title': clean_string_for_json(title) if title else filename,
            'description': clean_string_for_json(description),
            'duration': duration_str,
            'thumbnail': thumbnail_urls[0] if thumbnail_urls else '',
            'thumbnails': thumbnail_urls,
            'file_size': f"{file_size_mb} MB" if file_size_mb > 0 else 'Unknown',
            'quality': quality,
            'format': file_ext,
            'url': url,
            'platform': 'direct_url',
            'upload_date': '',
            # Advanced technical metadata
            'video_codec': advanced_metadata.get('video_codec', 'Unknown'),
            'audio_codec': advanced_metadata.get('audio_codec', 'Unknown'),
            'bitrate': f"{round((advanced_metadata.get('bitrate') or 0) / 1000)} kbps" if (advanced_metadata.get('bitrate') or 0) > 0 else 'Unknown',
            'fps': f"{advanced_metadata.get('fps') or 0} FPS" if (advanced_metadata.get('fps') or 0) > 0 else 'Unknown',
            'sample_rate': f"{(advanced_metadata.get('sample_rate') or 0)} Hz" if (advanced_metadata.get('sample_rate') or 0) > 0 else 'Unknown',
            'channels': (advanced_metadata.get('channels') or 0) if (advanced_metadata.get('channels') or 0) > 0 else 'Unknown',
            # Remove these fields for direct URLs
            'uploader': None,
            'view_count': None,
            'tags': []
        }
        
    except Exception as e:
        # Ultimate fallback with basic info
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1] if parsed_url.path else 'direct_video'
        title = filename.rsplit('.', 1)[0] if '.' in filename else filename
        title = title.replace('_', ' ').replace('-', ' ').replace('%20', ' ')
        
        return {
            'title': clean_string_for_json(title) if title else 'Direct Video Download',
            'description': f"**Error:** Could not analyze video file\n**URL:** {url}",
            'duration': 'Unknown',
            'thumbnail': '',
            'thumbnails': [],
            'file_size': 'Unknown',
            'quality': 'Unknown',
            'format': 'Unknown',
            'url': url,
            'platform': 'direct_url',
            'upload_date': '',
            'video_codec': 'Unknown',
            'audio_codec': 'Unknown', 
            'bitrate': 'Unknown',
            'fps': 'Unknown',
            'sample_rate': 'Unknown',
            'channels': 'Unknown',
            'uploader': None,
            'view_count': None,
            'tags': []
        }

def get_platform_display_name(platform):
    """Get display name for platform"""
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

def clean_description_from_technical_details(raw_description):
    """Clean description by removing technical details that should not be shown to users"""
    if not raw_description:
        return "No description available"
    
    # Remove technical details patterns that shouldn't be in user-facing descriptions
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
        r'\*\*Sample Rate:\*\*.*?(?=\n|\Z)',
        r'\*\*Audio:\*\*.*?(?=\n|\Z)',
        r'\*\*Total Bitrate:\*\*.*?(?=\n|\Z)'
    ]
    
    clean_desc = raw_description
    for pattern in technical_patterns:
        clean_desc = re.sub(pattern, '', clean_desc, flags=re.DOTALL | re.MULTILINE)
    
    # Clean up extra whitespace and newlines
    clean_desc = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_desc)  # Replace multiple newlines with double newlines
    clean_desc = clean_desc.strip()
    
    return clean_desc if clean_desc else "No description available"

def get_video_qualities_info(url):
    """Get available video qualities and file sizes for a URL using --list-formats approach"""
    try:
        platform = get_platform_from_url(url)
        
        # Use --list-formats equivalent config for accurate data
        list_config = {
            'quiet': True,
            'no_warnings': True,
            'listformats': False,  # We want actual format data, not just list
            'extract_flat': False,
        }
        
        # Add cookies for specific platforms
        if platform == 'youtube':
            list_config['cookiefile'] = 'cookies/cookies.txt'
        elif platform == 'instagram':
            list_config['cookiefile'] = 'cookies/instagram_cookies.txt'
        elif platform == 'vimeo':
            list_config['cookiefile'] = 'cookies/vimeo_cookies.txt'
        
        with yt_dlp.YoutubeDL(list_config) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info or 'formats' not in info:
                return [
                    {'format_id': 'best', 'height': 'Best Available', 'filesize': '~Auto', 'fps': 30, 'ext': 'mp4'}
                ]
            
            formats = info['formats']
            qualities = []
            seen_heights = set()
            
            # Filter and sort formats by quality  
            video_formats = [f for f in formats if f.get('height') and f.get('vcodec') != 'none']
            
            # Group formats by height to find the best representative for each resolution
            height_groups = {}
            for fmt in video_formats:
                height = fmt.get('height')
                if height:
                    if height not in height_groups:
                        height_groups[height] = []
                    height_groups[height].append(fmt)
            
            # Sort by height descending
            for height in sorted(height_groups.keys(), reverse=True):
                if height not in seen_heights:
                    seen_heights.add(height)
                    
                    # Choose the best format for this height
                    formats_for_height = height_groups[height]
                    
                    # Choose the format with the best balance of quality and efficiency
                    # Prefer smaller bitrates and file sizes while maintaining quality
                    def format_score(fmt):
                        score = 0
                        
                        # Get bitrate info
                        tbr = fmt.get('tbr', 0) or fmt.get('vbr', 0) or 0
                        filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                        
                        # Define target bitrates for each resolution (reasonable quality)
                        target_bitrates = {
                            2160: 15000,  # 4K: 15 Mbps target
                            1440: 10000,  # 1440p: 10 Mbps target  
                            1080: 6000,   # 1080p: 6 Mbps target
                            720: 4000,    # 720p: 4 Mbps target
                            480: 2000,    # 480p: 2 Mbps target
                            360: 1000,    # 360p: 1 Mbps target
                        }
                        
                        # Find target bitrate for this height
                        target = target_bitrates.get(height, 5000)
                        
                        # Heavily prefer formats with filesize info
                        if filesize > 0:
                            score += 10000
                            # For formats with filesize, prefer smaller files (efficiency)
                            # Calculate size per minute to normalize for duration
                            duration = info.get('duration', 180) or 180  # fallback to 3 min
                            size_per_min = filesize / (duration / 60) if duration > 0 else filesize
                            # Penalty increases with file size - prefer smaller files
                            score -= int(size_per_min / (1024 * 1024))  # Penalty per MB per minute
                        
                        # For bitrate scoring, prefer rates close to target (not too high)
                        if tbr > 0:
                            score += 5000  # Has bitrate info
                            # Calculate distance from target (penalty for being too far from ideal)
                            distance_from_target = abs(tbr - target)
                            if tbr <= target * 1.5:  # Within 150% of target is good
                                score += 2000
                                # Prefer lower bitrates when close to target
                                score += int((target * 1.5 - tbr) / 100)  # More points for lower bitrate
                            else:
                                # Penalty for very high bitrates
                                score -= int(distance_from_target / 100)
                        
                        # Format preferences
                        if fmt.get('ext') == 'mp4':
                            score += 500
                        
                        # Codec preferences (efficient codecs)
                        vcodec = fmt.get('vcodec', '').lower()
                        if any(codec in vcodec for codec in ['avc1', 'h264', 'x264']):
                            score += 200
                        elif 'vp9' in vcodec:
                            score += 150  # VP9 is efficient
                        elif 'av01' in vcodec:
                            score += 100  # AV1 is very efficient but less compatible
                        
                        return score
                    
                    # Sort formats by score and pick the best one
                    formats_for_height.sort(key=format_score, reverse=True)
                    fmt = formats_for_height[0]
                    
                    # Debug logging for format selection
                    if len(formats_for_height) > 1:
                        selected_tbr = fmt.get('tbr', 0) or fmt.get('vbr', 0) or 0
                        selected_size = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                        logging.debug(f"Selected {height}p format: bitrate={selected_tbr}kbps, size={selected_size}bytes, score={format_score(fmt)}")
                        # Log alternatives for comparison
                        for alt_fmt in formats_for_height[1:3]:  # Show up to 2 alternatives
                            alt_tbr = alt_fmt.get('tbr', 0) or alt_fmt.get('vbr', 0) or 0
                            alt_size = alt_fmt.get('filesize') or alt_fmt.get('filesize_approx') or 0
                            logging.debug(f"  Alternative {height}p: bitrate={alt_tbr}kbps, size={alt_size}bytes, score={format_score(alt_fmt)}")
                    
                    # Get real file size from format data
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                    
                    if filesize and filesize > 0:
                        if filesize < 1024 * 1024:  # Less than 1MB
                            size_str = f"{round(filesize / 1024, 1)} KB"
                        elif filesize < 1024 * 1024 * 1024:  # Less than 1GB
                            size_mb = round(filesize / (1024 * 1024), 1)
                            size_str = f"{size_mb} MB"
                        else:  # 1GB or larger
                            size_gb = round(filesize / (1024 * 1024 * 1024), 1)
                            size_str = f"{size_gb} GB"
                    else:
                        # If no exact size, try to calculate from bitrate and duration
                        tbr = fmt.get('tbr') or fmt.get('vbr', 0)  # Total bitrate or video bitrate
                        duration = info.get('duration', 0)
                        
                        if tbr and duration and tbr > 0 and duration > 0:
                            # Calculate size: bitrate (kbps) * duration (seconds) / 8 (bits to bytes) / 1024 (to MB)
                            estimated_mb = (tbr * duration) / (8 * 1024)
                            if estimated_mb < 1:
                                size_str = f"~{round(estimated_mb * 1024)} KB"
                            elif estimated_mb < 1024:
                                size_str = f"~{round(estimated_mb)} MB"
                            else:
                                size_str = f"~{round(estimated_mb / 1024, 1)} GB"
                        else:
                            # Last resort - basic estimation based on quality
                            estimated_size = estimate_file_size(height, duration or 180)
                            size_str = f"~{estimated_size}"
                    
                    qualities.append({
                        'format_id': fmt.get('format_id'),
                        'height': height,
                        'filesize': size_str,
                        'fps': fmt.get('fps', 30),
                        'ext': fmt.get('ext', 'mp4'),
                        'tbr': fmt.get('tbr', 0),  # Total bitrate
                        'vbr': fmt.get('vbr', 0),  # Video bitrate
                        'protocol': fmt.get('protocol', 'https'),
                        'format_note': fmt.get('format_note', '')
                    })
            
            # If no video formats found, try to get any formats
            if not qualities:
                all_formats = [f for f in formats if f.get('format_id')]
                if all_formats:
                    # Sort by preference (best quality first)
                    all_formats.sort(key=lambda x: (
                        x.get('height', 0),
                        x.get('tbr', 0),
                        x.get('filesize', 0) or x.get('filesize_approx', 0)
                    ), reverse=True)
                    
                    for fmt in all_formats[:10]:  # Take top 10 formats
                        height_info = f"{fmt.get('height', 'Audio')}p" if fmt.get('height') else 'Audio Only'
                        
                        filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                        if filesize and filesize > 0:
                            if filesize < 1024 * 1024 * 1024:
                                size_str = f"{round(filesize / (1024 * 1024), 1)} MB"
                            else:
                                size_str = f"{round(filesize / (1024 * 1024 * 1024), 1)} GB"
                        else:
                            size_str = '~Auto'
                        
                        qualities.append({
                            'format_id': fmt.get('format_id'),
                            'height': height_info,
                            'filesize': size_str,
                            'fps': fmt.get('fps', 30),
                            'ext': fmt.get('ext', 'mp4'),
                            'tbr': fmt.get('tbr', 0),
                            'vbr': fmt.get('vbr', 0),
                            'protocol': fmt.get('protocol', 'https'),
                            'format_note': fmt.get('format_note', '')
                        })
            
            # Add fallback qualities if still none found
            if not qualities:
                qualities = [
                    {'format_id': 'best', 'height': 'Best Available', 'filesize': '~Auto', 'fps': 30, 'ext': 'mp4'},
                    {'format_id': 'worst', 'height': 'Lowest Quality', 'filesize': '~Auto', 'fps': 30, 'ext': 'mp4'}
                ]
            
            return qualities
        
    except Exception as e:
        logging.error(f"Error getting video qualities: {e}")
        return [
            {'format_id': 'best', 'height': 'Best Available', 'filesize': '~Auto', 'fps': 30, 'ext': 'mp4'}
        ]

def estimate_file_size(height, duration):
    """Estimate file size based on quality and duration"""
    # Rough estimation based on typical bitrates
    bitrate_estimates = {
        2160: 25000,  # 4K - 25 Mbps
        1440: 16000,  # 1440p - 16 Mbps  
        1080: 8000,   # 1080p - 8 Mbps
        720: 5000,    # 720p - 5 Mbps
        480: 2500,    # 480p - 2.5 Mbps
        360: 1000,    # 360p - 1 Mbps
        240: 500      # 240p - 0.5 Mbps
    }
    
    # Find closest quality match
    closest_height = min(bitrate_estimates.keys(), key=lambda x: abs(x - height))
    estimated_bitrate = bitrate_estimates[closest_height]
    
    # Calculate size: bitrate (kbps) * duration (seconds) / 8 (bits to bytes) / 1024 (to MB)
    estimated_mb = (estimated_bitrate * duration) / (8 * 1024)
    
    if estimated_mb < 1:
        return f"{round(estimated_mb * 1024)} KB"
    elif estimated_mb < 1024:
        return f"{round(estimated_mb)} MB"
    else:
        return f"{round(estimated_mb / 1024, 1)} GB"

def download_video_with_progress(url, quality_format_id, download_id, progress_data):
    """Download video with real-time progress tracking"""
    try:
        platform = get_platform_from_url(url)
        config = get_platform_config(platform)
        
        # Create download directory
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        def progress_hook(d):
            if download_id in progress_data:
                if d['status'] == 'downloading':
                    # Extract progress information
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)
                    
                    # Calculate progress percentage
                    if total > 0:
                        progress_percent = (downloaded / total) * 100
                    else:
                        progress_percent = 0
                    
                    # Format speed
                    speed_str = "0 Mbps"
                    if speed:
                        speed_mbps = (speed * 8) / (1024 * 1024)  # Convert to Mbps
                        speed_str = f"{speed_mbps:.1f} Mbps"
                    
                    # Format ETA
                    eta_str = "--:--"
                    if eta and eta > 0:
                        eta_mins = int(eta // 60)
                        eta_secs = int(eta % 60)
                        eta_str = f"{eta_mins:02d}:{eta_secs:02d}"
                    
                    # Format file sizes
                    def format_bytes(bytes_val):
                        if bytes_val < 1024 * 1024:
                            return f"{bytes_val / 1024:.1f} KB"
                        elif bytes_val < 1024 * 1024 * 1024:
                            return f"{bytes_val / (1024 * 1024):.1f} MB"
                        else:
                            return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"
                    
                    # Update progress data
                    progress_data[download_id].update({
                        'status': 'downloading',
                        'progress': min(progress_percent, 100),
                        'speed': speed_str,
                        'eta': eta_str,
                        'downloaded': format_bytes(downloaded),
                        'total': format_bytes(total) if total > 0 else 'Unknown'
                    })
                    
                elif d['status'] == 'finished':
                    progress_data[download_id].update({
                        'status': 'processing',
                        'progress': 100,
                        'speed': '0 Mbps',
                        'eta': '00:00'
                    })
        
        # Configure yt-dlp for download
        ydl_opts = {
            **config,
            'format': quality_format_id,
            'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'writeinfojson': False,
            'writedescription': False,
        }
        
        # Check file size before download
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Could not extract video information")
                
            formats = info.get('formats', [])
            selected_format = None
            
            for fmt in formats:
                if fmt.get('format_id') == quality_format_id:
                    selected_format = fmt
                    break
            
            if selected_format:
                filesize = selected_format.get('filesize') or selected_format.get('filesize_approx')
                if filesize and filesize > 300 * 1024 * 1024:  # 300MB limit
                    progress_data[download_id].update({
                        'status': 'cancelled',
                        'error': f'File size ({filesize / (1024*1024):.1f} MB) exceeds 300MB limit'
                    })
                    return {'error': 'File too large'}
        
        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            # Get the downloaded filename
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            return {
                'filename': os.path.basename(filename),
                'file_path': filename
            }
            
    except Exception as e:
        logging.error(f"Download error: {e}")
        raise e
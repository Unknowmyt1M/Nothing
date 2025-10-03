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

def get_working_cookies_file(user_dir, user_cookies_file):
    """Get working cookies file with fallback system"""
    fallback_cookies = "cookies/fallback_cookies.txt"
    
    # Check if user cookies exist and have content
    if os.path.exists(user_cookies_file):
        try:
            with open(user_cookies_file, 'r') as f:
                content = f.read().strip()
                # Check if it's not just a placeholder
                if len(content) > 100 and 'LOGIN_INFO' in content:
                    logging.info(f"Using user cookies: {user_cookies_file}")
                    return user_cookies_file
        except:
            pass
    
    # Use fallback cookies if available
    if os.path.exists(fallback_cookies):
        logging.info(f"Using fallback cookies: {fallback_cookies}")
        return fallback_cookies
    
    # Return None if no working cookies found
    logging.warning("No working cookies found")
    return None

def download_and_upload_video(url, access_token, user_id, title, description, tags, privacy, upload_id, progress_data):
    """Download video and upload to YouTube"""
    user_dir = f"db/{user_id}"
    user_cookies_file = f"{user_dir}/cookies.txt"
    cookies_file = get_working_cookies_file(user_dir, user_cookies_file)
    
    # Update progress
    progress_data[upload_id]['status'] = 'downloading'
    progress_data[upload_id]['progress'] = 0
    
    def progress_hook(d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', d.get('total_bytes_estimate', 0))
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            if total > 0:
                progress = (downloaded / total) * 50  # Download is 50% of total progress
                progress_data[upload_id]['progress'] = round(progress, 1)
                progress_data[upload_id]['downloaded'] = format_bytes(downloaded)
                progress_data[upload_id]['total'] = format_bytes(total)
                progress_data[upload_id]['speed'] = format_bytes(speed) + '/s' if speed else '0 B/s'
                progress_data[upload_id]['eta'] = f"{eta}s" if eta else 'Unknown'
                progress_data[upload_id]['percentage'] = round((downloaded / total) * 100, 1)
            else:
                progress_data[upload_id]['progress'] = 0
                progress_data[upload_id]['downloaded'] = format_bytes(downloaded)
                progress_data[upload_id]['total'] = 'Unknown'
                progress_data[upload_id]['speed'] = format_bytes(speed) + '/s' if speed else '0 B/s'
                progress_data[upload_id]['eta'] = 'Unknown'
                progress_data[upload_id]['percentage'] = 0
    
    # Check if this is a direct URL
    from multi_platform_downloader import get_platform_from_url
    detected_platform = get_platform_from_url(url)
    
    # Download video in ultra high quality - 4K/1440p/1080p preference
    output_template = f"{user_dir}/%(title)s.%(ext)s"
    
    if detected_platform == 'direct_url':
        # For direct URLs, use simpler configuration
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
            'extractor_retries': 10,
            'ignoreerrors': False,
            'merge_output_format': 'mp4',
            'writesubtitles': False,
            'writeautomaticsub': False,
            'http_chunk_size': 10485760,
            'retries': 10,
            'file_access_retries': 10,
            'fragment_retries': 10,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    else:
        # For platform URLs, use quality-focused configuration
        ydl_opts = {
            'format': 'best[height>=2160][ext=mp4]/best[height>=1440][ext=mp4]/best[height>=1080][ext=mp4]/best[height>=720][ext=mp4]/best[ext=mp4]/best[ext=webm]/best',
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
            'cookiefile': cookies_file,
            'extractor_retries': 5,
            'ignoreerrors': False,
            'merge_output_format': 'mp4',  # Ensure final output is mp4
            'writesubtitles': False,
            'writeautomaticsub': False,
            'http_chunk_size': 10485760,  # 10MB chunks for better download stability
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get info first
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("Failed to extract video information")
            video_title = info.get('title', 'Downloaded Video')
            
            # Download the video
            ydl.download([url])
            
            # Find the downloaded file
            video_file = None
            for file in os.listdir(user_dir):
                if file.endswith(('.mp4', '.webm', '.mkv', '.avi')):
                    video_file = os.path.join(user_dir, file)
                    break
            
            if not video_file:
                raise Exception("Downloaded video file not found")
            
            # Update progress - starting upload
            progress_data[upload_id]['status'] = 'uploading'
            progress_data[upload_id]['progress'] = 50
            
            # Upload to YouTube
            youtube_url = upload_to_youtube(
                video_file, 
                access_token, 
                title or video_title, 
                description, 
                tags,
                privacy,
                upload_id,
                progress_data
            )
            
            # Save to history
            save_to_history(user_id, {
                'original_url': url,
                'title': title or video_title,
                'youtube_url': youtube_url,
                'upload_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tags': tags
            })
            
            # Clean up downloaded file
            cleanup_video_file(video_file)
            
            progress_data[upload_id]['status'] = 'completed'
            progress_data[upload_id]['progress'] = 100
            progress_data[upload_id]['youtube_url'] = youtube_url
            
            return {'success': True, 'youtube_url': youtube_url}
            
    except Exception as e:
        logging.error(f"Error in download_and_upload_video: {e}")
        # Clean up any downloaded files on error
        try:
            for file in os.listdir(user_dir):
                if file.endswith(('.mp4', '.webm', '.mkv', '.avi')):
                    cleanup_video_file(os.path.join(user_dir, file))
        except:
            pass
        progress_data[upload_id]['status'] = 'error'
        progress_data[upload_id]['error'] = str(e)
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
                'privacyStatus': privacy  # Use the selected privacy setting
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
                            progress_data[upload_id]['upload_eta'] = f"{int(eta_seconds)}s"
                        else:
                            progress_data[upload_id]['upload_eta'] = 'Unknown'
                    else:
                        progress_data[upload_id]['upload_speed'] = '0 B/s'
                        progress_data[upload_id]['upload_eta'] = 'Unknown'
                    
                    progress_data[upload_id]['progress'] = round(progress, 1)
                    progress_data[upload_id]['uploaded'] = format_bytes(uploaded_bytes)
                    progress_data[upload_id]['upload_percentage'] = round(status.progress() * 100, 1)
                else:
                    # Initial upload state
                    progress_data[upload_id]['progress'] = 50 + (retry * 5)
                    progress_data[upload_id]['upload_speed'] = '0 B/s'
                    progress_data[upload_id]['upload_eta'] = 'Calculating...'
                    
            except Exception as e:
                error = e
                retry += 1
                if retry > 3:
                    raise error
                    
        if response is not None:
            video_id = response['id']
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            return youtube_url
        else:
            raise Exception("YouTube upload failed - no response received")
            
    except Exception as e:
        logging.error(f"Error uploading to YouTube: {e}")
        raise Exception(f"YouTube upload failed: {e}")



def save_to_history(user_id, upload_data):
    """Save upload information to user's history"""
    history_file = f"db/{user_id}/history.json"
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = []
    
    history.append(upload_data)
    
    # Keep only last 50 uploads
    history = history[-50:]
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    if not bytes_value:
        return "0 B"
    
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TiB"

def cleanup_video_file(video_file):
    """Clean up downloaded video file"""
    try:
        if os.path.exists(video_file):
            os.remove(video_file)
            logging.info(f"Cleaned up video file: {video_file}")
    except Exception as e:
        logging.error(f"Error cleaning up video file {video_file}: {e}")

def test_video_download(test_urls, test_user_id="test_user"):
    """Test video downloading with different video types"""
    test_dir = f"db/{test_user_id}"
    os.makedirs(test_dir, exist_ok=True)
    
    results = []
    
    for i, url in enumerate(test_urls):
        try:
            logging.info(f"Testing URL {i+1}: {url}")
            
            # Extract metadata first
            from yt_metadata import extract_metadata
            cookies_file = "cookies/fallback_cookies.txt" if os.path.exists("cookies/fallback_cookies.txt") else None
            metadata = extract_metadata(url, cookies_file)
            
            # Test download
            output_template = f"{test_dir}/test_video_{i+1}.%(ext)s"
            ydl_opts = {
                'format': 'best[height<=720]/best',  # Better quality for testing
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'ignoreerrors': True,
                'cookiefile': cookies_file,
                'extractor_retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find downloaded file
            downloaded_file = None
            for file in os.listdir(test_dir):
                if file.startswith(f'test_video_{i+1}') and file.endswith(('.mp4', '.webm', '.mkv', '.avi')):
                    downloaded_file = os.path.join(test_dir, file)
                    break
            
            if downloaded_file and os.path.exists(downloaded_file):
                file_size = os.path.getsize(downloaded_file)
                results.append({
                    'url': url,
                    'status': 'success',
                    'title': metadata.get('title', 'Unknown'),
                    'file_size': format_bytes(file_size),
                    'downloaded_file': downloaded_file
                })
                # Clean up immediately after test
                cleanup_video_file(downloaded_file)
            else:
                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': 'Downloaded file not found'
                })
                
        except Exception as e:
            results.append({
                'url': url,
                'status': 'error',
                'error': str(e)
            })
            logging.error(f"Test error for {url}: {e}")
    
    # Clean up test directory
    try:
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
    except:
        pass
        
    return results

def get_download_progress(upload_id):
    """Get current download/upload progress"""
    # This would be implemented to track real-time progress
    # For now, return a placeholder
    return {
        'status': 'downloading',
        'progress': 45,
        'speed': '15.3 MiB/s',
        'downloaded': '156.7 MiB',
        'total': '324.34 MiB'
    }

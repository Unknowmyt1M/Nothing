import os
import json
import logging
import requests
import time
import threading
import asyncio
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from backend.database.json_db import add_to_history
from backend.utils.helpers import format_bytes, get_temp_dir
from backend.platforms import download_from_platform, get_platform_from_url, is_platform_supported
from backend.services.auth_service import refresh_access_token

# Global progress storage dictionaries
_upload_lock = threading.Lock()
upload_progress_data = {}

def upload_to_youtube(video_file, access_token, title, description, tags, privacy, upload_id, progress_data):
    """Upload video file to YouTube"""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        
        credentials = Credentials(token=access_token)
        youtube = build('youtube', 'v3', credentials=credentials)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': privacy
            }
        }
        
        media = MediaFileUpload(
            video_file,
            chunksize=1024 * 1024, # 1MB chunks for smooth progress updates
            resumable=True,
            mimetype='video/*'
        )
        
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        file_size = os.path.getsize(video_file)
        progress_data[upload_id]['total_upload'] = format_bytes(file_size)
        upload_start_time = time.time()
        
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = 50 + (status.progress() * 50)
                    uploaded_bytes = status.resumable_progress
                    elapsed_time = time.time() - upload_start_time
                    
                    if elapsed_time > 0:
                        upload_speed = uploaded_bytes / elapsed_time
                        progress_data[upload_id]['upload_speed'] = format_bytes(upload_speed) + '/s'
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
                    progress_data[upload_id]['progress'] = 50 + (retry * 5)
                    progress_data[upload_id]['upload_speed'] = '0 B/s'
                    progress_data[upload_id]['upload_eta'] = 'Calculating...'
            except Exception as e:
                error = e
                retry += 1
                if retry > 3:
                    raise error
                    
        if response is not None:
            return f"https://www.youtube.com/watch?v={response['id']}"
        else:
            raise Exception("YouTube upload failed - no response")
    except Exception as e:
        logging.error(f"Error uploading to YouTube in service: {e}")
        raise

def start_video_upload(url, title, description, tags, privacy, current_access_token, current_refresh_token, user_email_dir):
    """Start video download + YouTube upload background worker thread and return upload ID"""
    upload_id = f"up_{user_email_dir}_{int(time.time())}"
    
    with _upload_lock:
        upload_progress_data[upload_id] = {
            'status': 'starting',
            'progress': 0,
            'speed': '0 B/s',
            'downloaded': '0 B',
            'total': '0 B'
        }
    
    def worker():
        try:
            access_token = current_access_token
            if current_refresh_token:
                try:
                    access_token = refresh_access_token(current_refresh_token)
                except Exception as te:
                    logging.error(f"Failed token refresh in uploader: {te}")
                    
            if not is_platform_supported(url):
                platform = get_platform_from_url(url)
                raise Exception(f"Platform '{platform}' is not supported yet")
                
            platform = get_platform_from_url(url)
            download_path = get_temp_dir("uploads")
            os.makedirs(download_path, exist_ok=True)
            
            def dl_hook(d):
                if d['status'] == 'downloading':
                    try:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        speed = d.get('speed', 0)
                        
                        progress = (downloaded / total * 50) if total > 0 else 0
                        speed_str = format_bytes(speed) + '/s' if speed else '0 B/s'
                        
                        with _upload_lock:
                            upload_progress_data[upload_id].update({
                                'status': 'downloading',
                                'progress': progress,
                                'speed': speed_str,
                                'downloaded': format_bytes(downloaded),
                                'total': format_bytes(total)
                            })
                    except Exception as e:
                        logging.error(f"Download progress parsing error: {e}")
                        
            # Download file
            downloaded_file = download_from_platform(url, download_path, platform, dl_hook)
            if not downloaded_file or not os.path.exists(downloaded_file):
                raise Exception("Local download failed")
                
            with _upload_lock:
                upload_progress_data[upload_id].update({
                    'status': 'uploading',
                    'progress': 50,
                    'downloaded': '100%',
                    'speed': '0 B/s'
                })
            
            # Setup YouTube API Uploader
            result = upload_to_youtube(
                downloaded_file,
                access_token,
                title,
                description,
                tags,
                privacy,
                upload_id,
                upload_progress_data
            )
            
            # Clean up local file
            cleanup_video_file(downloaded_file)
                
            # Save upload event to history
            history_data = {
                'title': title,
                'platform': platform,
                'video_url': url,
                'youtube_url': result,
                'timestamp': time.time()
            }
            add_to_history(user_email_dir, history_data)
            
            with _upload_lock:
                upload_progress_data[upload_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'youtube_url': result
                })
        except Exception as e:
            logging.error(f"Upload task thread error: {e}")
            with _upload_lock:
                upload_progress_data[upload_id].update({
                    'status': 'error',
                    'error': str(e)
                })

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    
    return upload_id

def get_upload_progress(upload_id):
    """Retrieve current upload progress data"""
    with _upload_lock:
        return upload_progress_data.get(upload_id)

async def generate_upload_sse_stream(upload_id):
    """Generate Server-Sent Events (SSE) stream for upload progress (non-blocking)."""
    heartbeat_interval = 15  # seconds
    last_update_time = time.time()
    while True:
        data = get_upload_progress(upload_id)
        if not data:
            yield f"data: {json.dumps({'status': 'error', 'error': 'Upload progress not found'})}\n\n"
            break

        yield f"data: {json.dumps(data)}\n\n"
        last_update_time = time.time()

        if data.get('status') in ['completed', 'error', 'cancelled']:
            break

        # Sleep in small increments to check for heartbeat eligibility
        elapsed = 0.0
        while elapsed < 0.5:
            await asyncio.sleep(0.5)
            elapsed += 0.5
            if time.time() - last_update_time >= heartbeat_interval:
                yield ": heartbeat\n\n"
                last_update_time = time.time()

def cleanup_video_file(video_file):
    """Clean up downloaded video file"""
    try:
        if os.path.exists(video_file):
            os.remove(video_file)
            logging.info(f"Cleaned up video file: {video_file}")
    except Exception as e:
        logging.error(f"Error cleaning up video file {video_file}: {e}")

import os
import time
import json
import logging
import feedparser
import re
import requests
from datetime import datetime
from backend.database.json_db import (
    get_user_tokens,
    store_user_tokens as store_tokens_db,
    get_user_settings,
    get_user_channels,
    save_user_channels,
    get_automation_logs,
    save_automation_logs
)
from backend.platforms import (
    download_from_platform,
    get_platform_from_url
)
from backend.platforms import extract_platform_metadata # For parsing video details
from backend.services.auth_service import get_user_info, refresh_access_token
from backend.services.uploader_service import upload_to_youtube

def get_stored_user_tokens(user_email_dir):
    """Retrieve stored tokens from local DB"""
    try:
        tokens = get_user_tokens(user_email_dir)
        if tokens:
            return tokens.get('access_token'), tokens.get('refresh_token')
        return None, None
    except Exception:
        return None, None

def store_user_tokens(user_email_dir, access_token, refresh_token):
    """Store tokens into local DB"""
    try:
        store_tokens_db(user_email_dir, access_token, refresh_token)
    except Exception as e:
        logging.error(f"Error storing user tokens: {e}")

def add_automation_log(user_id, log_type, message, flush=False):
    """Add a new log message to the automation logs synchronously"""
    try:
        logs_data = get_automation_logs(user_id)
        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': time.time() * 1000,
            'type': log_type,
            'message': f"[{formatted_time}] {message}"
        }
        
        # If flush is True, replace the last message if it's a countdown
        if flush and logs_data.get('logs') and '⏳ Cooldown:' in logs_data['logs'][-1].get('message', ''):
            logs_data['logs'][-1] = log_entry
        else:
            if 'logs' not in logs_data:
                logs_data['logs'] = []
            logs_data['logs'].append(log_entry)
            
        # Limit to last 1000 logs
        if len(logs_data['logs']) > 1000:
            logs_data['logs'] = logs_data['logs'][-1000:]
            
        save_automation_logs(user_id, logs_data)
    except Exception as e:
        logging.error(f"Error writing automation log: {e}")

def set_automation_service_status(user_id, status):
    """Update background service active status"""
    try:
        logs_data = get_automation_logs(user_id)
        logs_data['service_status'] = status
        save_automation_logs(user_id, logs_data)
    except Exception as e:
        logging.error(f"Error setting automation service status: {e}")

def check_channel_video_count_rss(channel_id):
    """Check total recent video entries in channel RSS feed"""
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return len(feed.entries)
        return 0
    except Exception as e:
        logging.error(f"RSS feed check failed for channel {channel_id}: {e}")
        return 0

def get_channel_latest_videos_rss(channel_id, limit=3):
    """Fetch latest videos from a channel via RSS"""
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(rss_url)
        videos = []
        for entry in feed.entries[:limit]:
            videos.append({
                'video_id': entry.yt_videoid if hasattr(entry, 'yt_videoid') else entry.id.split(':')[-1],
                'title': entry.title,
                'published': entry.published,
                'url': entry.link,
                'thumbnail': f"https://i.ytimg.com/vi/{entry.yt_videoid}/mqdefault.jpg" if hasattr(entry, 'yt_videoid') else ''
            })
        return videos
    except Exception as e:
        logging.error(f"RSS video fetch failed: {e}")
        return []

def process_video_for_automation(user_id, video_url, video_title, video_metadata):
    """Process a single video download and upload to YouTube in automation context"""
    try:
        access_token, refresh_token = get_stored_user_tokens(user_id)
        if not access_token:
            raise Exception("No stored access token for uploader")
            
        # Test/refresh access token
        try:
            get_user_info(access_token)
        except Exception:
            if refresh_token:
                try:
                    access_token = refresh_access_token(refresh_token)
                    store_user_tokens(user_id, access_token, refresh_token)
                except Exception:
                    raise Exception("Access token refresh failed")
            else:
                raise Exception("Access token expired and no refresh token available")
                
        platform = get_platform_from_url(video_url)
        download_path = os.path.join('db', user_id, 'downloads')
        os.makedirs(download_path, exist_ok=True)
        
        # Download the file
        downloaded_file = download_from_platform(video_url, download_path, platform)
        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Video download failed")
            
        # Setup upload attributes
        upload_title = video_title
        upload_description = f"Original video from {platform.upper()}\n\n{video_metadata.get('description', '')}"
        upload_tags = video_metadata.get('tags', [])
        upload_privacy = 'public'
        
        upload_id = f"auto_{user_id}_{int(time.time())}"
        progress_data = {upload_id: {'status': 'uploading', 'progress': 0}}
        
        # Upload
        youtube_url = upload_to_youtube(
            downloaded_file,
            access_token,
            upload_title,
            upload_description,
            upload_tags,
            upload_privacy,
            upload_id,
            progress_data
        )
        
        # Clean up
        try:
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
        except:
            pass
            
        return youtube_url
    except Exception as e:
        logging.error(f"Error processing video in automation worker: {e}")
        raise

def automation_monitor_worker(user_id):
    """Background monitoring service loop that continuously monitors channels and downloads/uploads new videos"""
    try:
        set_automation_service_status(user_id, True)
        add_automation_log(user_id, 'success', '🚀 Started Monitoring Service')
        
        while True:
            # Check database for active status check
            logs_data = get_automation_logs(user_id)
            if not logs_data.get('service_status', False):
                break
                
            settings = get_user_settings(user_id)
            api_key = settings.get('api_key')
            monitor_interval = settings.get('monitor_interval', 300)
            
            channels_data = get_user_channels(user_id)
            channels = channels_data.get('channels', [])
            
            if not channels:
                add_automation_log(user_id, 'warning', 'No channels configured for monitoring. Sleeping...')
                time.sleep(10)
                continue
                
            channel_names = [ch.get('name', 'Unknown') for ch in channels]
            add_automation_log(user_id, 'info', f"🔍 Checking channels: {', '.join(channel_names)}")
            
            total_new_videos = 0
            new_videos_found = []
            
            for i, channel in enumerate(channels):
                # Verify status check in-between channel queries
                current_status = get_automation_logs(user_id)
                if not current_status.get('service_status', False):
                    break
                    
                channel_name = channel.get('name', 'Unknown')
                channel_id = channel.get('channel_id', '')
                
                try:
                    current_video_count = 0
                    try:
                        from backend.services.auth_service import get_channel_details_api_v3
                        channel_details = get_channel_details_api_v3(channel_id, api_key)
                        current_video_count = channel_details.get('video_count', 0)
                    except Exception:
                        current_video_count = check_channel_video_count_rss(channel_id)
                        
                    last_known_count = channel.get('last_video_count', 0)
                    
                    if current_video_count > last_known_count:
                        new_videos_count = current_video_count - last_known_count
                        total_new_videos += new_videos_count
                        
                        channels[i]['last_video_count'] = current_video_count
                        channels[i]['last_checked'] = time.time()
                        
                        # Fetch new videos details
                        try:
                            from backend.services.auth_service import get_channel_latest_videos_api_v3
                            latest_videos = get_channel_latest_videos_api_v3(channel_id, api_key, new_videos_count)
                        except Exception:
                            latest_videos = get_channel_latest_videos_rss(channel_id, new_videos_count)
                            
                        for video in latest_videos:
                            add_automation_log(user_id, 'info', f"📄 Extracting video details: {video.get('title', 'Unknown')}")
                            try:
                                metadata = extract_platform_metadata(video.get('url', ''))
                                add_automation_log(user_id, 'success', f"✅ Extracted metadata: {metadata.get('title', 'Unknown')}")
                                new_videos_found.append({
                                    'url': video.get('url', ''),
                                    'title': metadata.get('title', video.get('title', 'Unknown')),
                                    'metadata': metadata
                                })
                            except Exception as me:
                                add_automation_log(user_id, 'error', f"❌ Metadata extraction failed: {me}")
                    elif current_video_count < last_known_count:
                        channels[i]['last_video_count'] = current_video_count
                        
                except Exception as ce:
                    add_automation_log(user_id, 'error', f"❌ Error querying channel {channel_name}: {ce}")
                    
            if total_new_videos > 0:
                add_automation_log(user_id, 'info', f"📊 Found {total_new_videos} new video(s) for processing.")
                
            # Process video list
            for idx, video in enumerate(new_videos_found):
                # Double-check stop condition
                current_status = get_automation_logs(user_id)
                if not current_status.get('service_status', False):
                    break
                    
                video_title = video['title']
                add_automation_log(user_id, 'info', f"⬇️ Download & Upload start [{idx+1}/{len(new_videos_found)}]: {video_title}")
                try:
                    youtube_url = process_video_for_automation(user_id, video['url'], video_title, video['metadata'])
                    add_automation_log(user_id, 'success', f"✅ Completed download and upload: {youtube_url}")
                except Exception as pe:
                    add_automation_log(user_id, 'error', f"❌ Failed processing video: {pe}")
                    
            # Save final channel updates
            save_user_channels(user_id, channels_data)
            
            # Cooldown wait timer with countdown log streams
            remaining = monitor_interval
            add_automation_log(user_id, 'info', f"⏰ STARTING COOLDOWN: {monitor_interval} seconds")
            
            while remaining > 0:
                # Double-check status flag every second
                current_status = get_automation_logs(user_id)
                if not current_status.get('service_status', False):
                    break
                    
                mins = remaining // 60
                secs = remaining % 60
                msg = f"⏳ Cooldown: {mins}m {secs}s remaining" if mins > 0 else f"⏳ Cooldown: {secs}s remaining"
                add_automation_log(user_id, 'info', msg, flush=True)
                
                time.sleep(1)
                remaining -= 1
                
            # Loop check status exit
            current_status = get_automation_logs(user_id)
            if not current_status.get('service_status', False):
                break
                
    except Exception as e:
        add_automation_log(user_id, 'error', f"💥 Automation monitor crashed: {e}")
    finally:
        set_automation_service_status(user_id, False)
        add_automation_log(user_id, 'info', '🛑 Monitoring service stopped')

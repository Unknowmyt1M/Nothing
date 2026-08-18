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
    get_user_settings as json_get_settings,
    get_user_channels as json_get_channels,
    save_user_channels as json_save_channels,
    get_automation_logs as json_get_logs,
    save_automation_logs as json_save_logs,
)
from backend.database.supabase_client import supabase
from backend.platforms import (
    download_from_platform,
    get_platform_from_url
)
from backend.platforms import extract_platform_metadata
from backend.services.auth_service import get_user_info, refresh_access_token
from backend.services.uploader_service import upload_to_youtube
from backend.utils.helpers import get_temp_dir

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
    """Add a new log message to the automation logs. Writes to Supabase when configured, falls back to JSON."""
    try:
        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S")
        full_message = f"[{formatted_time}] {message}"

        if supabase.is_configured:
            try:
                supabase.insert("automation_logs", {
                    "user_id": user_id,
                    "level": log_type,
                    "message": full_message,
                })
                return
            except Exception as e:
                logging.warning("Supabase log write failed, using JSON: %s", e)

        logs_data = json_get_logs(user_id)
        log_entry = {
            'timestamp': time.time() * 1000,
            'type': log_type,
            'message': full_message,
        }
        if flush and logs_data.get('logs') and '⏳ Cooldown:' in logs_data['logs'][-1].get('message', ''):
            logs_data['logs'][-1] = log_entry
        else:
            if 'logs' not in logs_data:
                logs_data['logs'] = []
            logs_data['logs'].append(log_entry)
        if len(logs_data['logs']) > 1000:
            logs_data['logs'] = logs_data['logs'][-1000:]
        json_save_logs(user_id, logs_data)
    except Exception as e:
        logging.error(f"Error writing automation log: {e}")


def set_automation_service_status(user_id, status):
    """Update background service active status. Writes to Supabase when configured."""
    if supabase.is_configured:
        try:
            existing = supabase.select(
                "automation_status",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if existing:
                supabase.update("automation_status", {"is_active": status}, {"user_id": f"eq.{user_id}"})
            else:
                supabase.insert("automation_status", {"user_id": user_id, "is_active": status})
            return
        except Exception as e:
            logging.warning("Supabase status write failed, using JSON: %s", e)
    try:
        logs_data = json_get_logs(user_id)
        logs_data['service_status'] = status
        json_save_logs(user_id, logs_data)
    except Exception as e:
        logging.error(f"Error setting automation service status: {e}")


def get_automation_service_status(user_id):
    """Read current service status. Checks Supabase first, falls back to JSON."""
    if supabase.is_configured:
        try:
            results = supabase.select(
                "automation_status",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if results:
                return bool(results[0].get("is_active", False))
        except Exception:
            pass
    try:
        logs_data = json_get_logs(user_id)
        return bool(logs_data.get("service_status", False))
    except Exception:
        return False


def get_automation_settings(user_id):
    """Read settings. Checks Supabase first, falls back to JSON."""
    if supabase.is_configured:
        try:
            results = supabase.select(
                "user_settings",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if results:
                return results[0]
        except Exception:
            pass
    return json_get_settings(user_id)


def get_automation_channels(user_id):
    """Read monitored channels. Checks Supabase first, falls back to JSON."""
    if supabase.is_configured:
        try:
            results = supabase.select(
                "monitored_channels",
                filters={"user_id": f"eq.{user_id}", "is_active": "eq.true"},
            )
            channels = []
            for ch in results:
                channels.append({
                    "channel_id": ch.get("channel_id", ""),
                    "name": ch.get("channel_name", ""),
                    "logo_url": ch.get("channel_thumbnail", ""),
                    "monitor_interval": 300,
                    "quality": "1080p",
                    "total_videos": ch.get("video_count", 0),
                    "last_video_count": ch.get("video_count", 0),
                    "last_checked": None,
                    "_db_id": ch.get("id"),
                })
            return {"channels": channels}
        except Exception:
            pass
    return json_get_channels(user_id)


def save_automation_channels(user_id, channels_data):
    """Save channel updates. Writes to Supabase when configured."""
    if supabase.is_configured:
        try:
            for ch in channels_data.get("channels", []):
                db_id = ch.get("_db_id")
                if db_id:
                    supabase.update("monitored_channels", {
                        "video_count": ch.get("last_video_count", 0),
                    }, {"id": f"eq.{db_id}"})
            return
        except Exception as e:
            logging.warning("Supabase channel save failed: %s", e)
    json_save_channels(user_id, channels_data)

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
        download_path = get_temp_dir("auto_downloads")
        
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
            if not get_automation_service_status(user_id):
                break
                
            settings = get_automation_settings(user_id)
            api_key = settings.get('api_key')
            monitor_interval = settings.get('monitor_interval', 300)
            
            channels_data = get_automation_channels(user_id)
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
                if not get_automation_service_status(user_id):
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
                
            for idx, video in enumerate(new_videos_found):
                if not get_automation_service_status(user_id):
                    break
                    
                video_title = video['title']
                add_automation_log(user_id, 'info', f"⬇️ Download & Upload start [{idx+1}/{len(new_videos_found)}]: {video_title}")
                try:
                    youtube_url = process_video_for_automation(user_id, video['url'], video_title, video['metadata'])
                    add_automation_log(user_id, 'success', f"✅ Completed download and upload: {youtube_url}")
                except Exception as pe:
                    add_automation_log(user_id, 'error', f"❌ Failed processing video: {pe}")
                    
            save_automation_channels(user_id, channels_data)
            
            remaining = monitor_interval
            add_automation_log(user_id, 'info', f"⏰ STARTING COOLDOWN: {monitor_interval} seconds")
            
            while remaining > 0:
                if not get_automation_service_status(user_id):
                    break
                    
                mins = remaining // 60
                secs = remaining % 60
                msg = f"⏳ Cooldown: {mins}m {secs}s remaining" if mins > 0 else f"⏳ Cooldown: {secs}s remaining"
                add_automation_log(user_id, 'info', msg, flush=True)
                
                time.sleep(1)
                remaining -= 1
                
            if not get_automation_service_status(user_id):
                break
                
    except Exception as e:
        add_automation_log(user_id, 'error', f"💥 Automation monitor crashed: {e}")
    finally:
        set_automation_service_status(user_id, False)
        add_automation_log(user_id, 'info', '🛑 Monitoring service stopped')

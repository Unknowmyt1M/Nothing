import os
import json
import requests
import secrets
from urllib.parse import urlencode
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load client secrets from environment variables
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not found. Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables.")

# OAuth URLs
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

# Scopes for YouTube upload
SCOPES = [
    'openid',
    'email',
    'profile',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

def get_redirect_uri():
    domain = os.getenv("SITE_URL", "http://localhost:5000")
    return f"{domain}/google_login/callback"


def get_google_auth_url():
    """Generate Google OAuth authorization URL"""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': get_redirect_uri(),
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

def handle_google_callback(code):
    """Handle OAuth callback and exchange code for tokens"""
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': get_redirect_uri()
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()
    
    return response.json()

def refresh_access_token(refresh_token):
    """Refresh access token using refresh token"""
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    return token_data['access_token']

def get_user_info(access_token):
    """Get user information from Google"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    response.raise_for_status()
    
    return response.json()

def get_youtube_channel_info(access_token):
    """Get YouTube channel information"""
    url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'part': 'snippet,statistics',
        'mine': 'true'
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    if data['items']:
        return data['items'][0]
    else:
        raise Exception("No YouTube channel found for this account")

def get_youtube_api_service(access_token):
    """Get YouTube API service object"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        # Create credentials object
        credentials = Credentials(token=access_token)
        
        # Build and return YouTube service
        youtube = build('youtube', 'v3', credentials=credentials)
        return youtube
        
    except ImportError:
        raise Exception("Google API client library not installed. Please install google-api-python-client.")
    except Exception as e:
        raise Exception(f"Failed to create YouTube API service: {str(e)}")

def get_channel_details_api_v3(channel_id_or_url, api_key=None):
    """Get channel details using YouTube API v3"""
    import re
    
    # Extract channel ID from URL if needed
    channel_id = channel_id_or_url
    if 'youtube.com' in channel_id_or_url:
        if '/channel/' in channel_id_or_url:
            channel_id = channel_id_or_url.split('/channel/')[-1].split('?')[0]
        elif '/@' in channel_id_or_url:
            # For @username format, we need to resolve it
            response = requests.get(channel_id_or_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            channel_id_match = re.search(r'"channelId":"([^"]+)"', response.text)
            if channel_id_match:
                channel_id = channel_id_match.group(1)
            else:
                raise Exception('Could not extract channel ID from @username URL')
        elif '/c/' in channel_id_or_url or '/user/' in channel_id_or_url:
            # Handle custom URLs
            response = requests.get(channel_id_or_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            channel_id_match = re.search(r'"channelId":"([^"]+)"', response.text)
            if channel_id_match:
                channel_id = channel_id_match.group(1)
            else:
                raise Exception('Could not extract channel ID from custom URL')
    
    # Use API key priority: user provided > environment variable
    if not api_key:
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            raise Exception('YouTube API key not found. Please provide API key in settings.')
    
    # Fetch channel details using YouTube API v3
    api_url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'part': 'snippet,statistics',
        'id': channel_id,
        'key': api_key
    }
    
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get('items'):
        raise Exception('Channel not found or API request failed')
    
    channel_info = data['items'][0]
    snippet = channel_info['snippet']
    statistics = channel_info['statistics']
    
    # Format subscriber count
    subscriber_count = int(statistics.get('subscriberCount', 0))
    if subscriber_count >= 1_000_000:
        subscribers = f"{subscriber_count / 1_000_000:.1f}M subscribers"
    elif subscriber_count >= 1_000:
        subscribers = f"{subscriber_count / 1_000:.1f}K subscribers"
    else:
        subscribers = f"{subscriber_count} subscribers"
    
    return {
        'channel_id': channel_id,
        'name': snippet.get('title', 'Unknown Channel'),
        'logo_url': snippet.get('thumbnails', {}).get('high', {}).get('url', 
                    f"https://yt3.ggpht.com/a/default-user=s800-c-k-c0x00ffffff-no-rj"),
        'subscribers': subscribers,
        'subscriber_count': subscriber_count,
        'video_count': int(statistics.get('videoCount', 0)),
        'view_count': int(statistics.get('viewCount', 0)),
        'description': snippet.get('description', ''),
        'published_at': snippet.get('publishedAt', ''),
        'country': snippet.get('country', ''),
        'custom_url': snippet.get('customUrl', '')
    }

def get_channel_latest_videos_api_v3(channel_id, api_key=None, max_results=3):
    """Get latest videos from a channel using YouTube API v3"""
    
    # Use API key priority: user provided > environment variable  
    if not api_key:
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            raise Exception('YouTube API key not found. Please provide API key in settings.')
    
    # Fetch latest videos using YouTube API v3
    api_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'channelId': channel_id,
        'order': 'date',
        'type': 'video',
        'maxResults': max_results,
        'key': api_key
    }
    
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    videos = []
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        snippet = item['snippet']
        
        videos.append({
            'video_id': video_id,
            'title': snippet.get('title', 'Unknown Title'),
            'description': snippet.get('description', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'channel_title': snippet.get('channelTitle', '')
        })
    
    return videos

def get_channel_info_with_videos_api_v3(channel_id_or_url, api_key=None):
    """Get complete channel information including latest videos using YouTube API v3"""
    
    # Get channel details
    channel_details = get_channel_details_api_v3(channel_id_or_url, api_key)
    
    # Get latest videos
    latest_videos = get_channel_latest_videos_api_v3(channel_details['channel_id'], api_key, 3)
    
    # Combine both
    channel_details['latest_videos'] = latest_videos
    channel_details['total_videos'] = channel_details['video_count']
    
    return channel_details

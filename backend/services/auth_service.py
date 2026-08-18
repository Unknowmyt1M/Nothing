"""Google OAuth + Supabase Auth service layer.

Handles authorization URL generation, token exchange, token refresh, and
YouTube channel lookups. Supports both direct Google OAuth and Supabase Auth.
"""
import os
import re
import requests
import logging
import jwt
from urllib.parse import urlencode
from typing import Optional, Dict, Any

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    YOUTUBE_API_KEY,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)
from backend.database.json_db import store_user_tokens as json_store_tokens

logger = logging.getLogger(__name__)

# OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes for YouTube upload + analytics
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def get_redirect_uri() -> str:
    """Points to the API callback route."""
    return GOOGLE_REDIRECT_URI


def get_google_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": get_redirect_uri(),
        "scope": " ".join(SCOPES),
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def handle_google_callback(code: str) -> Dict[str, Any]:
    """Handle OAuth callback and exchange code for tokens."""
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": get_redirect_uri(),
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> str:
    """Refresh access token using refresh token."""
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]


def get_user_info(access_token: str) -> Dict[str, Any]:
    """Get user information from Google."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def get_youtube_channel_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Get YouTube channel information for logged-in user."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "snippet,statistics", "mine": "true"}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    if data.get("items"):
        return data["items"][0]
    raise Exception("No YouTube channel found for this account")


def get_youtube_api_service(access_token: str):
    """Get YouTube API service object."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=access_token)
        return build("youtube", "v3", credentials=credentials)
    except ImportError:
        raise Exception("Google API client library not installed. Please install google-api-python-client.")
    except Exception as e:
        raise Exception(f"Failed to create YouTube API service: {str(e)}")


# ---------------------------------------------------------------------------
# Supabase Auth helpers
# ---------------------------------------------------------------------------
def verify_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Supabase JWT and return the payload.

    Uses the JWT secret from Supabase to validate the token signature,
    expiration, and audience claims. Falls back to unsigned decode in
    development when the secret is not configured (with a warning).
    """
    if not token:
        return None

    from backend.config import SUPABASE_JWT_SECRET

    try:
        if SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            logger.warning(
                "SUPABASE_JWT_SECRET not set – decoding JWT WITHOUT signature "
                "verification. This is insecure and must not happen in production."
            )
            payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Supabase JWT has expired")
        return None
    except jwt.InvalidAudienceError:
        logger.warning("Supabase JWT has invalid audience")
        return None
    except Exception as e:
        logger.warning("Failed to decode Supabase JWT: %s", e)
        return None


def get_supabase_user(token: str) -> Optional[Dict[str, Any]]:
    """Get user info from Supabase using their JWT."""
    if not SUPABASE_URL or not token:
        return None
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {token}",
    }
    resp = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return None


def get_supabase_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user info from Supabase admin API by user ID."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
        headers=headers,
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def get_google_provider_token(supabase_user_id: str) -> Optional[Dict[str, Any]]:
    """Get the Google OAuth provider token for a Supabase user.
    
    This retrieves the stored Google access/refresh tokens from Supabase's
    identity data so the backend can make YouTube API calls.
    """
    user = get_supabase_user_by_id(supabase_user_id)
    if not user:
        return None
    
    identities = user.get("identities", [])
    for identity in identities:
        if identity.get("provider") == "google":
            data = identity.get("data", {})
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_at": data.get("expires_at"),
                "email": data.get("email"),
                "name": data.get("full_name") or data.get("name"),
                "avatar_url": data.get("avatar_url"),
            }
    return None


# ---------------------------------------------------------------------------
# Channel details via YouTube Data API v3
# ---------------------------------------------------------------------------
def _resolve_channel_id(channel_id_or_url: str) -> str:
    """Extract a plain channel ID from various YouTube URL forms."""
    channel_id = channel_id_or_url
    if "youtube.com" not in channel_id_or_url and "youtu.be" not in channel_id_or_url:
        return channel_id

    if "/channel/" in channel_id_or_url:
        channel_id = channel_id_or_url.split("/channel/")[-1].split("?")[0]
    else:
        response = requests.get(
            channel_id_or_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15,
        )
        response.raise_for_status()
        match = re.search(r'"channelId":"([^"]+)"', response.text)
        if match:
            channel_id = match.group(1)
        else:
            raise Exception("Could not extract channel ID from URL")
    return channel_id


def get_channel_details_api_v3(channel_id_or_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Get channel details using YouTube API v3."""
    channel_id = _resolve_channel_id(channel_id_or_url)

    if not api_key:
        api_key = YOUTUBE_API_KEY
    if not api_key:
        raise Exception("YouTube API key not found. Please provide API key in settings.")

    api_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "snippet,statistics", "id": channel_id, "key": api_key}
    response = requests.get(api_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if not data.get("items"):
        raise Exception("Channel not found or API request failed")

    channel_info = data["items"][0]
    snippet = channel_info["snippet"]
    statistics = channel_info["statistics"]

    subscriber_count = int(statistics.get("subscriberCount", 0))
    if subscriber_count >= 1_000_000:
        subscribers = f"{subscriber_count / 1_000_000:.1f}M subscribers"
    elif subscriber_count >= 1_000:
        subscribers = f"{subscriber_count / 1_000:.1f}K subscribers"
    else:
        subscribers = f"{subscriber_count} subscribers"

    return {
        "channel_id": channel_id,
        "name": snippet.get("title", "Unknown Channel"),
        "logo_url": snippet.get("thumbnails", {}).get("high", {}).get(
            "url", "https://yt3.ggpht.com/a/default-user=s800-c-k-c0x00ffffff-no-rj"
        ),
        "subscribers": subscribers,
        "subscriber_count": subscriber_count,
        "video_count": int(statistics.get("videoCount", 0)),
        "view_count": int(statistics.get("viewCount", 0)),
        "description": snippet.get("description", ""),
        "published_at": snippet.get("publishedAt", ""),
        "country": snippet.get("country", ""),
        "custom_url": snippet.get("customUrl", ""),
    }


def get_channel_latest_videos_api_v3(channel_id: str, api_key: Optional[str] = None, max_results: int = 3) -> list:
    """Get latest videos from a channel using YouTube API v3."""
    if not api_key:
        api_key = YOUTUBE_API_KEY
    if not api_key:
        raise Exception("YouTube API key not found. Please provide API key in settings.")

    api_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
    }
    response = requests.get(api_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        videos.append({
            "video_id": video_id,
            "title": snippet.get("title", "Unknown Title"),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel_title": snippet.get("channelTitle", ""),
        })
    return videos


def get_channel_info_with_videos_api_v3(channel_id_or_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Get complete channel information including latest videos."""
    channel_details = get_channel_details_api_v3(channel_id_or_url, api_key)
    latest_videos = get_channel_latest_videos_api_v3(channel_details["channel_id"], api_key, 3)
    channel_details["latest_videos"] = latest_videos
    channel_details["total_videos"] = channel_details["video_count"]
    return channel_details
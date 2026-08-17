"""Centralized configuration for the UpDownVid backend.

Loads environment variables with sensible defaults. All configuration is
imported from this single module so services can share consistent settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


# Server configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 3000))
DEBUG = _env_bool("DEBUG", True)

# The frontend (Next.js dev server) URL used for OAuth redirects back
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5000")

# Backend public base URL (used to build the Google OAuth redirect URI).
# Defaults to localhost:3000 which is how main.py proxies the API today.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:3000")

# Session signing secret for SessionMiddleware
SESSION_SECRET = os.environ.get(
    "SESSION_SECRET", "dev-secret-key-change-in-production"
)

# Allowed CORS origins (comma separated). Session/auth requires the exact host.
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5000,http://127.0.0.1:5000",
).split(",") if o.strip()]

# Google OAuth credentials
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:3000/api/auth/google_login/callback",
)

# YouTube API key (used for channel automation + channel info)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Download / upload limits
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", "20971520"))  # 20MB for direct URL downloads
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
COOKIES_DIR = os.environ.get("COOKIES_DIR", "cookies")

# SSE configuration
SSE_HEARTBEAT_INTERVAL = int(os.environ.get("SSE_HEARTBEAT_INTERVAL", "15"))  # seconds
SSE_POLL_INTERVAL = float(os.environ.get("SSE_POLL_INTERVAL", "0.5"))         # seconds

# Runtime flag used by platform modules / services
IS_PRODUCTION = _env_bool("IS_PRODUCTION", False)

__all__ = [
    "HOST", "PORT", "DEBUG", "FRONTEND_URL", "BACKEND_URL",
    "SESSION_SECRET", "CORS_ORIGINS",
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI",
    "YOUTUBE_API_KEY",
    "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY",
    "MAX_UPLOAD_SIZE", "DOWNLOAD_DIR", "COOKIES_DIR",
    "SSE_HEARTBEAT_INTERVAL", "SSE_POLL_INTERVAL", "IS_PRODUCTION",
]
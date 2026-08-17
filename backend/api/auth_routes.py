"""Google OAuth authentication routes (FastAPI).

Supports dual auth flows:
1. Legacy: Custom Google OAuth via /api/auth/google_login (backward compat)
2. Supabase: Google OAuth via Supabase Auth, synced via /api/auth/supabase_sync

Both flows persist tokens in session, JSON DB, and Supabase youtube_connections.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional

from backend.config import FRONTEND_URL
from backend.services.auth_service import (
    get_google_auth_url,
    handle_google_callback,
    get_user_info,
    refresh_access_token,
    get_youtube_channel_info,
    verify_supabase_jwt,
    get_google_provider_token,
)
from backend.database.json_db import store_user_tokens, save_oauth_tokens
from backend.database.supabase_client import supabase

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _user_id_from_email(email: str) -> str:
    return email.replace("@", "_").replace(".", "_")


def _sync_session_from_supabase(request: Request, user_id: str, google_tokens: dict, user_info: dict, youtube_channel: dict = None):
    """Persist Google tokens into session + JSON DB + Supabase. Returns response dict."""
    access_token = google_tokens.get("access_token")
    refresh_token = google_tokens.get("refresh_token")

    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    request.session["user_id"] = user_id
    request.session["user_name"] = user_info.get("name", "")
    request.session["user_email"] = user_info.get("email", "")
    request.session["supabase_user_id"] = user_id

    store_user_tokens(user_id, access_token, refresh_token)
    save_oauth_tokens(user_id, google_tokens)

    if supabase.is_configured:
        try:
            connection_data = {
                "user_id": user_id,
                "google_user_id": user_info.get("id", ""),
                "google_email": user_info.get("email", ""),
                "google_name": user_info.get("name", ""),
                "google_avatar_url": user_info.get("picture", ""),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_scope": "openid email profile youtube.upload youtube youtube.force-ssl youtube.readonly yt-analytics.readonly yt-analytics-monetary.readonly",
            }
            if youtube_channel:
                snippet = youtube_channel.get("snippet", {})
                stats = youtube_channel.get("statistics", {})
                connection_data.update({
                    "youtube_channel_id": youtube_channel.get("id", ""),
                    "youtube_channel_name": snippet.get("title", ""),
                    "youtube_channel_thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "youtube_subscriber_count": int(stats.get("subscriberCount", 0)),
                    "youtube_video_count": int(stats.get("videoCount", 0)),
                })
            supabase.upsert("youtube_connections", connection_data)
        except Exception as e:
            logger.warning("Failed to persist to Supabase: %s", e)

    return {
        "success": True,
        "user": {"name": user_info.get("name"), "email": user_info.get("email"), "picture": user_info.get("picture")},
        "youtube_channel": youtube_channel,
    }


class SupabaseCallbackBody(BaseModel):
    supabase_access_token: str


# ---------------------------------------------------------------------------
# Supabase OAuth endpoints (new flow)
# ---------------------------------------------------------------------------
@router.post("/auth/supabase_callback")
async def supabase_callback(request: Request, body: SupabaseCallbackBody):
    """Called by frontend after Supabase OAuth completes. Syncs tokens to backend."""
    try:
        payload = verify_supabase_jwt(body.supabase_access_token)
        if not payload:
            return JSONResponse({"error": "Invalid Supabase token"}, status_code=401)

        supabase_user_id = payload.get("sub")
        if not supabase_user_id:
            return JSONResponse({"error": "Invalid token payload"}, status_code=401)

        google_tokens = get_google_provider_token(supabase_user_id)
        if not google_tokens or not google_tokens.get("access_token"):
            return JSONResponse({"error": "No Google provider token found. Please reconnect your Google account in Supabase.", "code": "NO_GOOGLE_TOKEN"}, status_code=404)

        user_info = get_user_info(google_tokens["access_token"])
        user_id = _user_id_from_email(user_info["email"])

        youtube_channel = None
        try:
            youtube_channel = get_youtube_channel_info(google_tokens["access_token"])
        except Exception:
            pass

        result = _sync_session_from_supabase(request, user_id, google_tokens, user_info, youtube_channel)
        logger.info("Supabase OAuth synced for %s", user_id)
        return result
    except Exception as e:
        logger.error("Supabase callback error: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/auth/supabase_sync")
async def supabase_sync(request: Request, body: SupabaseCallbackBody):
    """Idempotent sync — called on page load if Supabase session exists."""
    try:
        payload = verify_supabase_jwt(body.supabase_access_token)
        if not payload:
            return JSONResponse({"error": "Invalid Supabase token"}, status_code=401)

        supabase_user_id = payload.get("sub")
        user_id_from_session = request.session.get("user_id")

        # If already synced with same user, return cached session data
        if user_id_from_session and request.session.get("access_token"):
            existing_name = request.session.get("user_name", "")
            existing_email = request.session.get("user_email", "")
            if existing_name or existing_email:
                youtube_channel = None
                try:
                    youtube_channel = get_youtube_channel_info(request.session["access_token"])
                except Exception:
                    pass
                return {
                    "success": True,
                    "user": {"name": existing_name, "email": existing_email, "picture": None},
                    "youtube_channel": youtube_channel,
                }

        # Not synced — perform full sync
        google_tokens = get_google_provider_token(supabase_user_id)
        if not google_tokens or not google_tokens.get("access_token"):
            return JSONResponse({"error": "No Google provider token found", "code": "NO_GOOGLE_TOKEN"}, status_code=404)

        user_info = get_user_info(google_tokens["access_token"])
        user_id = _user_id_from_email(user_info["email"])

        youtube_channel = None
        try:
            youtube_channel = get_youtube_channel_info(google_tokens["access_token"])
        except Exception:
            pass

        result = _sync_session_from_supabase(request, user_id, google_tokens, user_info, youtube_channel)
        logger.info("Supabase sync completed for %s", user_id)
        return result
    except Exception as e:
        logger.error("Supabase sync error: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Legacy Google OAuth endpoints (backward compatibility)
# ---------------------------------------------------------------------------
@router.get("/auth/google_login")
async def google_login():
    """Initiate Google OAuth login sequence."""
    try:
        auth_url = get_google_auth_url()
        return {"url": auth_url}
    except Exception as e:
        logger.error("Error generating auth url: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/auth/google_login/callback")
async def google_callback(request: Request, code: str = ""):
    """Handle Google OAuth callback redirect."""
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/accounts?error=Authorization+failed")

    try:
        tokens = handle_google_callback(code)
        request.session["access_token"] = tokens["access_token"]
        request.session["refresh_token"] = tokens.get("refresh_token")

        user_info = get_user_info(tokens["access_token"])
        user_email_dir = _user_id_from_email(user_info["email"])
        request.session["user_id"] = user_email_dir
        request.session["user_name"] = user_info["name"]
        request.session["user_email"] = user_info["email"]

        store_user_tokens(user_email_dir, tokens["access_token"], tokens.get("refresh_token"))
        save_oauth_tokens(user_email_dir, tokens)

        if supabase.is_configured:
            try:
                youtube_channel = None
                try:
                    youtube_channel = get_youtube_channel_info(tokens["access_token"])
                except Exception:
                    pass

                connection_data = {
                    "user_id": user_email_dir,
                    "google_user_id": user_info.get("id", ""),
                    "google_email": user_info.get("email", ""),
                    "google_name": user_info.get("name", ""),
                    "google_avatar_url": user_info.get("picture", ""),
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens.get("refresh_token"),
                    "token_scope": "openid email profile youtube.upload youtube youtube.force-ssl youtube.readonly yt-analytics.readonly yt-analytics-monetary.readonly",
                }
                if youtube_channel:
                    snippet = youtube_channel.get("snippet", {})
                    stats = youtube_channel.get("statistics", {})
                    connection_data.update({
                        "youtube_channel_id": youtube_channel.get("id", ""),
                        "youtube_channel_name": snippet.get("title", ""),
                        "youtube_channel_thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                        "youtube_subscriber_count": int(stats.get("subscriberCount", 0)),
                        "youtube_video_count": int(stats.get("videoCount", 0)),
                    })
                supabase.upsert("youtube_connections", connection_data)
            except Exception as e:
                logger.warning("Failed to save to Supabase: %s", e)

        logger.info("Google account connected for %s", user_email_dir)
        return RedirectResponse(f"{FRONTEND_URL}/accounts?connected=true")
    except Exception as e:
        logger.error("OAuth callback error: %s", e)
        return RedirectResponse(f"{FRONTEND_URL}/accounts?error={str(e)}")


@router.get("/auth/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    request.session.clear()
    return {"success": True, "message": "Successfully logged out"}


@router.get("/auth/status")
async def status(request: Request):
    """Get currently logged-in user credentials."""
    access_token = request.session.get("access_token")

    # If no access token, try recovering from Supabase user_id
    if not access_token:
        supabase_uid = request.session.get("supabase_user_id")
        if supabase_uid:
            try:
                google_tokens = get_google_provider_token(supabase_uid)
                if google_tokens and google_tokens.get("access_token"):
                    request.session["access_token"] = google_tokens["access_token"]
                    request.session["refresh_token"] = google_tokens.get("refresh_token")
                    access_token = google_tokens["access_token"]
                    user_info = get_user_info(access_token)
                    request.session["user_name"] = user_info.get("name", "")
                    request.session["user_email"] = user_info.get("email", "")
                    request.session["user_id"] = _user_id_from_email(user_info["email"])
            except Exception:
                pass

    if not access_token:
        return {"authenticated": False, "user": None}

    try:
        user_info = get_user_info(access_token)
        youtube_channel = None
        try:
            youtube_channel = get_youtube_channel_info(access_token)
        except Exception:
            pass

        supabase_connection = None
        if supabase.is_configured:
            try:
                results = supabase.select(
                    "youtube_connections",
                    filters={"user_id": f"eq.{request.session.get('user_id', '')}"},
                    limit=1,
                )
                if results:
                    supabase_connection = results[0]
            except Exception:
                pass

        return {
            "authenticated": True,
            "user": {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "picture": user_info.get("picture"),
            },
            "youtube_channel": youtube_channel,
            "supabase_connection": supabase_connection,
        }
    except Exception as e:
        refresh_token = request.session.get("refresh_token")
        if refresh_token:
            try:
                new_token = refresh_access_token(refresh_token)
                request.session["access_token"] = new_token
                user_info = get_user_info(new_token)
                youtube_channel = None
                try:
                    youtube_channel = get_youtube_channel_info(new_token)
                except Exception:
                    pass
                return {
                    "authenticated": True,
                    "user": {
                        "name": user_info.get("name"),
                        "email": user_info.get("email"),
                        "picture": user_info.get("picture"),
                    },
                    "youtube_channel": youtube_channel,
                }
            except Exception as re:
                logger.error("Failed token refresh: %s", re)

        request.session.clear()
        return {"authenticated": False, "user": None, "error": "Session expired"}
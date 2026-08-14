"""Google OAuth authentication routes (FastAPI).

Maintains the same URL contract as the original Flask blueprints while
persisting login state via Starlette's signed-cookie SessionMiddleware.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.config import FRONTEND_URL
from backend.services.auth_service import (
    get_google_auth_url,
    handle_google_callback,
    get_user_info,
    refresh_access_token,
    get_youtube_channel_info,
)
from backend.database.json_db import store_user_tokens, save_oauth_tokens

logger = logging.getLogger(__name__)

router = APIRouter()


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
        user_email_dir = user_info["email"].replace("@", "_").replace(".", "_")
        request.session["user_id"] = user_email_dir
        request.session["user_name"] = user_info["name"]
        request.session["user_email"] = user_info["email"]

        # Persist tokens in the local JSON database (keeps existing data usable)
        store_user_tokens(user_email_dir, tokens["access_token"], tokens.get("refresh_token"))
        save_oauth_tokens(user_email_dir, tokens)

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
    if not access_token:
        return {"authenticated": False, "user": None}

    try:
        user_info = get_user_info(access_token)
        youtube_channel = None
        try:
            youtube_channel = get_youtube_channel_info(access_token)
        except Exception:
            pass  # optional channel info

        return {
            "authenticated": True,
            "user": {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "picture": user_info.get("picture"),
            },
            "youtube_channel": youtube_channel,
        }
    except Exception as e:
        # Token might have expired — try refresh
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
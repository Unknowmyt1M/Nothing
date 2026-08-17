"""FastAPI authentication dependency.

Provides `get_current_user()` which validates the Supabase JWT from
the session cookie and returns the authenticated user payload.
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException

from backend.services.auth_service import verify_supabase_jwt, get_supabase_user

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency that extracts and validates the authenticated user.
    
    Checks the session for a Supabase access token and verifies it.
    Raises HTTPException 401 if not authenticated.
    
    Returns:
        dict with keys: user_id, email, name, avatar_url, access_token
    """
    # Check session for Supabase access token
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")
    user_id = request.session.get("user_id")
    
    if not access_token or not user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": True,
                "code": "AUTHENTICATION_REQUIRED",
                "title": "Login required",
                "message": "You must be signed in to access this resource.",
                "retryable": False,
            },
        )
    
    # Try to get user info from session
    user_info = {
        "user_id": user_id,
        "email": request.session.get("user_email", ""),
        "name": request.session.get("user_name", ""),
        "avatar_url": request.session.get("user_avatar", ""),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    
    # Validate the token is still good by checking Supabase
    supabase_user = get_supabase_user(access_token)
    if supabase_user:
        user_info["email"] = supabase_user.get("email", user_info["email"])
        user_info["name"] = supabase_user.get("user_metadata", {}).get("full_name", user_info["name"])
        user_info["avatar_url"] = supabase_user.get("user_metadata", {}).get("avatar_url", user_info["avatar_url"])
    else:
        # Token might be expired — the caller should handle refresh
        logger.warning("Could not validate Supabase token for user %s", user_id)
    
    return user_info


async def get_optional_user(request: Request) -> Optional[dict]:
    """Like get_current_user but returns None instead of raising 401."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

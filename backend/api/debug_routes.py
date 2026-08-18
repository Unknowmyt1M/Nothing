"""Debug routes (FastAPI).

Only active when DEBUG is enabled. Provides platform status, cookie checks,
and metadata extraction diagnostics used by the development console.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.config import DEBUG
from backend.platforms import (
    extract_platform_metadata,
    get_platform_from_url,
    is_platform_supported,
    get_supported_platforms,
    get_platform_display_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class URLRequest(BaseModel):
    url: str = Field(..., min_length=1)


@router.get("/debug/platform_status")
async def platform_status():
    platform_configs = {
        "youtube": {"display_name": "YouTube", "supported": True},
        "instagram": {"display_name": "Instagram", "supported": True},
        "facebook": {"display_name": "Facebook", "supported": True},
        "twitter": {"display_name": "Twitter/X", "supported": True},
        "tiktok": {"display_name": "TikTok", "supported": True},
        "vimeo": {"display_name": "Vimeo", "supported": True},
        "reddit": {"display_name": "Reddit", "supported": True},
        "twitch": {"display_name": "Twitch", "supported": True},
        "rumble": {"display_name": "Rumble", "supported": True},
        "direct_url": {"display_name": "Direct URL", "supported": True},
    }
    platforms_info = []
    for platform, config in platform_configs.items():
        platforms_info.append({
            "platform": platform,
            "display_name": config["display_name"],
            "supported": config["supported"],
            "status": "Supported",
        })
    return {
        "platforms": platforms_info,
        "total_count": len(platforms_info),
        "supported_count": len([p for p in platforms_info if p["supported"]]),
        "success": True,
    }


@router.get("/debug/check_cookies")
async def check_cookies(request: Request):
    """Check cookie availability. Tries Supabase Storage first, then local fs."""
    from backend.services.cookie_manager import get_cookie_path, _storage_available

    cookie_platforms = {
        "youtube": "youtube",
        "instagram": "instagram",
        "tiktok": "tiktok",
        "twitter": "twitter",
        "facebook": "facebook",
        "twitch": "twitch",
        "rumble": "rumble",
        "vimeo": "vimeo",
    }
    cookie_status = {}
    for platform_name, storage_name in cookie_platforms.items():
        path = get_cookie_path(storage_name)
        cookie_status[f"{platform_name}_cookies_exists"] = path is not None

    return {
        **cookie_status,
        "storage_backend": "supabase" if _storage_available() else "none",
        "user_session_active": "access_token" in request.session,
    }


@router.post("/debug/test_metadata")
async def test_metadata_extraction(req: URLRequest):
    try:
        metadata = extract_platform_metadata(req.url)
        return {"success": True, "metadata": metadata}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
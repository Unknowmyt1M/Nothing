"""Automation (channel monitoring) routes (FastAPI).

Uses Supabase as primary storage with JSON fallback.
"""
import logging
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from backend.database.json_db import (
    get_user_settings as json_get_settings,
    save_user_settings as json_save_settings,
    get_user_channels as json_get_channels,
    save_user_channels as json_save_channels,
    get_automation_logs as json_get_logs,
    save_automation_logs as json_save_logs,
)
from backend.database.supabase_client import supabase
from backend.services.automation_service import (
    automation_monitor_worker,
    add_automation_log,
    set_automation_service_status,
)
from backend.services.auth_service import (
    get_channel_info_with_videos_api_v3,
    get_channel_latest_videos_api_v3,
)
from backend.config import YOUTUBE_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class SettingsModel(BaseModel):
    monitor_interval: Optional[int] = 300
    quality: Optional[str] = "1080p"
    metadata_mode: Optional[str] = "original"
    custom_metadata: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None


class ChannelUrlRequest(BaseModel):
    channel_url: str = Field(..., min_length=1)


class ChannelInfoRequest(BaseModel):
    channel_info: Dict[str, Any]


class ChannelRemoveRequest(BaseModel):
    channel_id: str = Field(..., min_length=1)


def get_user_id(request: Request) -> str:
    """Get clean email identifier key from session."""
    if "access_token" not in request.session:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return request.session.get("user_id")


# ---------------------------------------------------------------------------
# Settings — Supabase primary, JSON fallback
# ---------------------------------------------------------------------------
@router.get("/automation/get_settings")
async def get_settings(request: Request):
    try:
        user_id = get_user_id(request)
        if supabase.is_configured:
            try:
                results = supabase.select(
                    "user_settings",
                    filters={"user_id": f"eq.{user_id}"},
                    limit=1,
                )
                if results:
                    return results[0]
            except Exception as e:
                logger.warning("Supabase read failed, using JSON: %s", e)
        return json_get_settings(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting settings: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "An error occurred while loading settings."},
            status_code=500,
        )


@router.post("/automation/save_settings")
async def save_settings(request: Request, settings: SettingsModel):
    try:
        user_id = get_user_id(request)
        data = settings.model_dump(exclude_none=True)
        if supabase.is_configured:
            try:
                data["user_id"] = user_id
                supabase.upsert("user_settings", data)
                return {"success": True}
            except Exception as e:
                logger.warning("Supabase write failed, using JSON: %s", e)
        json_save_settings(user_id, data)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error saving settings: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "An error occurred while saving settings."},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Channels — Supabase primary, JSON fallback
# ---------------------------------------------------------------------------
@router.get("/automation/get_channels")
async def get_channels(request: Request):
    try:
        user_id = get_user_id(request)
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
                    })
                return {"channels": channels}
            except Exception as e:
                logger.warning("Supabase read failed, using JSON: %s", e)
        return json_get_channels(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting channels: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "An error occurred while loading channels."},
            status_code=500,
        )


@router.post("/automation/fetch_channel_info")
async def fetch_channel_info(request: Request, data: ChannelUrlRequest):
    try:
        channel_url = data.channel_url
        if not ("youtube.com" in channel_url or "youtu.be" in channel_url):
            return JSONResponse(
                {"error": "Please provide a valid YouTube channel URL"}, status_code=400
            )

        user_id = get_user_id(request)
        settings = get_user_settings(user_id)
        api_key = settings.get("api_key") or YOUTUBE_API_KEY

        channel_info = get_channel_info_with_videos_api_v3(channel_url, api_key)

        return {
            "success": True,
            "channel_id": channel_info["channel_id"],
            "name": channel_info["name"],
            "logo_url": channel_info["logo_url"],
            "subscriber_count": channel_info.get("subscribers", "Unknown"),
            "total_videos": channel_info.get("video_count", 0),
            "latest_videos": channel_info.get("latest_videos", []),
        }
    except Exception as e:
        logger.error("Error fetching channel details: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to fetch channel information."},
            status_code=500,
        )


@router.get("/automation/fetch_latest_videos")
async def fetch_latest_videos(request: Request, channel_id: str):
    try:
        if not channel_id:
            return JSONResponse({"error": "channel_id is required"}, status_code=400)

        user_id = get_user_id(request)
        settings = get_user_settings(user_id)
        api_key = settings.get("api_key") or YOUTUBE_API_KEY

        videos = get_channel_latest_videos_api_v3(channel_id, api_key, max_results=5)
        return {"success": True, "videos": videos}
    except Exception as e:
        logger.error("Error fetching latest videos: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to fetch latest videos."},
            status_code=500,
        )


@router.post("/automation/add_channel")
async def add_channel(request: Request, data: ChannelInfoRequest):
    try:
        user_id = get_user_id(request)
        channel_info = data.channel_info

        if supabase.is_configured:
            try:
                existing = supabase.select(
                    "monitored_channels",
                    filters={"user_id": f"eq.{user_id}", "channel_id": f"eq.{channel_info['channel_id']}"},
                    limit=1,
                )
                if existing:
                    return JSONResponse(
                        {"error": "Channel is already being monitored"}, status_code=400
                    )
                supabase.insert("monitored_channels", {
                    "user_id": user_id,
                    "channel_url": channel_info.get("channel_url", f"https://www.youtube.com/channel/{channel_info['channel_id']}"),
                    "channel_id": channel_info["channel_id"],
                    "channel_name": channel_info.get("name", ""),
                    "channel_thumbnail": channel_info.get("logo_url", ""),
                    "channel_description": channel_info.get("description", ""),
                    "subscriber_count": channel_info.get("subscriber_count", 0),
                    "video_count": channel_info.get("total_videos", 0),
                    "is_active": True,
                })
                return {"success": True, "channel": channel_info}
            except Exception as e:
                logger.warning("Supabase write failed, using JSON: %s", e)

        channels_data = json_get_channels(user_id)
        for existing in channels_data.get("channels", []):
            if existing["channel_id"] == channel_info["channel_id"]:
                return JSONResponse(
                    {"error": "Channel is already being monitored"}, status_code=400
                )
        channel_info["monitor_interval"] = channel_info.get("monitor_interval", 300)
        channel_info["quality"] = channel_info.get("quality", "1080p")
        channel_info["last_checked"] = None
        channel_info["last_video_count"] = channel_info.get("total_videos", 0)
        if "channels" not in channels_data:
            channels_data["channels"] = []
        channels_data["channels"].append(channel_info)
        json_save_channels(user_id, channels_data)
        return {"success": True, "channel": channel_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding channel: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to add channel."},
            status_code=500,
        )


@router.post("/automation/remove_channel")
async def remove_channel(request: Request, data: ChannelRemoveRequest):
    try:
        user_id = get_user_id(request)
        if supabase.is_configured:
            try:
                supabase.delete("monitored_channels", {
                    "user_id": f"eq.{user_id}",
                    "channel_id": f"eq.{data.channel_id}",
                })
                return {"success": True}
            except Exception as e:
                logger.warning("Supabase delete failed, using JSON: %s", e)

        channels_data = json_get_channels(user_id)
        channels_data["channels"] = [
            ch for ch in channels_data.get("channels", [])
            if ch["channel_id"] != data.channel_id
        ]
        json_save_channels(user_id, channels_data)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing channel: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to remove channel."},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------
@router.get("/automation/get_logs")
async def get_logs(request: Request):
    try:
        if "access_token" not in request.session:
            return JSONResponse(
                {"logs": [], "service_status": False, "error": "Not authenticated"},
                status_code=401,
            )
        user_id = get_user_id(request)

        if supabase.is_configured:
            try:
                results = supabase.select(
                    "automation_logs",
                    filters={"user_id": f"eq.{user_id}"},
                    order="created_at.desc",
                    limit=100,
                )
                filtered_logs = []
                for log in results:
                    filtered_logs.append({
                        "timestamp": log.get("created_at", ""),
                        "type": log.get("level", "info"),
                        "message": str(log.get("message", "")),
                    })

                status_result = supabase.select(
                    "automation_status",
                    filters={"user_id": f"eq.{user_id}"},
                    limit=1,
                )
                service_active = bool(status_result[0].get("is_active", False)) if status_result else False

                return {"logs": filtered_logs, "service_status": service_active}
            except Exception as e:
                logger.warning("Supabase read failed, using JSON: %s", e)

        logs_data = json_get_logs(user_id)
        logs = logs_data.get("logs", [])
        if not isinstance(logs, list):
            logs = []
        filtered_logs = []
        for log in logs[-100:]:
            if isinstance(log, dict) and "timestamp" in log and "message" in log:
                filtered_logs.append({
                    "timestamp": log.get("timestamp", 0),
                    "type": log.get("type", "info"),
                    "message": str(log.get("message", "")),
                })
        return {
            "logs": filtered_logs,
            "service_status": bool(logs_data.get("service_status", False)),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting logs: %s", e)
        return JSONResponse(
            {"logs": [], "service_status": False,
             "error": "Failed to load automation logs."},
            status_code=500,
        )


@router.post("/automation/clear_logs")
async def clear_logs(request: Request):
    try:
        user_id = get_user_id(request)
        if supabase.is_configured:
            try:
                supabase.delete("automation_logs", {"user_id": f"eq.{user_id}"})
                return {"success": True}
            except Exception as e:
                logger.warning("Supabase delete failed, using JSON: %s", e)
        logs_data = {"logs": [], "service_status": False}
        json_save_logs(user_id, logs_data)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error clearing logs: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to clear logs."},
            status_code=500,
        )


@router.post("/automation/start_monitoring")
async def start_monitoring(request: Request):
    try:
        user_id = get_user_id(request)

        if supabase.is_configured:
            try:
                existing = supabase.select(
                    "automation_status",
                    filters={"user_id": f"eq.{user_id}"},
                    limit=1,
                )
                if existing and existing[0].get("is_active", False):
                    return {"success": True, "message": "Service already active"}
                supabase.upsert("automation_status", {
                    "user_id": user_id,
                    "is_active": True,
                })
            except Exception as e:
                logger.warning("Supabase write failed: %s", e)
        else:
            status_data = json_get_logs(user_id)
            if status_data.get("service_status", False):
                return {"success": True, "message": "Service already active"}

        thread = threading.Thread(target=automation_monitor_worker, args=(user_id,), daemon=True)
        thread.start()

        add_automation_log(user_id, "success", "Monitoring service activated successfully")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting monitoring: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to start monitoring service."},
            status_code=500,
        )


@router.post("/automation/stop_monitoring")
async def stop_monitoring(request: Request):
    try:
        user_id = get_user_id(request)
        if supabase.is_configured:
            try:
                supabase.update("automation_status", {"is_active": False}, {"user_id": f"eq.{user_id}"})
            except Exception as e:
                logger.warning("Supabase update failed: %s", e)
        set_automation_service_status(user_id, False)
        add_automation_log(user_id, "info", "Monitoring service stopped by user")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error stopping monitoring: %s", e)
        return JSONResponse(
            {"error": True, "code": "INTERNAL_ERROR",
             "message": "Failed to stop monitoring service."},
            status_code=500,
        )
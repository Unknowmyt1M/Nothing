"""Downloader routes (FastAPI).

Metadata extraction, quality listing, downloads with SSE progress, and the
YouTube upload pipeline. Request bodies are validated with Pydantic.
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse

from pydantic import BaseModel, Field

from backend.config import FRONTEND_URL
from backend.platforms import (
    extract_platform_metadata,
    get_platform_from_url,
    is_platform_supported,
    get_supported_platforms,
    get_platform_display_name,
)
from backend.services.downloader_service import (
    get_video_qualities,
    start_video_download,
    generate_download_sse_stream,
)
from backend.services.uploader_service import (
    start_video_upload,
    get_upload_progress,
    generate_upload_sse_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------
class URLRequest(BaseModel):
    url: str = Field(..., min_length=1)


class ExtractRequest(BaseModel):
    url: str = Field(..., min_length=1)
    platform: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str = Field(..., min_length=1)
    quality: str = Field(..., min_length=1)


class UploadRequest(BaseModel):
    url: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = ""
    tags: str = ""
    privacy: str = "public"


# ---------------------------------------------------------------------------
# Metadata & detection
# ---------------------------------------------------------------------------
@router.post("/downloader/extract_metadata")
async def extract_metadata_route(req: ExtractRequest, request: Request):
    try:
        if not is_platform_supported(req.url):
            platform = get_platform_from_url(req.url)
            return JSONResponse(
                {"error": f'Platform "{platform}" is not supported yet'}, status_code=400
            )
        metadata = extract_platform_metadata(req.url, req.platform)
        return metadata
    except Exception as e:
        logger.error("Error extracting metadata: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/downloader/get_video_qualities")
async def get_video_qualities_route(req: URLRequest):
    try:
        qualities = get_video_qualities(req.url)
        return {"qualities": qualities, "success": True}
    except Exception as e:
        logger.error("Error getting qualities list: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/downloader/detect_platform")
async def detect_platform(req: URLRequest):
    try:
        platform = get_platform_from_url(req.url)
        return {
            "platform": platform,
            "display_name": get_platform_display_name(platform),
            "supported": is_platform_supported(req.url),
            "url": req.url,
        }
    except Exception as e:
        logger.error("Error detecting platform: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/downloader/supported_platforms")
async def supported_platforms():
    platforms = get_supported_platforms()
    return {
        "platforms": [
            {
                "id": p,
                "name": get_platform_display_name(p),
                "description": f"Download videos from {get_platform_display_name(p)}",
            }
            for p in platforms
        ],
        "total": len(platforms),
    }


# ---------------------------------------------------------------------------
# Download + SSE progress
# ---------------------------------------------------------------------------
@router.post("/downloader/download_video")
async def download_video(req: DownloadRequest):
    try:
        download_id = start_video_download(req.url, req.quality)
        return {"download_id": download_id}
    except Exception as e:
        logger.error("Error triggering video download: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/downloader/progress/{download_id}")
async def progress_stream(download_id: str):
    """Real-time SSE progress stream for downloads."""
    async def event_generator():
        loop = asyncio.get_event_loop()
        for event in generate_download_sse_stream(download_id):
            yield event
            await loop.run_in_executor(None, asyncio.sleep, 0)

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# YouTube upload pipeline + SSE progress
# ---------------------------------------------------------------------------
@router.post("/downloader/upload_video")
async def upload_video(req: UploadRequest, request: Request):
    """Download video locally and upload to YouTube."""
    if "access_token" not in request.session:
        return JSONResponse({"error": "Unauthorized authentication required"}, status_code=401)

    try:
        user_email_dir = request.session.get("user_id")
        tags = [t.strip() for t in req.tags.split(",") if t.strip()] if req.tags else []
        upload_id = start_video_upload(
            url=req.url,
            title=req.title,
            description=req.description,
            tags=tags,
            privacy=req.privacy,
            current_access_token=request.session.get("access_token"),
            current_refresh_token=request.session.get("refresh_token"),
            user_email_dir=user_email_dir,
        )
        return {"upload_id": upload_id}
    except Exception as e:
        logger.error("Error starting upload task: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/downloader/upload_progress/{upload_id}")
async def upload_progress_stream(upload_id: str):
    """Real-time SSE progress stream for uploads."""
    async def event_generator():
        loop = asyncio.get_event_loop()
        for event in generate_upload_sse_stream(upload_id):
            yield event
            await loop.run_in_executor(None, asyncio.sleep, 0)

    return EventSourceResponse(event_generator())
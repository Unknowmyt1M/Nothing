"""Downloader routes (FastAPI).

Metadata extraction, quality listing, downloads with SSE progress, and the
YouTube upload pipeline. Uses structured error responses via AppError.
"""
import logging
import re
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse

from pydantic import BaseModel, Field

from backend.errors import (
    AppError,
    invalid_url,
    unsupported_platform,
    extraction_error,
    parse_ytdl_error,
)
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
    cancel_download,
)
from backend.services.uploader_service import (
    start_video_upload,
    generate_upload_sse_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------
_URL_RE = re.compile(
    r'^https?://'                    # scheme
    r'[a-zA-Z0-9]'                  # starts with alnum
    r'[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*$',  # valid URL chars
)
_QUALITY_RE = re.compile(r'^\d{3,4}p?$')
_VALID_QUALITY_LITERALS = {"best", "worst", "audio"}


def _validate_url(url: str) -> AppError | None:
    """Return an AppError if the URL is invalid, else None."""
    if not url or not url.strip():
        return invalid_url("(empty)")
    url = url.strip()
    if len(url) > 2048:
        return invalid_url("URL exceeds 2048 characters")
    if " " in url and "%20" not in url:
        return invalid_url(url[:100])
    if not _URL_RE.match(url):
        return invalid_url(url[:100])
    # Must have a TLD
    try:
        parsed = urlparse(url)
        if not parsed.hostname or "." not in parsed.hostname:
            return invalid_url(url[:100])
    except Exception:
        return invalid_url(url[:100])
    return None


def _error_response(err: AppError) -> JSONResponse:
    return JSONResponse(err.to_dict(), status_code=err.status_code)


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------
class URLRequest(BaseModel):
    url: str = ""


class ExtractRequest(BaseModel):
    url: str = ""
    platform: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str = ""
    quality: str = ""
    model_config = {"extra": "forbid"}


class UploadRequest(BaseModel):
    url: str = ""
    title: str = ""
    description: str = ""
    tags: str = ""
    privacy: str = "public"
    description: str = ""
    tags: str = ""
    privacy: str = "public"


# ---------------------------------------------------------------------------
# Metadata & detection
# ---------------------------------------------------------------------------
@router.post("/downloader/extract_metadata")
async def extract_metadata_route(req: ExtractRequest, request: Request):
    url = req.url.strip()
    err = _validate_url(url)
    if err:
        return _error_response(err)

    if not is_platform_supported(url):
        platform = get_platform_from_url(url)
        return _error_response(unsupported_platform(platform))

    try:
        metadata = extract_platform_metadata(url, req.platform)
        return metadata
    except AppError as e:
        return _error_response(e)
    except Exception as e:
        logger.error("Error extracting metadata: %s", e)
        return _error_response(extraction_error(str(e)))


@router.post("/downloader/get_video_qualities")
async def get_video_qualities_route(req: URLRequest):
    url = req.url.strip()
    err = _validate_url(url)
    if err:
        return _error_response(err)

    if not is_platform_supported(url):
        platform = get_platform_from_url(url)
        return _error_response(unsupported_platform(platform))

    try:
        qualities = get_video_qualities(url)
        return {"qualities": qualities, "success": True}
    except AppError as e:
        return _error_response(e)
    except Exception as e:
        logger.error("Error getting qualities list: %s", e)
        return _error_response(extraction_error(str(e)))


@router.post("/downloader/detect_platform")
async def detect_platform(req: URLRequest):
    url = req.url.strip()
    err = _validate_url(url)
    if err:
        return _error_response(err)

    try:
        platform = get_platform_from_url(url)
        return {
            "platform": platform,
            "display_name": get_platform_display_name(platform),
            "supported": is_platform_supported(url),
            "url": url,
        }
    except Exception as e:
        logger.error("Error detecting platform: %s", e)
        return _error_response(invalid_url(url[:100]))


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
    url = req.url.strip()
    err = _validate_url(url)
    if err:
        return _error_response(err)

    quality = (req.quality or "").strip()
    if not quality:
        return _error_response(invalid_url("Missing quality parameter"))

    if quality.lower() not in _VALID_QUALITY_LITERALS and not _QUALITY_RE.match(quality):
        return _error_response(invalid_url(f"Invalid quality '{quality}': must be like 720p, 1080, best, worst, or audio"))

    if not is_platform_supported(url):
        platform = get_platform_from_url(url)
        return _error_response(unsupported_platform(platform))

    try:
        download_id = start_video_download(url, req.quality)
        return {"download_id": download_id}
    except AppError as e:
        return _error_response(e)
    except Exception as e:
        logger.error("Error triggering video download: %s", e)
        return _error_response(download_error(str(e)))


@router.post("/downloader/cancel_download/{download_id}")
async def cancel_download_route(download_id: str):
    """Cancel an in-progress download and clean up temp files."""
    success = cancel_download(download_id)
    return {"success": success, "message": "Download cancelled" if success else "Download not found or already finished"}


@router.get("/downloader/progress/{download_id}")
async def progress_stream(download_id: str):
    """Real-time SSE progress stream for downloads."""
    return EventSourceResponse(generate_download_sse_stream(download_id))


# ---------------------------------------------------------------------------
# YouTube upload pipeline + SSE progress
# ---------------------------------------------------------------------------
@router.post("/downloader/upload_video")
async def upload_video(req: UploadRequest, request: Request):
    if "access_token" not in request.session:
        return JSONResponse(
            {"error": True, "code": "AUTHENTICATION_REQUIRED", "title": "Login required",
             "message": "You must be logged in to upload to YouTube.",
             "suggestion": "Connect your Google account in the Integrations page.",
             "retryable": False},
            status_code=401,
        )

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
        return _error_response(download_error(str(e)))


@router.get("/downloader/upload_progress/{upload_id}")
async def upload_progress_stream(upload_id: str):
    """Real-time SSE progress stream for uploads."""
    return EventSourceResponse(generate_upload_sse_stream(upload_id))

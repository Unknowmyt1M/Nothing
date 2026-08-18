"""Video download orchestration service.

Downloads videos in background threads and exposes progress for SSE streaming.
Progress is kept in-memory keyed by a download_id.
Supports cancellation, file size limits, and automatic cleanup.
"""
import os
import time
import glob
import json
import logging
import threading
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator

from backend.errors import (
    AppError,
    parse_ytdl_error,
    file_too_large,
    download_cancelled,
    download_error,
    network_error,
)
from backend.platforms import (
    get_platform_from_url,
    get_available_formats_list,
    download_from_platform,
)
from backend.utils.helpers import format_bytes, get_temp_dir

logger = logging.getLogger(__name__)

# In-memory progress store keyed by download_id
download_progress_data: Dict[str, Dict[str, Any]] = {}
_progress_lock = threading.Lock()

# Cancellation events keyed by download_id
_cancel_events: Dict[str, threading.Event] = {}

# Configurable limits
MAX_FILE_SIZE_MB = float(os.environ.get("MAX_FILE_SIZE_MB", "4096"))  # 4 GB default
AUTO_CLEANUP_AGE_SECONDS = int(os.environ.get("AUTO_CLEANUP_AGE", "3600"))  # 1 hour

# Periodic cleanup thread handle
_cleanup_thread: Optional[threading.Thread] = None


def get_video_qualities(url: str) -> list:
    """Retrieve available video formats for quality selection."""
    formats = get_available_formats_list(url)
    qualities = []
    seen_heights = set()

    video_formats = [f for f in formats if f.get("height") and f.get("vcodec") != "none"]
    video_formats.sort(key=lambda x: x.get("height") or 0, reverse=True)

    for fmt in video_formats:
        height = fmt.get("height")
        if height and height not in seen_heights:
            seen_heights.add(height)
            filesize = fmt.get("filesize") or fmt.get("filesize_approx") or 0
            qualities.append({
                "format_id": fmt.get("format_id"),
                "height": height,
                "filesize": format_bytes(filesize) if filesize > 0 else "Unknown size",
                "filesize_bytes": filesize,
                "ext": fmt.get("ext", "mp4"),
            })
    return qualities


def _set_progress(download_id: str, **fields) -> None:
    with _progress_lock:
        if download_id in download_progress_data:
            download_progress_data[download_id].update(fields)


def start_video_download(url: str, quality: str) -> str:
    """Start background video download thread and return download ID."""
    download_id = f"dl_{int(time.time())}_{abs(hash(url)) % 10000}"

    # Ensure uniqueness
    with _progress_lock:
        while download_id in download_progress_data:
            download_id = f"dl_{int(time.time())}_{abs(hash(url)) % 10000}_{os.urandom(2).hex()}"

        download_progress_data[download_id] = {
            "status": "starting",
            "progress": 0,
            "speed": "0 B/s",
            "eta": "--:--",
            "downloaded": "0 B",
            "total": "0 B",
            "filename": None,
            "quality": quality,
            "download_id": download_id,
        }

    cancel_event = threading.Event()
    _cancel_events[download_id] = cancel_event

    def worker():
        try:
            platform = get_platform_from_url(url)
            last_progress = 0.0

            def progress_callback(d):
                nonlocal last_progress
                if cancel_event.is_set():
                    raise Exception("cancelled")
                if d["status"] == "downloading":
                    try:
                        downloaded = d.get("downloaded_bytes", 0)
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        speed = d.get("speed", 0)
                        eta = d.get("eta", 0)
                        progress = (downloaded / total * 100) if total > 0 else 0

                        # File size safety check
                        if total > 0 and total > MAX_FILE_SIZE_MB * 1024 * 1024:
                            _set_progress(
                                download_id,
                                status="error",
                                error_code="FILE_TOO_LARGE",
                                error=str(file_too_large(total / (1024 * 1024), MAX_FILE_SIZE_MB).message),
                                error_time=time.time(),
                            )
                            cancel_event.set()
                            return

                        # Keep progress monotonic across the multiple streams yt-dlp reports
                        if progress < last_progress and last_progress < 100:
                            progress = last_progress
                        last_progress = progress
                        _set_progress(
                            download_id,
                            status="downloading",
                            progress=progress,
                            speed=f"{format_bytes(speed)}/s" if speed else "0 B/s",
                            eta=f"{int(eta)}s" if eta else "--:--",
                            downloaded=format_bytes(downloaded),
                            total=format_bytes(total),
                        )
                    except Exception as pe:
                        logger.error("Progress parse error: %s", pe)

            filename = download_from_platform(
                url, get_temp_dir(), platform, progress_callback, quality, cancel_event
            )
            _set_progress(
                download_id,
                status="completed",
                progress=100,
                filename=os.path.basename(filename),
                completed_at=time.time(),
            )
        except Exception as e:
            err_str = str(e)
            # Check if it's a cancellation
            if "cancelled" in err_str.lower() or isinstance(e, AppError) and e.code == "DOWNLOAD_CANCELLED":
                _set_progress(download_id, status="cancelled", cancelled_at=time.time())
                logger.info("Download %s cancelled by user", download_id)
            else:
                # Parse yt-dlp error into structured error
                app_err = parse_ytdl_error(err_str) if not isinstance(e, AppError) else e
                _set_progress(
                    download_id,
                    status="error",
                    error_code=app_err.code,
                    error=app_err.message,
                    error_suggestion=getattr(app_err, 'suggestion', ''),
                    error_time=time.time(),
                )
                logger.error("Download thread error for %s: %s", download_id, e)
        finally:
            # Clean up cancel event
            _cancel_events.pop(download_id, None)
            # Schedule delayed cleanup
            _schedule_cleanup(download_id)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return download_id


def cancel_download(download_id: str) -> bool:
    """Cancel an in-progress download. Returns True if cancel signal was sent."""
    event = _cancel_events.get(download_id)
    if event:
        event.set()
        return True
    return False


def _schedule_cleanup(download_id: str, delay: int = 300) -> None:
    """Remove a download's progress data after `delay` seconds."""
    def _do_cleanup():
        time.sleep(delay)
        with _progress_lock:
            download_progress_data.pop(download_id, None)
    thread = threading.Thread(target=_do_cleanup, daemon=True)
    thread.start()


def get_download_progress(download_id: str) -> Optional[Dict[str, Any]]:
    return download_progress_data.get(download_id)


async def generate_download_sse_stream(download_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events (SSE) stream for download progress (non-blocking)."""
    heartbeat_interval = 15  # seconds
    last_update_time = time.time()
    while True:
        data = get_download_progress(download_id)
        if not data:
            yield f"data: {json.dumps({'status': 'error', 'error': 'Download not found', 'code': 'NOT_FOUND'})}\n\n"
            break
        # Don't send internal fields to the client
        clean = {k: v for k, v in data.items() if not k.startswith('_')}
        yield f"data: {json.dumps(clean)}\n\n"
        last_update_time = time.time()
        if data.get("status") in ("completed", "error", "cancelled"):
            break
        # Sleep in small increments to check for heartbeat eligibility
        elapsed = 0.0
        while elapsed < 0.5:
            await asyncio.sleep(0.5)
            elapsed += 0.5
            if time.time() - last_update_time >= heartbeat_interval:
                yield ": heartbeat\n\n"
                last_update_time = time.time()


def cleanup_stale_progress(max_age_seconds: int = None) -> int:
    """Periodic cleanup of old progress entries to avoid memory leaks.
    Returns number of entries cleaned.
    """
    if max_age_seconds is None:
        max_age_seconds = AUTO_CLEANUP_AGE_SECONDS
    cutoff = time.time() - max_age_seconds
    count = 0
    with _progress_lock:
        stale = [k for k, v in download_progress_data.items()
                 if v.get("status") in ("completed", "error", "cancelled")
                 and (v.get("completed_at") or v.get("error_time") or v.get("cancelled_at") or 0) < cutoff]
        for k in stale:
            download_progress_data.pop(k, None)
            count += 1
    if count:
        logger.info("Cleaned %d stale download progress entries", count)
    return count


def cleanup_downloads_directory(max_age_seconds: int = None) -> int:
    """Remove downloaded files older than max_age_seconds from the downloads dir."""
    if max_age_seconds is None:
        max_age_seconds = AUTO_CLEANUP_AGE_SECONDS
    downloads_dir = get_temp_dir()
    if not os.path.isdir(downloads_dir):
        return 0
    cutoff = time.time() - max_age_seconds
    removed = 0
    for fpath in glob.glob(os.path.join(downloads_dir, "*")):
        if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
            try:
                os.remove(fpath)
                removed += 1
            except OSError:
                pass
    if removed:
        logger.info("Cleaned %d stale files from downloads/", removed)
    return removed


def _periodic_cleanup_loop():
    """Background loop that cleans stale progress and files every 10 minutes."""
    while True:
        time.sleep(600)
        try:
            cleanup_stale_progress()
            cleanup_downloads_directory()
        except Exception as e:
            logger.error("Periodic cleanup error: %s", e)


def start_cleanup_thread():
    """Start the background cleanup daemon (call once at app startup)."""
    global _cleanup_thread
    if _cleanup_thread and _cleanup_thread.is_alive():
        return
    _cleanup_thread = threading.Thread(target=_periodic_cleanup_loop, daemon=True)
    _cleanup_thread.start()
    logger.info("Started periodic cleanup thread")

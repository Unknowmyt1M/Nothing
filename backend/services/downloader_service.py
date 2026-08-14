"""Video download orchestration service.

Downloads videos in background threads and exposes progress for SSE streaming.
Progress is kept in-memory keyed by a download_id.
"""
import os
import time
import json
import logging
import threading
from typing import Dict, Any, Optional, Generator

from backend.platforms import (
    get_platform_from_url,
    get_available_formats_list,
    download_from_platform,
)
from backend.utils.helpers import format_bytes

logger = logging.getLogger(__name__)

# In-memory progress store keyed by download_id
download_progress_data: Dict[str, Dict[str, Any]] = {}
_progress_lock = threading.Lock()


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
                "ext": fmt.get("ext", "mp4"),
            })
    return qualities


def _set_progress(download_id: str, **fields) -> None:
    with _progress_lock:
        download_progress_data[download_id].update(fields)


def start_video_download(url: str, quality: str) -> str:
    """Start background video download thread and return download ID."""
    download_id = f"dl_{int(time.time())}_{abs(hash(url)) % 10000}"
    download_progress_data[download_id] = {
        "status": "starting",
        "progress": 0,
        "speed": "0 B/s",
        "eta": "--:--",
        "downloaded": "0 B",
        "total": "0 B",
        "filename": None,
        "quality": quality,
    }

    def worker():
        try:
            platform = get_platform_from_url(url)

            def progress_callback(d):
                if d["status"] == "downloading":
                    try:
                        downloaded = d.get("downloaded_bytes", 0)
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        speed = d.get("speed", 0)
                        eta = d.get("eta", 0)
                        progress = (downloaded / total * 100) if total > 0 else 0
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

            filename = download_from_platform(url, "downloads", platform, progress_callback)
            _set_progress(
                download_id,
                status="completed",
                progress=100,
                filename=os.path.basename(filename),
                completed_at=time.time(),
            )
        except Exception as e:
            logger.error("Download thread error: %s", e)
            _set_progress(download_id, status="error", error=str(e), error_time=time.time())

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return download_id


def get_download_progress(download_id: str) -> Optional[Dict[str, Any]]:
    return download_progress_data.get(download_id)


def generate_download_sse_stream(download_id: str) -> Generator[str, None, None]:
    """Generate Server-Sent Events (SSE) stream for download progress."""
    while True:
        data = get_download_progress(download_id)
        if not data:
            yield f"data: {json.dumps({'status': 'error', 'error': 'Download not found'})}\n\n"
            break
        yield f"data: {json.dumps(data)}\n\n"
        if data.get("status") in ("completed", "error", "cancelled"):
            break
        time.sleep(0.5)


def cleanup_stale_progress(max_age_seconds: int = 3600) -> None:
    """Periodic cleanup of old progress entries to avoid memory leaks."""
    cutoff = time.time() - max_age_seconds
    with _progress_lock:
        stale = [k for k, v in download_progress_data.items()
                 if (v.get("completed_at") or v.get("error_time") or 0) < cutoff]
        for k in stale:
            download_progress_data.pop(k, None)
    if stale:
        logger.info("Cleaned %d stale download progress entries", len(stale))
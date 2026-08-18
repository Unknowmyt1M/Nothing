"""Centralized error classification system for the Nothing backend.

Every error returned to the frontend follows a structured format:
  - code: machine-readable error category
  - title: short user-facing label
  - message: human-readable explanation
  - suggestion: recommended action (optional)
  - retryable: whether the client should offer retry
  - details: technical info for debugging (stripped in production)
"""
from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from backend.config import DEBUG


class AppError(Exception):
    """Structured application error with code, title, message, suggestion."""

    def __init__(
        self,
        code: str,
        title: str,
        message: str,
        suggestion: str = "",
        retryable: bool = False,
        details: str = "",
        status_code: int = 400,
    ):
        self.code = code
        self.title = title
        self.message = message
        self.suggestion = suggestion
        self.retryable = retryable
        self.details = details
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "error": True,
            "code": self.code,
            "title": self.title,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.details and DEBUG:
            result["details"] = self.details
        return result


# ---------------------------------------------------------------------------
# Factory helpers — one per error category
# ---------------------------------------------------------------------------

def invalid_url(url: str = "") -> AppError:
    return AppError(
        code="INVALID_URL",
        title="Invalid video URL",
        message="That doesn't look like a valid video URL. Please check the link and try again.",
        suggestion="Paste a complete URL starting with http:// or https://",
        retryable=False,
        details=f"Received: {url[:200]}" if url else "Empty URL",
    )


def unsupported_platform(platform: str = "unknown") -> AppError:
    name = platform.replace("_", " ").title() if platform else "this website"
    return AppError(
        code="UNSUPPORTED_PLATFORM",
        title="Platform not supported",
        message=f"Nothing doesn't support {name} yet.",
        suggestion="Try a URL from YouTube, Instagram, TikTok, Facebook, Twitter/X, Vimeo, Reddit, Twitch, Rumble, or Dailymotion.",
        retryable=False,
        details=f"Detected platform: {platform}",
    )


def content_unavailable(details: str = "") -> AppError:
    return AppError(
        code="CONTENT_UNAVAILABLE",
        title="Video unavailable",
        message="This video may have been deleted, made private, or is no longer accessible.",
        suggestion="Verify the link works in your browser, then try again.",
        retryable=False,
        details=details,
    )


def private_content() -> AppError:
    return AppError(
        code="PRIVATE_CONTENT",
        title="Private content",
        message="This video is private or restricted and cannot be accessed without authentication.",
        suggestion="If you own this video, ensure it is set to public or unlisted.",
        retryable=False,
    )


def authentication_required() -> AppError:
    return AppError(
        code="AUTHENTICATION_REQUIRED",
        title="Login required",
        message="This content requires you to be logged in to access it.",
        suggestion="Connect your account in the Integrations page, or try a different video.",
        retryable=False,
    )


def region_restricted() -> AppError:
    return AppError(
        code="REGION_RESTRICTED",
        title="Region restricted",
        message="This video is not available in your current region.",
        suggestion="Try a different video or use a VPN if appropriate.",
        retryable=False,
    )


def format_unavailable(quality: str = "") -> AppError:
    msg = f"The requested {quality} format is no longer available for this video." if quality else "The requested format is not available for this video."
    return AppError(
        code="FORMAT_UNAVAILABLE",
        title="Quality unavailable",
        message=msg,
        suggestion="Try a different quality option or use Auto.",
        retryable=True,
    )


def network_error(original: str = "") -> AppError:
    return AppError(
        code="NETWORK_ERROR",
        title="Connection problem",
        message="The download was interrupted by a network problem.",
        suggestion="Check your internet connection and try again.",
        retryable=True,
        details=original,
    )


def timeout_error() -> AppError:
    return AppError(
        code="TIMEOUT",
        title="Request timed out",
        message="The request took too long to complete.",
        suggestion="The server may be temporarily busy. Try again in a moment.",
        retryable=True,
    )


def rate_limited() -> AppError:
    return AppError(
        code="RATE_LIMITED",
        title="Too many requests",
        message="The platform is rate-limiting requests right now.",
        suggestion="Wait a minute and try again.",
        retryable=True,
    )


def extraction_error(original: str = "") -> AppError:
    return AppError(
        code="EXTRACTION_ERROR",
        title="Extraction failed",
        message="Could not extract video information from this URL.",
        suggestion="The URL may be invalid, the content may be unavailable, or the platform may have changed. Try a different URL.",
        retryable=True,
        details=original,
    )


def download_error(original: str = "") -> AppError:
    return AppError(
        code="DOWNLOAD_ERROR",
        title="Download failed",
        message="An error occurred while downloading the video.",
        suggestion="Try again, or select a different quality.",
        retryable=True,
        details=original,
    )


def merge_error(original: str = "") -> AppError:
    return AppError(
        code="MERGE_ERROR",
        title="Merge failed",
        message="The video and audio streams could not be combined.",
        suggestion="Try a different quality format.",
        retryable=True,
        details=original,
    )


def ffmpeg_error(original: str = "") -> AppError:
    return AppError(
        code="FFMPEG_ERROR",
        title="Video processing error",
        message="The system encountered an error processing the video file.",
        suggestion="Try a different quality or format.",
        retryable=True,
        details=original,
    )


def storage_error(original: str = "") -> AppError:
    return AppError(
        code="STORAGE_ERROR",
        title="Storage error",
        message="There is not enough disk space or a file system error occurred.",
        suggestion="Free up disk space and try again.",
        retryable=False,
        details=original,
    )


def file_too_large(size_mb: float = 0, limit_mb: float = 0) -> AppError:
    size_str = f"{size_mb:.0f} MB" if size_mb else "unknown size"
    limit_str = f"{limit_mb:.0f} MB" if limit_mb else "the limit"
    return AppError(
        code="FILE_TOO_LARGE",
        title="File too large",
        message=f"This file ({size_str}) exceeds the safe download limit ({limit_str}).",
        suggestion="Try a lower quality to reduce the file size.",
        retryable=True,
        details=f"Size: {size_mb:.1f} MB, Limit: {limit_mb:.1f} MB",
    )


def unsupported_url_type(resource_type: str = "this URL", platform: str = "") -> AppError:
    platform_note = f" on {platform}" if platform else ""
    return AppError(
        code="UNSUPPORTED_URL_TYPE",
        title="Unsupported URL type",
        message=f"This link points to {resource_type}{platform_note}, not a downloadable video.",
        suggestion="Paste a direct link to a video, not a channel, playlist, search, or other page.",
        retryable=False,
        details=f"Resource type: {resource_type}, Platform: {platform or 'unknown'}",
    )


def bot_check() -> AppError:
    return AppError(
        code="BOT_CHECK",
        title="Bot detection triggered",
        message="The platform detected automated access and blocked the request.",
        suggestion="Wait a few minutes and try again, or try a different video.",
        retryable=True,
    )


def age_restricted() -> AppError:
    return AppError(
        code="AGE_RESTRICTED",
        title="Age-restricted content",
        message="This video is age-restricted and requires authentication to access.",
        suggestion="Connect an authorized account or try a different video.",
        retryable=False,
    )


def youtube_auth_expired() -> AppError:
    return AppError(
        code="YOUTUBE_AUTH_EXPIRED",
        title="YouTube authorization expired",
        message="Your YouTube connection has expired. Reconnect Google to continue.",
        suggestion="Go to Integrations and reconnect your Google account.",
        retryable=False,
    )


def database_error(original: str = "") -> AppError:
    return AppError(
        code="DATABASE_ERROR",
        title="Database error",
        message="A database error occurred while processing your request.",
        suggestion="Try again in a moment.",
        retryable=True,
        details=original,
    )


def download_cancelled() -> AppError:
    return AppError(
        code="DOWNLOAD_CANCELLED",
        title="Download cancelled",
        message="The download was safely cancelled and temporary files were removed.",
        retryable=True,
    )


def unknown_error(original: str = "") -> AppError:
    return AppError(
        code="UNKNOWN_ERROR",
        title="Something went wrong",
        message="An unexpected error occurred. Please try again.",
        suggestion="If the problem continues, try a different quality or URL.",
        retryable=True,
        details=original,
    )


def parse_ytdl_error(error_str: str) -> AppError:
    """Parse a yt-dlp error message into the most appropriate AppError."""
    lower = error_str.lower()

    if "unsupported url" in lower or "no suitable extractor" in lower:
        return extraction_error(error_str)
    if "video unavailable" in lower or "this video is not available" in lower:
        return content_unavailable(error_str)
    if "private video" in lower or "this video is private" in lower:
        return private_content()
    if "sign in" in lower or "login" in lower or "authentication" in lower:
        return authentication_required()
    if "not available in your country" in lower or "geo" in lower:
        return region_restricted()
    if "http error 429" in lower or "too many requests" in lower or "rate" in lower:
        return rate_limited()
    if "timeout" in lower or "timed out" in lower:
        return timeout_error()
    if "connection" in lower or "network" in lower or "resolve" in lower or "dns" in lower:
        return network_error(error_str)
    if "format" in lower and ("not available" in lower or "unavailable" in lower):
        return format_unavailable(error_str)
    if "ffmpeg" in lower or "merge" in lower:
        return merge_error(error_str)
    if "disk" in lower or "no space" in lower or "storage" in lower:
        return storage_error(error_str)
    if "permission" in lower or "access denied" in lower:
        return storage_error(error_str)

    return extraction_error(error_str)

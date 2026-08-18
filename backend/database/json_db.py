"""Data access layer with Supabase-first, JSON-file fallback.

Every public function keeps the same signature it always had so callers
don't need to change.  When Supabase is configured the data lives in
the remote database; otherwise a local JSON file is used (useful for
local development without Supabase).
"""
import os
import json
import logging
import time
import threading

from backend.database.supabase_client import supabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON-file fallback (only used when Supabase is NOT configured)
# ---------------------------------------------------------------------------
_db_lock = threading.Lock()
DB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "db")
)


def _ensure_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def _get_user_dir(user_id):
    clean_id = "".join(c for c in user_id if c.isalnum() or c in ("_", "-")).strip() or "default"
    path = os.path.join(DB_DIR, clean_id)
    os.makedirs(path, exist_ok=True)
    return path


def _read_json(path, default):
    with _db_lock:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Error reading %s: %s", path, exc)
            return default


def _write_json(path, data):
    with _db_lock:
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            if os.path.exists(path):
                os.remove(path)
            os.rename(tmp, path)
            return True
        except Exception as exc:
            logger.error("Error writing %s: %s", path, exc)
            try:
                os.remove(path + ".tmp")
            except OSError:
                pass
            return False


def database_init():
    """Ensure local JSON fallback directory exists."""
    _ensure_db_dir()


# ===== Tokens =====

def get_user_tokens(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "youtube_connections",
                columns="access_token,refresh_token",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if rows:
                return {
                    "user_id": user_id,
                    "access_token": rows[0].get("access_token"),
                    "refresh_token": rows[0].get("refresh_token"),
                }
            return None
        except Exception as exc:
            logger.warning("Supabase get_user_tokens failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "tokens.json")
    return _read_json(path, None)


def store_user_tokens(user_id, access_token, refresh_token):
    if supabase.is_configured:
        try:
            supabase.upsert(
                "youtube_connections",
                {
                    "user_id": user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            )
            logger.info("Tokens stored in Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase store_user_tokens failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "tokens.json")
    data = {"user_id": user_id, "access_token": access_token, "refresh_token": refresh_token}
    return _write_json(path, data)


# ===== Settings =====

_DEFAULT_SETTINGS = {
    "monitor_interval": 300,
    "quality": "1080p",
    "metadata_mode": "original",
    "custom_metadata": {"title": "", "description": "", "tags": []},
}


def get_user_settings(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "user_settings",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if rows:
                row = rows[0]
                return {
                    "user_id": user_id,
                    "monitor_interval": row.get("monitor_interval", 300),
                    "quality": row.get("quality", "1080p"),
                    "metadata_mode": row.get("metadata_mode", "original"),
                    "custom_metadata": row.get("custom_metadata", _DEFAULT_SETTINGS["custom_metadata"]),
                    "api_key": row.get("api_key"),
                }
            return dict(_DEFAULT_SETTINGS)
        except Exception as exc:
            logger.warning("Supabase get_user_settings failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "settings.json")
    return _read_json(path, dict(_DEFAULT_SETTINGS))


def save_user_settings(user_id, settings):
    merged = {**settings, "user_id": user_id}

    if supabase.is_configured:
        try:
            supabase.upsert(
                "user_settings",
                {
                    "user_id": user_id,
                    "monitor_interval": merged.get("monitor_interval", 300),
                    "quality": merged.get("quality", "1080p"),
                    "metadata_mode": merged.get("metadata_mode", "original"),
                    "custom_metadata": merged.get("custom_metadata", {}),
                    "api_key": merged.get("api_key"),
                },
            )
            logger.info("Settings stored in Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase save_user_settings failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "settings.json")
    return _write_json(path, merged)


# ===== Channels =====

def get_user_channels(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "monitored_channels",
                filters={"user_id": f"eq.{user_id}"},
                order="created_at.asc",
            )
            channels = []
            for r in rows:
                channels.append({
                    "id": r.get("id"),
                    "channel_id": r.get("channel_id", ""),
                    "url": r.get("channel_url", ""),
                    "name": r.get("channel_name", "Unknown"),
                    "video_count": r.get("video_count", 0),
                    "is_active": r.get("is_active", True),
                })
            return {"channels": channels}
        except Exception as exc:
            logger.warning("Supabase get_user_channels failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "channels.json")
    return _read_json(path, {"channels": []})


def save_user_channels(user_id, channels_data):
    channels = channels_data.get("channels", [])

    if supabase.is_configured:
        try:
            for ch in channels:
                if ch.get("id"):
                    supabase.update(
                        "monitored_channels",
                        {"video_count": ch.get("video_count", 0)},
                        {"id": f"eq.{ch['id']}"},
                    )
            logger.info("Channel counts updated in Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase save_user_channels failed, using JSON: %s", exc)

    merged = {**channels_data, "user_id": user_id}
    path = os.path.join(_get_user_dir(user_id), "channels.json")
    return _write_json(path, merged)


# ===== OAuth Tokens (full token.json data) =====

def get_oauth_tokens(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "youtube_connections",
                filters={"user_id": f"eq.{user_id}"},
                limit=1,
            )
            if rows:
                row = rows[0]
                return {
                    "user_id": user_id,
                    "tokens": {
                        "access_token": row.get("access_token"),
                        "refresh_token": row.get("refresh_token"),
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "client_id": row.get("google_client_id"),
                    },
                }
            return None
        except Exception as exc:
            logger.warning("Supabase get_oauth_tokens failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "oauth_tokens.json")
    return _read_json(path, None)


def save_oauth_tokens(user_id, token_data):
    tokens = token_data.get("tokens", token_data) if isinstance(token_data, dict) else token_data

    if supabase.is_configured:
        try:
            supabase.upsert(
                "youtube_connections",
                {
                    "user_id": user_id,
                    "access_token": tokens.get("access_token"),
                    "refresh_token": tokens.get("refresh_token"),
                },
            )
            logger.info("OAuth tokens stored in Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase save_oauth_tokens failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "oauth_tokens.json")
    data = {"user_id": user_id, "tokens": tokens}
    return _write_json(path, data)


def delete_oauth_tokens(user_id):
    if supabase.is_configured:
        try:
            supabase.delete("youtube_connections", {"user_id": f"eq.{user_id}"})
            logger.info("OAuth tokens deleted from Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase delete_oauth_tokens failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "oauth_tokens.json")
    with _db_lock:
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as exc:
                logger.error("Error deleting oauth_tokens: %s", exc)
                return False
        return True


# ===== Automation Logs =====

def get_automation_logs(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "automation_logs",
                filters={"user_id": f"eq.{user_id}"},
                order="created_at.desc",
                limit=100,
            )
            logs = []
            for r in rows:
                logs.append({
                    "timestamp": _parse_timestamp(r.get("created_at")),
                    "type": r.get("level", "info"),
                    "message": r.get("message", ""),
                })
            logs.reverse()  # oldest first
            return {"logs": logs, "service_status": False}
        except Exception as exc:
            logger.warning("Supabase get_automation_logs failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "automation_logs.json")
    return _read_json(path, {"logs": [], "service_status": False})


def save_automation_logs(user_id, logs_data):
    """Save logs data. When on Supabase, individual rows are used so this
    is mainly a no-op or a service_status update."""
    if supabase.is_configured:
        # Service status is stored in automation_status, not in logs
        return True

    merged = {**logs_data, "user_id": user_id}
    path = os.path.join(_get_user_dir(user_id), "automation_logs.json")
    return _write_json(path, merged)


# ===== Upload History =====

def get_user_history(user_id):
    if supabase.is_configured:
        try:
            rows = supabase.select(
                "upload_history",
                filters={"user_id": f"eq.{user_id}"},
                order="created_at.desc",
                limit=50,
            )
            history = []
            for r in rows:
                history.append({
                    "title": r.get("title"),
                    "platform": r.get("platform"),
                    "video_url": r.get("source_url"),
                    "youtube_url": r.get("youtube_video_url"),
                    "timestamp": _parse_timestamp(r.get("created_at")),
                })
            history.reverse()
            return history
        except Exception as exc:
            logger.warning("Supabase get_user_history failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "history.json")
    return _read_json(path, [])


def add_to_history(user_id, upload_data):
    if supabase.is_configured:
        try:
            supabase.insert(
                "upload_history",
                {
                    "user_id": user_id,
                    "title": upload_data.get("title"),
                    "source_url": upload_data.get("video_url"),
                    "youtube_video_url": upload_data.get("youtube_url"),
                    "platform": upload_data.get("platform"),
                    "status": "completed",
                },
            )
            logger.info("History entry added to Supabase for %s", user_id)
            return True
        except Exception as exc:
            logger.warning("Supabase add_to_history failed, using JSON: %s", exc)

    path = os.path.join(_get_user_dir(user_id), "history.json")
    history = get_user_history(user_id)
    if not isinstance(history, list):
        history = []
    history.append(upload_data)
    if len(history) > 50:
        history = history[-50:]
    return _write_json(path, history)


# ===== Helpers =====

def _parse_timestamp(ts):
    """Convert an ISO timestamp string from Supabase to a Unix epoch float."""
    if not ts:
        return time.time() * 1000
    try:
        from datetime import datetime, timezone
        if isinstance(ts, (int, float)):
            return float(ts)
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.timestamp() * 1000
    except Exception:
        return time.time() * 1000

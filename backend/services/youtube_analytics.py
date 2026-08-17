"""YouTube Analytics service layer.

Wraps YouTube Analytics API v2 and YouTube Data API v3 to fetch channel
analytics, top videos, traffic sources, demographics, and revenue data.
All functions return partial results on error instead of raising.
"""
import logging
import time
import requests
from typing import Optional
from datetime import datetime, timedelta

from backend.services.auth_service import get_youtube_api_service

logger = logging.getLogger(__name__)

ANALYTICS_BASE = "https://youtubeanalytics.googleapis.com/v2"
DATA_API_BASE = "https://www.googleapis.com/youtube/v3"

_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300


def _cache_key(channel_id: str, start_date: str, end_date: str) -> str:
    return f"{channel_id}:{start_date}:{end_date}"


def _get_cached(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < _CACHE_TTL:
        return entry[1]
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = (time.time(), data)


def _clean_expired_cache():
    now = time.time()
    expired = [k for k, (ts, _) in _cache.items() if now - ts >= _CACHE_TTL]
    for k in expired:
        del _cache[k]


def _analytics_request(access_token: str, endpoint: str, params: dict) -> dict:
    url = f"{ANALYTICS_BASE}/{endpoint}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_channel_overview(access_token: str) -> dict:
    """Get channel overview: name, avatar, subscriber count, total videos, total views."""
    result = {
        "name": "",
        "avatar_url": "",
        "subscriber_count": 0,
        "total_videos": 0,
        "total_views": 0,
        "channel_id": "",
        "description": "",
        "country": "",
        "_errors": {},
    }

    try:
        url = f"{DATA_API_BASE}/channels"
        params = {"part": "snippet,statistics,contentDetails", "mine": "true"}
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            result["_errors"]["channels"] = "No channel found"
            return result

        ch = items[0]
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})
        result["channel_id"] = ch.get("id", "")
        result["name"] = snippet.get("title", "")
        result["avatar_url"] = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
        result["subscriber_count"] = int(stats.get("subscriberCount", 0))
        result["total_videos"] = int(stats.get("videoCount", 0))
        result["total_views"] = int(stats.get("viewCount", 0))
        result["description"] = snippet.get("description", "")
        result["country"] = snippet.get("country", "")
    except Exception as e:
        logger.error("Error fetching channel overview: %s", e)
        result["_errors"]["channels"] = str(e)

    return result


def get_channel_analytics(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
    metrics: Optional[list[str]] = None,
) -> dict:
    """Fetch analytics from YouTube Analytics API v2.

    Returns time series data grouped by day plus summary KPIs.
    """
    ck = _cache_key(channel_id, start_date, end_date)
    cached = _get_cached(f"analytics:{ck}")
    if cached:
        return cached

    default_metrics = ["views", "estimatedMinutesWatched", "subscribersGained", "subscribersLost"]
    use_metrics = metrics or default_metrics

    result = {
        "time_series": [],
        "summary": {},
        "_errors": {},
    }

    try:
        params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(use_metrics),
            "dimensions": "day",
            "sort": "day",
        }
        data = _analytics_request(access_token, "reports", params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])

        col_names = [c.get("name", "") for c in columns]
        time_series = []
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            time_series.append(entry)

        result["time_series"] = time_series

        summary = {}
        for name in use_metrics:
            vals = [r.get(name, 0) for r in time_series if name in r]
            summary[name] = sum(vals) if vals else 0
        result["summary"] = summary

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error %s: %s", status, e)
        result["_errors"]["analytics"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching channel analytics: %s", e)
        result["_errors"]["analytics"] = str(e)

    _clean_expired_cache()
    _set_cache(f"analytics:{ck}", result)
    return result


def get_top_videos(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
    max_results: int = 10,
) -> list[dict]:
    """Get top-performing videos for a period.

    Uses Analytics API for metrics, then enriches with Data API for thumbnails.
    """
    ck = _cache_key(channel_id, start_date, end_date)
    cached = _get_cached(f"videos:{ck}")
    if cached:
        return cached

    videos = []

    try:
        params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched,likes,comments,subscribersGained",
            "dimensions": "video",
            "sort": "-views",
            "maxResults": str(max_results),
        }
        data = _analytics_request(access_token, "reports", params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]

        video_ids = []
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            if "video" in entry:
                video_ids.append(entry["video"])
            videos.append(entry)

        if video_ids:
            try:
                svc = get_youtube_api_service(access_token)
                resp = svc.videos().list(
                    part="snippet,statistics",
                    id=",".join(video_ids[:50]),
                ).execute()
                details_map = {}
                for item in resp.get("items", []):
                    vid = item["id"]
                    snippet = item.get("snippet", {})
                    details_map[vid] = {
                        "title": snippet.get("title", ""),
                        "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                        "published_at": snippet.get("publishedAt", ""),
                    }
                for v in videos:
                    vid = v.get("video", "")
                    details = details_map.get(vid, {})
                    v["title"] = details.get("title", vid)
                    v["thumbnail"] = details.get("thumbnail", "")
                    v["url"] = f"https://www.youtube.com/watch?v={vid}"
            except Exception as e:
                logger.warning("Could not enrich video details: %s", e)

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error for top videos %s: %s", status, e)
    except Exception as e:
        logger.error("Error fetching top videos: %s", e)

    _clean_expired_cache()
    _set_cache(f"videos:{ck}", videos)
    return videos


def get_traffic_sources(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Get traffic source breakdown."""
    ck = _cache_key(channel_id, start_date, end_date)
    cached = _get_cached(f"traffic:{ck}")
    if cached:
        return cached

    result = {"sources": [], "_errors": {}}

    try:
        params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "insightTrafficSourceType",
            "sort": "-views",
        }
        data = _analytics_request(access_token, "reports", params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]

        sources = []
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            sources.append(entry)

        result["sources"] = sources

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error for traffic %s: %s", status, e)
        result["_errors"]["traffic"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching traffic sources: %s", e)
        result["_errors"]["traffic"] = str(e)

    _clean_expired_cache()
    _set_cache(f"traffic:{ck}", result)
    return result


def get_audience_demographics(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Get audience demographics: geography, age, gender."""
    ck = _cache_key(channel_id, start_date, end_date)
    cached = _get_cached(f"audience:{ck}")
    if cached:
        return cached

    result = {"geography": [], "age_groups": [], "gender": [], "_errors": {}}

    geography_params = {
        "ids": f"channel=={channel_id}",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": "views",
        "dimensions": "country",
        "sort": "-views",
        "maxResults": "25",
    }

    try:
        data = _analytics_request(access_token, "reports", geography_params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            result["geography"].append(entry)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error for geography %s: %s", status, e)
        result["_errors"]["geography"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching geography: %s", e)
        result["_errors"]["geography"] = str(e)

    try:
        age_params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "viewerPercentage",
            "dimensions": "ageGroup",
            "sort": "-viewerPercentage",
        }
        data = _analytics_request(access_token, "reports", age_params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            result["age_groups"].append(entry)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error for age groups %s: %s", status, e)
        result["_errors"]["age_groups"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching age groups: %s", e)
        result["_errors"]["age_groups"] = str(e)

    try:
        gender_params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "viewerPercentage",
            "dimensions": "gender",
            "sort": "-viewerPercentage",
        }
        data = _analytics_request(access_token, "reports", gender_params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            result["gender"].append(entry)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        logger.error("Analytics API error for gender %s: %s", status, e)
        result["_errors"]["gender"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching gender: %s", e)
        result["_errors"]["gender"] = str(e)

    _clean_expired_cache()
    _set_cache(f"audience:{ck}", result)
    return result


def get_revenue_data(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Get revenue data if available.

    Returns {"available": False} if the channel doesn't have monetization
    or if the API returns a permission error.
    """
    ck = _cache_key(channel_id, start_date, end_date)
    cached = _get_cached(f"revenue:{ck}")
    if cached:
        return cached

    result = {
        "available": False,
        "time_series": [],
        "summary": {},
        "_errors": {},
    }

    try:
        params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "estimatedRevenue,estimatedRedPartnerRevenue,playbackBasedCpm,estimatedMinutesWatched",
            "dimensions": "day",
            "sort": "day",
        }
        data = _analytics_request(access_token, "reports", params)
        rows = data.get("rows", [])
        columns = data.get("columnHeaders", [])
        col_names = [c.get("name", "") for c in columns]

        time_series = []
        for row in rows:
            entry = {}
            for i, val in enumerate(row):
                if i < len(col_names):
                    entry[col_names[i]] = val
            time_series.append(entry)

        result["time_series"] = time_series
        result["available"] = True

        summary = {}
        for name in ["estimatedRevenue", "estimatedRedPartnerRevenue", "playbackBasedCpm", "estimatedMinutesWatched"]:
            vals = [r.get(name, 0) for r in time_series if name in r]
            summary[name] = sum(vals) if vals else 0
        if time_series:
            for name in ["estimatedRevenue", "estimatedRedPartnerRevenue"]:
                vals = [r.get(name, 0) for r in time_series if name in r]
                days_with_revenue = [v for v in vals if v > 0]
                if days_with_revenue:
                    summary[f"{name}Avg"] = sum(days_with_revenue) / len(days_with_revenue)
        result["summary"] = summary

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 0) if e.response is not None else 0
        if status in (401, 403):
            logger.info("Revenue data not available (HTTP %s)", status)
            result["_errors"]["revenue"] = "Revenue data not available for this channel"
        else:
            logger.error("Analytics API error for revenue %s: %s", status, e)
            result["_errors"]["revenue"] = f"HTTP {status}: {str(e)}"
    except Exception as e:
        logger.error("Error fetching revenue data: %s", e)
        result["_errors"]["revenue"] = str(e)

    _clean_expired_cache()
    _set_cache(f"revenue:{ck}", result)
    return result


def export_analytics_data(
    access_token: str,
    channel_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Aggregate all analytics data for export."""
    overview = get_channel_overview(access_token)
    analytics = get_channel_analytics(access_token, channel_id, start_date, end_date)
    videos = get_top_videos(access_token, channel_id, start_date, end_date, max_results=50)
    traffic = get_traffic_sources(access_token, channel_id, start_date, end_date)
    audience = get_audience_demographics(access_token, channel_id, start_date, end_date)
    revenue = get_revenue_data(access_token, channel_id, start_date, end_date)

    return {
        "overview": overview,
        "analytics": analytics,
        "top_videos": videos,
        "traffic_sources": traffic,
        "audience_demographics": audience,
        "revenue": revenue,
        "date_range": {"start": start_date, "end": end_date},
        "generated_at": datetime.utcnow().isoformat(),
    }

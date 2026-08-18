"""YouTube Analytics routes (FastAPI).

Provides endpoints for channel overview, analytics, top videos,
traffic sources, audience demographics, revenue, and data export.
All endpoints require session authentication.
"""
import io
import csv
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse

from backend.services.auth_service import refresh_access_token
from backend.services.youtube_analytics import (
    get_channel_overview,
    get_channel_analytics,
    get_top_videos,
    get_traffic_sources,
    get_audience_demographics,
    get_revenue_data,
    export_analytics_data,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _auth_error() -> JSONResponse:
    return JSONResponse(
        {"error": True, "code": "AUTHENTICATION_REQUIRED", "title": "Login required",
         "message": "You must be logged in to access analytics.",
         "suggestion": "Connect your Google account in the Integrations page.",
         "retryable": False},
        status_code=401,
    )


def _default_date_range() -> tuple[str, str]:
    end = datetime.utcnow()
    start = end - timedelta(days=28)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _resolve_token(request: Request) -> str | None:
    access_token = request.session.get("access_token")
    if not access_token:
        return None

    refresh_token = request.session.get("refresh_token")
    if not refresh_token:
        return access_token

    try:
        _test_resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if _test_resp.status_code == 401:
            new_token = refresh_access_token(refresh_token)
            request.session["access_token"] = new_token
            return new_token
    except Exception as e:
        logger.debug("Token validation failed, using as-is: %s", e)

    return access_token


@router.get("/analytics/overview")
async def analytics_overview(request: Request):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    try:
        data = get_channel_overview(access_token)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error("Error in analytics overview: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load channel overview."},
            status_code=500,
        )


@router.get("/analytics/channel")
async def analytics_channel(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = get_channel_analytics(access_token, channel_id, start_date, end_date)
        return {
            "success": True,
            "data": data,
            "date_range": {"start": start_date, "end": end_date},
        }
    except Exception as e:
        logger.error("Error in analytics channel: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load channel analytics."},
            status_code=500,
        )


@router.get("/analytics/videos")
async def analytics_videos(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(10, ge=1, le=100, description="Max videos to return"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = get_top_videos(access_token, channel_id, start_date, end_date, max_results=limit)
        return {
            "success": True,
            "data": data,
            "date_range": {"start": start_date, "end": end_date},
        }
    except Exception as e:
        logger.error("Error in analytics videos: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load top videos."},
            status_code=500,
        )


@router.get("/analytics/traffic")
async def analytics_traffic(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = get_traffic_sources(access_token, channel_id, start_date, end_date)
        return {
            "success": True,
            "data": data,
            "date_range": {"start": start_date, "end": end_date},
        }
    except Exception as e:
        logger.error("Error in analytics traffic: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load traffic sources."},
            status_code=500,
        )


@router.get("/analytics/audience")
async def analytics_audience(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = get_audience_demographics(access_token, channel_id, start_date, end_date)
        return {
            "success": True,
            "data": data,
            "date_range": {"start": start_date, "end": end_date},
        }
    except Exception as e:
        logger.error("Error in analytics audience: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load audience demographics."},
            status_code=500,
        )


@router.get("/analytics/revenue")
async def analytics_revenue(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = get_revenue_data(access_token, channel_id, start_date, end_date)
        return {
            "success": True,
            "data": data,
            "date_range": {"start": start_date, "end": end_date},
        }
    except Exception as e:
        logger.error("Error in analytics revenue: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to load revenue data."},
            status_code=500,
        )


@router.get("/analytics/export")
async def analytics_export(
    request: Request,
    channel_id: str = Query(..., description="YouTube channel ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    format: str = Query("json", description="Export format: json or csv"),
):
    access_token = _resolve_token(request)
    if not access_token:
        return _auth_error()

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    try:
        data = export_analytics_data(access_token, channel_id, start_date, end_date)
    except Exception as e:
        logger.error("Error in analytics export: %s", e)
        return JSONResponse(
            {"success": False, "error": "Failed to export analytics data."},
            status_code=500,
        )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Section", "Metric", "Value"])
        ov = data.get("overview", {})
        for key in ["name", "subscriber_count", "total_videos", "total_views", "country"]:
            writer.writerow(["Overview", key, ov.get(key, "")])

        writer.writerow([])
        writer.writerow(["Analytics Time Series"])
        ts = data.get("analytics", {}).get("time_series", [])
        if ts:
            writer.writerow(["Date"] + list(ts[0].keys()))
            for row in ts:
                writer.writerow([row.get("day", "")] + list(row.values()))

        writer.writerow([])
        writer.writerow(["Top Videos"])
        for v in data.get("top_videos", []):
            writer.writerow([v.get("title", v.get("video", "")), v.get("views", 0), v.get("estimatedMinutesWatched", 0)])

        output.seek(0)
        filename = f"analytics_{channel_id}_{start_date}_{end_date}.csv"
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return {
        "success": True,
        "data": data,
        "date_range": {"start": start_date, "end": end_date},
    }

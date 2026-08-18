"""Supabase REST API client for the UpDownVid backend.

Uses the Supabase REST API (PostgREST) with the service-role key for
backend operations. Frontend uses the anon key via the Supabase JS client.
"""
import logging
import requests
from typing import Any, Dict, List, Optional

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Lightweight Supabase REST API client."""

    def __init__(self, url: str = "", key: str = ""):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.key = key or SUPABASE_SERVICE_ROLE_KEY
        self.rest_url = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def _request(
        self,
        method: str,
        table: str,
        *,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        filters: Optional[Dict] = None,
    ) -> requests.Response:
        """Make a REST API request to Supabase."""
        url = f"{self.rest_url}/{table}"
        headers = dict(self.headers)
        query_params = dict(params or {})

        if filters:
            for key, value in filters.items():
                query_params[key] = value

        resp = requests.request(
            method,
            url,
            json=data,
            params=query_params,
            headers=headers,
            timeout=15,
        )
        return resp

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: Optional[Dict] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """SELECT rows from a table."""
        params = {"select": columns}
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        resp = self._request("GET", table, params=params, filters=filters)
        resp.raise_for_status()
        return resp.json()

    def insert(self, table: str, data: Dict | List[Dict]) -> List[Dict]:
        """INSERT row(s) into a table."""
        resp = self._request("POST", table, data=data)
        resp.raise_for_status()
        return resp.json()

    def upsert(self, table: str, data: Dict | List[Dict]) -> List[Dict]:
        """UPSERT (insert or update) row(s) into a table."""
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        url = f"{self.rest_url}/{table}"
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def update(self, table: str, data: Dict, filters: Dict) -> List[Dict]:
        """UPDATE rows matching filters."""
        resp = self._request("PATCH", table, data=data, filters=filters)
        resp.raise_for_status()
        return resp.json()

    def delete(self, table: str, filters: Dict) -> List[Dict]:
        """DELETE rows matching filters."""
        resp = self._request("DELETE", table, filters=filters)
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, bucket: str, path: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to Supabase Storage."""
        url = f"{self.url}/storage/v1/object/upload/{bucket}/{path}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": content_type,
        }
        resp = requests.post(url, data=data, headers=headers, timeout=30)
        if resp.status_code in (200, 201, 409):  # 409 = already exists
            return True
        logger.warning("Storage upload failed (%s %d): %s", path, resp.status_code, resp.text[:200])
        return False

    def download_file(self, bucket: str, path: str) -> Optional[bytes]:
        """Download a file from Supabase Storage. Returns None on failure."""
        url = f"{self.url}/storage/v1/object/{bucket}/{path}"
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.content
        return None

    def file_exists(self, bucket: str, path: str) -> bool:
        """Check if a file exists in Supabase Storage."""
        url = f"{self.url}/storage/v1/object/info/{bucket}/{path}"
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}"}
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.status_code == 200

    def delete_file(self, bucket: str, path: str) -> bool:
        """Delete a file from Supabase Storage."""
        url = f"{self.url}/storage/v1/object/{bucket}/{path}"
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}"}
        resp = requests.delete(url, headers=headers, timeout=15)
        return resp.status_code in (200, 204, 404)

    def rpc(self, function_name: str, params: Optional[Dict] = None) -> Any:
        """Call a Supabase Edge Function / database function via REST."""
        url = f"{self.rest_url}/rpc/{function_name}"
        resp = requests.post(
            url,
            json=params or {},
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


# Singleton — import and use directly
supabase = SupabaseClient()

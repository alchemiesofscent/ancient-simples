from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SupabaseRestError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupabaseRestClient:
    supabase_url: str
    api_key: str

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        base = self.supabase_url.rstrip("/")
        url = f"{base}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"

        req_headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if headers:
            req_headers.update(headers)

        data: bytes | None = None
        if json_body is not None:
            req_headers["Content-Type"] = "application/json"
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url=url, method=method, headers=req_headers, data=data)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, dict(resp.headers.items()), resp.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            raise SupabaseRestError(
                f"{method} {url} -> HTTP {e.code}: {body.decode('utf-8', errors='replace')}"
            ) from e
        except urllib.error.URLError as e:
            raise SupabaseRestError(f"{method} {url} -> network error: {e}") from e

    def get_json(self, path: str, *, query: dict[str, str] | None = None) -> Any:
        status, _headers, body = self._request("GET", path, query=query)
        if status < 200 or status >= 300:
            raise SupabaseRestError(f"GET {path} unexpected status {status}")
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        *,
        on_conflict: str,
        return_representation: bool = False,
    ) -> None:
        if not rows:
            return
        prefer = "resolution=merge-duplicates"
        prefer += ",return=representation" if return_representation else ",return=minimal"
        self._request(
            "POST",
            f"/rest/v1/{table}",
            query={"on_conflict": on_conflict},
            headers={"Prefer": prefer},
            json_body=rows,
        )

    def count(self, table: str) -> int:
        status, headers, _body = self._request(
            "GET",
            f"/rest/v1/{table}",
            query={"select": "*", "limit": "1"},
            headers={"Prefer": "count=exact"},
        )
        if status < 200 or status >= 300:
            raise SupabaseRestError(f"count({table}) unexpected status {status}")

        content_range = headers.get("Content-Range") or headers.get("content-range") or ""
        if "/" not in content_range:
            raise SupabaseRestError(f"count({table}) missing Content-Range header")
        total = content_range.split("/", 1)[1]
        return int(total)


def _load_repo_dotenv_if_present() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env.local"
    if not dotenv_path.exists():
        return

    try:
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            os.environ.setdefault(key, value)
    except Exception:
        return


def env_required(name: str) -> str:
    _load_repo_dotenv_if_present()
    v = os.environ.get(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v

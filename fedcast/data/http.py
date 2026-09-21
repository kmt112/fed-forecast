from __future__ import annotations

import json
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (fedcast research tool)"


def get(url: str, params: dict[str, str] | None = None, timeout: int = 30) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_json(url: str, params: dict[str, str] | None = None) -> dict:
    return json.loads(get(url, params))


def get_text(url: str, params: dict[str, str] | None = None) -> str:
    raw = get(url, params)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:  # federalreserve.gov serves some pages as Windows-1252
        return raw.decode("cp1252", errors="replace")

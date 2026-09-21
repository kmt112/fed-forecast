from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

BROWSER_UA = "Mozilla/5.0 (fedcast research tool)"  # Yahoo and federalreserve.gov expect a browser-like agent
# FRED stalls connections from agents it does not recognise (browser-like or custom); the stock urllib agent is accepted
PLAIN_UA = f"Python-urllib/{sys.version_info.major}.{sys.version_info.minor}"


def get(url: str, params: dict[str, str] | None = None, timeout: int = 30,
        user_agent: str = BROWSER_UA) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_json(url: str, params: dict[str, str] | None = None, user_agent: str = BROWSER_UA) -> dict:
    return json.loads(get(url, params, user_agent=user_agent))


def get_text(url: str, params: dict[str, str] | None = None) -> str:
    raw = get(url, params)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:  # federalreserve.gov serves some pages as Windows-1252
        return raw.decode("cp1252", errors="replace")

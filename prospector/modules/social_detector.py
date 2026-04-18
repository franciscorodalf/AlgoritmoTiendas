"""
social_detector.py
------------------
Detecta perfiles de Instagram y Facebook de un negocio vía DuckDuckGo.

Útil para ajustar el pitch de ventas: un negocio con Instagram activo
pero sin web tiene un argumento de venta distinto a uno sin presencia.
"""

from __future__ import annotations

import re
from typing import Optional

try:
    from ddgs import DDGS
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


_RE_INSTA = re.compile(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)", re.I)
_RE_FB    = re.compile(r"https?://(?:www\.)?facebook\.com/([^/?#\s]+)", re.I)

_FB_SKIP = {"pages", "pg", "people", "sharer", "login", "dialog"}


def _first_match(results: list[dict], regex: re.Pattern) -> Optional[str]:
    for r in results:
        url = r.get("href", "")
        m = regex.search(url)
        if m:
            return m.group(0).split("?")[0].rstrip("/")
    return None


def find_instagram(name: str, city: str = "") -> Optional[str]:
    if not _AVAILABLE:
        return None
    try:
        q = f'"{name}" {city} instagram'.strip()
        results = list(DDGS().text(q, max_results=6, region="es-es"))
        for r in results:
            url = r.get("href", "")
            m = _RE_INSTA.search(url)
            if m:
                handle = m.group(1).rstrip("/")
                if handle.lower() not in {"p", "explore", "reel", "tv"}:
                    return "https://instagram.com/" + handle
    except Exception:
        pass
    return None


def find_facebook(name: str, city: str = "") -> Optional[str]:
    if not _AVAILABLE:
        return None
    try:
        q = f'"{name}" {city} facebook'.strip()
        results = list(DDGS().text(q, max_results=6, region="es-es"))
        for r in results:
            url = r.get("href", "")
            m = _RE_FB.search(url)
            if m:
                slug = m.group(1).split("/")[0].lower()
                if slug not in _FB_SKIP:
                    return m.group(0).split("?")[0].rstrip("/")
    except Exception:
        pass
    return None


def detect(name: str, address: str = "") -> dict:
    """Devuelve {'instagram': url|None, 'facebook': url|None}."""
    if not _AVAILABLE:
        return {"instagram": None, "facebook": None}
    city = address.split(",")[0].strip() if address else ""
    return {
        "instagram": find_instagram(name, city),
        "facebook":  find_facebook(name, city),
    }


def available() -> bool:
    return _AVAILABLE


__all__ = ["detect", "find_instagram", "find_facebook", "available"]

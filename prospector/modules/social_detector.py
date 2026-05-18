"""
social_detector.py
------------------
Detecta perfiles de Instagram, Facebook y TikTok de un negocio vía DuckDuckGo.

Útil para ajustar el pitch de ventas: un negocio con Instagram/TikTok activo
pero sin web tiene un argumento de venta distinto a uno sin presencia.
"""

from __future__ import annotations

import re
import time
from typing import Optional

try:
    from ddgs import DDGS
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


_RE_INSTA = re.compile(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)", re.I)
_RE_FB    = re.compile(r"https?://(?:www\.)?(?:m\.|web\.)?facebook\.com/([^/?#\s]+)", re.I)
_RE_TT    = re.compile(r"https?://(?:www\.|m\.)?tiktok\.com/@([a-zA-Z0-9_.]+)", re.I)

# Slugs de Facebook que NO son páginas de negocio
_FB_SKIP = {"pages", "pg", "people", "sharer", "login", "dialog",
            "events", "groups", "watch", "marketplace", "story.php",
            "profile.php", "permalink.php", "notes", "search", "help"}

# Handles de Instagram que NO son cuentas reales
_IG_SKIP = {"p", "explore", "reel", "reels", "tv", "stories",
            "accounts", "direct", "about", "developers"}

# Handles de TikTok que NO son cuentas reales (rutas internas)
_TT_SKIP = {"discover", "tag", "music", "trending", "live", "explore"}

# Delay por defecto entre llamadas DDG. DDG empieza a bloquear con bursts
# >5 queries/segundo. 0.6 s da margen.
_DEFAULT_DELAY = 0.6


def _ddgs_text(session, query: str, max_results: int = 6) -> list[dict]:
    """Lanza una búsqueda con la sesión dada. Lanza si falla."""
    return list(session.text(query, max_results=max_results, region="es-es"))


def _extract_instagram(results: list[dict]) -> Optional[str]:
    for r in results:
        url = r.get("href", "")
        m = _RE_INSTA.search(url)
        if not m:
            continue
        handle = m.group(1).rstrip("/").lower()
        if handle and handle not in _IG_SKIP:
            return "https://instagram.com/" + handle
    return None


def _extract_facebook(results: list[dict]) -> Optional[str]:
    for r in results:
        url = r.get("href", "")
        m = _RE_FB.search(url)
        if not m:
            continue
        slug = m.group(1).split("/")[0].lower()
        if slug and slug not in _FB_SKIP:
            return m.group(0).split("?")[0].rstrip("/")
    return None


def _extract_tiktok(results: list[dict]) -> Optional[str]:
    for r in results:
        url = r.get("href", "")
        m = _RE_TT.search(url)
        if not m:
            continue
        handle = m.group(1).rstrip("/").lower()
        if handle and handle not in _TT_SKIP:
            return "https://tiktok.com/@" + handle
    return None


def empty_result() -> dict:
    """Estructura vacía (claves estables para el resto del pipeline)."""
    return {"instagram": None, "facebook": None, "tiktok": None}


def detect(
    name: str,
    address: str = "",
    *,
    delay: float = _DEFAULT_DELAY,
    include_tiktok: bool = True,
) -> dict:
    """
    Devuelve {'instagram': url|None, 'facebook': url|None, 'tiktok': url|None}.

    Usa una única sesión DDGS para las búsquedas (más eficiente y menos
    propenso a bloqueo) y aplica `delay` entre ellas. Si DDG falla en una
    búsqueda, el campo correspondiente queda en None pero no propagamos
    el error (a diferencia de web_verifier, aquí los None no son cascada
    crítica — el caller puede decidir conservar valores previos).

    `include_tiktok=False` salta la tercera búsqueda DDG si te importa más
    la velocidad/cuota que TikTok.
    """
    if not _AVAILABLE:
        return empty_result()
    city = address.split(",")[0].strip() if address else ""

    insta_url: Optional[str] = None
    fb_url: Optional[str] = None
    tt_url: Optional[str] = None
    try:
        session = DDGS()
        try:
            insta_url = _extract_instagram(
                _ddgs_text(session, f'"{name}" {city} instagram'.strip())
            )
        except Exception:
            pass
        time.sleep(delay)
        try:
            fb_url = _extract_facebook(
                _ddgs_text(session, f'"{name}" {city} facebook'.strip())
            )
        except Exception:
            pass
        if include_tiktok:
            time.sleep(delay)
            try:
                tt_url = _extract_tiktok(
                    _ddgs_text(session, f'"{name}" {city} tiktok'.strip())
                )
            except Exception:
                pass
    except Exception:
        # No se pudo crear la sesión DDG en absoluto
        pass
    return {"instagram": insta_url, "facebook": fb_url, "tiktok": tt_url}


def find_instagram(name: str, city: str = "") -> Optional[str]:
    """Atajo: solo Instagram (compatibilidad)."""
    return detect(name, city, include_tiktok=False).get("instagram")


def find_facebook(name: str, city: str = "") -> Optional[str]:
    """Atajo: solo Facebook (compatibilidad)."""
    return detect(name, city, include_tiktok=False).get("facebook")


def find_tiktok(name: str, city: str = "") -> Optional[str]:
    """Atajo: solo TikTok."""
    return detect(name, city).get("tiktok")


def available() -> bool:
    return _AVAILABLE


__all__ = [
    "detect", "empty_result",
    "find_instagram", "find_facebook", "find_tiktok",
    "available",
]

"""
web_auditor.py
--------------
Audita una URL para clasificar la presencia digital del negocio.

A diferencia del filtro binario "tiene web / no tiene web", esto da una
clasificación útil para personalizar el outreach:

  - none          : no hay URL → lead frío (no le importa la presencia)
  - social_only   : la URL es Facebook/Instagram → lead premium
  - free_builder  : Wix gratis, WordPress.com, web.app, gx.do, etc. → premium
  - obsolete      : web propia, pero sin SSL, sin viewport, o claramente vieja
  - good          : web moderna, no es target

El auditor hace UNA petición HTTP por dominio (HEAD si es posible, GET
ligero si no), con timeout corto. Si falla la petición devolvemos el
mejor diagnóstico posible solo con la URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Hosts que NO son web propia
# ---------------------------------------------------------------------------

_SOCIAL_HOSTS: frozenset[str] = frozenset({
    "facebook.com", "m.facebook.com", "fb.com", "fb.me", "web.facebook.com",
    "instagram.com", "linktr.ee", "lnk.bio",
    "twitter.com", "x.com", "t.co",
    "tiktok.com", "youtube.com", "youtu.be",
    "wa.me", "whatsapp.com", "chat.whatsapp.com",
    "google.com", "maps.google.com", "g.page", "goo.gl",
})

_DIRECTORY_HOSTS: frozenset[str] = frozenset({
    "tripadvisor.com", "tripadvisor.es", "yelp.com", "yelp.es",
    "thefork.es", "thefork.com", "elTenedor.es",
    "paginasamarillas.es", "yellow.es", "guiadeempresas.com",
    "einforma.com", "axesor.es",
})

# Plataformas "gratis" — el negocio probablemente las hizo él mismo
# y son fáciles de reemplazar por una web propia.
_FREE_BUILDER_PATTERNS: tuple[str, ...] = (
    ".wixsite.com", ".wix.com", ".wordpress.com", ".blogspot.com",
    ".webnode.es", ".webnode.com", ".jimdo.com", ".jimdosite.com",
    ".weebly.com", ".strikingly.com", ".square.site", ".godaddysites.com",
    ".webs.com", ".my-free.website", ".sitio.mx", ".webcindario.com",
    ".000webhostapp.com", ".carrd.co", ".bandcamp.com",
    ".github.io", ".netlify.app", ".vercel.app",
    ".myportfolio.com", ".tumblr.com",
)

# Generadores conocidos (header `generator` o meta tag) que en sí
# no dicen "obsoleto" pero están en el radar.
_GENERATOR_RE = re.compile(
    r'<meta\s+name=["\']generator["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_VIEWPORT_RE = re.compile(r'<meta\s+name=["\']viewport["\']', re.IGNORECASE)
_YEAR_RE = re.compile(r"©\s*(?:&copy;\s*)?(20\d{2})")


@dataclass
class AuditResult:
    category: str             # none|social_only|free_builder|obsolete|good|unknown
    https: bool
    mobile_ready: bool
    last_year_in_footer: int | None
    generator: str | None
    final_url: str | None
    error: str | None
    is_target: bool           # True si vale la pena pitchear (cualquier ≠ good)

    def to_dict(self) -> dict:
        return {
            "category":            self.category,
            "https":               self.https,
            "mobile_ready":        self.mobile_ready,
            "last_year_in_footer": self.last_year_in_footer,
            "generator":           self.generator,
            "final_url":           self.final_url,
            "error":               self.error,
            "is_target":           self.is_target,
        }


def _host(url: str) -> str:
    return re.sub(r"^https?://", "", url).split("/")[0].lower().lstrip("www.")


def _classify_by_host(url: str) -> str | None:
    """Clasificación rápida por hostname sin red."""
    host = _host(url)
    if not host:
        return None
    if any(host == h or host.endswith("." + h) for h in _SOCIAL_HOSTS):
        return "social_only"
    if any(host == h or host.endswith("." + h) for h in _DIRECTORY_HOSTS):
        return "social_only"   # tratado igual: no es web propia
    for p in _FREE_BUILDER_PATTERNS:
        if host.endswith(p):
            return "free_builder"
    return None


def audit(url: str | None, *, timeout: float = 5.0) -> AuditResult:
    """Audita una URL. Si `url` es None devuelve category='none'."""
    if not url:
        return AuditResult(
            category="none", https=False, mobile_ready=False,
            last_year_in_footer=None, generator=None, final_url=None,
            error=None, is_target=True,
        )

    by_host = _classify_by_host(url)
    if by_host:
        return AuditResult(
            category=by_host, https=url.startswith("https://"),
            mobile_ready=False, last_year_in_footer=None, generator=None,
            final_url=url, error=None, is_target=True,
        )

    if not _HAS_REQUESTS:
        return AuditResult(
            category="unknown", https=url.startswith("https://"),
            mobile_ready=False, last_year_in_footer=None, generator=None,
            final_url=url, error="requests no instalado",
            is_target=False,  # conservador: no hacemos pitch sobre desconocido
        )

    try:
        resp = requests.get(
            url, timeout=timeout, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ProspectorBot/1.0)"},
        )
    except Exception as exc:
        # No carga → web rota / sitio caído. Es target premium.
        return AuditResult(
            category="obsolete", https=url.startswith("https://"),
            mobile_ready=False, last_year_in_footer=None, generator=None,
            final_url=url, error=f"sin respuesta: {exc.__class__.__name__}",
            is_target=True,
        )

    final_url = resp.url
    https = final_url.startswith("https://")

    # Re-clasificar por host final por si redirigió a una red social
    by_final_host = _classify_by_host(final_url)
    if by_final_host:
        return AuditResult(
            category=by_final_host, https=https,
            mobile_ready=False, last_year_in_footer=None, generator=None,
            final_url=final_url, error=None, is_target=True,
        )

    html = resp.text[:80_000] if resp.text else ""
    mobile = bool(_VIEWPORT_RE.search(html))
    gen_m = _GENERATOR_RE.search(html)
    generator = gen_m.group(1).strip() if gen_m else None
    year_m = _YEAR_RE.search(html)
    last_year = int(year_m.group(1)) if year_m else None

    # Heurísticas para "obsoleta": HTTP, sin viewport, footer con año < 2022,
    # o respuesta HTTP no 2xx.
    is_obsolete = (
        not https
        or not mobile
        or (last_year is not None and last_year < 2022)
        or resp.status_code >= 400
    )

    if is_obsolete:
        return AuditResult(
            category="obsolete", https=https, mobile_ready=mobile,
            last_year_in_footer=last_year, generator=generator,
            final_url=final_url, error=None, is_target=True,
        )

    return AuditResult(
        category="good", https=https, mobile_ready=mobile,
        last_year_in_footer=last_year, generator=generator,
        final_url=final_url, error=None, is_target=False,
    )


def available() -> bool:
    return _HAS_REQUESTS


__all__ = ["AuditResult", "audit", "available"]

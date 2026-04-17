"""
web_verifier.py
---------------
Verificación secundaria de webs: detecta falsos positivos de Google Places.

Google Places a veces devuelve negocios con `website=None` aunque tienen web
(p. ej. ayuntamientos, negocios con web en redes sociales, etc.).

Este módulo hace una búsqueda en DuckDuckGo por cada candidato y descarta
los que claramente tienen página web propia.

Dependencia: pip install ddgs
"""

from __future__ import annotations

import re
import time
from typing import Callable

try:
    from ddgs import DDGS
    _HAS_DDGS = True
except ImportError:
    _HAS_DDGS = False

# ---------------------------------------------------------------------------
# Dominios que NO cuentan como "web propia del negocio"
# (directorios, redes sociales, agregadores…)
# ---------------------------------------------------------------------------

_SKIP_DOMAINS: set[str] = {
    "google.com", "google.es", "maps.google.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tripadvisor.com", "tripadvisor.es", "yelp.com", "yelp.es",
    "booking.com", "foursquare.com", "linkedin.com",
    "yellow.es", "paginasamarillas.es", "guiadeempresas.com",
    "empresite.es", "cylex.es", "infobel.com",
    "wikipedia.org", "wikimedia.org",
    "elconfidencial.com", "lavanguardia.com", "elmundo.es",
    "20minutos.es", "eldiario.es",
    # Directorios de empresas locales
    "einforma.com", "axesor.es", "ecoem.es",
}

# ---------------------------------------------------------------------------
# Palabras en el nombre que indican entidades públicas (casi siempre tienen web)
# ---------------------------------------------------------------------------

_PUBLIC_KEYWORDS: list[str] = [
    "ayuntamiento", "municipio", "cabildo", "gobierno", "consejería",
    "ministerio", "diputación", "administración pública",
    "instituto público", "colegio público", "universidad", "hospital público",
]


def _is_public_entity(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in _PUBLIC_KEYWORDS)


def _domain(url: str) -> str:
    return re.sub(r"https?://", "", url).split("/")[0].lower().lstrip("www.")


def _is_own_website(url: str) -> bool:
    """True si la URL parece la web propia del negocio (no un directorio)."""
    d = _domain(url)
    return not any(skip in d for skip in _SKIP_DOMAINS)


def find_website(name: str, address: str, timeout: int = 8) -> str | None:
    """
    Busca la web oficial de un negocio en DuckDuckGo.

    Devuelve la URL si la encuentra, None si no hay evidencia de web propia.
    """
    if not _HAS_DDGS:
        return None

    # Entidades públicas: asumimos directamente que tienen web
    if _is_public_entity(name):
        return f"(entidad pública — asumir web)"

    city = address.split(",")[0].strip() if address else ""
    query = f'"{name}" {city} sitio web oficial'

    try:
        results = list(DDGS().text(query, max_results=6, region="es-es"))
        for r in results:
            url = r.get("href", "")
            if url and _is_own_website(url):
                return url
    except Exception:
        pass

    return None


def filter_no_website(
    businesses: list,
    log_fn: Callable[[str], None] | None = None,
    delay: float = 0.6,
) -> list:
    """
    Recibe la lista candidata de Google Places y elimina los que
    realmente sí tienen web (falsos positivos).

    Parameters
    ----------
    businesses : lista de Business
    log_fn     : función de logging (recibe un str)
    delay      : segundos entre búsquedas (respetar rate-limit de DDG)
    """
    if not _HAS_DDGS:
        if log_fn:
            log_fn("⚠ ddgs no instalado — sin verificación secundaria (pip install ddgs)")
        return businesses

    confirmed = []
    for biz in businesses:
        url = find_website(biz.name, biz.address)
        if url:
            if log_fn:
                log_fn(f"   ⏭ {biz.name} — web encontrada ({url[:60]})")
        else:
            confirmed.append(biz)
        time.sleep(delay)

    return confirmed


def available() -> bool:
    return _HAS_DDGS


__all__ = ["find_website", "filter_no_website", "available"]

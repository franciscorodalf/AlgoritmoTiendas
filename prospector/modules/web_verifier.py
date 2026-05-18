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


# Sentinel devuelto cuando el negocio es una entidad pública (no consultamos
# DDG, asumimos que tiene web). Caller distingue por identidad.
PUBLIC_ENTITY = "__public_entity__"


class VerificationFailed(RuntimeError):
    """Se lanza cuando DDG falla (rate limit, timeout, etc.)."""


def find_website(name: str, address: str, timeout: int = 8) -> str | None:
    """
    Busca la web oficial de un negocio en DuckDuckGo.

    Devuelve:
      - la URL si encuentra una web propia,
      - PUBLIC_ENTITY si el negocio es una entidad pública (asumimos web),
      - None si DDG no encontró evidencia de web propia.

    Lanza VerificationFailed si DDG falla (rate limit o red).
    """
    if not _HAS_DDGS:
        return None

    # Entidades públicas: no gastamos query DDG
    if _is_public_entity(name):
        return PUBLIC_ENTITY

    city = address.split(",")[0].strip() if address else ""
    query = f'"{name}" {city} sitio web oficial'

    try:
        results = list(DDGS().text(query, max_results=6, region="es-es"))
    except Exception as exc:
        # rate limit / red / timeout — propagamos para que el caller
        # pueda abortar o aplicar backoff
        raise VerificationFailed(str(exc)) from exc

    for r in results:
        url = r.get("href", "")
        if url and _is_own_website(url):
            return url
    return None


def filter_no_website(
    businesses: list,
    log_fn: Callable[[str], None] | None = None,
    delay: float = 0.6,
    max_consecutive_errors: int = 3,
) -> list:
    """
    Recibe la lista candidata de Google Places y elimina los que
    realmente sí tienen web (falsos positivos).

    Si DDG empieza a fallar repetidamente (rate limit), abortamos la
    verificación para no quemar más segundos y devolvemos los restantes
    como NO verificados — el caller puede decidir qué hacer con ellos.

    Parameters
    ----------
    businesses : lista de Business
    log_fn     : función de logging (recibe un str)
    delay      : segundos entre búsquedas (respetar rate-limit de DDG)
    max_consecutive_errors : si DDG falla N veces seguidas, abortamos.
    """
    if not _HAS_DDGS:
        if log_fn:
            log_fn("⚠ ddgs no instalado — sin verificación secundaria (pip install ddgs)")
        return businesses

    confirmed: list = []
    consecutive_errors = 0

    for i, biz in enumerate(businesses):
        try:
            url = find_website(biz.name, biz.address)
            consecutive_errors = 0
        except VerificationFailed as exc:
            consecutive_errors += 1
            if log_fn:
                log_fn(f"   ⚠ DDG error en {biz.name}: {exc}")
            if consecutive_errors >= max_consecutive_errors:
                # Abortamos: los restantes pasan SIN verificar (mejor que
                # falsos positivos en cascada). El caller verá cuántos.
                remaining = businesses[i:]
                if log_fn:
                    log_fn(f"   ✗ {consecutive_errors} errores DDG seguidos — "
                           f"abortando verificación, {len(remaining)} sin verificar")
                confirmed.extend(remaining)
                return confirmed
            # No incluimos este biz; reintenta con el siguiente
            time.sleep(delay * 2)
            continue

        if url is None:
            confirmed.append(biz)
        elif url is PUBLIC_ENTITY:
            if log_fn:
                log_fn(f"   ⏭ {biz.name} — entidad pública (descartado)")
        else:
            if log_fn:
                log_fn(f"   ⏭ {biz.name} — web encontrada ({url[:60]})")
        time.sleep(delay)

    return confirmed


def available() -> bool:
    return _HAS_DDGS


__all__ = [
    "find_website", "filter_no_website", "available",
    "PUBLIC_ENTITY", "VerificationFailed",
]

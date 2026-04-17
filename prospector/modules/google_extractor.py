"""
google_extractor.py
-------------------
Busca negocios locales en Google Places y extrae sus datos.

Entrada flexible:
    - Nombre concreto:       "Barbería El Rincón Santa Cruz"
    - Zona:                  "La Laguna, Tenerife"
    - Sector:                "peluquerías"
    - Sector + zona:         "peluquerías en La Laguna"
    - Lista libre:           cualquier texto que entienda Google Places

Salida: lista de diccionarios `Business` con todos los datos necesarios.
Filtro: descarta negocios que YA tengan página web (son los que nos interesan).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Iterable

import googlemaps
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------


@dataclass
class Business:
    """Datos de un negocio extraídos de Google Places."""

    place_id: str
    name: str
    category: str                      # tipo principal (ej. "restaurant")
    categories_all: list[str]          # todos los tipos que devuelve Google
    address: str
    phone: str | None
    website: str | None                # si existe ya, el negocio se descartará
    rating: float | None
    review_count: int
    opening_hours: list[str]           # horario en formato legible
    reviews: list[dict]                # [{author, rating, text, time}]
    photo_references: list[str]        # IDs de fotos para descargar luego
    location: dict                     # {"lat": ..., "lng": ...}
    maps_url: str
    price_level: int | None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------


class GoogleExtractor:
    """Envoltorio sobre googlemaps que simplifica búsquedas y extracción."""

    # Campos que pedimos en place_details. Se factura por grupo de campos,
    # así que pedimos solo lo que usamos.
    _DETAIL_FIELDS = [
        "place_id",
        "name",
        "type",
        "formatted_address",
        "international_phone_number",
        "website",
        "rating",
        "user_ratings_total",
        "opening_hours",
        "review",
        "photo",
        "geometry/location",
        "url",
        "price_level",
    ]

    def __init__(self, api_key: str | None = None, language: str | None = None):
        key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not key or key == "tu_api_key_aqui":
            raise RuntimeError(
                "Falta GOOGLE_PLACES_API_KEY. Configúrala en .env "
                "(copia .env.example y rellena la clave)."
            )
        self.client = googlemaps.Client(key=key)
        self.language = language or os.getenv("DEFAULT_LANGUAGE", "es")
        self.default_region = os.getenv("DEFAULT_REGION", "Tenerife, España")

    # ---------------- búsqueda de alto nivel ----------------

    def search(
        self,
        query: str,
        *,
        region: str | None = None,
        max_results: int = 20,
        only_without_website: bool = True,
        throttle: float = 0.15,
    ) -> list[Business]:
        """
        Busca negocios con una query libre. Si no pasas región, se añade
        automáticamente la región por defecto (Tenerife) al final de la query
        para sesgar resultados.

        Parameters
        ----------
        query : cualquier cosa que entienda Google Maps
        region : sobrescribe DEFAULT_REGION del .env
        max_results : corte duro (Places devuelve hasta 60 paginando)
        only_without_website : si True, filtra negocios que ya tengan web
        throttle : segundos entre detalles (suaves con la API)
        """
        full_query = self._compose_query(query, region)
        place_ids = self._text_search_all_pages(full_query, max_results)

        businesses: list[Business] = []
        for pid in place_ids:
            try:
                biz = self._fetch_details(pid)
            except Exception as exc:  # pragma: no cover - red, no determinista
                print(f"[google_extractor] error en {pid}: {exc}")
                continue

            if only_without_website and biz.website:
                continue  # ya tiene web → no es nuestro target

            businesses.append(biz)
            time.sleep(throttle)

        return businesses

    def search_many(
        self,
        queries: Iterable[str],
        **kwargs,
    ) -> list[Business]:
        """Útil para batches: pasa una lista de queries y devuelve todo junto."""
        seen: set[str] = set()
        out: list[Business] = []
        for q in queries:
            for biz in self.search(q, **kwargs):
                if biz.place_id in seen:
                    continue
                seen.add(biz.place_id)
                out.append(biz)
        return out

    def search_nearby(
        self,
        lat: float,
        lng: float,
        radius_m: int = 2000,
        *,
        only_without_website: bool = True,
        max_results: int = 30,
        throttle: float = 0.15,
        skip_ids: set[str] | None = None,
    ) -> list[Business]:
        """
        Busca TODOS los negocios en un área circular (sin filtro de tipo).
        Útil para explorar una zona completa y encontrar cualquier local sin web.

        Parameters
        ----------
        lat, lng   : centro del área (WGS-84)
        radius_m   : radio en metros (máx. 50 000 m según Google)
        skip_ids   : place_ids a ignorar (ya procesados previamente)
        """
        skip = skip_ids or set()
        place_ids = self._nearby_all_pages(lat, lng, radius_m, max_results)

        businesses: list[Business] = []
        for pid in place_ids:
            if pid in skip:
                continue
            try:
                biz = self._fetch_details(pid)
            except Exception as exc:
                print(f"[google_extractor] error en {pid}: {exc}")
                continue
            if only_without_website and biz.website:
                continue
            businesses.append(biz)
            time.sleep(throttle)

        return businesses

    def _nearby_all_pages(
        self, lat: float, lng: float, radius_m: int, max_results: int
    ) -> list[str]:
        """Pagina places_nearby hasta max_results o 3 páginas (60 resultados)."""
        ids: list[str] = []
        page_token = None
        pages = 0
        while True:
            kwargs: dict = {
                "location": (lat, lng),
                "radius": radius_m,
                "language": self.language,
            }
            if page_token:
                kwargs["page_token"] = page_token
            resp = self.client.places_nearby(**kwargs)
            for r in resp.get("results", []):
                pid = r.get("place_id")
                if pid and pid not in ids:
                    ids.append(pid)
                if len(ids) >= max_results:
                    return ids
            page_token = resp.get("next_page_token")
            pages += 1
            if not page_token or pages >= 3:
                break
            time.sleep(2)
        return ids

    # ---------------- helpers internos ----------------

    def _compose_query(self, query: str, region: str | None) -> str:
        region = region if region is not None else self.default_region
        if not region:
            return query
        # Si el usuario ya nombró la región no la duplicamos.
        q_low = query.lower()
        region_tokens = [t.strip().lower() for t in region.split(",") if t.strip()]
        if any(t in q_low for t in region_tokens):
            return query
        return f"{query} en {region}"

    def _text_search_all_pages(self, query: str, max_results: int) -> list[str]:
        """Pagina hasta agotar o llegar al máximo. Devuelve place_ids únicos."""
        ids: list[str] = []
        page_token = None
        pages = 0
        while True:
            kwargs = {"query": query, "language": self.language}
            if page_token:
                kwargs["page_token"] = page_token
            resp = self.client.places(**kwargs)
            for r in resp.get("results", []):
                pid = r.get("place_id")
                if pid and pid not in ids:
                    ids.append(pid)
                if len(ids) >= max_results:
                    return ids
            page_token = resp.get("next_page_token")
            pages += 1
            if not page_token or pages >= 3:  # Google solo da 3 páginas = 60 resultados
                break
            # El token tarda unos segundos en activarse.
            time.sleep(2)
        return ids

    def _fetch_details(self, place_id: str) -> Business:
        resp = self.client.place(
            place_id=place_id,
            fields=self._DETAIL_FIELDS,
            language=self.language,
        )
        r = resp.get("result", {})

        types = r.get("types", []) or []
        reviews = [
            {
                "author": rv.get("author_name"),
                "rating": rv.get("rating"),
                "text": rv.get("text", ""),
                "time": rv.get("time"),
            }
            for rv in r.get("reviews", []) or []
        ]

        opening = []
        oh = r.get("opening_hours") or {}
        if "weekday_text" in oh:
            opening = list(oh["weekday_text"])

        photos = [p["photo_reference"] for p in r.get("photos", []) or []]
        loc = (r.get("geometry") or {}).get("location", {}) or {}

        return Business(
            place_id=r.get("place_id", place_id),
            name=r.get("name", ""),
            category=types[0] if types else "",
            categories_all=types,
            address=r.get("formatted_address", ""),
            phone=r.get("international_phone_number"),
            website=r.get("website"),
            rating=r.get("rating"),
            review_count=r.get("user_ratings_total", 0) or 0,
            opening_hours=opening,
            reviews=reviews,
            photo_references=photos,
            location={"lat": loc.get("lat"), "lng": loc.get("lng")},
            maps_url=r.get("url", ""),
            price_level=r.get("price_level"),
        )

    # ---------------- utilidades ----------------

    def download_photo(self, photo_reference: str, max_width: int = 800) -> bytes:
        """
        Descarga el binario de una foto de Google Places.
        Se usa más adelante por image_analyzer.py para extraer paleta.
        """
        result = self.client.places_photo(
            photo_reference=photo_reference,
            max_width=max_width,
        )
        return b"".join(chunk for chunk in result if chunk)


__all__ = ["GoogleExtractor", "Business"]

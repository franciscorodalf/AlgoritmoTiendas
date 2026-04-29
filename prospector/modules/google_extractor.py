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
# Whitelist de tipos comerciales (SMB con web potencial)
# ---------------------------------------------------------------------------
#
# Estos son los tipos que pasan al pipeline. Cualquier resultado de
# `places_nearby` cuyo `types` no intersecte con esta lista se descarta
# antes de llamar a `place_details` (que es lo caro). Esto evita procesar
# paradas de guagua, parkings, ATMs, ayuntamientos, etc.

_COMMERCIAL_TYPES: frozenset[str] = frozenset({
    # Comida / bebida
    "restaurant", "meal_takeaway", "meal_delivery", "food", "bar",
    "bakery", "cafe", "ice_cream_shop", "night_club",
    # Belleza
    "hair_care", "nail_salon", "barber_shop",
    "beauty_salon", "spa",
    # Floristería
    "florist",
    # Salud privada
    "dentist", "doctor", "physiotherapist", "veterinary_care",
    "pharmacy",
    # Automoción
    "car_repair", "car_dealer", "car_wash",
    # Moda / retail
    "clothing_store", "shoe_store", "jewelry_store",
    # Fitness
    "gym", "fitness_center",
    # Otros SMB con web potencial
    "book_store", "pet_store", "electronics_store",
    "furniture_store", "home_goods_store", "hardware_store",
    "bicycle_store", "liquor_store",
    "real_estate_agency", "travel_agency", "lawyer", "accounting",
    "laundry", "moving_company", "locksmith", "plumber", "electrician",
    "tourist_attraction",
})

# Tipos que NUNCA queremos, aunque en raros casos compartan etiqueta
# con algo comercial. Solo se aplica al modo nearby.
_BLACKLIST_TYPES: frozenset[str] = frozenset({
    "parking", "transit_station", "bus_station", "train_station",
    "subway_station", "taxi_stand", "light_rail_station", "airport",
    "atm", "gas_station",
    "city_hall", "local_government_office", "embassy", "courthouse",
    "post_office", "fire_station", "police",
    "school", "primary_school", "secondary_school", "university",
    "cemetery", "funeral_home",
    "park", "zoo",
    "intersection", "route", "street_address", "premise",
})


def _is_commercial(types: list[str] | None) -> bool:
    """True si la lista de tipos contiene al menos un tipo comercial y
    ningún tipo de la blacklist."""
    if not types:
        return False
    tset = set(types)
    if tset & _BLACKLIST_TYPES:
        return False
    return bool(tset & _COMMERCIAL_TYPES)


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
        # Contadores de uso de la API (para auditoría de coste)
        self.calls_text_search = 0
        self.calls_nearby = 0
        self.calls_place_details = 0
        self.calls_photo = 0

    def reset_counters(self) -> None:
        self.calls_text_search = 0
        self.calls_nearby = 0
        self.calls_place_details = 0
        self.calls_photo = 0

    def usage(self) -> dict:
        return {
            "text_search":   self.calls_text_search,
            "nearby":        self.calls_nearby,
            "place_details": self.calls_place_details,
            "photo":         self.calls_photo,
            "total":         (self.calls_text_search + self.calls_nearby
                              + self.calls_place_details + self.calls_photo),
        }

    # ---------------- búsqueda de alto nivel ----------------

    def search(
        self,
        query: str,
        *,
        region: str | None = None,
        max_results: int = 20,
        only_without_website: bool = True,
        throttle: float = 0.15,
        skip_ids: set[str] | None = None,
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
        skip_ids : place_ids a ignorar (ya procesados previamente). Se filtran
                   ANTES de pedir place_details, así no malgastamos cuota.
        """
        skip = skip_ids or set()
        full_query = self._compose_query(query, region)
        candidates = self._text_search_all_pages(full_query, max_results)

        businesses: list[Business] = []
        for pid, _types in candidates:
            if pid in skip:
                continue
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
        """Útil para batches: pasa una lista de queries y devuelve todo junto.

        Si pasas `skip_ids` lo respeta; además acumula los pids ya devueltos
        para no duplicar entre queries del mismo batch.
        """
        accumulated_skip = set(kwargs.pop("skip_ids", None) or set())
        out: list[Business] = []
        for q in queries:
            results = self.search(q, skip_ids=accumulated_skip, **kwargs)
            for biz in results:
                accumulated_skip.add(biz.place_id)
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
        commercial_only: bool = True,
    ) -> list[Business]:
        """
        Busca negocios en un área circular.

        Parameters
        ----------
        lat, lng   : centro del área (WGS-84)
        radius_m   : radio en metros (máx. 50 000 m según Google)
        skip_ids   : place_ids a ignorar (ya procesados previamente).
                     Filtran ANTES de place_details para no gastar cuota.
        commercial_only : si True (default), descarta paradas de guagua,
                     parkings, ATMs, ayuntamientos, etc. usando la whitelist
                     `_COMMERCIAL_TYPES`. Apaga si quieres explorar todo.
        """
        skip = skip_ids or set()
        candidates = self._nearby_all_pages(lat, lng, radius_m, max_results)

        businesses: list[Business] = []
        for pid, types in candidates:
            if pid in skip:
                continue
            if commercial_only and not _is_commercial(types):
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
    ) -> list[tuple[str, list[str]]]:
        """Pagina places_nearby. Devuelve (place_id, types) para poder
        filtrar por tipo comercial sin pedir place_details."""
        out: list[tuple[str, list[str]]] = []
        seen_ids: set[str] = set()
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
            self.calls_nearby += 1
            for r in resp.get("results", []):
                pid = r.get("place_id")
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)
                out.append((pid, list(r.get("types", []) or [])))
                if len(out) >= max_results:
                    return out
            page_token = resp.get("next_page_token")
            pages += 1
            if not page_token or pages >= 3:
                break
            time.sleep(2)
        return out

    # ---------------- helpers internos ----------------

    # Lista de zonas reconocibles dentro de Tenerife. Si la query menciona
    # una de ellas asumimos que el usuario ya está acotando geográficamente
    # y no añadimos la región por defecto.
    _TENERIFE_PLACES: frozenset[str] = frozenset({
        "tenerife", "santa cruz", "la laguna", "adeje", "arona", "candelaria",
        "puerto de la cruz", "los cristianos", "las américas", "las americas",
        "los gigantes", "garachico", "icod", "tacoronte", "la orotava",
        "guimar", "güímar", "guia de isora", "guía de isora", "el médano",
        "el medano", "san isidro", "buzanada", "playa san juan", "alcalá",
        "alcala", "tegueste", "tejina", "bajamar", "punta del hidalgo",
        "valle de guerra", "fasnia", "arico", "vilaflor", "san miguel",
        "granadilla", "abona", "buenavista", "el sauzal", "matanza",
        "victoria de acentejo", "rosario", "candelaria", "santa úrsula",
        "santa ursula",
    })

    def _query_already_localized(self, q_low: str) -> bool:
        """True si la query ya menciona Tenerife o una zona conocida."""
        return any(p in q_low for p in self._TENERIFE_PLACES)

    def _compose_query(self, query: str, region: str | None) -> str:
        region = region if region is not None else self.default_region
        if not region:
            return query
        q_low = query.lower()
        # Si el usuario ya nombró la región o una zona de Tenerife, no
        # duplicamos. Comparamos con palabras concretas, no substring loose.
        region_tokens = [t.strip().lower() for t in region.split(",") if t.strip()]
        if any(t and t in q_low for t in region_tokens):
            return query
        if self._query_already_localized(q_low):
            return query
        return f"{query} en {region}"

    def _text_search_all_pages(
        self, query: str, max_results: int
    ) -> list[tuple[str, list[str]]]:
        """Pagina hasta agotar o llegar al máximo.
        Devuelve (place_id, types) para mantener simetría con nearby."""
        out: list[tuple[str, list[str]]] = []
        seen_ids: set[str] = set()
        page_token = None
        pages = 0
        while True:
            kwargs = {"query": query, "language": self.language}
            if page_token:
                kwargs["page_token"] = page_token
            resp = self.client.places(**kwargs)
            self.calls_text_search += 1
            for r in resp.get("results", []):
                pid = r.get("place_id")
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)
                out.append((pid, list(r.get("types", []) or [])))
                if len(out) >= max_results:
                    return out
            page_token = resp.get("next_page_token")
            pages += 1
            if not page_token or pages >= 3:  # Google solo da 3 páginas = 60 resultados
                break
            # El token tarda unos segundos en activarse.
            time.sleep(2)
        return out

    def _fetch_details(self, place_id: str) -> Business:
        resp = self.client.place(
            place_id=place_id,
            fields=self._DETAIL_FIELDS,
            language=self.language,
        )
        self.calls_place_details += 1
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
        self.calls_photo += 1
        return b"".join(chunk for chunk in result if chunk)


__all__ = ["GoogleExtractor", "Business"]

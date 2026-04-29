"""
registry.py
-----------
Base de datos JSON persistente para el CRM de leads.

Esquema v2:
{
  "version": 2,
  "businesses": {
    "<place_id>": {
      "place_id":     "...",
      "name":         "...",
      "sector":       "barberia",
      "address":      "...",
      "phone":        "+34 ...",
      "rating":       4.7,
      "review_count": 174,
      "maps_url":     "...",
      "output_file":  "bobe_barber_shop.txt",
      "processed_at": "2026-04-17 10:30:00",
      "last_updated": "2026-04-17 11:45:00",
      "status":       "found",          // found|contacted|interested|quoted|closed|rejected
      "score":        8,
      "notes":        "",
      "social":       {"instagram": "https://...", "facebook": null},
      "outreach":     {"whatsapp": "...", "email": "..."}
    }
  }
}
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "output" / "registry.json"

# Estados válidos del pipeline CRM
STATUSES = ["found", "contacted", "interested", "quoted", "closed", "rejected"]
DEFAULT_STATUS = "found"


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _load_raw() -> dict:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 2, "businesses": {}}


def _save(data: dict) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _migrate(data: dict) -> dict:
    """Convierte esquema v1 (place_ids) a v2 (businesses) si hace falta.

    Las entradas migradas tienen address/phone/rating vacíos porque la
    versión v1 no los persistía. Para enriquecerlas hay que llamar al
    endpoint POST /api/businesses/<pid>/refresh que vuelve a pedir los
    detalles a Google Places. Mientras tanto, el campo `needs_refresh`
    se marca a True para que el frontend pueda destacarlas.
    """
    if data.get("version") == 2:
        return data
    old = data.get("place_ids", {})
    new_businesses = {}
    for pid, entry in old.items():
        new_businesses[pid] = {
            "place_id":      pid,
            "name":          entry.get("name", ""),
            "sector":        "",
            "address":       "",
            "phone":         None,
            "rating":        None,
            "review_count":  0,
            "maps_url":      "",
            "output_file":   entry.get("output_file", ""),
            "processed_at":  entry.get("processed_at", _now()),
            "last_updated":  _now(),
            "status":        DEFAULT_STATUS,
            "score":         0,
            "notes":         "",
            "social":        {"instagram": None, "facebook": None, "tiktok": None},
            "outreach":      {"whatsapp": "", "email": ""},
            "needs_refresh": True,
        }
    return {"version": 2, "businesses": new_businesses}


def _load() -> dict:
    """Carga aplicando migración si es v1."""
    data = _load_raw()
    if data.get("version") != 2:
        data = _migrate(data)
        _save(data)
    return data


# ---------------------------------------------------------------------------
# Operaciones
# ---------------------------------------------------------------------------

def is_known(place_id: str) -> bool:
    return place_id in _load()["businesses"]


def known_ids() -> set[str]:
    return set(_load()["businesses"].keys())


def count() -> int:
    return len(_load()["businesses"])


def all_entries() -> dict:
    return _load()["businesses"]


def get(place_id: str) -> dict | None:
    return _load()["businesses"].get(place_id)


def upsert(place_id: str, **fields) -> dict:
    """Crea o actualiza una entrada. Conserva campos no especificados."""
    data = _load()
    entry = data["businesses"].get(place_id, {
        "place_id":     place_id,
        "name":         "",
        "sector":       "",
        "address":      "",
        "phone":        None,
        "rating":       None,
        "review_count": 0,
        "maps_url":     "",
        "output_file":  "",
        "processed_at": _now(),
        "status":       DEFAULT_STATUS,
        "score":        0,
        "notes":        "",
        "social":       {"instagram": None, "facebook": None, "tiktok": None},
        "outreach":     {"whatsapp": "", "email": ""},
    })
    entry.update(fields)
    entry["last_updated"] = _now()
    data["businesses"][place_id] = entry
    _save(data)
    return entry


def register(place_id: str, name: str, output_file: str, **extra) -> dict:
    """Atajo para el pipeline principal."""
    return upsert(
        place_id,
        name=name,
        output_file=output_file,
        **extra,
    )


def update_status(place_id: str, status: str) -> dict | None:
    if status not in STATUSES:
        raise ValueError(f"status inválido: {status}")
    entry = get(place_id)
    if not entry:
        return None
    return upsert(place_id, status=status)


def update_notes(place_id: str, notes: str) -> dict | None:
    entry = get(place_id)
    if not entry:
        return None
    return upsert(place_id, notes=notes)


def delete(place_id: str) -> bool:
    data = _load()
    if place_id in data["businesses"]:
        del data["businesses"][place_id]
        _save(data)
        return True
    return False


def find_by_output_file(filename: str) -> dict | None:
    for entry in _load()["businesses"].values():
        if entry.get("output_file") == filename:
            return entry
    return None


# ---------------------------------------------------------------------------
# Stats (para el dashboard)
# ---------------------------------------------------------------------------

def stats() -> dict:
    entries = _load()["businesses"].values()
    by_status = {s: 0 for s in STATUSES}
    by_sector: dict[str, int] = {}
    total_score = 0
    count_with_score = 0
    with_instagram = 0
    with_facebook = 0
    with_tiktok = 0

    for e in entries:
        by_status[e.get("status", DEFAULT_STATUS)] = \
            by_status.get(e.get("status", DEFAULT_STATUS), 0) + 1
        sec = e.get("sector") or "default"
        by_sector[sec] = by_sector.get(sec, 0) + 1
        s = e.get("score", 0)
        if s:
            total_score += s
            count_with_score += 1
        soc = e.get("social") or {}
        if soc.get("instagram"): with_instagram += 1
        if soc.get("facebook"):  with_facebook += 1
        if soc.get("tiktok"):    with_tiktok += 1

    return {
        "total":            sum(by_status.values()),
        "by_status":        by_status,
        "by_sector":        by_sector,
        "avg_score":        round(total_score / count_with_score, 1) if count_with_score else 0,
        "with_instagram":   with_instagram,
        "with_facebook":    with_facebook,
        "with_tiktok":      with_tiktok,
    }


__all__ = [
    "STATUSES", "DEFAULT_STATUS",
    "is_known", "known_ids", "count", "all_entries", "get",
    "upsert", "register", "update_status", "update_notes",
    "delete", "find_by_output_file", "stats",
]

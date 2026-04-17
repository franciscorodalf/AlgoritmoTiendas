"""
registry.py
-----------
Registro persistente de negocios ya procesados.
Evita duplicados entre sesiones guardando un JSON en output/registry.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "output" / "registry.json"


def _load() -> dict:
    if _REGISTRY_PATH.exists():
        try:
            return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"place_ids": {}}


def _save(data: dict) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_known(place_id: str) -> bool:
    """True si este place_id ya fue procesado en una sesión anterior."""
    return place_id in _load()["place_ids"]


def register(place_id: str, name: str, output_file: str) -> None:
    """Marca un negocio como procesado."""
    data = _load()
    data["place_ids"][place_id] = {
        "name": name,
        "output_file": output_file,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save(data)


def known_ids() -> set[str]:
    """Devuelve el set completo de place_ids ya procesados."""
    return set(_load()["place_ids"].keys())


def all_entries() -> dict:
    """Devuelve todo el registro {place_id: {name, output_file, processed_at}}."""
    return _load()["place_ids"]


def count() -> int:
    return len(_load()["place_ids"])


__all__ = ["is_known", "register", "known_ids", "all_entries", "count"]

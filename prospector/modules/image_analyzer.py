"""
image_analyzer.py
-----------------
Descarga la imagen de perfil de un negocio (logo o foto) y extrae
una paleta de colores coherente para la web.

Estrategia:
  1. ColorThief saca el color dominante (más rápido y bastante fiable).
  2. K-means sobre los píxeles da una paleta de 5 colores priorizando
     saturación (ignoramos fondos blancos/grises insulsos).
  3. Clasificamos cada color en {primario, secundario, acento, neutro}
     por luminosidad y saturación.

Salida: dict con hex codes listos para el prompt final.
"""

from __future__ import annotations

import colorsys
import io
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from colorthief import ColorThief
from PIL import Image
from sklearn.cluster import KMeans


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------


@dataclass
class Palette:
    """Paleta cromática derivada de la imagen del negocio."""

    primary: str       # color principal (el más característico)
    secondary: str     # complementario o contrastante
    accent: str        # highlight / CTA
    neutral: str       # fondos / texto suave
    all_hex: list[str]  # paleta completa por si la plantilla la quiere

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Cargadores
# ---------------------------------------------------------------------------


def load_image(source: bytes | str | Path) -> Image.Image:
    """Acepta bytes crudos, ruta en disco o path. Devuelve PIL.Image RGB."""
    if isinstance(source, (bytes, bytearray)):
        img = Image.open(io.BytesIO(source))
    else:
        img = Image.open(source)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# Extracción de paleta
# ---------------------------------------------------------------------------


def extract_palette(source: bytes | str | Path, palette_size: int = 6) -> Palette:
    """
    Extrae paleta de `palette_size` colores (por defecto 6) y la clasifica.
    """
    img = load_image(source)
    img.thumbnail((400, 400))  # rebaja coste sin perder información

    # 1. Color dominante con ColorThief (robusto con logos)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    ct = ColorThief(bio)
    dominant = _rgb_to_hex(ct.get_color(quality=1))

    # 2. Paleta amplia con K-means, ignorando casi-blancos y casi-negros.
    pixels = np.array(img).reshape(-1, 3)
    pixels = _filter_insipid(pixels)
    if len(pixels) < palette_size:
        pixels = np.array(img).reshape(-1, 3)  # fallback

    k = min(palette_size, max(2, len(pixels)))
    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42).fit(pixels)
    centers = kmeans.cluster_centers_.astype(int)

    hexes = [_rgb_to_hex(tuple(c)) for c in centers]
    if dominant not in hexes:
        hexes.insert(0, dominant)

    # 3. Ordena y clasifica
    hexes_sorted = _sort_by_saturation(hexes)
    primary = dominant
    secondary = _pick_contrast(primary, hexes_sorted)
    accent = _pick_accent(primary, hexes_sorted)
    neutral = _pick_neutral(hexes_sorted) or "#F5F0EB"

    return Palette(
        primary=primary,
        secondary=secondary,
        accent=accent,
        neutral=neutral,
        all_hex=hexes_sorted,
    )


# ---------------------------------------------------------------------------
# Helpers de color
# ---------------------------------------------------------------------------


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = (int(max(0, min(255, v))) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hsv(hex_color: str) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in _hex_to_rgb(hex_color))
    return colorsys.rgb_to_hsv(r, g, b)


def _filter_insipid(pixels: np.ndarray) -> np.ndarray:
    """Descarta píxeles casi-blancos, casi-negros y muy grises."""
    out = []
    for r, g, b in pixels:
        r_, g_, b_ = r / 255, g / 255, b / 255
        _, s, v = colorsys.rgb_to_hsv(r_, g_, b_)
        if v < 0.1 or v > 0.95:
            continue
        if s < 0.12:
            continue
        out.append((r, g, b))
    return np.array(out) if out else pixels


def _sort_by_saturation(hexes: list[str]) -> list[str]:
    return sorted(set(hexes), key=lambda h: (-_hsv(h)[1], -_hsv(h)[2]))


def _pick_contrast(primary: str, palette: list[str]) -> str:
    """Busca un color con tono distinto al primario."""
    h_p, _, _ = _hsv(primary)
    best, best_score = palette[0], -1.0
    for c in palette:
        if c == primary:
            continue
        h_c, s_c, v_c = _hsv(c)
        diff = min(abs(h_c - h_p), 1 - abs(h_c - h_p))  # distancia circular
        score = diff * s_c * v_c
        if score > best_score:
            best, best_score = c, score
    return best


def _pick_accent(primary: str, palette: list[str]) -> str:
    """Color más saturado distinto del primario."""
    for c in palette:
        if c == primary:
            continue
        _, s, v = _hsv(c)
        if s > 0.5 and v > 0.5:
            return c
    return palette[-1] if len(palette) > 1 else primary


def _pick_neutral(palette: list[str]) -> str | None:
    """Busca un tono neutro luminoso (fondo crema, blanco hueso...)."""
    for c in palette:
        _, s, v = _hsv(c)
        if s < 0.2 and v > 0.7:
            return c
    return None


__all__ = ["Palette", "extract_palette", "load_image"]

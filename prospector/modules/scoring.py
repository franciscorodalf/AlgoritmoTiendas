"""
scoring.py
----------
Calcula la puntuación (0-10) de un negocio como lead de ventas.

Factores:
  - nº de reseñas  (negocio activo = más probable de invertir)
  - rating          (calidad → puede permitirse pagar web)
  - sector          (algunos mueven más dinero que otros)
  - teléfono disponible
  - fotos disponibles
  - confirmado sin web propia
"""

from __future__ import annotations

import math

# Peso relativo por sector (0.0 - 1.0). Ajustable según tu experiencia.
_SECTOR_WEIGHTS: dict[str, float] = {
    "clinica":     1.00,   # salud paga bien
    "estetica":    1.00,
    "taller":      0.90,
    "restaurante": 0.90,
    "gimnasio":    0.90,
    "tienda_ropa": 0.85,
    "peluqueria":  0.80,
    "barberia":    0.80,
    "cafeteria":   0.70,
    "floristeria": 0.70,
    # default = 0 a propósito: si un lead cae aquí significa que no
    # supimos clasificarlo (probablemente sea ruido tipo parking, ATM,
    # ayuntamiento). No queremos darle puntuación de regalo.
    "default":     0.0,
}


def calculate(
    *,
    review_count: int = 0,
    rating: float | None = None,
    sector: str = "default",
    has_phone: bool = False,
    has_photos: bool = False,
    confirmed_no_web: bool = True,
) -> int:
    """
    Devuelve un entero 0-10.

    Reparto aproximado:
      0-3  reseñas      (log-scaled)
      0-2  rating       (1.5 puntos por cada ★ por encima de 3)
      0-2  sector       (2 × peso_sector)
      0-1  teléfono
      0-1  fotos
      0-1  sin web confirmado
    """
    score = 0.0

    # Reseñas
    score += min(math.log(max(review_count, 0) + 1) / 2, 3)

    # Rating
    if rating is not None:
        score += max(0.0, min(2.0, (rating - 3.0) * 1.5))

    # Sector
    score += 2.0 * _SECTOR_WEIGHTS.get(sector, _SECTOR_WEIGHTS["default"])

    if has_phone:        score += 1.0
    if has_photos:       score += 1.0
    if confirmed_no_web: score += 1.0

    return int(round(min(score, 10.0)))


def label(score: int) -> str:
    """Etiqueta humana para un score."""
    if score >= 8: return "🔥 Caliente"
    if score >= 6: return "⭐ Buena"
    if score >= 4: return "📊 Regular"
    return "❄️ Fría"


__all__ = ["calculate", "label"]

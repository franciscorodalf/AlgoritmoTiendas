"""
activity.py
-----------
Métricas de actividad de un negocio derivadas de sus reseñas.

Las reseñas que da Google traen `time` (epoch UTC). Con eso podemos
derivar tres señales clave para detectar leads "vivos":

  - last_review_days   : días desde la reseña más reciente
                         (>540 días → probablemente fantasma)
  - first_review_days  : días desde la reseña más antigua que da Google
                         (proxy de antigüedad mínima del negocio)
  - review_velocity    : reseñas por mes en el último año
                         (señal de tracción reciente)

Como Google solo devuelve hasta 5 reseñas en place_details, estas
métricas son aproximadas. Aún así son suficientes para descartar
negocios "fantasma" y priorizar leads con tracción reciente.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


_DAY_SECONDS = 86_400


@dataclass
class ActivitySignals:
    last_review_days: int | None    # None si no hay reseñas con time
    first_review_days: int | None
    review_velocity: float           # reseñas/mes (estimado)
    is_dormant: bool                 # última reseña > 540 días
    is_fresh: bool                   # última reseña < 60 días

    def to_dict(self) -> dict:
        return {
            "last_review_days":  self.last_review_days,
            "first_review_days": self.first_review_days,
            "review_velocity":   self.review_velocity,
            "is_dormant":        self.is_dormant,
            "is_fresh":          self.is_fresh,
        }


def compute(reviews: list[dict], total_review_count: int = 0) -> ActivitySignals:
    """
    Calcula señales de actividad. `reviews` es la lista que devuelve
    Google Places (cada item con `time` en epoch). `total_review_count`
    es `user_ratings_total` (lo usamos para velocity).
    """
    if not reviews:
        return ActivitySignals(
            last_review_days=None,
            first_review_days=None,
            review_velocity=0.0,
            is_dormant=False,  # sin datos no podemos afirmar nada
            is_fresh=False,
        )

    times: list[int] = []
    for rv in reviews:
        t = rv.get("time")
        if isinstance(t, (int, float)) and t > 0:
            times.append(int(t))

    if not times:
        return ActivitySignals(
            last_review_days=None,
            first_review_days=None,
            review_velocity=0.0,
            is_dormant=False,
            is_fresh=False,
        )

    now = int(time.time())
    last_t = max(times)
    first_t = min(times)
    last_days = max(0, (now - last_t) // _DAY_SECONDS)
    first_days = max(0, (now - first_t) // _DAY_SECONDS)

    # Velocity: reseñas/mes. Estimamos como total_review_count / meses_de_vida
    # acotado por la antigüedad MÍNIMA conocida (first_review_days). Es una
    # cota inferior — el negocio puede ser más viejo de lo que dice la 5ª reseña.
    months_alive = max(1.0, first_days / 30.0)
    velocity = (total_review_count or len(reviews)) / months_alive

    return ActivitySignals(
        last_review_days=last_days,
        first_review_days=first_days,
        review_velocity=round(velocity, 2),
        is_dormant=last_days > 540,
        is_fresh=last_days < 60,
    )


__all__ = ["ActivitySignals", "compute"]

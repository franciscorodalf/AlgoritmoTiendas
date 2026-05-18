"""
outreach.py
-----------
Genera mensajes de contacto (WhatsApp, email) personalizados por sector
y por etapa del CRM (primer contacto, follow-up, propuesta, cierre).

Plantillas Jinja2 en templates/outreach/:
  - <channel>.j2                  → first_contact (default, retrocompat)
  - <channel>/<stage>.j2          → otras etapas (follow_up_1, follow_up_2,
                                      proposal, closing)
"""

from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "outreach"

# Etapas válidas. first_contact usa la plantilla raíz <channel>.j2 para
# compatibilidad con el código previo.
STAGES = ["first_contact", "follow_up_1", "follow_up_2", "proposal", "closing"]
DEFAULT_STAGE = "first_contact"

# Mapa estado CRM → etapa de outreach sugerida
STATUS_TO_STAGE = {
    "found":       "first_contact",
    "contacted":   "follow_up_1",
    "interested":  "proposal",
    "quoted":      "closing",
    "closed":      "closing",
    "rejected":    "first_contact",
}


class OutreachBuilder:
    """Construye mensajes personalizados para un negocio."""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render(self, channel: str, ctx: dict, stage: str = DEFAULT_STAGE) -> str:
        # first_contact se renderiza desde la plantilla raíz para retrocompat.
        # Otras etapas viven en la subcarpeta <channel>/<stage>.j2.
        if stage == DEFAULT_STAGE:
            template_path = f"{channel}.j2"
        else:
            template_path = f"{channel}/{stage}.j2"
        try:
            t = self.env.get_template(template_path)
        except TemplateNotFound:
            return ""
        return t.render(**ctx).strip()

    def render(self, channel: str, stage: str, ctx: dict) -> str:
        """Renderiza un canal/etapa concretos. Acepta etapas no válidas
        devolviendo string vacío sin lanzar."""
        if stage not in STAGES:
            return ""
        return self._render(channel, ctx, stage=stage)

    def context(
        self,
        *,
        name: str,
        address: str = "",
        phone: str | None = None,
        rating: float | None = None,
        review_count: int = 0,
        sector: str = "default",
        keywords: list[str] | None = None,
        selling_points: list[str] | None = None,
        web_category: str = "none",
    ) -> dict:
        """Construye el ctx que se pasa a las plantillas. Útil para
        renderizar etapas individuales sin reconstruir el dict cada vez."""
        city = address.split(",")[0].strip() if address else ""
        return {
            "name":           name,
            "city":           city,
            "sector":         sector,
            "rating":         rating,
            "review_count":   review_count,
            "has_phone":      bool(phone),
            "phone":          phone or "",
            "keywords":       (keywords or [])[:3],
            "selling_points": (selling_points or [])[:2],
            "web_category":   web_category,
        }

    def build(
        self,
        *,
        name: str,
        address: str = "",
        phone: str | None = None,
        rating: float | None = None,
        review_count: int = 0,
        sector: str = "default",
        keywords: list[str] | None = None,
        selling_points: list[str] | None = None,
        web_category: str = "none",
    ) -> dict:
        """Devuelve {'whatsapp': str, 'email': str}.

        Si `keywords` / `selling_points` vienen de `review_analyzer`, las
        plantillas las usan para personalizar el mensaje (matar la
        sospecha de bot).
        `web_category` (de web_auditor) cambia el pitch:
          - 'social_only' → "tienes IG/FB pero no web propia, pierdes…"
          - 'free_builder' / 'obsolete' → "te podemos sacar de Wix/web vieja…"
          - 'none' → mensaje base "sin web propia…"
        """
        ctx = self.context(
            name=name, address=address, phone=phone, rating=rating,
            review_count=review_count, sector=sector,
            keywords=keywords, selling_points=selling_points,
            web_category=web_category,
        )
        return {
            "whatsapp": self._render("whatsapp", ctx),
            "email":    self._render("email", ctx),
        }


__all__ = ["OutreachBuilder", "STAGES", "DEFAULT_STAGE", "STATUS_TO_STAGE"]

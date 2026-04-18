"""
outreach.py
-----------
Genera mensajes de contacto (WhatsApp, email) personalizados por sector.

Usa plantillas Jinja2 en templates/outreach/.
"""

from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "outreach"


class OutreachBuilder:
    """Construye mensajes personalizados para un negocio."""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render(self, channel: str, ctx: dict) -> str:
        try:
            t = self.env.get_template(f"{channel}.j2")
        except TemplateNotFound:
            return ""
        return t.render(**ctx).strip()

    def build(
        self,
        *,
        name: str,
        address: str = "",
        phone: str | None = None,
        rating: float | None = None,
        review_count: int = 0,
        sector: str = "default",
    ) -> dict:
        """Devuelve {'whatsapp': str, 'email': str}."""
        city = address.split(",")[0].strip() if address else ""
        ctx = {
            "name":         name,
            "city":         city,
            "sector":       sector,
            "rating":       rating,
            "review_count": review_count,
            "has_phone":    bool(phone),
            "phone":        phone or "",
        }
        return {
            "whatsapp": self._render("whatsapp", ctx),
            "email":    self._render("email", ctx),
        }


__all__ = ["OutreachBuilder"]

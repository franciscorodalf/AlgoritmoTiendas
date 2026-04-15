"""
prompt_builder.py
-----------------
Ensambla el prompt final para Bolt / v0 / Framer.

Reúne los outputs de los otros módulos:
    - Business (google_extractor)
    - Palette (image_analyzer)
    - VisualProfile (typography_rules)
    - ReviewInsights (review_analyzer)

...y los pasa por una plantilla Jinja2 específica del sector.
Si el sector no tiene plantilla, cae en default.j2.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import asdict, is_dataclass
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class PromptBuilder:
    def __init__(self, templates_dir: Path | str | None = None):
        self.templates_dir = Path(templates_dir) if templates_dir else _TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(disabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def build(
        self,
        *,
        business: Any,
        palette: Any,
        profile: Any,
        insights: Any,
    ) -> str:
        """Devuelve el prompt final como string listo para pegar."""
        context = {
            "business": _to_dict(business),
            "palette": _to_dict(palette),
            "profile": _to_dict(profile),
            "insights": _to_dict(insights),
        }

        template_name = context["profile"].get("template", "default.j2")
        if not (self.templates_dir / template_name).exists():
            template_name = "default.j2"

        template = self.env.get_template(template_name)
        return template.render(**context).strip() + "\n"

    def save(self, prompt: str, out_path: Path | str) -> Path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        return out


def _to_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return dict(obj.__dict__) if hasattr(obj, "__dict__") else {}


__all__ = ["PromptBuilder"]

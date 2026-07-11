"""
review_analyzer.py
------------------
Analiza las reseñas de Google de un negocio con un LLM local (Ollama).

Devuelve insights estructurados en JSON:
    - keywords:        palabras clave que los clientes repiten
    - tone:            tono predominante del negocio (ej. "familiar", "premium")
    - selling_points:  razones por las que los clientes vuelven
    - vibe:            atmósfera/sensación global
    - target_audience: perfil aproximado de cliente
    - warnings:        quejas recurrentes (si las hay)
    - quotes:          citas LITERALES de reseñas (sin pasar por el LLM —
                       los resúmenes convergen, las frases reales son únicas)

Uso: todo corre en local. No se envía nada a APIs de pago.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict, field

import ollama
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------


@dataclass
class ReviewInsights:
    keywords: list[str]
    tone: str
    selling_points: list[str]
    vibe: str
    target_audience: str
    warnings: list[str]
    quotes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Citas literales (sin LLM)
# ---------------------------------------------------------------------------


def extract_quotes(reviews: list[dict], max_quotes: int = 3) -> list[str]:
    """
    Selecciona frases literales de reseñas para usar tal cual en la web.

    Criterio: reseñas de 4-5 estrellas con texto ni muy corto ni muy largo.
    Es Python puro y determinista a propósito — un resumen del LLM convierte
    "me arreglaron el color que me destrozaron en otro sitio" en "buen
    servicio de color", y ahí se pierde justo lo que hace única la web.
    """
    candidates = []
    for rv in reviews or []:
        text = " ".join((rv.get("text") or "").split())
        rating = rv.get("rating") or 0
        if rating < 4 or not (25 <= len(text) <= 200):
            continue
        # Preferimos 5★ y longitud de cita "de portada" (~90 caracteres)
        candidates.append((-(rating), abs(len(text) - 90), text))

    candidates.sort()
    quotes: list[str] = []
    for _, _, text in candidates:
        # Evita citas casi duplicadas (mismo arranque)
        if any(text[:25].lower() == q[:25].lower() for q in quotes):
            continue
        quotes.append(text)
        if len(quotes) >= max_quotes:
            break
    return quotes


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60"))

_SYSTEM_PROMPT = """Eres un analista de marketing especializado en negocios locales españoles.
Analizas reseñas de Google y extraes insights accionables para construir una web que venda.
Respondes siempre con JSON válido, en español, sin texto adicional."""

_USER_TEMPLATE = """Analiza las siguientes reseñas de Google del negocio "{name}" ({category}).

RESEÑAS:
{reviews_block}

Devuelve un JSON con esta estructura exacta (sin markdown, sin explicaciones):
{{
  "keywords": ["palabra1", "palabra2", "..."],  // 5-8 palabras que los clientes repiten
  "tone": "...",                                 // 2-4 palabras que describen el tono (ej. "familiar, cercano, tradicional")
  "selling_points": ["...", "..."],              // 3-5 frases cortas: lo que más valoran
  "vibe": "...",                                 // 1-2 frases: la atmósfera general
  "target_audience": "...",                      // 1 frase: perfil del cliente típico
  "warnings": ["..."]                            // 0-3 quejas recurrentes, o [] si no hay
}}"""


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------


class ReviewAnalyzer:
    def __init__(self, model: str | None = None, host: str | None = None,
                 timeout: float | None = None):
        self.model = model or _DEFAULT_MODEL
        self.host = host or _DEFAULT_HOST
        self.timeout = timeout if timeout is not None else _DEFAULT_TIMEOUT
        # Algunas versiones del cliente ollama no aceptan `timeout=` en el
        # constructor — caemos al default si así es.
        try:
            self.client = ollama.Client(host=self.host, timeout=self.timeout)
        except TypeError:
            self.client = ollama.Client(host=self.host)

    # ---------------- API pública ----------------

    def analyze(
        self,
        name: str,
        category: str,
        reviews: list[dict],
        *,
        fallback_on_empty: bool = True,
    ) -> ReviewInsights:
        """
        Analiza reseñas. Si no hay reseñas devuelve un fallback genérico (para
        no bloquear la generación del prompt cuando el negocio es muy nuevo).
        """
        if not reviews:
            if fallback_on_empty:
                return self._empty_fallback(category)
            raise ValueError("No hay reseñas que analizar.")

        # Las citas literales no dependen del LLM: se extraen siempre.
        # (Si el LLM falla más abajo, la excepción se propaga igual que antes.)

        reviews_block = self._format_reviews(reviews)
        user_prompt = _USER_TEMPLATE.format(
            name=name,
            category=category or "negocio local",
            reviews_block=reviews_block,
        )

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3},
        )

        raw = response["message"]["content"]
        data = self._extract_json(raw)
        insights = self._to_insights(data)
        insights.quotes = extract_quotes(reviews)
        return insights

    def ping(self) -> bool:
        """Comprueba que Ollama está corriendo Y el modelo descargado."""
        try:
            resp = self.client.list()
            models = resp.get("models", []) if isinstance(resp, dict) else []
            # Acepta nombre exacto o tag base (ej. 'llama3.1' matchea 'llama3.1:8b')
            target_base = self.model.split(":")[0]
            for m in models:
                name = (m.get("name") or m.get("model") or "") if isinstance(m, dict) else str(m)
                if name == self.model or name.startswith(target_base + ":"):
                    return True
            return False
        except Exception:
            return False

    def has_server(self) -> bool:
        """Solo comprueba que Ollama responde (sin verificar el modelo)."""
        try:
            self.client.list()
            return True
        except Exception:
            return False

    # ---------------- helpers internos ----------------

    @staticmethod
    def _format_reviews(reviews: list[dict]) -> str:
        lines = []
        for i, rv in enumerate(reviews[:10], 1):  # cap a 10 para no saturar el prompt
            text = (rv.get("text") or "").strip().replace("\n", " ")
            rating = rv.get("rating", "?")
            lines.append(f"{i}. [{rating}★] {text}")
        return "\n".join(lines)

    @staticmethod
    def _extract_json(raw: str) -> dict:
        """
        El modelo a veces envuelve el JSON en ```json ... ``` o antepone texto.
        Buscamos el primer bloque JSON válido.
        """
        # Quita fences de markdown si existen
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

        # Intenta parseo directo
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Busca el primer objeto JSON en el texto
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"No se pudo parsear JSON de la respuesta:\n{raw[:400]}")

    @staticmethod
    def _to_insights(data: dict) -> ReviewInsights:
        return ReviewInsights(
            keywords=_as_list(data.get("keywords")),
            tone=str(data.get("tone", "")).strip(),
            selling_points=_as_list(data.get("selling_points")),
            vibe=str(data.get("vibe", "")).strip(),
            target_audience=str(data.get("target_audience", "")).strip(),
            warnings=_as_list(data.get("warnings")),
        )

    @staticmethod
    def _empty_fallback(category: str) -> ReviewInsights:
        return ReviewInsights(
            keywords=[],
            tone="profesional, cercano",
            selling_points=["Atención personalizada", "Servicio de calidad"],
            vibe=f"Negocio local de {category or 'servicios'} en Tenerife.",
            target_audience="Clientes locales de la zona.",
            warnings=[],
            quotes=[],
        )


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [str(v).strip()]


__all__ = ["ReviewAnalyzer", "ReviewInsights", "extract_quotes"]

"""
creative_director.py
--------------------
Segunda pasada de Ollama: en vez de delegar la decisión creativa en
Bolt/v0 (que converge siempre a lo mismo), generamos aquí el concepto
visual único de cada web y lo inyectamos en el prompt.

A diferencia de review_analyzer (temperatura 0.3, tarea de extracción),
aquí queremos divergencia: temperatura alta y un encargo abierto.

Si Ollama no está disponible, `fallback_concept()` construye un concepto
determinista a partir del arquetipo y la estructura — peor que el LLM,
pero nunca bloquea el pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, asdict

import ollama
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CreativeConcept:
    concept: str            # idea rectora en 1-2 frases (metáfora / atmósfera)
    hero_idea: str          # cómo aterrizar el hero para ESTE negocio
    signature_section: str  # una sección distintiva que no está en plantillas comunes
    photo_direction: str    # dirección de fotografía/imagen coherente con el concepto

    def to_dict(self) -> dict:
        return asdict(self)


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60"))

_SYSTEM_PROMPT = """Eres director creativo de un estudio de diseño web premiado.
Tu especialidad: webs para negocios locales que NO parecen plantilla.
Trabajas con lo concreto: el nombre real, el barrio, lo que dicen las reseñas.
Huyes de clichés del sector. Respondes siempre con JSON válido, en español,
sin texto adicional."""

_USER_TEMPLATE = """Negocio real de Tenerife que necesita un concepto de web único:

  - Nombre: {name}
  - Sector: {sector}
  - Zona: {address}
  - Arquetipo visual asignado: {variant} — {visual_vibe}
  - Paleta (del logo real): primario {primary}, secundario {secondary}, acento {accent}
  - Lo que repiten sus clientes: {keywords}
  - Frases literales de reseñas: {quotes}
  - Patrón de hero ya decidido: {hero_pattern}

Inventa la dirección creativa de SU web. Debe nacer de los datos de ESTE
negocio (nombre, zona, lo que dicen sus clientes), no del sector en general.
Prohibido lo que pondría cualquier plantilla de {sector}.

Devuelve un JSON con esta estructura exacta (sin markdown, sin explicaciones):
{{
  "concept": "...",            // 1-2 frases: la idea rectora (metáfora, atmósfera o historia que organiza toda la web)
  "hero_idea": "...",          // 1-2 frases: cómo aterrizar el patrón de hero indicado para ESTE negocio (qué imagen, qué titular, qué detalle)
  "signature_section": "...",  // 1-2 frases: UNA sección distintiva inventada para este negocio que no aparece en webs típicas del sector
  "photo_direction": "..."     // 1 frase: dirección de fotografía coherente con el concepto (luz, encuadre, qué mostrar)
}}"""


class CreativeDirector:
    def __init__(self, model: str | None = None, host: str | None = None,
                 timeout: float | None = None, temperature: float = 0.9):
        self.model = model or _DEFAULT_MODEL
        self.host = host or _DEFAULT_HOST
        self.timeout = timeout if timeout is not None else _DEFAULT_TIMEOUT
        self.temperature = temperature
        try:
            self.client = ollama.Client(host=self.host, timeout=self.timeout)
        except TypeError:
            self.client = ollama.Client(host=self.host)

    def direct(self, *, business, profile, palette, insights, structure) -> CreativeConcept:
        """
        Genera el concepto creativo con el LLM local. Lanza excepción si
        Ollama falla — el caller decide si usar fallback_concept().
        """
        biz = _as_dict(business)
        prof = _as_dict(profile)
        pal = _as_dict(palette)
        ins = _as_dict(insights)
        struct = _as_dict(structure)

        user_prompt = _USER_TEMPLATE.format(
            name=biz.get("name", ""),
            sector=prof.get("sector", "negocio local"),
            address=biz.get("address", "Tenerife"),
            variant=prof.get("variant", "base"),
            visual_vibe=prof.get("visual_vibe", ""),
            primary=pal.get("primary", "-"),
            secondary=pal.get("secondary", "-"),
            accent=pal.get("accent", "-"),
            keywords=", ".join(ins.get("keywords", [])) or "sin datos",
            quotes=" | ".join(ins.get("quotes", [])) or "sin citas",
            hero_pattern=struct.get("hero", ""),
        )

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": self.temperature},
        )
        data = _extract_json(response["message"]["content"])
        return CreativeConcept(
            concept=str(data.get("concept", "")).strip(),
            hero_idea=str(data.get("hero_idea", "")).strip(),
            signature_section=str(data.get("signature_section", "")).strip(),
            photo_direction=str(data.get("photo_direction", "")).strip(),
        )


# --- Fallback sin LLM ---------------------------------------------------------

_FALLBACK_SIGNATURES: list[str] = [
    "Una cinta de marquesina con palabras reales sacadas de las reseñas del negocio, "
    "recorriendo la pantalla como sello de identidad.",
    "Un bloque 'un día aquí': el horario del negocio contado como pequeña línea de "
    "tiempo con lo que pasa en el local a cada hora.",
    "Una nota personal del dueño en primera persona, maquetada como carta breve con firma.",
    "Un mapa ilustrado del barrio con el local marcado y 2-3 referencias reales cercanas "
    "para llegar sin perderse.",
    "Un módulo de cifras vivas: años abiertos, valoración de Google y número de reseñas, "
    "animadas al entrar en pantalla.",
    "Un antes/ahora del negocio: cómo empezó y cómo es hoy, en dos imágenes enfrentadas.",
]


def fallback_concept(*, business, profile, structure) -> CreativeConcept:
    """
    Concepto determinista sin LLM: combina el vibe del arquetipo, el hero ya
    elegido y una sección distintiva seleccionada por hash del negocio.
    """
    biz = _as_dict(business)
    prof = _as_dict(profile)
    struct = _as_dict(structure)

    seed = biz.get("place_id") or biz.get("name", "negocio")
    idx = int(hashlib.md5(str(seed).encode("utf-8")).hexdigest()[:8], 16) % len(_FALLBACK_SIGNATURES)

    name = biz.get("name", "el negocio")
    return CreativeConcept(
        concept=f"Trasladar a la web la sensación real de entrar en {name}: "
                f"{prof.get('visual_vibe', 'identidad propia y cercana')}.",
        hero_idea=struct.get("hero", "Hero con imagen fuerte del negocio y CTA directo."),
        signature_section=_FALLBACK_SIGNATURES[idx],
        photo_direction="Fotografía del local y las personas reales; si no hay fotos, "
                        "placeholders específicos de este tipo de local, nunca stock genérico.",
    )


# --- helpers -------------------------------------------------------------------


def _as_dict(obj) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return dict(obj.__dict__) if hasattr(obj, "__dict__") else {}


def _extract_json(raw: str) -> dict:
    """Mismo criterio tolerante que review_analyzer: el modelo a veces envuelve el JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No se pudo parsear JSON de la respuesta:\n{raw[:400]}")


__all__ = ["CreativeConcept", "CreativeDirector", "fallback_concept"]

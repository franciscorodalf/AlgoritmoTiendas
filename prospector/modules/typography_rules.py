"""
typography_rules.py
-------------------
Tabla de reglas que mapea (categoría Google Places) → (tipografías + vibe).

La categoría de Google viene en inglés y en formato tipo "hair_care",
"car_repair", "restaurant". Normalizamos a sectores propios y si no
encaja en ninguno cae en un default sensato.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class VisualProfile:
    sector: str              # clave interna (ej. "barberia")
    heading_font: str        # tipografía de títulos
    body_font: str           # tipografía de cuerpo
    font_vibe: str           # descripción breve para el prompt
    visual_vibe: str         # estética general
    template: str            # nombre del .j2 a usar

    def to_dict(self) -> dict:
        return asdict(self)


# --- Perfiles maestros ------------------------------------------------------

_PROFILES: dict[str, VisualProfile] = {
    "restaurante": VisualProfile(
        sector="restaurante",
        heading_font="Playfair Display (serif elegante, cálida)",
        body_font="Inter o Lora (sans/serif legible)",
        font_vibe="Serif elegante con carácter editorial",
        visual_vibe="Mediterránea, acogedora, gastronómica, con toques de madera y tierra",
        template="restaurante.j2",
    ),
    "cafeteria": VisualProfile(
        sector="cafeteria",
        heading_font="Fraunces o DM Serif Display (redondeada, amigable)",
        body_font="Inter o Nunito",
        font_vibe="Redondeada con personalidad artesanal",
        visual_vibe="Cálida, artesanal, con tonos tierra y pastel suaves",
        template="cafeteria.j2",
    ),
    "barberia": VisualProfile(
        sector="barberia",
        heading_font="Bebas Neue o Oswald (bold, urban)",
        body_font="Inter o Work Sans",
        font_vibe="Bold, industrial, con presencia masculina",
        visual_vibe="Barbería clásica con toques urbanos, madera oscura y dorados",
        template="barberia.j2",
    ),
    "peluqueria": VisualProfile(
        sector="peluqueria",
        heading_font="Cormorant Garamond o Marcellus (serif sofisticada)",
        body_font="Inter",
        font_vibe="Serif sofisticada, femenina y moderna",
        visual_vibe="Elegante, cuidada, luminosa, con toques rosados o pastel",
        template="peluqueria.j2",
    ),
    "clinica": VisualProfile(
        sector="clinica",
        heading_font="Inter o DM Sans (sans-serif limpia)",
        body_font="Inter",
        font_vibe="Sans-serif minimalista que transmite confianza",
        visual_vibe="Profesional, aséptica pero cercana, azules y blancos luminosos",
        template="clinica.j2",
    ),
    "taller": VisualProfile(
        sector="taller",
        heading_font="Archivo Black o Barlow Condensed (industrial, robusta)",
        body_font="Barlow o Roboto",
        font_vibe="Industrial, sólida, directa",
        visual_vibe="Mecánica, robusta, con grises metálicos y acentos en rojo o amarillo",
        template="taller.j2",
    ),
    "tienda_ropa": VisualProfile(
        sector="tienda_ropa",
        heading_font="Editorial New o Bodoni (editorial, moderna)",
        body_font="Inter o Neue Haas",
        font_vibe="Editorial, moderna, ligera",
        visual_vibe="Fresca, dinámica, tipo revista de moda, generosos espacios en blanco",
        template="tienda_ropa.j2",
    ),
    "gimnasio": VisualProfile(
        sector="gimnasio",
        heading_font="Oswald o Anton (condensada, potente)",
        body_font="Inter",
        font_vibe="Condensada, potente, atlética",
        visual_vibe="Enérgica, oscura con acentos vibrantes (lima, naranja, rojo)",
        template="gimnasio.j2",
    ),
    "floristeria": VisualProfile(
        sector="floristeria",
        heading_font="Cormorant Garamond o Fraunces (serif delicada, botánica)",
        body_font="Inter o Nunito",
        font_vibe="Serif delicada con toques románticos",
        visual_vibe="Botánica, natural, fresca, verdes y pasteles suaves, fotografía macro",
        template="floristeria.j2",
    ),
    "estetica": VisualProfile(
        sector="estetica",
        heading_font="DM Serif Display o Cormorant (serif sofisticada)",
        body_font="Inter",
        font_vibe="Serif elegante que transmite cuidado premium",
        visual_vibe="Cuidada, premium, luminosa, tonos nude, beige y rosado, sensación de bienestar",
        template="estetica.j2",
    ),
    "default": VisualProfile(
        sector="default",
        heading_font="Inter (sans-serif versátil)",
        body_font="Inter",
        font_vibe="Moderna, profesional, versátil",
        visual_vibe="Limpia, moderna, adaptable a cualquier sector",
        template="default.j2",
    ),
}


# --- Mapa de categorías Google Places → sector interno ---------------------
#
# Google devuelve tipos como 'restaurant', 'bakery', 'bar', 'hair_care'...
# La lista oficial: https://developers.google.com/maps/documentation/places/web-service/supported_types

_CATEGORY_MAP: dict[str, str] = {
    # Comida
    "restaurant": "restaurante",
    "meal_takeaway": "restaurante",
    "meal_delivery": "restaurante",
    "food": "restaurante",
    "bar": "restaurante",
    "bakery": "cafeteria",
    "cafe": "cafeteria",
    "ice_cream_shop": "cafeteria",
    # Belleza / peluquería
    "hair_care": "peluqueria",
    "nail_salon": "peluqueria",
    "barber_shop": "barberia",
    # Centros de estética / spa (tratamientos faciales, corporales, aparatología)
    "beauty_salon": "estetica",
    "spa": "estetica",
    # Floristerías
    "florist": "floristeria",
    # Salud
    "dentist": "clinica",
    "doctor": "clinica",
    "physiotherapist": "clinica",
    "health": "clinica",
    "hospital": "clinica",
    "veterinary_care": "clinica",
    # Automoción
    "car_repair": "taller",
    "car_dealer": "taller",
    "car_wash": "taller",
    # Moda
    "clothing_store": "tienda_ropa",
    "shoe_store": "tienda_ropa",
    "jewelry_store": "tienda_ropa",
    # Fitness
    "gym": "gimnasio",
    "fitness_center": "gimnasio",
}


# --- Detección por nombre (fallback y override de categorías ambiguas) -----
#
# Google Places a veces devuelve categorías demasiado genéricas
# (ej. "establishment", "point_of_interest") o confunde barberías con
# peluquerías. Si el nombre del negocio contiene alguna keyword muy
# específica, la usamos para corregir la clasificación.
#
# El orden importa: de más específico a menos específico.

_NAME_KEYWORDS: dict[str, list[str]] = {
    "barberia": ["barber", "barbería", "barberia"],
    "floristeria": ["floristería", "floristeria", "florería", "floreria", "florist"],
    "estetica": ["estética", "estetica", " spa", "wellness", "centro de belleza"],
    "clinica": ["clínica", "clinica", "dental", "dentista", "fisio", "veterinari", "médic"],
    "taller": ["taller", "mecánic", "mecanic", "neumátic", "chapa y pintura", "itv"],
    "gimnasio": [" gym", "gimnasio", "fitness", "crossfit", "box de "],
    "cafeteria": ["cafetería", "cafeteria", "café ", "coffee", "heladería",
                  "heladeria", "panadería", "panaderia", "pastelería", "pasteleria"],
    "restaurante": ["restaurante", "restaurant", "asador", "bistró", "bistro",
                    "taberna", "grill", "pizzería", "pizzeria", "marisquería"],
    "tienda_ropa": ["boutique", "moda", "fashion", "zapatería", "zapateria"],
    "peluqueria": ["peluquería", "peluqueria", "salón de belleza",
                   "salon de belleza", "hair salon"],
}


def _match_by_name(name: str) -> str | None:
    """Devuelve el primer sector cuyo keyword aparece en el nombre, o None."""
    if not name:
        return None
    name_low = name.lower()
    for sector, keywords in _NAME_KEYWORDS.items():
        if any(kw in name_low for kw in keywords):
            return sector
    return None


def resolve_sector(categories: list[str] | str, name: str = "") -> str:
    """
    Devuelve la clave interna de sector.

    Estrategia:
      1. Si el nombre del negocio contiene una keyword fuerte → gana.
         (arregla barberías mal tipadas como hair_care, etc.)
      2. Si no, usamos el mapa de categorías de Google.
      3. Si nada matchea → "default".
    """
    by_name = _match_by_name(name)
    if by_name:
        return by_name

    if isinstance(categories, str):
        categories = [categories]
    for cat in categories:
        sector = _CATEGORY_MAP.get(cat)
        if sector:
            return sector
    return "default"


def get_profile(categories: list[str] | str, name: str = "") -> VisualProfile:
    """Devuelve el VisualProfile completo para un negocio."""
    sector = resolve_sector(categories, name)
    return _PROFILES.get(sector, _PROFILES["default"])


def list_sectors() -> list[str]:
    return list(_PROFILES.keys())


__all__ = ["VisualProfile", "get_profile", "resolve_sector", "list_sectors"]

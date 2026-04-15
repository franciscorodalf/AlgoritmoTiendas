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


def resolve_sector(categories: list[str] | str) -> str:
    """Devuelve la clave interna de sector a partir de los tipos de Google."""
    if isinstance(categories, str):
        categories = [categories]
    for cat in categories:
        sector = _CATEGORY_MAP.get(cat)
        if sector:
            return sector
    return "default"


def get_profile(categories: list[str] | str) -> VisualProfile:
    """Devuelve el VisualProfile completo para un negocio."""
    sector = resolve_sector(categories)
    return _PROFILES.get(sector, _PROFILES["default"])


def list_sectors() -> list[str]:
    return list(_PROFILES.keys())


__all__ = ["VisualProfile", "get_profile", "resolve_sector", "list_sectors"]

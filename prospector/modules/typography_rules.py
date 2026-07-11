"""
typography_rules.py
-------------------
Mapea (categoría Google Places) → sector, y elige un ARQUETIPO visual
dentro del sector para que dos negocios iguales no reciban la misma web.

Antes: 1 sector = 1 perfil fijo → todas las peluquerías eran clones.
Ahora: cada sector tiene 3-4 arquetipos y se elige según señales reales
del negocio:

  - keywords de las reseñas (qué dicen sus clientes)
  - paleta del logo (oscura/clara, viva/apagada, cálida/fría)
  - nivel de precio de Google Places
  - desempate determinista con hash del place_id
    (mismo negocio → siempre el mismo arquetipo; negocios distintos → varía)

Si no se pasan señales (llamadas antiguas), devuelve el arquetipo base
del sector — comportamiento idéntico al anterior.
"""

from __future__ import annotations

import colorsys
import hashlib
from dataclasses import dataclass, asdict, field


@dataclass
class VisualProfile:
    sector: str              # clave interna (ej. "barberia")
    variant: str             # nombre del arquetipo (ej. "brutalista-urbana")
    heading_font: str        # tipografía de títulos
    body_font: str           # tipografía de cuerpo
    font_vibe: str           # descripción breve para el prompt
    visual_vibe: str         # estética general
    template: str            # nombre del .j2 a usar
    # --- señales para la selección (no salen en el prompt) ---
    keywords_hint: tuple = field(default=())   # palabras que lo activan
    palette_hint: tuple = field(default=())    # rasgos de paleta que lo favorecen
    min_price: int | None = None               # nivel de precio mínimo (Google 0-4)

    def to_dict(self) -> dict:
        return asdict(self)


# --- Arquetipos por sector ---------------------------------------------------
#
# El PRIMER arquetipo de cada lista es el "base": el que se usa si no hay
# señales. Los demás compiten por puntuación de señales.

_ARCHETYPES: dict[str, list[VisualProfile]] = {
    "restaurante": [
        VisualProfile(
            sector="restaurante", variant="mediterraneo-calido",
            heading_font="Playfair Display (serif elegante, cálida)",
            body_font="Inter o Lora (sans/serif legible)",
            font_vibe="Serif elegante con carácter editorial",
            visual_vibe="Mediterránea, acogedora, gastronómica, con toques de madera y tierra",
            template="restaurante.j2",
            keywords_hint=("terraza", "mediterráneo", "pescado", "fresco", "vistas"),
            palette_hint=("warm", "light"),
        ),
        VisualProfile(
            sector="restaurante", variant="bistro-nocturno",
            heading_font="DM Serif Display (serif con contraste dramático)",
            body_font="Inter",
            font_vibe="Serif dramática sobre fondos oscuros",
            visual_vibe="Bistró elegante y nocturno: fondo oscuro, fotografía de plato en primer plano con luz puntual, carta tratada como pieza tipográfica",
            template="restaurante.j2",
            keywords_hint=("romántico", "cena", "vino", "autor", "íntimo", "degustación"),
            palette_hint=("dark",),
            min_price=2,
        ),
        VisualProfile(
            sector="restaurante", variant="cantina-familiar",
            heading_font="Fraunces (serif redondeada con personalidad)",
            body_font="Nunito",
            font_vibe="Redondeada, generosa, sin pretensiones",
            visual_vibe="Casa de comidas canaria: colores vivos, manteles y producto local, cercanía de guachinche, cero minimalismo frío",
            template="restaurante.j2",
            keywords_hint=("casero", "familiar", "abundante", "guachinche", "típico",
                           "canario", "de toda la vida", "barato"),
            palette_hint=("vivid", "warm"),
        ),
    ],
    "cafeteria": [
        VisualProfile(
            sector="cafeteria", variant="artesanal-tierra",
            heading_font="Fraunces o DM Serif Display (redondeada, amigable)",
            body_font="Inter o Nunito",
            font_vibe="Redondeada con personalidad artesanal",
            visual_vibe="Cálida, artesanal, con tonos tierra y pastel suaves",
            template="cafeteria.j2",
            keywords_hint=("acogedor", "tranquilo", "desayuno", "artesanal", "casero"),
            palette_hint=("warm", "muted"),
        ),
        VisualProfile(
            sector="cafeteria", variant="specialty-minimal",
            heading_font="Space Grotesk (sans geométrica con carácter)",
            body_font="Inter",
            font_vibe="Sans moderna, precisa, de cafetería de especialidad",
            visual_vibe="Nórdica y luminosa: mucho blanco, fotografía macro del café y del latte art, rejilla limpia, un solo acento de color",
            template="cafeteria.j2",
            keywords_hint=("specialty", "espresso", "brunch", "flat white", "moderno",
                           "de especialidad", "tostado"),
            palette_hint=("light", "muted"),
        ),
        VisualProfile(
            sector="cafeteria", variant="dulce-retro",
            heading_font="Fraunces itálica (serif dulce y expresiva)",
            body_font="Nunito",
            font_vibe="Expresiva, golosa, con guiños retro",
            visual_vibe="Pastelería/heladería alegre: pasteles saturados, formas redondas, ilustración ligera, energía de merienda en familia",
            template="cafeteria.j2",
            keywords_hint=("tarta", "helado", "dulce", "niños", "familia", "pastel",
                           "crepes", "gofres"),
            palette_hint=("vivid",),
        ),
    ],
    "barberia": [
        VisualProfile(
            sector="barberia", variant="clasica-dorada",
            heading_font="Bebas Neue o Oswald (bold, urban)",
            body_font="Inter o Work Sans",
            font_vibe="Bold, industrial, con presencia masculina",
            visual_vibe="Barbería clásica con toques urbanos, madera oscura y dorados",
            template="barberia.j2",
            keywords_hint=("clásico", "de siempre", "confianza", "detalle"),
            palette_hint=("dark", "warm"),
        ),
        VisualProfile(
            sector="barberia", variant="brutalista-street",
            heading_font="Archivo Black (pesada, sin concesiones)",
            body_font="Work Sans",
            font_vibe="Tipografía gigante como elemento gráfico principal",
            visual_vibe="Street y crudo: blanco/negro de alto contraste, fotografía en bruto, composición asimétrica, energía de barrio joven",
            template="barberia.j2",
            keywords_hint=("fade", "tattoo", "urbano", "joven", "degradado", "diseño",
                           "freestyle"),
            palette_hint=("vivid", "dark"),
        ),
        VisualProfile(
            sector="barberia", variant="vintage-caballeros",
            heading_font="Playfair Display (serif clásica con carácter)",
            body_font="Lora",
            font_vibe="Serif de grabado antiguo, señorial",
            visual_vibe="Club de caballeros: crema y burdeos, ornamentos finos de grabado, navaja y toalla caliente, ritual tradicional",
            template="barberia.j2",
            keywords_hint=("navaja", "tradicional", "afeitado", "clásico", "toalla",
                           "caballero"),
            palette_hint=("muted", "warm"),
        ),
    ],
    "peluqueria": [
        VisualProfile(
            sector="peluqueria", variant="editorial-premium",
            heading_font="Cormorant Garamond o Marcellus (serif sofisticada)",
            body_font="Inter",
            font_vibe="Serif sofisticada, femenina y moderna",
            visual_vibe="Elegante, cuidada, luminosa, con toques rosados o pastel",
            template="peluqueria.j2",
            keywords_hint=("elegante", "novias", "eventos", "tratamiento", "keratina"),
            palette_hint=("light",),
            min_price=2,
        ),
        VisualProfile(
            sector="peluqueria", variant="estudio-urbano",
            heading_font="Space Grotesk (sans con personalidad)",
            body_font="Inter",
            font_vibe="Sans contemporánea, directa, de estudio creativo",
            visual_vibe="Estudio urbano: neutros con UN acento intenso, fotografía de color y mechas como protagonista, actitud joven y unisex",
            template="peluqueria.j2",
            keywords_hint=("moderno", "joven", "mechas", "balayage", "unisex", "color",
                           "fantasía", "estilo"),
            palette_hint=("vivid", "dark"),
        ),
        VisualProfile(
            sector="peluqueria", variant="natural-organica",
            heading_font="Fraunces (serif suave y orgánica)",
            body_font="Nunito",
            font_vibe="Serif cálida con formas orgánicas",
            visual_vibe="Natural y serena: tonos tierra y verdes suaves, materiales naturales, luz de mañana, ritmo pausado",
            template="peluqueria.j2",
            keywords_hint=("natural", "orgánico", "tranquilo", "cercano", "familiar",
                           "vegano", "ecológico"),
            palette_hint=("muted", "warm"),
        ),
        VisualProfile(
            sector="peluqueria", variant="clasica-de-barrio",
            heading_font="Libre Baskerville (serif honesta y legible)",
            body_font="Source Sans 3",
            font_vibe="Serif de confianza, sin pretensiones",
            visual_vibe="Peluquería de barrio con orgullo: cálida, honesta, fotografía real del local y las clientas de siempre, cero postureo",
            template="peluqueria.j2",
            keywords_hint=("barrio", "de toda la vida", "precio", "rápido", "amable",
                           "señoras", "trato"),
        ),
    ],
    "clinica": [
        VisualProfile(
            sector="clinica", variant="azul-confianza",
            heading_font="Inter o DM Sans (sans-serif limpia)",
            body_font="Inter",
            font_vibe="Sans-serif minimalista que transmite confianza",
            visual_vibe="Profesional, aséptica pero cercana, azules y blancos luminosos",
            template="clinica.j2",
            keywords_hint=("profesional", "limpio", "puntual", "serio"),
            palette_hint=("cool", "light"),
        ),
        VisualProfile(
            sector="clinica", variant="calida-humana",
            heading_font="Lora (serif humanista)",
            body_font="Source Sans 3",
            font_vibe="Serif suave que humaniza lo sanitario",
            visual_vibe="Cálida y humana: tonos arena y verdes suaves, fotografía de trato real paciente-profesional, cero frialdad de hospital",
            template="clinica.j2",
            keywords_hint=("trato", "cercano", "familiar", "paciencia", "niños",
                           "amable", "explica", "confianza"),
            palette_hint=("warm", "muted"),
        ),
        VisualProfile(
            sector="clinica", variant="tech-premium",
            heading_font="Inter (sans precisa, pesos altos)",
            body_font="Inter",
            font_vibe="Sans técnica y precisa",
            visual_vibe="Vanguardia médica: fondo sobrio casi oscuro, un acento eléctrico, imágenes de tecnología y precisión, sensación de puntero",
            template="clinica.j2",
            keywords_hint=("tecnología", "moderna", "puntera", "implante", "láser",
                           "3d", "digital", "estética"),
            palette_hint=("dark", "cool"),
            min_price=2,
        ),
    ],
    "taller": [
        VisualProfile(
            sector="taller", variant="industrial-clasico",
            heading_font="Archivo Black o Barlow Condensed (industrial, robusta)",
            body_font="Barlow o Roboto",
            font_vibe="Industrial, sólida, directa",
            visual_vibe="Mecánica, robusta, con grises metálicos y acentos en rojo o amarillo",
            template="taller.j2",
            keywords_hint=("confianza", "años", "experiencia", "honrado"),
            palette_hint=("dark",),
        ),
        VisualProfile(
            sector="taller", variant="tecnico-preciso",
            heading_font="Barlow (sans técnica y ordenada)",
            body_font="Roboto",
            font_vibe="Técnica, limpia, de manual de instrucciones bien hecho",
            visual_vibe="Diagnóstico digital: fondo claro, esquemas técnicos finos, orden y precisión, sensación de taller moderno y transparente",
            template="taller.j2",
            keywords_hint=("diagnosis", "electrónica", "rápido", "honesto", "presupuesto",
                           "transparente", "moderno"),
            palette_hint=("light", "cool"),
        ),
        VisualProfile(
            sector="taller", variant="motor-pasion",
            heading_font="Anton (condensada, competición)",
            body_font="Barlow",
            font_vibe="Condensada de dorsal de carreras",
            visual_vibe="Pasión por el motor: negro profundo con acento racing, fotografía dramática de detalle mecánico, franjas y velocidad contenida",
            template="taller.j2",
            keywords_hint=("deportivo", "preparación", "4x4", "moto", "competición",
                           "llantas", "escape"),
            palette_hint=("dark", "vivid"),
        ),
    ],
    "tienda_ropa": [
        VisualProfile(
            sector="tienda_ropa", variant="editorial-moda",
            heading_font="Editorial New o Bodoni (editorial, moderna)",
            body_font="Inter o Neue Haas",
            font_vibe="Editorial, moderna, ligera",
            visual_vibe="Fresca, dinámica, tipo revista de moda, generosos espacios en blanco",
            template="tienda_ropa.j2",
            keywords_hint=("tendencia", "colección", "moda", "estilo"),
            palette_hint=("light",),
        ),
        VisualProfile(
            sector="tienda_ropa", variant="street-joven",
            heading_font="Archivo Black (pesada, urbana)",
            body_font="Inter",
            font_vibe="Display contundente de cartel urbano",
            visual_vibe="Street: colores saturados, rejilla rota, stickers y actitud, fotografía de calle con flash directo",
            template="tienda_ropa.j2",
            keywords_hint=("joven", "urbano", "sneakers", "street", "zapatillas",
                           "original", "diferente"),
            palette_hint=("vivid",),
        ),
        VisualProfile(
            sector="tienda_ropa", variant="boutique-atemporal",
            heading_font="Cormorant Garamond (serif de lujo tranquilo)",
            body_font="Inter",
            font_vibe="Serif serena, de marca atemporal",
            visual_vibe="Lujo tranquilo: neutros cálidos, pocas piezas muy bien fotografiadas, aire y calma, asesoramiento personal como bandera",
            template="tienda_ropa.j2",
            keywords_hint=("boutique", "calidad", "asesoramiento", "exclusiva", "tejidos",
                           "atemporal", "personal"),
            palette_hint=("muted", "warm"),
            min_price=2,
        ),
    ],
    "gimnasio": [
        VisualProfile(
            sector="gimnasio", variant="energia-oscura",
            heading_font="Oswald o Anton (condensada, potente)",
            body_font="Inter",
            font_vibe="Condensada, potente, atlética",
            visual_vibe="Enérgica, oscura con acentos vibrantes (lima, naranja, rojo)",
            template="gimnasio.j2",
            keywords_hint=("máquinas", "pesas", "sala", "musculación"),
            palette_hint=("dark", "vivid"),
        ),
        VisualProfile(
            sector="gimnasio", variant="boutique-wellness",
            heading_font="DM Serif Display (serif serena)",
            body_font="Inter",
            font_vibe="Serif calmada, de estudio boutique",
            visual_vibe="Bienestar y equilibrio: claro y sereno, madera y luz natural, movimiento consciente, respiración más que sudor",
            template="gimnasio.j2",
            keywords_hint=("yoga", "pilates", "bienestar", "tranquilo", "estiramientos",
                           "postura", "relajación"),
            palette_hint=("light", "muted"),
        ),
        VisualProfile(
            sector="gimnasio", variant="box-competicion",
            heading_font="Anton (crudo, de competición)",
            body_font="Barlow Condensed",
            font_vibe="Cruda, de pizarra de box",
            visual_vibe="Box de entrenamiento: hormigón y metal, tiza, fotografía real de esfuerzo, comunidad y marcas en la pizarra",
            template="gimnasio.j2",
            keywords_hint=("crossfit", "box", "fuerza", "comunidad", "wod", "halterofilia",
                           "funcional"),
            palette_hint=("dark",),
        ),
    ],
    "floristeria": [
        VisualProfile(
            sector="floristeria", variant="botanica-romantica",
            heading_font="Cormorant Garamond o Fraunces (serif delicada, botánica)",
            body_font="Inter o Nunito",
            font_vibe="Serif delicada con toques románticos",
            visual_vibe="Botánica, natural, fresca, verdes y pasteles suaves, fotografía macro",
            template="floristeria.j2",
            keywords_hint=("ramos", "bodas", "romántico", "delicado"),
            palette_hint=("light", "muted"),
        ),
        VisualProfile(
            sector="floristeria", variant="estudio-contemporaneo",
            heading_font="Space Grotesk (sans de estudio de diseño)",
            body_font="Inter",
            font_vibe="Sans contemporánea, de dirección de arte",
            visual_vibe="Estudio floral contemporáneo: fondo neutro, ramos esculturales fotografiados como objetos de diseño, composición audaz",
            template="floristeria.j2",
            keywords_hint=("diseño", "eventos", "moderno", "autor", "original",
                           "decoración", "espacios"),
            palette_hint=("vivid", "light"),
        ),
        VisualProfile(
            sector="floristeria", variant="mercado-de-barrio",
            heading_font="Lora (serif cálida y honesta)",
            body_font="Nunito",
            font_vibe="Serif cercana, de tienda de siempre",
            visual_vibe="Floristería de barrio: flor fresca del día, cubos de zinc, calidez de mercado, el detalle para hoy mismo",
            template="floristeria.j2",
            keywords_hint=("barrio", "fresca", "detalle", "cercano", "de siempre",
                           "encargo", "rapidez"),
            palette_hint=("warm",),
        ),
    ],
    "estetica": [
        VisualProfile(
            sector="estetica", variant="nude-premium",
            heading_font="DM Serif Display o Cormorant (serif sofisticada)",
            body_font="Inter",
            font_vibe="Serif elegante que transmite cuidado premium",
            visual_vibe="Cuidada, premium, luminosa, tonos nude, beige y rosado, sensación de bienestar",
            template="estetica.j2",
            keywords_hint=("cuidado", "piel", "facial", "manicura"),
            palette_hint=("light", "muted"),
        ),
        VisualProfile(
            sector="estetica", variant="clinica-estetica",
            heading_font="Inter (sans clínica, pesos marcados)",
            body_font="Inter",
            font_vibe="Sans de precisión médica",
            visual_vibe="Precisión y resultados: blanco clínico con un acento frío, aparatología como protagonista, antes/después tratado con rigor",
            template="estetica.j2",
            keywords_hint=("láser", "aparatología", "resultados", "medicina", "depilación",
                           "radiofrecuencia", "tecnología"),
            palette_hint=("cool", "light"),
        ),
        VisualProfile(
            sector="estetica", variant="ritual-spa",
            heading_font="Cormorant Garamond (serif sensorial)",
            body_font="Nunito",
            font_vibe="Serif suave, de ritual pausado",
            visual_vibe="Ritual sensorial: oscuro cálido, piedra, velas y vapor, texturas naturales, el tiempo se detiene",
            template="estetica.j2",
            keywords_hint=("masaje", "relajante", "ritual", "spa", "desconectar",
                           "aromas", "experiencia"),
            palette_hint=("dark", "warm"),
        ),
    ],
    "default": [
        VisualProfile(
            sector="default", variant="versatil",
            heading_font="Inter (sans-serif versátil)",
            body_font="Inter",
            font_vibe="Moderna, profesional, versátil",
            visual_vibe="Limpia, moderna, adaptable a cualquier sector",
            template="default.j2",
        ),
        VisualProfile(
            sector="default", variant="tipografico-contraste",
            heading_font="Space Grotesk (sans con carácter)",
            body_font="Inter",
            font_vibe="Tipografía como protagonista, alto contraste",
            visual_vibe="Sobria y contundente: la tipografía lleva el peso, un solo acento de color de marca, composición asimétrica",
            template="default.j2",
            palette_hint=("dark", "vivid"),
        ),
    ],
}

# Compatibilidad con código antiguo: sector → arquetipo base.
_PROFILES: dict[str, VisualProfile] = {s: variants[0] for s, variants in _ARCHETYPES.items()}


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


# --- Rasgos de paleta -------------------------------------------------------


def _hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def palette_traits(palette: dict | None) -> set[str]:
    """
    Clasifica la paleta del logo en rasgos simples:
      dark/light  (luminosidad del primario)
      vivid/muted (saturación media de primario+secundario+acento)
      warm/cool   (tono del primario)
    """
    if not palette:
        return set()
    if hasattr(palette, "to_dict"):
        palette = palette.to_dict()

    traits: set[str] = set()
    try:
        hues = [_hex_to_hls(palette[k]) for k in ("primary", "secondary", "accent")
                if palette.get(k)]
        if not hues:
            return set()
        h_prim, l_prim, _ = hues[0]

        traits.add("dark" if l_prim < 0.45 else "light")

        avg_sat = sum(s for _, _, s in hues) / len(hues)
        traits.add("vivid" if avg_sat > 0.45 else "muted")

        # Cálido: rojos/naranjas/amarillos (h<0.17) y magentas (h>0.87)
        traits.add("warm" if (h_prim < 0.17 or h_prim > 0.87) else "cool")
    except (ValueError, KeyError, TypeError):
        return set()
    return traits


# --- Selección de arquetipo -------------------------------------------------


def _keywords_text(keywords) -> str:
    """Acepta lista de strings o un string y devuelve un blob en minúsculas."""
    if not keywords:
        return ""
    if isinstance(keywords, str):
        return keywords.lower()
    return " ".join(str(k) for k in keywords).lower()


def _stable_jitter(seed: str, variant: str) -> float:
    """Desempate determinista en [0, 1): mismo negocio → mismo resultado."""
    digest = hashlib.md5(f"{seed}::{variant}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def select_archetype(
    sector: str,
    *,
    palette: dict | None = None,
    keywords=None,
    price_level: int | None = None,
    seed: str = "",
) -> VisualProfile:
    """
    Elige el arquetipo del sector que mejor encaja con las señales del negocio.

    Puntuación:
      +2 por cada keyword_hint que aparece en las reseñas/keywords
      +1 por cada rasgo de paleta que coincide con palette_hint
      -3 si el arquetipo exige un nivel de precio que el negocio no alcanza
      + jitter determinista (<1) para que los empates no caigan siempre igual
    """
    candidates = _ARCHETYPES.get(sector, _ARCHETYPES["default"])
    if len(candidates) == 1:
        return candidates[0]

    text = _keywords_text(keywords)
    traits = palette_traits(palette)

    best, best_score = candidates[0], float("-inf")
    for arc in candidates:
        score = 0.0
        score += 2 * sum(1 for kw in arc.keywords_hint if kw in text)
        score += sum(1 for t in arc.palette_hint if t in traits)
        if arc.min_price is not None and price_level is not None and price_level < arc.min_price:
            score -= 3
        score += _stable_jitter(seed or "sin-seed", arc.variant)
        if score > best_score:
            best, best_score = arc, score
    return best


def get_profile(
    categories: list[str] | str,
    name: str = "",
    *,
    palette: dict | None = None,
    keywords=None,
    price_level: int | None = None,
    seed: str = "",
) -> VisualProfile:
    """
    Devuelve el VisualProfile para un negocio.

    Sin señales (palette/keywords/price_level/seed) devuelve el arquetipo
    base del sector — mismo comportamiento que la versión antigua.
    Con señales, elige el arquetipo que mejor encaja.
    """
    sector = resolve_sector(categories, name)
    if palette is None and keywords is None and price_level is None and not seed:
        return _PROFILES.get(sector, _PROFILES["default"])
    return select_archetype(
        sector, palette=palette, keywords=keywords,
        price_level=price_level, seed=seed,
    )


def archetypes_for(sector: str) -> list[VisualProfile]:
    """Todos los arquetipos definidos para un sector."""
    return list(_ARCHETYPES.get(sector, _ARCHETYPES["default"]))


def list_sectors() -> list[str]:
    return list(_ARCHETYPES.keys())


__all__ = [
    "VisualProfile", "get_profile", "select_archetype", "archetypes_for",
    "resolve_sector", "palette_traits", "list_sectors",
]

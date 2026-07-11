"""
smoke_test.py
-------------
Test de humo sin tocar APIs externas. Verifica:
  - image_analyzer.py con una imagen generada
  - typography_rules.py: resolución de sector + selección de arquetipos
  - review_analyzer.py: extracción de citas literales (sin LLM)
  - structure_rules.py: estructura variable y determinista
  - prompt_builder.py ensamblando con todas las plantillas y arquetipos

No necesita Google API ni Ollama para correr.
Ejecuta: python smoke_test.py
"""

import io
import sys
from pathlib import Path

# Windows consola: fuerza UTF-8 para que no explote al imprimir símbolos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import numpy as np

from modules.google_extractor import Business
from modules.image_analyzer import extract_palette
from modules.typography_rules import (
    get_profile, archetypes_for, list_sectors, palette_traits,
)
from modules.review_analyzer import ReviewInsights, extract_quotes
from modules.structure_rules import build_structure, HERO_PATTERNS
from modules.creative_director import fallback_concept
from modules.prompt_builder import PromptBuilder


def _make_fake_logo_bytes() -> bytes:
    """Crea una imagen PNG con colores dominantes claros."""
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    arr[:100, :100] = [44, 24, 16]      # marrón oscuro (primario)
    arr[:100, 100:] = [212, 168, 83]    # dorado (acento)
    arr[100:, :100] = [245, 240, 235]   # crema (neutro)
    arr[100:, 100:] = [70, 40, 30]      # marrón medio
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fake_business(place_id: str = "FAKE_123") -> Business:
    return Business(
        place_id=place_id,
        name="Barbería El Rincón",
        category="barber_shop",
        categories_all=["barber_shop", "hair_care", "establishment"],
        address="Calle La Noria 12, Santa Cruz de Tenerife",
        phone="+34 922 12 34 56",
        website=None,
        rating=4.8,
        review_count=127,
        opening_hours=[
            "lunes: 9:00–20:00",
            "martes: 9:00–20:00",
            "miércoles: 9:00–20:00",
            "jueves: 9:00–20:00",
            "viernes: 9:00–20:00",
            "sábado: 10:00–18:00",
            "domingo: cerrado",
        ],
        reviews=[
            {"author": "Juan", "rating": 5, "text": "Trato excelente y el corte clavado.", "time": 0},
        ],
        photo_references=[],
        location={"lat": 28.4636, "lng": -16.2518},
        maps_url="https://maps.google.com/?cid=123",
        price_level=2,
    )


def _fake_insights() -> ReviewInsights:
    return ReviewInsights(
        keywords=["trato personal", "profesionalidad", "ambiente", "precio justo"],
        tone="cercano, masculino, artesanal",
        selling_points=[
            "Corte clásico con atención al detalle",
            "Ambiente relajado y acogedor",
            "Barberos experimentados",
        ],
        vibe="Barbería clásica con alma de barrio.",
        target_audience="Hombres de 25-55 años que valoran el servicio cuidado.",
        warnings=[],
        quotes=["Trato excelente y el corte clavado, volveré seguro."],
    )


def test_palette():
    palette = extract_palette(_make_fake_logo_bytes())
    assert palette.primary.startswith("#")
    assert palette.secondary.startswith("#")
    assert palette.accent.startswith("#")
    assert palette.neutral.startswith("#")
    print(f"  ✓ Palette: primario={palette.primary} secundario={palette.secondary}")
    return palette


def test_typography_rules():
    # Casos por categoría Google (sin nombre)
    cases = [
        (["barber_shop"], "", "barberia"),
        (["restaurant", "food"], "", "restaurante"),
        (["hair_care"], "", "peluqueria"),
        (["dentist"], "", "clinica"),
        (["car_repair"], "", "taller"),
        (["clothing_store"], "", "tienda_ropa"),
        (["gym"], "", "gimnasio"),
        (["cafe"], "", "cafeteria"),
        (["florist"], "", "floristeria"),
        (["beauty_salon"], "", "estetica"),
        (["spa"], "", "estetica"),
        (["some_unknown_type"], "", "default"),
        # El nombre tiene prioridad: arregla categorías ambiguas
        (["hair_care"], "Bobe Barber Shop", "barberia"),
        (["establishment"], "Barbería El Rincón", "barberia"),
        (["establishment"], "Floristería Las Rosas", "floristeria"),
        (["establishment"], "Clínica Dental Sur", "clinica"),
        (["establishment"], "Taller Hnos. García", "taller"),
        (["establishment"], "Pizzería Don Luigi", "restaurante"),
        (["establishment"], "Cafetería La Esquina", "cafeteria"),
        (["beauty_salon"], "Centro de Estética Laura", "estetica"),
        (["establishment"], "CrossFit Tenerife", "gimnasio"),
    ]
    for cats, name, expected in cases:
        profile = get_profile(cats, name=name)
        assert profile.sector == expected, \
            f"{cats} + '{name}' → {profile.sector} (esperaba {expected})"
    print(f"  ✓ Typography rules: {len(cases)} casos OK")
    print(f"  ✓ Sectores definidos: {list_sectors()}")


def test_archetype_selection():
    # 1. Sin señales → arquetipo base (compatibilidad con comportamiento antiguo)
    base = get_profile(["hair_care"])
    assert base.variant == "editorial-premium", base.variant

    # 2. Las keywords de reseñas empujan al arquetipo correcto
    urbano = get_profile(
        ["hair_care"], seed="X1",
        keywords="ambiente joven y moderno, me hicieron un balayage y mechas increíbles",
    )
    assert urbano.variant == "estudio-urbano", urbano.variant

    barrio = get_profile(
        ["hair_care"], seed="X1",
        keywords="peluquería de barrio de toda la vida, precio justo y trato amable",
    )
    assert barrio.variant == "clasica-de-barrio", barrio.variant

    # 3. Determinista: mismo negocio (seed) → mismo arquetipo siempre
    a = get_profile(["hair_care"], seed="PLACE_A", keywords="corte")
    b = get_profile(["hair_care"], seed="PLACE_A", keywords="corte")
    assert a.variant == b.variant

    # 4. Sin señales fuertes, negocios distintos NO caen todos en el mismo arquetipo
    variants = {
        get_profile(["hair_care"], seed=f"PLACE_{i}", keywords="corte bonito").variant
        for i in range(12)
    }
    assert len(variants) > 1, f"12 negocios sin señal cayeron todos en: {variants}"

    # 5. Rasgos de paleta
    traits = palette_traits({"primary": "#111111", "secondary": "#222222", "accent": "#333333"})
    assert "dark" in traits and "muted" in traits

    n_arcs = sum(len(archetypes_for(s)) for s in list_sectors())
    print(f"  ✓ Selección de arquetipos OK ({n_arcs} arquetipos en {len(list_sectors())} sectores)")
    print(f"  ✓ Variantes elegidas entre 12 seeds: {sorted(variants)}")


def test_quotes():
    reviews = [
        {"rating": 5, "text": "Me arreglaron el color que me destrozaron en otro sitio. Salí feliz."},
        {"rating": 5, "text": "Top."},  # demasiado corta → fuera
        {"rating": 2, "text": "Esperé cuarenta minutos y nadie me atendió, mala experiencia."},  # nota baja → fuera
        {"rating": 4, "text": "Muy buen trato y siempre con una sonrisa, el local es pequeño pero acogedor."},
        {"rating": 5, "text": "Me arreglaron el color que llevaba mal de otro salón hace tiempo."},  # casi duplicada → fuera
        {"rating": 5, "text": "x" * 500},  # demasiado larga → fuera
    ]
    quotes = extract_quotes(reviews, max_quotes=3)
    assert len(quotes) == 2, quotes
    assert quotes[0].startswith("Me arreglaron el color")
    assert all("Esperé cuarenta" not in q for q in quotes)
    print(f"  ✓ Citas literales: {len(quotes)} seleccionadas, filtros OK")


def test_structure():
    # Determinista
    s1 = build_structure("peluqueria", seed="PLACE_A")
    s2 = build_structure("peluqueria", seed="PLACE_A")
    assert s1 == s2

    # El hero sale del pool y el cierre (contacto/ubicación) es siempre el último
    assert s1.hero in HERO_PATTERNS
    assert "Ubicación" in s1.sections[-1] or "contacto" in s1.sections[-1].lower()

    # Variedad real entre negocios del mismo sector
    heroes = {build_structure("peluqueria", seed=f"P_{i}").hero for i in range(12)}
    layouts = {tuple(build_structure("peluqueria", seed=f"P_{i}").sections) for i in range(12)}
    assert len(heroes) > 2, f"solo {len(heroes)} heros distintos en 12 negocios"
    assert len(layouts) > 6, f"solo {len(layouts)} estructuras distintas en 12 negocios"

    # Todos los sectores construyen sin romper
    for sector in list_sectors():
        st = build_structure(sector, seed="ANY")
        assert st.hero and len(st.sections) >= 5
    print(f"  ✓ Estructuras: deterministas, {len(heroes)} heros y {len(layouts)} layouts distintos en 12 seeds")


def test_prompt_builder():
    builder = PromptBuilder()
    biz = _fake_business()
    palette = test_palette()
    profile = get_profile(biz.categories_all)
    insights = _fake_insights()

    prompt = builder.build(
        business=biz,
        palette=palette,
        profile=profile,
        insights=insights,
    )

    assert "Barbería El Rincón" in prompt
    assert palette.primary in prompt
    assert "Bebas Neue" in prompt or "Oswald" in prompt  # tipografía de barbería (arquetipo base)
    assert "Reserva" in prompt or "WhatsApp" in prompt
    # Bloques nuevos: concepto creativo, arquitectura variable y citas literales
    assert "CONCEPTO CREATIVO" in prompt
    assert "ARQUITECTURA DE LA PÁGINA" in prompt
    assert "el corte clavado" in prompt  # la cita literal llega al prompt

    # Mismo negocio → mismo prompt (variación determinista, no aleatoria)
    prompt2 = builder.build(business=biz, palette=palette, profile=profile, insights=insights)
    assert prompt == prompt2

    # Negocio distinto del mismo sector → prompt estructuralmente distinto
    biz_b = _fake_business(place_id="OTRO_999")
    prompt_b = builder.build(business=biz_b, palette=palette, profile=profile, insights=insights)
    assert prompt != prompt_b, "dos negocios distintos generaron exactamente el mismo prompt"

    out = Path(__file__).parent / "output" / "_smoke_test.txt"
    builder.save(prompt, out)
    print(f"  ✓ Prompt generado ({len(prompt)} chars) → {out.name}")
    print(f"\n--- PREVIEW (primeras 40 líneas) ---")
    for line in prompt.splitlines()[:40]:
        print(f"  {line}")


def test_all_templates_render():
    """Renderiza todas las plantillas con TODOS sus arquetipos."""
    builder = PromptBuilder()
    biz = _fake_business()
    palette = extract_palette(_make_fake_logo_bytes())
    insights = _fake_insights()

    total = 0
    for sector in list_sectors():
        for profile in archetypes_for(sector):
            structure = build_structure(sector, seed=biz.place_id)
            concept = fallback_concept(business=biz, profile=profile, structure=structure)
            prompt = builder.build(
                business=biz, palette=palette, profile=profile,
                insights=insights, structure=structure, concept=concept,
            )
            assert len(prompt) > 100, f"prompt vacío para {sector}/{profile.variant}"
            assert profile.heading_font.split(" ")[0] in prompt
            total += 1
    print(f"  ✓ Todas las plantillas renderizan: {total} combinaciones sector×arquetipo")


if __name__ == "__main__":
    print("=== SMOKE TEST ===\n")
    print("[1] image_analyzer.py")
    test_palette()
    print("\n[2] typography_rules.py — sectores")
    test_typography_rules()
    print("\n[3] typography_rules.py — arquetipos")
    test_archetype_selection()
    print("\n[4] review_analyzer.py — citas literales")
    test_quotes()
    print("\n[5] structure_rules.py — estructura variable")
    test_structure()
    print("\n[6] Todas las plantillas × arquetipos")
    test_all_templates_render()
    print("\n[7] prompt_builder.py + pipeline")
    test_prompt_builder()
    print("\n=== ✓ TODO OK ===")

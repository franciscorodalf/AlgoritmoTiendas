"""
smoke_test.py
-------------
Test de humo sin tocar APIs externas. Verifica:
  - image_analyzer.py con una imagen generada
  - typography_rules.py con categorías reales de Google
  - prompt_builder.py ensamblando con todas las plantillas

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
from modules.typography_rules import get_profile, list_sectors
from modules.review_analyzer import ReviewInsights
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


def _fake_business() -> Business:
    return Business(
        place_id="FAKE_123",
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
    cases = [
        (["barber_shop"], "barberia"),
        (["restaurant", "food"], "restaurante"),
        (["hair_care"], "peluqueria"),
        (["dentist"], "clinica"),
        (["car_repair"], "taller"),
        (["clothing_store"], "tienda_ropa"),
        (["gym"], "gimnasio"),
        (["cafe"], "cafeteria"),
        (["florist"], "floristeria"),
        (["beauty_salon"], "estetica"),
        (["spa"], "estetica"),
        (["some_unknown_type"], "default"),
    ]
    for cats, expected in cases:
        profile = get_profile(cats)
        assert profile.sector == expected, f"{cats} → {profile.sector} (esperaba {expected})"
    print(f"  ✓ Typography rules: {len(cases)} casos OK")
    print(f"  ✓ Sectores definidos: {list_sectors()}")


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
    assert "Bebas Neue" in prompt or "Oswald" in prompt  # tipografía de barbería
    assert "Reserva" in prompt or "WhatsApp" in prompt

    out = Path(__file__).parent / "output" / "_smoke_test.txt"
    builder.save(prompt, out)
    print(f"  ✓ Prompt generado ({len(prompt)} chars) → {out.name}")
    print(f"\n--- PREVIEW (primeras 30 líneas) ---")
    for line in prompt.splitlines()[:30]:
        print(f"  {line}")


def test_all_templates_render():
    """Renderiza todas las plantillas para verificar que ninguna rompe."""
    builder = PromptBuilder()
    biz = _fake_business()
    palette = extract_palette(_make_fake_logo_bytes())
    insights = _fake_insights()

    for sector in list_sectors():
        profile = get_profile([f"__force_{sector}__"])  # forzamos default primero
        # Sobrescribimos el sector manualmente:
        from modules.typography_rules import _PROFILES  # noqa
        profile = _PROFILES[sector]
        prompt = builder.build(business=biz, palette=palette, profile=profile, insights=insights)
        assert len(prompt) > 100, f"prompt vacío para {sector}"
    print(f"  ✓ Todas las plantillas ({len(list_sectors())}) renderizan sin error")


if __name__ == "__main__":
    print("=== SMOKE TEST ===\n")
    print("[1] image_analyzer.py")
    test_palette()
    print("\n[2] typography_rules.py")
    test_typography_rules()
    print("\n[3] Todas las plantillas Jinja2")
    test_all_templates_render()
    print("\n[4] prompt_builder.py + pipeline")
    test_prompt_builder()
    print("\n=== ✓ TODO OK ===")

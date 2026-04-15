"""
main.py
-------
Orquestador del algoritmo de prospección.

Modos de uso:

  # Búsqueda libre (sector + zona o lo que quieras)
  python main.py "peluquerías en La Laguna"
  python main.py "barbería" --region "Adeje, Tenerife"

  # Nombre concreto
  python main.py "Barbería El Rincón Santa Cruz"

  # Varias queries en un batch
  python main.py --queries queries.txt

  # Limitar cuántos resultados procesar
  python main.py "cafeterías Tenerife" --max 5

  # Incluir también los que ya tienen web (modo auditoría)
  python main.py "restaurantes Garachico" --include-with-website
"""

from __future__ import annotations

import argparse
import re
import sys
import traceback
from pathlib import Path

# Windows consola: fuerza UTF-8 para que rich pueda imprimir símbolos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table

from modules.google_extractor import GoogleExtractor, Business
from modules.image_analyzer import extract_palette, Palette
from modules.typography_rules import get_profile
from modules.review_analyzer import ReviewAnalyzer
from modules.prompt_builder import PromptBuilder


console = Console()
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


# ---------------------------------------------------------------------------
# Pipeline por negocio
# ---------------------------------------------------------------------------


def process_business(
    biz: Business,
    extractor: GoogleExtractor,
    analyzer: ReviewAnalyzer,
    builder: PromptBuilder,
) -> Path:
    """Procesa un negocio completo y devuelve la ruta del prompt generado."""

    # 1. Paleta a partir de la primera foto disponible
    palette = _get_palette(biz, extractor)

    # 2. Perfil visual (tipografía + vibe) por sector
    profile = get_profile(biz.categories_all or biz.category)

    # 3. Insights de reseñas via Ollama (local)
    insights = analyzer.analyze(
        name=biz.name,
        category=profile.sector,
        reviews=biz.reviews,
    )

    # 4. Ensamblaje final
    prompt = builder.build(
        business=biz,
        palette=palette,
        profile=profile,
        insights=insights,
    )

    out_path = OUTPUT_DIR / f"{_slugify(biz.name)}.txt"
    builder.save(prompt, out_path)
    return out_path


def _get_palette(biz: Business, extractor: GoogleExtractor) -> Palette:
    """Intenta con cada photo_reference hasta que una funcione."""
    for ref in biz.photo_references[:3]:
        try:
            img_bytes = extractor.download_photo(ref, max_width=600)
            if img_bytes:
                return extract_palette(img_bytes)
        except Exception as exc:
            console.print(f"  [yellow]⚠ foto falló: {exc}[/yellow]")
            continue

    # Fallback: paleta neutra razonable
    return Palette(
        primary="#2C3E50",
        secondary="#C0A062",
        accent="#E8C547",
        neutral="#F5F0EB",
        all_hex=["#2C3E50", "#C0A062", "#E8C547", "#F5F0EB"],
    )


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[áà]", "a", s)
    s = re.sub(r"[éè]", "e", s)
    s = re.sub(r"[íì]", "i", s)
    s = re.sub(r"[óò]", "o", s)
    s = re.sub(r"[úù]", "u", s)
    s = re.sub(r"ñ", "n", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "negocio"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Genera prompts de web personalizados para negocios locales en Tenerife.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("query", nargs="?", help="Nombre, sector o 'sector en zona'.")
    p.add_argument("--queries", type=Path,
                   help="Fichero con una query por línea (batch).")
    p.add_argument("--region", default=None,
                   help="Sobrescribe la región por defecto (ej. 'Adeje, Tenerife').")
    p.add_argument("--max", type=int, default=10,
                   help="Máximo de negocios a procesar por query (default: 10).")
    p.add_argument("--include-with-website", action="store_true",
                   help="No filtrar los que ya tienen web (útil para auditar).")
    p.add_argument("--skip-ollama", action="store_true",
                   help="Saltar análisis de reseñas (útil si Ollama no está disponible).")
    return p.parse_args()


def collect_queries(args) -> list[str]:
    if args.queries:
        return [line.strip() for line in args.queries.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")]
    if args.query:
        return [args.query]
    console.print("[red]Debes pasar una query o un fichero con --queries.[/red]")
    sys.exit(2)


def main() -> None:
    args = parse_args()
    queries = collect_queries(args)

    # --- Inicialización ---
    try:
        extractor = GoogleExtractor()
    except RuntimeError as exc:
        console.print(f"[red]✗ {exc}[/red]")
        sys.exit(1)

    analyzer = ReviewAnalyzer()
    if not args.skip_ollama and not analyzer.ping():
        console.print(
            "[yellow]⚠ Ollama no responde en "
            f"{analyzer.host}. Inicia Ollama o usa --skip-ollama.[/yellow]"
        )
        sys.exit(1)

    builder = PromptBuilder()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Búsqueda ---
    console.rule("[bold cyan]Buscando en Google Places[/bold cyan]")
    businesses = extractor.search_many(
        queries,
        region=args.region,
        max_results=args.max,
        only_without_website=not args.include_with_website,
    )

    if not businesses:
        console.print("[yellow]No se encontraron negocios sin web. Prueba otra query o --include-with-website.[/yellow]")
        return

    _print_summary(businesses)

    # --- Procesado ---
    console.rule("[bold cyan]Generando prompts[/bold cyan]")
    ok, fail = 0, 0
    for i, biz in enumerate(businesses, 1):
        console.print(f"\n[{i}/{len(businesses)}] [bold]{biz.name}[/bold] — {biz.address}")
        try:
            if args.skip_ollama:
                _write_skeleton(biz, builder)
            else:
                path = process_business(biz, extractor, analyzer, builder)
                console.print(f"  [green]✓ {path.name}[/green]")
            ok += 1
        except Exception as exc:
            fail += 1
            console.print(f"  [red]✗ {exc}[/red]")
            if "--debug" in sys.argv:
                traceback.print_exc()

    console.rule()
    console.print(f"[green]✓ {ok}[/green] generados · [red]{fail}[/red] fallos · "
                  f"Prompts en: [cyan]{OUTPUT_DIR}[/cyan]")


def _print_summary(businesses: list[Business]) -> None:
    table = Table(title=f"{len(businesses)} negocios candidatos")
    table.add_column("#", justify="right")
    table.add_column("Nombre", style="bold")
    table.add_column("Categoría")
    table.add_column("★")
    table.add_column("Reseñas", justify="right")
    table.add_column("Tel")
    for i, b in enumerate(businesses, 1):
        table.add_row(
            str(i), b.name, b.category,
            f"{b.rating:.1f}" if b.rating else "-",
            str(b.review_count),
            b.phone or "-",
        )
    console.print(table)


def _write_skeleton(biz: Business, builder: PromptBuilder) -> None:
    """Versión mínima sin LLM (fallback con --skip-ollama)."""
    from modules.review_analyzer import ReviewInsights
    profile = get_profile(biz.categories_all or biz.category)
    palette = Palette(
        primary="#2C3E50", secondary="#C0A062",
        accent="#E8C547", neutral="#F5F0EB",
        all_hex=["#2C3E50", "#C0A062", "#E8C547", "#F5F0EB"],
    )
    insights = ReviewInsights(
        keywords=[], tone="", selling_points=[],
        vibe="", target_audience="", warnings=[],
    )
    prompt = builder.build(business=biz, palette=palette, profile=profile, insights=insights)
    builder.save(prompt, OUTPUT_DIR / f"{_slugify(biz.name)}.txt")


if __name__ == "__main__":
    main()

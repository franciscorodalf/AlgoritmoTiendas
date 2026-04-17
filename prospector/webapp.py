"""
webapp.py
---------
Servidor Flask: API REST + sirve el frontend de Prospector Tenerife.

Endpoints
─────────
GET  /                           → frontend (static/index.html)
GET  /api/health                 → estado de Ollama + API key + estadísticas
GET  /api/prompts                → lista de prompts ya generados
GET  /api/prompts/<name>         → contenido de un prompt
GET  /api/registry               → negocios ya procesados (dedup)
POST /api/generate               → búsqueda por texto { query, max, region, skip_ollama }
POST /api/discover               → búsqueda por zona  { lat, lng, radius_m, max, skip_ollama }
GET  /api/jobs/<id>              → estado de un job en background

Arranca con: python start.py   (o vía start.bat)
"""

from __future__ import annotations

import os
import sys
import threading
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent))

from modules.google_extractor import GoogleExtractor
from modules.review_analyzer import ReviewAnalyzer
from modules.prompt_builder import PromptBuilder
from modules import registry
from main import process_business, _slugify, _write_skeleton, OUTPUT_DIR

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")

# Jobs en memoria (sencillo, single-process)
_jobs: dict[str, dict] = {}
_lock = threading.Lock()

# Tenerife: bounding box para validar coordenadas
_TENERIFE_BOUNDS = {
    "lat_min": 27.97, "lat_max": 28.60,
    "lng_min": -16.95, "lng_max": -16.08,
}


def _in_tenerife(lat: float, lng: float) -> bool:
    b = _TENERIFE_BOUNDS
    return b["lat_min"] <= lat <= b["lat_max"] and b["lng_min"] <= lng <= b["lng_max"]


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(str(STATIC), "index.html")


# ---------------------------------------------------------------------------
# Prompts ya generados
# ---------------------------------------------------------------------------

@app.route("/api/prompts")
def list_prompts():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [f for f in OUTPUT_DIR.glob("*.txt") if not f.name.startswith("_")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    reg = registry.all_entries()
    result = []
    for f in files:
        entry = next((v for v in reg.values() if v.get("output_file") == f.name), None)
        result.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
            "business_name": entry["name"] if entry else f.name.replace(".txt", "").replace("_", " ").title(),
            "processed_at": entry["processed_at"] if entry else None,
        })
    return jsonify(result)


@app.route("/api/prompts/<path:name>")
def read_prompt(name: str):
    target = OUTPUT_DIR / name
    if not target.exists() or not target.is_file():
        return jsonify({"error": "not found"}), 404
    return jsonify({"name": name, "content": target.read_text(encoding="utf-8")})


# ---------------------------------------------------------------------------
# Registry (deduplicación)
# ---------------------------------------------------------------------------

@app.route("/api/registry")
def get_registry():
    return jsonify({
        "count": registry.count(),
        "entries": registry.all_entries(),
    })


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    has_key = bool(os.getenv("GOOGLE_PLACES_API_KEY"))
    analyzer = ReviewAnalyzer()
    ollama_ok = analyzer.ping()
    return jsonify({
        "google_api_key": has_key,
        "ollama": ollama_ok,
        "ollama_host": analyzer.host,
        "output_dir": str(OUTPUT_DIR),
        "prompts_count": len(list(OUTPUT_DIR.glob("*.txt"))) if OUTPUT_DIR.exists() else 0,
        "registry_count": registry.count(),
    })


# ---------------------------------------------------------------------------
# Core pipeline (compartido por generate y discover)
# ---------------------------------------------------------------------------

def _run_pipeline(job_id: str, businesses: list, payload: dict) -> None:
    log: list[str] = []

    def emit(msg: str) -> None:
        log.append(msg)
        with _lock:
            _jobs[job_id]["log"] = list(log)

    try:
        with _lock:
            _jobs[job_id]["status"] = "running"

        skip_ollama = bool(payload.get("skip_ollama", False))
        analyzer = ReviewAnalyzer()
        builder = PromptBuilder()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if not skip_ollama and not analyzer.ping():
            raise RuntimeError(f"Ollama no responde en {analyzer.host}")

        # --- Filtrar ya procesados ---
        known = registry.known_ids()
        fresh = [b for b in businesses if b.place_id not in known]
        dupes = len(businesses) - len(fresh)
        if dupes:
            emit(f"⏭ {dupes} ya procesados anteriormente — omitidos")
        if not fresh:
            emit("✓ Todos los negocios encontrados ya estaban procesados")
            with _lock:
                _jobs[job_id]["status"] = "done"
                _jobs[job_id]["generated"] = []
            return

        emit(f"✓ {len(fresh)} negocios nuevos a procesar")

        extractor = GoogleExtractor()
        generated: list[str] = []

        for i, biz in enumerate(fresh, 1):
            emit(f"[{i}/{len(fresh)}] {biz.name}")
            try:
                if skip_ollama:
                    _write_skeleton(biz, builder)
                    out_name = f"{_slugify(biz.name)}.txt"
                else:
                    path = process_business(biz, extractor, analyzer, builder)
                    out_name = path.name
                registry.register(biz.place_id, biz.name, out_name)
                generated.append(out_name)
                emit(f"   ✓ {out_name}")
            except Exception as exc:
                emit(f"   ✗ {exc}")

        with _lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["generated"] = generated

    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)
        emit(f"✗ ERROR: {exc}")
        emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# /api/generate — búsqueda por texto
# ---------------------------------------------------------------------------

def _run_generate(job_id: str, payload: dict) -> None:
    log: list[str] = []

    def emit(msg: str) -> None:
        log.append(msg)
        with _lock:
            _jobs[job_id]["log"] = list(log)

    try:
        query = payload["query"].strip()
        max_results = int(payload.get("max", 5))
        region = payload.get("region") or None
        include_with_website = bool(payload.get("include_with_website", False))

        emit(f"▶ Buscando: {query}")
        extractor = GoogleExtractor()
        businesses = extractor.search_many(
            [query],
            region=region,
            max_results=max_results,
            only_without_website=not include_with_website,
        )
        emit(f"✓ {len(businesses)} candidatos en Google")
        _run_pipeline(job_id, businesses, payload)

    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)
        emit(f"✗ ERROR: {exc}")
        emit(traceback.format_exc())


@app.route("/api/generate", methods=["POST"])
def generate():
    payload = request.get_json(force=True) or {}
    if not payload.get("query"):
        return jsonify({"error": "query requerida"}), 400

    job_id = _new_job()
    t = threading.Thread(target=_run_generate, args=(job_id, payload), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


# ---------------------------------------------------------------------------
# /api/discover — búsqueda por zona (Leaflet map)
# ---------------------------------------------------------------------------

def _run_discover(job_id: str, payload: dict) -> None:
    log: list[str] = []

    def emit(msg: str) -> None:
        log.append(msg)
        with _lock:
            _jobs[job_id]["log"] = list(log)

    try:
        lat = float(payload["lat"])
        lng = float(payload["lng"])
        radius_m = int(payload.get("radius_m", 2000))
        max_results = int(payload.get("max", 20))
        include_with_website = bool(payload.get("include_with_website", False))

        if not _in_tenerife(lat, lng):
            raise ValueError(
                f"Las coordenadas ({lat:.4f}, {lng:.4f}) están fuera de Tenerife. "
                "Solo operamos en la isla."
            )

        emit(f"▶ Explorando zona: ({lat:.5f}, {lng:.5f}), radio {radius_m}m")
        extractor = GoogleExtractor()
        known = registry.known_ids()
        businesses = extractor.search_nearby(
            lat, lng, radius_m,
            only_without_website=not include_with_website,
            max_results=max_results,
            skip_ids=known,
        )
        emit(f"✓ {len(businesses)} negocios sin web encontrados")
        _run_pipeline(job_id, businesses, payload)

    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)
        emit(f"✗ ERROR: {exc}")
        emit(traceback.format_exc())


@app.route("/api/discover", methods=["POST"])
def discover():
    payload = request.get_json(force=True) or {}
    if "lat" not in payload or "lng" not in payload:
        return jsonify({"error": "Se requieren lat y lng"}), 400

    job_id = _new_job()
    t = threading.Thread(target=_run_discover, args=(job_id, payload), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def _new_job() -> str:
    import time
    job_id = f"job_{int(time.time() * 1000)}"
    with _lock:
        _jobs[job_id] = {"status": "queued", "log": [], "generated": []}
    return job_id


@app.route("/api/jobs/<job_id>")
def job_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


# ---------------------------------------------------------------------------

def main() -> None:
    host = os.getenv("WEBAPP_HOST", "127.0.0.1")
    port = int(os.getenv("WEBAPP_PORT", "5000"))
    print(f"\n  Prospector UI → http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

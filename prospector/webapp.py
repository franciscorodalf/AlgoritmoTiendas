"""
webapp.py
---------
Flask API + frontend Prospector Tenerife (CRM completo).

Endpoints
─────────
Prompts
  GET    /api/prompts                 lista de prompts generados
  GET    /api/prompts/<name>          contenido de un prompt
  PUT    /api/prompts/<name>          guardar edición
  DELETE /api/prompts/<name>          eliminar prompt

Negocios (CRM)
  GET    /api/businesses              lista completa con status/score/social
  GET    /api/businesses/<pid>        ficha individual
  PATCH  /api/businesses/<pid>        actualizar status/notes/score
  POST   /api/businesses/<pid>/regenerate_outreach
                                      regenerar mensajes WhatsApp/email
  POST   /api/businesses/<pid>/detect_social
                                      buscar redes sociales

Stats & export
  GET    /api/stats                   dashboard stats
  GET    /api/export/csv              exportar todo a CSV

Búsquedas
  POST   /api/generate                búsqueda por texto
  POST   /api/discover                búsqueda por zona
  GET    /api/jobs/<id>               estado de un job
"""

from __future__ import annotations

import csv
import io
import os
import sys
import threading
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flask import Flask, jsonify, request, send_from_directory, Response

sys.path.insert(0, str(Path(__file__).parent))

from modules.google_extractor import GoogleExtractor
from modules.review_analyzer import ReviewAnalyzer
from modules.prompt_builder import PromptBuilder
from modules.outreach import OutreachBuilder
from modules.typography_rules import get_profile
from modules import registry, web_verifier, social_detector, scoring
from main import process_business, _slugify, _write_skeleton, OUTPUT_DIR

BASE   = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")

_jobs: dict[str, dict] = {}
_lock = threading.Lock()

_TENERIFE_BOUNDS = dict(lat_min=27.97, lat_max=28.60, lng_min=-16.95, lng_max=-16.08)

_outreach_builder = OutreachBuilder()


def _in_tenerife(lat: float, lng: float) -> bool:
    b = _TENERIFE_BOUNDS
    return b["lat_min"] <= lat <= b["lat_max"] and b["lng_min"] <= lng <= b["lng_max"]


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(str(STATIC), "index.html")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@app.route("/api/prompts")
def list_prompts():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [f for f in OUTPUT_DIR.glob("*.txt") if not f.name.startswith("_")],
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    result = []
    for f in files:
        entry = registry.find_by_output_file(f.name)
        if entry:
            result.append({
                "name":          f.name,
                "size":          f.stat().st_size,
                "business_name": entry.get("name") or f.name,
                "sector":        entry.get("sector") or "",
                "status":        entry.get("status", "found"),
                "score":         entry.get("score", 0),
                "processed_at":  entry.get("processed_at"),
                "place_id":      entry.get("place_id"),
            })
        else:
            result.append({
                "name":          f.name,
                "size":          f.stat().st_size,
                "business_name": f.name.replace(".txt","").replace("_"," ").title(),
                "sector":        "",
                "status":        "found",
                "score":         0,
                "processed_at":  None,
                "place_id":      None,
            })
    return jsonify(result)


@app.route("/api/prompts/<path:name>", methods=["GET"])
def read_prompt(name: str):
    target = OUTPUT_DIR / name
    if not target.exists() or not target.is_file():
        return jsonify({"error": "not found"}), 404
    return jsonify({"name": name, "content": target.read_text(encoding="utf-8")})


@app.route("/api/prompts/<path:name>", methods=["PUT"])
def update_prompt(name: str):
    target = OUTPUT_DIR / name
    if not target.exists():
        return jsonify({"error": "not found"}), 404
    payload = request.get_json(force=True) or {}
    target.write_text(payload.get("content", ""), encoding="utf-8")
    return jsonify({"ok": True})


@app.route("/api/prompts/<path:name>", methods=["DELETE"])
def delete_prompt(name: str):
    target = OUTPUT_DIR / name
    if target.exists():
        target.unlink()
    entry = registry.find_by_output_file(name)
    if entry and request.args.get("purge") == "1":
        registry.delete(entry["place_id"])
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Businesses (CRM)
# ---------------------------------------------------------------------------

@app.route("/api/businesses")
def list_businesses():
    return jsonify(list(registry.all_entries().values()))


@app.route("/api/businesses/<pid>")
def get_business(pid: str):
    entry = registry.get(pid)
    if not entry:
        return jsonify({"error": "not found"}), 404
    return jsonify(entry)


@app.route("/api/businesses/<pid>", methods=["PATCH"])
def patch_business(pid: str):
    payload = request.get_json(force=True) or {}
    allowed = {"status", "notes", "score"}
    fields = {k: v for k, v in payload.items() if k in allowed}
    if "status" in fields and fields["status"] not in registry.STATUSES:
        return jsonify({"error": "status inválido"}), 400
    updated = registry.upsert(pid, **fields)
    return jsonify(updated)


@app.route("/api/businesses/<pid>/regenerate_outreach", methods=["POST"])
def regenerate_outreach(pid: str):
    entry = registry.get(pid)
    if not entry:
        return jsonify({"error": "not found"}), 404
    msgs = _outreach_builder.build(
        name=entry.get("name", ""),
        address=entry.get("address", ""),
        phone=entry.get("phone"),
        rating=entry.get("rating"),
        review_count=entry.get("review_count", 0),
        sector=entry.get("sector", "default"),
    )
    updated = registry.upsert(pid, outreach=msgs)
    return jsonify(updated)


@app.route("/api/businesses/<pid>/detect_social", methods=["POST"])
def api_detect_social(pid: str):
    entry = registry.get(pid)
    if not entry:
        return jsonify({"error": "not found"}), 404
    if not social_detector.available():
        return jsonify({"error": "ddgs no disponible"}), 503
    social = social_detector.detect(entry.get("name", ""), entry.get("address", ""))
    updated = registry.upsert(pid, social=social)
    return jsonify(updated)


# ---------------------------------------------------------------------------
# Stats & CSV
# ---------------------------------------------------------------------------

@app.route("/api/stats")
def api_stats():
    return jsonify(registry.stats())


@app.route("/api/export/csv")
def export_csv():
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([
        "place_id", "name", "sector", "status", "score",
        "address", "phone", "rating", "review_count",
        "instagram", "facebook", "maps_url",
        "output_file", "processed_at", "notes",
    ])
    for e in registry.all_entries().values():
        soc = e.get("social") or {}
        writer.writerow([
            e.get("place_id",""), e.get("name",""), e.get("sector",""),
            e.get("status",""), e.get("score",0),
            e.get("address",""), e.get("phone","") or "",
            e.get("rating","") or "", e.get("review_count",0),
            soc.get("instagram","") or "", soc.get("facebook","") or "",
            e.get("maps_url",""), e.get("output_file",""),
            e.get("processed_at",""), (e.get("notes","") or "").replace("\n"," | "),
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="prospector_leads.csv"'},
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    analyzer = ReviewAnalyzer()
    n_prompts = len([f for f in OUTPUT_DIR.glob("*.txt") if not f.name.startswith("_")]) \
                if OUTPUT_DIR.exists() else 0
    return jsonify({
        "google_api_key":   bool(os.getenv("GOOGLE_PLACES_API_KEY")),
        "ollama":           analyzer.ping(),
        "ollama_host":      analyzer.host,
        "web_verifier":     web_verifier.available(),
        "social_detector":  social_detector.available(),
        "prompts_count":    n_prompts,
        "registry_count":   registry.count(),
    })


# ---------------------------------------------------------------------------
# Pipeline (compartido)
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

        skip_ollama   = bool(payload.get("skip_ollama", False))
        skip_verify   = bool(payload.get("skip_verify", False))
        skip_social   = bool(payload.get("skip_social", False))

        # 1. Dedup
        known = registry.known_ids()
        fresh = [b for b in businesses if b.place_id not in known]
        dupes = len(businesses) - len(fresh)
        if dupes:
            emit(f"⏭ {dupes} ya procesados — omitidos")
        if not fresh:
            emit("✓ Nada nuevo que procesar")
            with _lock:
                _jobs[job_id]["status"] = "done"
                _jobs[job_id]["generated"] = []
            return

        emit(f"🔎 {len(fresh)} candidatos nuevos")

        # 2. Verificación de web (secundaria)
        if not skip_verify:
            emit("🌐 Verificando webs ocultas (anti-falsos-positivos)…")
            fresh = web_verifier.filter_no_website(fresh, log_fn=emit)
            emit(f"✓ {len(fresh)} confirmados sin web")
        else:
            emit("⚡ Verificación web omitida")

        if not fresh:
            with _lock:
                _jobs[job_id]["status"] = "done"
                _jobs[job_id]["generated"] = []
            return

        # 3. IA + enriquecimiento + persistencia
        analyzer  = ReviewAnalyzer()
        builder   = PromptBuilder()
        extractor = GoogleExtractor()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if not skip_ollama and not analyzer.ping():
            raise RuntimeError(f"Ollama no responde en {analyzer.host}")

        generated: list[str] = []
        for i, biz in enumerate(fresh, 1):
            emit(f"[{i}/{len(fresh)}] {biz.name}")
            try:
                # Generar prompt
                if skip_ollama:
                    _write_skeleton(biz, builder)
                    out_name = f"{_slugify(biz.name)}.txt"
                else:
                    path = process_business(biz, extractor, analyzer, builder)
                    out_name = path.name

                # Resolver sector real
                profile = get_profile(biz.categories_all or biz.category, name=biz.name)
                sector  = profile.sector

                # Score
                score = scoring.calculate(
                    review_count=biz.review_count or 0,
                    rating=biz.rating,
                    sector=sector,
                    has_phone=bool(biz.phone),
                    has_photos=bool(biz.photo_references),
                    confirmed_no_web=not skip_verify,
                )

                # Outreach
                outreach = _outreach_builder.build(
                    name=biz.name, address=biz.address,
                    phone=biz.phone, rating=biz.rating,
                    review_count=biz.review_count or 0, sector=sector,
                )

                # Social media (opcional, lento)
                social = {"instagram": None, "facebook": None}
                if not skip_social and social_detector.available():
                    emit(f"   🔍 buscando redes sociales…")
                    social = social_detector.detect(biz.name, biz.address)
                    if social["instagram"]: emit(f"   📸 Instagram: {social['instagram']}")
                    if social["facebook"]:  emit(f"   📘 Facebook: {social['facebook']}")

                # Guardar todo en el registro
                registry.upsert(
                    biz.place_id,
                    name=biz.name, sector=sector,
                    address=biz.address, phone=biz.phone,
                    rating=biz.rating, review_count=biz.review_count or 0,
                    maps_url=biz.maps_url, output_file=out_name,
                    score=score, outreach=outreach, social=social,
                    status=registry.DEFAULT_STATUS,
                )
                generated.append(out_name)
                emit(f"   ✓ {out_name} (score {score}/10)")
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
        with _lock: _jobs[job_id]["log"] = list(log)
    try:
        query             = payload["query"].strip()
        max_results       = int(payload.get("max", 5))
        region            = payload.get("region") or None
        include_with_web  = bool(payload.get("include_with_website", False))

        emit(f"▶ Buscando: {query}")
        extractor  = GoogleExtractor()
        businesses = extractor.search_many(
            [query], region=region, max_results=max_results,
            only_without_website=not include_with_web,
        )
        emit(f"✓ {len(businesses)} candidatos en Google Places")
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
    threading.Thread(target=_run_generate, args=(job_id, payload), daemon=True).start()
    return jsonify({"job_id": job_id})


# ---------------------------------------------------------------------------
# /api/discover — búsqueda por zona
# ---------------------------------------------------------------------------

def _run_discover(job_id: str, payload: dict) -> None:
    log: list[str] = []
    def emit(msg: str) -> None:
        log.append(msg)
        with _lock: _jobs[job_id]["log"] = list(log)
    try:
        lat              = float(payload["lat"])
        lng              = float(payload["lng"])
        radius_m         = int(payload.get("radius_m", 2000))
        max_results      = int(payload.get("max", 20))
        include_with_web = bool(payload.get("include_with_website", False))

        if not _in_tenerife(lat, lng):
            raise ValueError(f"Coordenadas ({lat:.4f}, {lng:.4f}) fuera de Tenerife.")

        emit(f"▶ Explorando zona ({lat:.5f}, {lng:.5f}), radio {radius_m} m")
        extractor  = GoogleExtractor()
        known      = registry.known_ids()
        businesses = extractor.search_nearby(
            lat, lng, radius_m,
            only_without_website=not include_with_web,
            max_results=max_results, skip_ids=known,
        )
        emit(f"✓ {len(businesses)} candidatos en Google Places")
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
    threading.Thread(target=_run_discover, args=(job_id, payload), daemon=True).start()
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

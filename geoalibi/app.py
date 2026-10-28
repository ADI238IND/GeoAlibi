from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import demo, meta, pretrained
from .store import Store
from .vision import decode_image, investigate, png

load_dotenv()
ROOT = Path(__file__).parent
store = Store(Path(os.getenv("GEOALIBI_DATA_DIR", ".geoalibi")))
BUDGET = float(os.getenv("GEOALIBI_API_BUDGET_USD", "10"))
app = FastAPI(title="GeoAlibi", version="0.5.0")
lock = asyncio.Semaphore(1)


@app.middleware("http")
async def guard(request: Request, call_next):
    # Local research workstation. No public deployment without authentication.
    if request.headers.get("host", "").split(":")[0] not in {"localhost", "127.0.0.1", "testserver"}:
        return JSONResponse({"detail": "This build accepts localhost only. Add authentication before public deployment."}, status_code=403)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "Cross-origin writes are blocked."}, status_code=403)
        length = request.headers.get("content-length")
        if not length or not length.isdigit() or int(length) > 27 * 1024 * 1024:
            return JSONResponse({"detail": "Request must have a Content-Length of at most 27 MB."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
    return response


@app.get("/")
def index():
    return FileResponse(ROOT / "static/index.html")


@app.get("/api/status")
def status():
    return {"meta_configured": meta.available(), "sam_configured": meta.sam_available(), "detector_configured": pretrained.available(), "model": meta.MODEL,
            "budget": store.budget(BUDGET), "mode": "local research prototype", "demo_cases": demo.CASES}


@app.get("/api/runs")
def recent():
    return store.recent()


@app.post('/api/preview')
async def preview(image: UploadFile = File(...)):
    try:
        decoded=decode_image(await image.read(12*1024*1024+1))
        return Response(png(decoded),media_type='image/png',headers={'Cache-Control':'no-store'})
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    finally:
        await image.close()


def get_run(run_id):
    if not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise HTTPException(404, "Investigation not found")
    report = store.get(run_id)
    if report is None:
        raise HTTPException(404, "Investigation not found")
    return report


@app.get("/api/runs/{run_id}")
def get(run_id: str):
    return get_run(run_id)


@app.get("/api/runs/{run_id}/report")
def export(run_id: str):
    return JSONResponse(get_run(run_id), headers={"Content-Disposition": f'attachment; filename="geoalibi-{run_id[:8]}.json"'})


@app.get("/api/runs/{run_id}/assets/{name}.png")
def asset(run_id: str, name: str):
    report = get_run(run_id)
    if name not in report["assets"]:
        raise HTTPException(404, "Asset not found")
    return FileResponse(store.root / run_id / (name + ".png"), media_type="image/png")


@app.get('/api/runs/{run_id}/packet')
def packet(run_id: str):
    from .dossier import build_packet
    report = get_run(run_id)
    assets = {name:(store.root/run_id/(name+'.png')).read_bytes() for name in report['assets']}
    return Response(build_packet(report,assets), media_type='application/zip', headers={'Content-Disposition':f'attachment; filename="geoalibi-{run_id[:8]}-evidence.zip"'})


class Review(BaseModel):
    decision: str = Field(pattern="^(confirmed|dismissed|needs_field_check|unreviewed)$")
    note: str = Field(default="", max_length=1000)


@app.post("/api/runs/{run_id}/reviews/{region_id}")
def review(run_id: str, region_id: str, body: Review):
    report = get_run(run_id)
    if region_id not in {r["id"] for r in report["regions"]}:
        raise HTTPException(404, "Region not found")
    store.review(run_id, region_id, body.decision, body.note)
    return get_run(run_id)


class EvidenceResponse(BaseModel):
    request_index: int = Field(ge=0)
    status: str = Field(pattern="^(provided|unavailable|retracted)$")
    source: str = Field(default="", max_length=500)
    note: str = Field(min_length=1, max_length=1500)


@app.post("/api/runs/{run_id}/evidence/{region_id}")
def add_evidence(run_id: str, region_id: str, body: EvidenceResponse):
    report = get_run(run_id)
    region = next((r for r in report["regions"] if r["id"] == region_id), None)
    if region is None:
        raise HTTPException(404, "Region not found")
    if body.request_index >= len(region.get("evidence_requests", [])):
        raise HTTPException(422, "Evidence request does not exist")
    if not body.note.strip() or (body.status == "provided" and not body.source.strip()):
        raise HTTPException(422, "Provide a note and a source reference for supplied evidence")
    store.add_evidence(run_id, region_id, body.request_index, body.status, body.source.strip(), body.note.strip())
    return get_run(run_id)


async def run(a, b, title, threshold, min_area, use_meta, use_sam, synthetic=False, detector="baseline", landmarks=None):
    async with lock:
        try:
            if detector not in {"baseline", "unet"}:
                raise ValueError("Unknown proposal detector.")
            result = await asyncio.to_thread(investigate, a, b, threshold=threshold, min_area=min_area, detector_fn=pretrained.propose if detector == "unet" else None, landmarks=landmarks)
            if use_meta:
                try:
                    await meta.enrich(result, store, BUDGET, with_sam=use_sam)
                except ValueError as exc:
                    result.report["meta"] = {"status": "blocked", "reason": str(exc)}
            run_id = uuid.uuid4().hex
            result.report.update({"id": run_id, "synthetic": synthetic, "assets": {name: f"/api/runs/{run_id}/assets/{name}.png" for name in result.images}})
            folder = store.root / run_id
            folder.mkdir()
            for name, image in result.images.items():
                (folder / (name + ".png")).write_bytes(png(image))
            store.save(run_id, title, result.report)
            return get_run(run_id)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc


class DemoRequest(BaseModel):
    detector: str = Field(default="baseline", pattern="^(baseline|unet)$")
    case: str = "mixed"
    use_meta: bool = False
    use_sam: bool = False
    threshold: float = Field(default=.12, ge=.04, le=.4)
    min_area: int = Field(default=70, ge=16, le=10000)


@app.post("/api/demo")
async def demo_run(body: DemoRequest):
    if body.case not in demo.CASES:
        raise HTTPException(422, "Unknown fixture")
    a, b, _ = demo.pair(body.case)
    return await run(a, b, "Illustrative fixture · " + demo.CASES[body.case], body.threshold, body.min_area, body.use_meta, body.use_sam, synthetic=True, detector=body.detector)


@app.post("/api/analyze")
async def upload(before: UploadFile = File(...), after: UploadFile = File(...), title: str = Form("Untitled investigation"),
                 threshold: float = Form(.12, ge=.04, le=.4), min_area: int = Form(70, ge=16, le=10000),
                 use_meta: bool = Form(False), use_sam: bool = Form(False), detector: str = Form("baseline"), landmarks: str = Form("")):
    try:
        a = decode_image(await before.read(12 * 1024 * 1024 + 1))
        b = decode_image(await after.read(12 * 1024 * 1024 + 1))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await before.close()
        await after.close()
    points=None
    if landmarks.strip():
        try:
            if len(landmarks)>5000:raise ValueError('Too many landmark characters.')
            points=json.loads(landmarks)
            if points is None:raise ValueError('Landmark JSON must be an array.')
        except ValueError as exc:
            raise HTTPException(422,'Landmarks must be a JSON array of numeric coordinate rows.') from exc
    return await run(a, b, title.strip()[:120] or "Untitled investigation", threshold, min_area, use_meta, use_sam, detector=detector, landmarks=points)


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


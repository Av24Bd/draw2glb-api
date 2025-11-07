# app/main.py
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse

# --- local modules (must exist in app/)
from .parser import parse_pdf_dims
from .storage import path_for  # helper that returns Path(STORAGE_DIR) / file_id
from .models import ParseResponse                   # pydantic model for /parse response
from .mesher import build_glb_from_spec as build_glb  # returns GLB bytes from a spec dict

# -----------------------------------------------------------------------------
# App & CORS
# -----------------------------------------------------------------------------
app = FastAPI(title="draw2glb-api")

_frontend = os.getenv("FRONTEND_ORIGIN", "*").strip()
if _frontend == "*" or not _frontend:
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in _frontend.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health() -> Dict[str, bool]:
    return {"ok": True}

# -----------------------------------------------------------------------------
# Ingest: upload PDF/PNG/JPG -> file_id
# -----------------------------------------------------------------------------
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> Dict[str, str]:
    suffix = Path(file.filename).suffix.lower() or ".pdf"
    # keep extension so later checks (is pdf?) are trivial
    file_id = f"{uuid.uuid4().hex}{suffix}"
    p = path_for(file_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    p.write_bytes(data)
    return {"file_id": file_id}

# -----------------------------------------------------------------------------
# Parse: extract dims/features from drawing
# -----------------------------------------------------------------------------
@app.post("/parse", response_model=ParseResponse)
async def parse(payload: Dict[str, Any]):
    t0 = time.time()
    file_id = payload.get("file_id")
    if not file_id:
        raise HTTPException(status_code=400, detail="file_id required")

    p = path_for(file_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="file not found")

    if p.suffix.lower() == ".pdf":
        parsed = parse_pdf_dims(p.read_bytes(), hard_limit_s=20)
        print(f"[parse] took {round(time.time()-t0, 2)}s -> {parsed.get('dims')}, "
              f"conf={parsed.get('confidence')}")
        return parsed

    # fallback for images/unknown
    print(f"[parse] non-pdf fallback in {round(time.time()-t0, 2)}s")
    return {
        "dims": {"width": 250.0, "depth": 250.0, "height": 100.0},
        "features_proposed": {},
        "confidence": 0.1,
    }

# -----------------------------------------------------------------------------
# Build: build GLB from a spec dict (same contract the frontend sends)
# -----------------------------------------------------------------------------
@app.post("/build")
async def build(spec: Dict[str, Any]):
    try:
        glb_bytes: bytes = build_glb(spec)  # your mesher returns GLB bytes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"build failed: {e}")

    headers = {
        "Content-Disposition": 'attachment; filename="model.glb"',
        "Cache-Control": "no-store",
    }
    return StreamingResponse(
        content=iter([glb_bytes]),
        media_type="model/gltf-binary",
        headers=headers,
    )

# -----------------------------------------------------------------------------
# Root (optional)
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return JSONResponse({"service": "draw2glb-api", "health": "/health"})

# app/main.py
import io, os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .storage import put_file, path_for
from .models import IngestResponse, ParseResponse, ModelSpec, BBox, Features
from .parser import parse_pdf_dims
from .mesher import build_mesh_from_spec, export_glb

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app = FastAPI(title="Draw2GLB API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_ORIGIN == "*" else [FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    data = await file.read()
    suffix = ".pdf" if file.filename.lower().endswith(".pdf") else ".bin"
    fid = put_file(data, suffix)
    return {"file_id": fid, "page_count": 1}

@app.post("/parse", response_model=ParseResponse)
async def parse(payload: dict):
    file_id = payload.get("file_id")
    if not file_id:
        raise HTTPException(400, "file_id required")
    p = path_for(file_id)
    if p.suffix.lower() == ".pdf":
        parsed = parse_pdf_dims(p.read_bytes())
        return parsed
    # image or unknown -> safe fallback
    dims = BBox(width=250.0, depth=250.0, height=100.0)
    return ParseResponse(dims=dims, features_proposed=Features(), confidence=0.1)

@app.post("/build")
async def build(spec: ModelSpec):
    mesh = build_mesh_from_spec(spec)
    glb = export_glb(mesh)
    return StreamingResponse(
        io.BytesIO(glb),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=model.glb"},
    )

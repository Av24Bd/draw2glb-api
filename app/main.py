# in app/main.py, inside parse(...)
import time
@app.post("/parse", response_model=ParseResponse)
async def parse(payload: dict):
    t0 = time.time()
    file_id = payload.get("file_id")
    if not file_id:
        raise HTTPException(400, "file_id required")
    p = path_for(file_id)
    if p.suffix.lower() == ".pdf":
        parsed = parse_pdf_dims(p.read_bytes(), hard_limit_s=20)
        print(f"[parse] took {round(time.time()-t0,2)}s -> {parsed.get('dims')}, conf={parsed.get('confidence')}")
        return parsed
    # image/unknown
    print(f"[parse] non-pdf fallback in {round(time.time()-t0,2)}s")
    return {"dims": {"width": 250.0, "depth": 250.0, "height": 100.0}, "features_proposed": {}, "confidence": 0.1}

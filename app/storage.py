import os, uuid
from pathlib import Path

BASE = Path(os.getenv("STORAGE_DIR", "/tmp/draw2glb"))
BASE.mkdir(parents=True, exist_ok=True)

def put_file(data: bytes, suffix: str) -> str:
    file_id = str(uuid.uuid4())
    p = BASE / f"{file_id}{suffix}"
    with open(p, "wb") as f:
        f.write(data)
    return file_id

def path_for(file_id: str) -> Path:
    for p in BASE.glob(f"{file_id}.*"):
        return p
    raise FileNotFoundError(file_id)

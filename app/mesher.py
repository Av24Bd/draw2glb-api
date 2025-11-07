# app/mesher.py
from __future__ import annotations
from typing import Any, Dict

# We use trimesh for a simple, block-accurate GLB.
# This keeps the contract that the function returns GLB bytes.
try:
    import trimesh
except Exception as e:  # pragma: no cover
    trimesh = None


_MM_TO_M = 0.001


def _read_dims(spec: Dict[str, Any]) -> tuple[float, float, float]:
    """
    Accepts either:
      spec = {"dims": {"width": ..., "depth": ..., "height": ...}, "units": "mm"}
      or     {"width": ..., "depth": ..., "height": ...}
    Returns (w, d, h) in METERS.
    """
    dims = spec.get("dims") if isinstance(spec, dict) else None
    if dims is None:
        dims = spec  # allow flat dict

    w = float(dims["width"])
    d = float(dims["depth"])
    h = float(dims["height"])

    units = (spec.get("units") or "mm").lower() if isinstance(spec, dict) else "mm"
    scale = _MM_TO_M if units == "mm" else 1.0
    return w * scale, d * scale, h * scale


def build_glb_from_spec(spec: Dict[str, Any]) -> bytes:
    """
    Minimal mesher: creates a rectangular box matching the requested extents.
    Returns GLB bytes.
    """
    if trimesh is None:  # pragma: no cover
        raise RuntimeError("trimesh is not available in the runtime")

    w, d, h = _read_dims(spec)
    body = trimesh.creation.box(extents=[w, d, h])

    # (Optional) here you can approximate features (slope, chamfer, feet) using
    # additional primitives & CSG booleans. Keeping it simple for now.

    scene = trimesh.Scene(body)
    glb_bytes = scene.export(file_type="glb")
    return glb_bytes if isinstance(glb_bytes, bytes) else glb_bytes.read()


# Backwards-compat helper so either name can be imported.
def build_glb(spec: Dict[str, Any]) -> bytes:
    return build_glb_from_spec(spec)


__all__ = ["build_glb_from_spec", "build_glb"]

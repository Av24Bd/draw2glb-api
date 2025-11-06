import trimesh
from .models import ModelSpec

MM_TO_M = 0.001

def build_mesh_from_spec(spec: ModelSpec) -> trimesh.Trimesh:
    w = spec.bbox.width * MM_TO_M
    d = spec.bbox.depth * MM_TO_M
    h = spec.bbox.height * MM_TO_M
    mesh = trimesh.creation.box(extents=[w, d, h])
    mesh.visual.material = trimesh.visual.material.PBRMaterial(
        name="base", baseColorFactor=[0.85, 0.85, 0.88, 1.0]
    )
    return mesh

def export_glb(mesh: trimesh.Trimesh) -> bytes:
    scene = trimesh.Scene(mesh)
    glb = scene.export(file_type="glb")
    return glb if isinstance(glb, bytes) else glb.read()

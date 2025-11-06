from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Literal

class ViewRect(BaseModel):
    page: int
    x: int; y: int; w: int; h: int

class BBox(BaseModel):
    width: float
    depth: float
    height: float

class PanelSlope(BaseModel):
    axis: Literal["Y"] = "Y"
    rise: float
    run: float

class Feet(BaseModel):
    countX: int
    countY: int
    size: Tuple[float, float, float]
    pad: Tuple[float, float]
    fillet: float = 0.0

class Cutout(BaseModel):
    at: Tuple[float, float, float]
    size: Tuple[float, float, float]

class Features(BaseModel):
    frontChamfer: Optional[float] = None
    panelSlope: Optional[PanelSlope] = None
    feet: Optional[Feet] = None
    cutouts: Optional[List[Cutout]] = []
    globalFillet: Optional[float] = None

class ModelSpec(BaseModel):
    units: Literal["mm"] = "mm"
    bbox: BBox
    features: Features = Features()

class IngestResponse(BaseModel):
    file_id: str
    page_count: int

class ParseResponse(BaseModel):
    dims: BBox
    features_proposed: Features = Features()
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

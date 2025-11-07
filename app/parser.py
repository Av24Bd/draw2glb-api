# app/parser.py
from typing import List, Tuple
import re, time
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import pytesseract

NUM_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+")

def _find_nums(text: str) -> List[float]:
    nums = [float(m.group()) for m in NUM_RE.finditer(text or "")]
    # plausible mm values
    return [n for n in nums if 5 <= n <= 3000]

def _pick_dims(nums: List[float]) -> Tuple[float, float, float, float]:
    if not nums:
        return 250.0, 250.0, 100.0, 0.0
    rounded = [round(n, 1) for n in nums]
    vals, counts = np.unique(rounded, return_counts=True)
    order = np.argsort(-counts)
    top = [float(vals[i]) for i in order[:3]]
    while len(top) < 3:
        top.append(top[-1] if top else 100.0)
    top.sort()
    h, w, d = top[0], top[1], top[2]
    conf = min(1.0, float(sum(counts[order[:3]]) / max(1, len(nums))))
    return w, d, h, round(conf, 2)

def _rasterize_first_page(pdf_bytes: bytes, dpi: int = 150) -> Image.Image:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def parse_pdf_dims(pdf_bytes: bytes, hard_limit_s: int = 20):
    """Always return within hard_limit_s seconds."""
    t0 = time.time()
    try:
        # 1) FAST PATH: vector text extraction (usually < 1s)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        txt = doc.load_page(0).get_text("text")
        nums = _find_nums(txt)
        if len(nums) < 3:
            # Try raw blocks too
            nums += _find_nums(doc.load_page(0).get_text("rawtext"))
        if len(nums) >= 3:
            w, d, h, conf = _pick_dims(nums)
            chamfer = 4.25 if any(abs(n - 4.25) < 0.2 for n in nums) else None
            return {
                "dims": {"width": w, "depth": d, "height": h},
                "features_proposed": {"frontChamfer": chamfer, "panelSlope": None,
                                      "feet": None, "cutouts": [], "globalFillet": None},
                "confidence": conf
            }

        # 2) FALLBACK: quick OCR with timeout (keep under hard_limit_s)
        if time.time() - t0 < hard_limit_s - 5:
            img = _rasterize_first_page(pdf_bytes, dpi=150)
            try:
                text = pytesseract.image_to_string(
                    img, timeout=12,
                    config="--psm 6 -c tessedit_char_whitelist=0123456789.-"
                )
                nums = _find_nums(text)
                w, d, h, conf = _pick_dims(nums)
                chamfer = 4.25 if any(abs(n - 4.25) < 0.2 for n in nums) else None
                return {
                    "dims": {"width": w, "depth": d, "height": h},
                    "features_proposed": {"frontChamfer": chamfer, "panelSlope": None,
                                          "feet": None, "cutouts": [], "globalFillet": None},
                    "confidence": conf

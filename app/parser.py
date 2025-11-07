# app/parser.py  — fast, safe parser (no OCR/NumPy)
from typing import List, Tuple
import re
from collections import Counter
import fitz  # PyMuPDF

NUM_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+")

def _find_nums(text: str) -> List[float]:
    nums = [float(m.group()) for m in NUM_RE.finditer(text or "")]
    return [n for n in nums if 5 <= n <= 3000]  # plausible mm

def _pick_dims(nums: List[float]) -> Tuple[float, float, float, float]:
    if not nums:
        return 250.0, 250.0, 100.0, 0.0
    rounded = [round(n, 1) for n in nums]
    counts = Counter(rounded)
    top = [n for n, _ in counts.most_common(3)]
    while len(top) < 3:
        top.append(top[-1] if top else 100.0)
    top.sort()
    h, w, d = top[0], top[1], top[2]
    conf = min(1.0, sum(counts[n] for n in top) / max(1, len(rounded)))
    return w, d, h, round(conf, 2)

def parse_pdf_dims(pdf_bytes: bytes, hard_limit_s: int = 20):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        text = (page.get_text("text") or "") + "\n" + (page.get_text("rawtext") or "")
        nums = _find_nums(text)
        if len(nums) >= 3:
            w, d, h, conf = _pick_dims(nums)
            chamfer = 4.25 if any(abs(n - 4.25) < 0.2 for n in nums) else None
            return {
                "dims": {"width": w, "depth": d, "height": h},
                "features_proposed": {"frontChamfer": chamfer, "panelSlope": None,
                                      "feet": None, "cutouts": [], "globalFillet": None},
                "confidence": conf
            }
    except Exception:
        pass
    return {
        "dims": {"width": 250.0, "depth": 250.0, "height": 100.0},
        "features_proposed": {},
        "confidence": 0.1
    }

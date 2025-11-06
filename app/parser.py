from typing import List
import re, numpy as np
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
from .models import ParseResponse, BBox, Features

NUM_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+")

def rasterize_first_page(pdf_bytes: bytes, dpi: int = 300) -> Image.Image:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def ocr_numbers(img: Image.Image) -> List[float]:
    gray = img.convert("L")
    text = pytesseract.image_to_string(
        gray, config="--psm 6 -c tessedit_char_whitelist=0123456789.-"
    )
    nums = [float(m.group()) for m in NUM_RE.finditer(text)]
    return [n for n in nums if 5 <= n <= 3000]

def parse_pdf_dims(pdf_bytes: bytes) -> ParseResponse:
    img = rasterize_first_page(pdf_bytes)
    nums = ocr_numbers(img)
    if not nums:
        return ParseResponse(dims=BBox(width=250, depth=250, height=100),
                             features_proposed=Features(), confidence=0.1)
    rounded = [round(n, 1) for n in nums]
    vals, counts = np.unique(rounded, return_counts=True)
    order = np.argsort(-counts)
    top = [float(vals[i]) for i in order[:3]]
    while len(top) < 3: top.append(top[-1] if top else 100.0)
    top.sort()
    h = top[0]; w = top[1]; d = top[2]
    conf = min(1.0, float(sum(counts[order[:3]]) / max(1, len(nums))))
    features = Features(frontChamfer=4.25 if any(abs(n-4.25) < 0.2 for n in nums) else None)
    return ParseResponse(dims=BBox(width=w, depth=d, height=h),
                         features_proposed=features, confidence=round(conf, 2))

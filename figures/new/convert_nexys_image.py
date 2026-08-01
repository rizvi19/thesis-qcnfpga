"""Deterministically convert the retained HEIC board photograph for LaTeX inclusion.

The conversion preserves the full frame and native pixel dimensions; it performs no
crop, recoloring, resampling, or enhancement.
"""

from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "figures" / "nexys_img.HEIC"
OUTPUT = ROOT / "figures" / "new" / "nexys_img.jpg"

register_heif_opener()
with Image.open(SOURCE) as image:
    image.convert("RGB").save(OUTPUT, format="JPEG", quality=96, subsampling=0)

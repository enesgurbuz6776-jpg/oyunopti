"""Render the official website's SVG logo into a multi-resolution Windows ICO."""
from pathlib import Path
import io
from PIL import Image
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "icon.svg"
OUTPUT = ROOT / "desktop" / "assets" / "oyunopti.ico"

if not SVG.is_file():
    raise SystemExit(f"Site logo not found: {SVG}")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

png = cairosvg.svg2png(url=str(SVG), output_width=512, output_height=512)
image = Image.open(io.BytesIO(png)).convert("RGBA")
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
image.save(OUTPUT, format="ICO", sizes=sizes)

with Image.open(OUTPUT) as check:
    assert check.format == "ICO", "Invalid Windows icon"
    assert (256, 256) in check.info["sizes"], "256x256 icon missing"
print(f"Generated {OUTPUT} ({OUTPUT.stat().st_size} bytes)")

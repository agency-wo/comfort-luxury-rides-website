"""Brand assets from the client's round badge logo (500x500 RGBA PNG with a ragged cut-out).

Crops to the alpha bounding box, cleans the semi-transparent fringe, and exports:
  assets/img/brand/logo-badge-88.png / -176.png / -352.png   (header at 44 px, 2x, 4x)
  assets/img/brand/logo-badge.webp                           (alpha WebP, 176 px, for the header)
  favicon-32.png, favicon-48.png, icon-192.png, apple-touch-icon.png (180, flattened)
  favicon.ico (16+32+48)
usage: python _tools/prep_brand.py
"""
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_source" / "originals" / "COMFORT_LUXURY_RIDES_LOGO-removebg.png"
BRAND = ROOT / "assets" / "img" / "brand"
BRAND.mkdir(parents=True, exist_ok=True)
BG = (11, 11, 13)  # #0B0B0D

im = Image.open(SRC).convert("RGBA")
a = im.getchannel("A")
# the cut-out left faint fringe pixels: threshold the alpha, then soften the edge by a hair
a = a.point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.GaussianBlur(0.6))
im.putalpha(a)
bbox = a.getbbox()
im = im.crop(bbox)
s = max(im.size)
sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
sq.paste(im, ((s - im.width) // 2, (s - im.height) // 2), im)


def save_png(size, path, flatten=False, quant=True):
    """PNG out. The gold gradient compresses badly as truecolour, so served PNGs are
    quantised to 256 colours (alpha preserved); quant=False keeps the truecolour master."""
    r = sq.resize((size, size), Image.LANCZOS)
    if flatten:
        base = Image.new("RGB", (size, size), BG)
        base.paste(r, (0, 0), r)
        r = base
    if quant:
        r = r.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
    r.save(path, optimize=True)


save_png(88, BRAND / "logo-badge-88.png")
save_png(176, BRAND / "logo-badge-176.png")
save_png(352, BRAND / "logo-badge-352.png", quant=False)   # master for make_og.py only, not served
sq.resize((176, 176), Image.LANCZOS).save(BRAND / "logo-badge.webp", quality=82, method=6)
save_png(32, ROOT / "favicon-32.png")
save_png(48, ROOT / "favicon-48.png")
save_png(192, ROOT / "icon-192.png")
save_png(180, ROOT / "apple-touch-icon.png", flatten=True)
# ICO: save from the 48 px master and let Pillow derive the smaller frames
sq.resize((48, 48), Image.LANCZOS).save(ROOT / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

print("badge bbox", bbox, "->", sq.size)
for p in sorted(BRAND.glob("*")) + sorted(ROOT.glob("favicon*")) + [ROOT / "apple-touch-icon.png", ROOT / "icon-192.png"]:
    print(f"{p.relative_to(ROOT)}  {p.stat().st_size} B")

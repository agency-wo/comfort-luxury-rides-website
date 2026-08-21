"""Open Graph image (1200x630): near-black panel with badge and wordmark, Denali photo on the right.

Adapted from flysystem.io/tools/make_og.py. Pillow cannot read woff2, so the variable fonts
shipped with the site are decompressed to TTF inside _tools/ (ignored by git) on first run.
usage: python _tools/make_og.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "og" / "og-default.jpg"
OUT.parent.mkdir(parents=True, exist_ok=True)
HERO = ROOT / "_source" / "originals" / "Luxury-Taxi-ARIZONA.png"
BADGE = ROOT / "assets" / "img" / "brand" / "logo-badge-352.png"
BG, GOLD, TEXT, MUTED = (11, 11, 13), (201, 161, 90), (237, 232, 223), (181, 176, 166)


def ttf(woff2: Path, out: Path) -> Path:
    if not out.exists():
        f = TTFont(woff2)
        f.flavor = None
        f.save(out)
    return out


serif = ttf(ROOT / "assets/fonts/cormorant-var.woff2", ROOT / "_tools/cormorant-var.ttf")
sans = ttf(ROOT / "assets/fonts/inter-var.woff2", ROOT / "_tools/inter-var.ttf")


def font(path, size, wght):
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


W, H, PANEL = 1200, 630, 560
canvas = Image.new("RGB", (W, H), BG)

# photo on the right, cover-cropped, fading into the panel on its left edge
hero = Image.open(HERO).convert("RGBA")
flat = Image.new("RGBA", hero.size, BG + (255,))
flat.paste(hero, (0, 0), hero)
hero = flat.convert("RGB")
tw, th = W - PANEL, H
scale = max(tw / hero.width, th / hero.height)
hero = hero.resize((round(hero.width * scale), round(hero.height * scale)), Image.LANCZOS)
hx = (hero.width - tw) // 2
hy = (hero.height - th) // 2
crop = hero.crop((hx, hy, hx + tw, hy + th))
fade = Image.linear_gradient("L").rotate(90, expand=True).resize((tw, th))
fade = fade.point(lambda v: min(255, int(v * 1.6)))  # mostly opaque, dark only at the seam
canvas.paste(crop, (PANEL, 0), fade)

d = ImageDraw.Draw(canvas)
badge = Image.open(BADGE).convert("RGBA").resize((132, 132), Image.LANCZOS)
canvas.paste(badge, (72, 110), badge)
f1 = font(serif, 70, 600)
f2 = font(sans, 21, 600)
f3 = font(sans, 17, 500)
d.text((70, 272), "Comfort", font=f1, fill=TEXT)
d.text((70, 342), "Luxury Rides", font=f1, fill=TEXT)
d.line([72, 444, 332, 444], fill=GOLD, width=2)
d.text((72, 466), "BLACK CAR SERVICE  ·  SCOTTSDALE, AZ", font=f2, fill=GOLD)
d.text((72, 506), "Airport transfers, corporate, events, hourly. Available 24/7.", font=f3, fill=MUTED)
canvas.save(OUT, quality=86, optimize=True, progressive=True)
print(OUT.relative_to(ROOT), OUT.stat().st_size // 1024, "KB")

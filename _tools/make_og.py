"""Open Graph share images (1200x630), one per page: near-black panel with badge, a page headline
in the real brand font, and that page's hero photo on the right.

Adapted from flysystem.io/tools/make_og.py. Pillow cannot read woff2, so the variable fonts
shipped with the site are decompressed to TTF inside _tools/ (ignored by git) on first run.
usage: python _tools/make_og.py            writes assets/img/og/og-<slug>.jpg for every page + og-default.jpg
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "assets" / "img" / "og"
OUTDIR.mkdir(parents=True, exist_ok=True)
SRC = ROOT / "_source" / "originals"
BADGE = ROOT / "assets" / "img" / "brand" / "logo-badge-352.png"
BG, GOLD, TEXT, MUTED = (11, 11, 13), (201, 161, 90), (237, 232, 223), (181, 176, 166)

# slug, source photo (in _source/originals), focal point y (0..1, where to centre the cover crop),
# headline lines, kicker (gold caps), sub (muted)
PAGES = [
    ("default",   "Luxury-Taxi-ARIZONA.png",                          0.45, ["Comfort", "Luxury Rides"],            "BLACK CAR SERVICE  ·  SCOTTSDALE, AZ", "Airport transfers, corporate, events, hourly. Available 24/7."),
    ("home",      "Luxury-Taxi-ARIZONA.png",                          0.45, ["Black car service", "in Scottsdale"],  "COMFORT LUXURY RIDES  ·  24/7",          "Chauffeured GMC Yukon XL Denali SUVs, Scottsdale and Phoenix."),
    ("airport",   "Luxury-Taxi-Service-in-Scottsdale-Arizona-5.jpeg", 0.40, ["Airport car service", "PHX · SDL · AZA"], "COMFORT LUXURY RIDES  ·  SCOTTSDALE", "Timed to your flight. Flat rate, fixed before you book."),
    ("corporate", "8.png",                                            0.50, ["Corporate", "car service"],            "COMFORT LUXURY RIDES  ·  SCOTTSDALE", "Executive transfers and meeting days, confirmed in one reply."),
    ("events",    "Luxury-Taxi-Service-ARIZONA.png",                  0.55, ["Event", "transportation"],             "COMFORT LUXURY RIDES  ·  SCOTTSDALE", "Games, the Open, weddings, nights out. Up to six guests."),
    ("hourly",    "Taxi-Service-ARIZONA.png",                         0.60, ["Private driver", "by the hour"],       "COMFORT LUXURY RIDES  ·  SCOTTSDALE", "The car and chauffeur stay with you, one hourly rate."),
    ("fleet",     "Luxury-Taxi-ARIZONA.png",                          0.60, ["GMC Yukon", "XL Denali"],              "THE FLEET  ·  COMFORT LUXURY RIDES",  "Black full-size SUVs, up to six passengers with luggage."),
    ("about",     "Administrator-of-Company.jpeg",                    0.25, ["Family-owned", "since 2020"],          "ABOUT  ·  COMFORT LUXURY RIDES",      "Scottsdale chauffeur service run by Ergi Janku."),
    ("contact",   "Luxury-Taxi-Service-ARIZONA.png",                  0.55, ["Get a quote"],                         "COMFORT LUXURY RIDES  ·  24/7",       "Call or WhatsApp (586) 222-4809. Flat price, usually within the hour."),
]


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


def compose(slug, photo, focal_y, lines, kicker, sub):
    W, H, PANEL = 1200, 630, 560
    canvas = Image.new("RGB", (W, H), BG)
    hero = Image.open(SRC / photo).convert("RGBA")
    flat = Image.new("RGBA", hero.size, BG + (255,))
    flat.paste(hero, (0, 0), hero)
    hero = flat.convert("RGB")
    tw, th = W - PANEL, H
    scale = max(tw / hero.width, th / hero.height)
    hero = hero.resize((round(hero.width * scale), round(hero.height * scale)), Image.LANCZOS)
    hx = (hero.width - tw) // 2
    hy = int(max(0, min(hero.height - th, hero.height * focal_y - th / 2)))
    crop = hero.crop((hx, hy, hx + tw, hy + th))
    fade = Image.linear_gradient("L").rotate(90, expand=True).resize((tw, th))
    fade = fade.point(lambda v: min(255, int(v * 1.6)))
    canvas.paste(crop, (PANEL, 0), fade)

    d = ImageDraw.Draw(canvas)
    badge = Image.open(BADGE).convert("RGBA").resize((120, 120), Image.LANCZOS)
    canvas.paste(badge, (72, 96), badge)
    size = 70 if max(len(l) for l in lines) <= 18 else 58
    f1 = font(serif, size, 600)
    f2 = font(sans, 20, 600)
    f3 = font(sans, 17, 500)
    y = 250 if len(lines) > 1 else 290
    for line in lines:
        d.text((70, y), line, font=f1, fill=TEXT)
        y += size + 2
    y += 18
    d.line([72, y, 332, y], fill=GOLD, width=2)
    y += 22
    d.text((72, y), kicker, font=f2, fill=GOLD)
    y += 40
    d.text((72, y), sub, font=f3, fill=MUTED)
    out = OUTDIR / f"og-{slug}.jpg"
    canvas.save(out, quality=86, optimize=True, progressive=True)
    print(out.relative_to(ROOT), out.stat().st_size // 1024, "KB")


for row in PAGES:
    compose(*row)

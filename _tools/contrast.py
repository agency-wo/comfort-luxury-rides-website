"""WCAG contrast check for the design tokens actually used as text/background pairs.
Fails (exit 1) if any pair is below its required ratio (4.5 text, 3.0 large text / UI).
usage: python _tools/contrast.py
"""
import sys

TOK = {
    "bg": "#0B0B0D", "surface": "#16161A", "surface-2": "#1E1E24",
    "gold": "#C9A15A", "gold-deep": "#B8923F", "gold-text-l": "#7D5F1D", "gold-line-l": "#9A7A38",
    "text": "#EDE8DF", "text-muted": "#B5B0A6", "paper": "#F4F0E8", "paper-2": "#ECE6DA",
    "ink": "#15151A", "ink-muted": "#5B5850", "sunset": "#D96C3D", "wa": "#25D366", "wa-text": "#062A12",
    "white": "#FFFFFF", "focus": "#E8C57A", "err": "#9A2A1D", "line-paper": "#D9D2C3",
}


def lum(hexc):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(TOK[a]), lum(TOK[b])
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# (foreground, background, minimum, where)
PAIRS = [
    ("text", "bg", 4.5, "body on dark"), ("text-muted", "bg", 4.5, "muted on dark"),
    ("gold", "bg", 4.5, "gold text/eyebrow on dark"), ("gold", "surface", 4.5, "gold on surface"),
    ("gold", "surface-2", 4.5, "gold on surface-2"), ("bg", "gold", 4.5, "button text on gold"),
    ("bg", "gold-deep", 4.5, "button text on gold hover"), ("text", "surface", 4.5, "body on surface"),
    ("text-muted", "surface", 4.5, "muted on surface"), ("ink", "paper", 4.5, "body on paper"),
    ("ink-muted", "paper", 4.5, "muted on paper"), ("ink", "paper-2", 4.5, "body on paper-2"),
    ("ink-muted", "paper-2", 4.5, "muted on paper-2"), ("gold-text-l", "paper", 4.5, "gold text on paper"),
    ("gold-text-l", "paper-2", 4.5, "gold text on paper-2"), ("gold-text-l", "white", 4.5, "gold text on white"),
    ("gold-line-l", "paper", 3.0, "gold hairline on paper"), ("sunset", "bg", 4.5, "sunset accent on dark"),
    ("wa-text", "wa", 4.5, "WhatsApp button text"), ("err", "paper", 4.5, "form error on paper"),
    ("err", "white", 4.5, "form error on white"), ("ink", "white", 4.5, "input text"),
    ("ink-muted", "white", 4.5, "input placeholder-ish on white"), ("focus", "bg", 3.0, "focus ring on dark"),
    ("gold-text-l", "paper", 3.0, "focus ring on paper"), ("paper", "ink", 4.5, "btn--ink hover text"),
    ("white", "bg", 4.5, "headings on dark"), ("white", "surface", 4.5, "headings on surface"),
]

bad = 0
for fg, bg, need, where in PAIRS:
    r = ratio(fg, bg)
    ok = r >= need
    bad += 0 if ok else 1
    print(f"{'ok ' if ok else 'BAD'} {r:5.2f}:1  (need {need})  {fg} on {bg}  {where}")
print("CONTRAST PASS" if not bad else f"CONTRAST FAIL: {bad} pair(s)")
sys.exit(1 if bad else 0)

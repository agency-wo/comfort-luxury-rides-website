"""Generate llms-full.txt: the visible text of every indexable page, in sitemap order, so an AI
crawler can read the whole site in one fetch. Derived from the pages themselves (no separate copy
to drift). Follows the MINA RANK llms-full pattern.
usage: python _tools/gen_llms_full.py
"""
import re, html
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "https://comfortluxuryrides.com"
ORDER = ["", "airport-car-service/", "corporate-transportation/", "event-transportation/",
         "hourly-chauffeur-service/", "fleet/", "about/", "contact/", "privacy/"]
BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "summary", "figcaption", "td", "th", "address", "blockquote", "dt", "dd"}
SKIP = {"script", "style", "svg", "header", "footer", "nav", "form", "button"}
VOID = {"img", "input", "br", "hr", "meta", "link", "source", "use", "path", "circle", "rect", "wbr", "col", "area", "base", "embed", "param", "track"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip_stack, self.cur, self.in_main = [], [], [], False
        self.title = ""; self._t = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title": self._t = True
        if tag == "main": self.in_main = True
        if tag not in VOID and (tag in SKIP or a.get("aria-hidden") == "true" or "call-bar" in (a.get("class") or "") or "lightbox" in (a.get("class") or "")):
            self.skip_stack.append(tag)
        if tag in BLOCK and not self.skip_stack and self.in_main:
            self.flush()
            if tag in ("h2", "h3"): self.cur.append(("#" * (int(tag[1]))) + " ")
    def handle_endtag(self, tag):
        if tag == "title": self._t = False
        if tag == "main": self.in_main = False
        if self.skip_stack and self.skip_stack[-1] == tag: self.skip_stack.pop()
        if tag in BLOCK and not self.skip_stack and self.in_main: self.flush()
    def handle_data(self, data):
        if self._t: self.title += data
        if not self.skip_stack and self.in_main: self.cur.append(data)
    def flush(self):
        t = " ".join("".join(self.cur).split())
        if t: self.out.append(t)
        self.cur = []


parts = ["# Comfort Luxury Rides", "",
         "The full visible text of every page on https://comfortluxuryrides.com/, in the order llms.txt lists them,",
         "generated from the pages themselves by _tools/gen_llms_full.py. Chauffeured luxury SUV (black car) service,",
         "Scottsdale and the Phoenix metro, Arizona. Phone +1 (586) 222-4809 (also WhatsApp). Email comfortluxuryrides@gmail.com.",
         "11545 N Frank Lloyd Wright Blvd, Scottsdale, AZ 85259. Open 24 hours a day, 7 days a week.", ""]
for rel in ORDER:
    p = ROOT / rel / "index.html"
    src = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S)
    t = Text(); t.feed(src); t.flush()
    title = " ".join(html.unescape(t.title).split())
    parts += [f"## {title}", f"{HOST}/{rel}", ""]
    seen = set()
    for line in t.out:
        if line in seen: continue
        seen.add(line); parts.append(line)
    parts.append("")
(ROOT / "llms-full.txt").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8", newline="\n")
print("llms-full.txt", (ROOT / "llms-full.txt").stat().st_size // 1024, "KB,", len(parts), "lines")

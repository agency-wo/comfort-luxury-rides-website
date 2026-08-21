"""Site gate for comfortluxuryrides.com. Read-only. Exit 1 on any finding; warnings are listed but do not fail.

usage: python _tools/verify.py [--strict]     (--strict turns data-confirm and placeholder warnings into failures)

Modelled on MINA RANK/.build/verify.py (52 checks) but purpose-built for this nine-page site.
Every check is numbered and named so a failure can be found in this file by its number.
"""
import json, os, re, sys, html
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "https://comfortluxuryrides.com"
STRICT = "--strict" in sys.argv
PHONE_DISPLAY = "(586) 222-4809"
PHONE_TEL = "tel:+15862224809"
WA_URL = "https://wa.me/15862224809?text=Hi%2C%20I%27d%20like%20a%20quote%20for%20a%20ride%20in%20Scottsdale."
ADDRESS_1 = "11545 N Frank Lloyd Wright Blvd"
ADDRESS_2 = "Scottsdale, AZ 85259"
EMAIL = "comfortluxuryrides@gmail.com"
FORM_ACTION = "https://api.web3forms.com/submit"
KEY_PLACEHOLDER = "WEB3FORMS_ACCESS_KEY_PLACEHOLDER"

findings, warnings = [], []
def fail(page, msg): findings.append(f"{page}: {msg}")
def warn(page, msg): warnings.append(f"{page}: {msg}")

SKIP_DIRS = {"_tools", "_source", "node_modules", ".git"}
pages = sorted(p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS))

def url_of(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html": return "/"
    if rel == "404.html": return "/404.html"
    return "/" + rel[:-len("index.html")] if rel.endswith("/index.html") else "/" + rel


class Collector(HTMLParser):
    """Flat list of (tag, attrs, text-so-far index) plus text runs, ids, and FAQ pairs."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.text_parts, self.ids = [], [], set()
        self.stack, self.faq, self._faq_cur = [], [], None
        self.in_main, self.in_ld, self.ld = False, False, []
        self.h1, self._h1_buf = [], None
        self.summaries, self._sum_buf = [], None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a, self.in_main))
        self.stack.append(tag)
        if a.get("id"): self.ids.add(a["id"])
        if tag == "main": self.in_main = True
        if tag == "script" and a.get("type") == "application/ld+json": self.in_ld = True
        if tag == "h1": self._h1_buf = []
        if tag == "details" and "faq-item" in (a.get("class") or ""):
            self._faq_cur = {"q": [], "a": [], "in_summary": False}
        if tag == "summary" and self._faq_cur is not None: self._faq_cur["in_summary"] = True
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        if tag == "main": self.in_main = False
        if tag == "script": self.in_ld = False
        if tag == "h1" and self._h1_buf is not None:
            self.h1.append(" ".join("".join(self._h1_buf).split())); self._h1_buf = None
        if tag == "summary" and self._faq_cur is not None: self._faq_cur["in_summary"] = False
        if tag == "details" and self._faq_cur is not None:
            self.faq.append((" ".join("".join(self._faq_cur["q"]).split()), " ".join("".join(self._faq_cur["a"]).split())))
            self._faq_cur = None
        if self.stack and self.stack[-1] == tag: self.stack.pop()
    def handle_data(self, data):
        if self.in_ld: self.ld.append(data); return
        if self._h1_buf is not None: self._h1_buf.append(data)
        if self._faq_cur is not None:
            (self._faq_cur["q"] if self._faq_cur["in_summary"] else self._faq_cur["a"]).append(data)
        if self.stack and self.stack[-1] not in ("script", "style"): self.text_parts.append(data)


def strip_comments(s): return re.sub(r"<!--.*?-->", "", s, flags=re.S)
def rel_file(href: str):
    """Map a site-absolute href/src to a file on disk (None if external or anchor-only)."""
    if not href or href.startswith(("http:", "https:", "mailto:", "tel:", "data:", "#", "//")): return None
    path = href.split("#")[0].split("?")[0]
    if not path: return None
    if not path.startswith("/"): return "REL:" + path
    p = ROOT / path.lstrip("/")
    if path.endswith("/"): p = p / "index.html"
    return p

titles, descs, chrome_top, chrome_bottom = {}, {}, {}, {}
sitemap_urls = set(re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))) if (ROOT / "sitemap.xml").exists() else set()
page_urls = set()

for p in pages:
    rel = p.relative_to(ROOT).as_posix()
    raw = p.read_text(encoding="utf-8")
    src = strip_comments(raw)
    url = url_of(p)
    is404 = rel == "404.html"
    if not is404: page_urls.add(HOST + url)
    c = Collector(); c.feed(src)
    text = " ".join(" ".join(c.text_parts).split())
    head_lower = raw[:4000].lower()

    # 1. one h1
    if len(c.h1) != 1: fail(rel, f"check 1: expected one <h1>, found {len(c.h1)}")

    # 2/3. title and description
    m = re.search(r"<title>(.*?)</title>", src, re.S); title = html.unescape(m.group(1).strip()) if m else ""
    if not (20 <= len(title) <= 60): fail(rel, f"check 2: title length {len(title)} (want 20-60): {title!r}")
    if title in titles: fail(rel, f"check 2: duplicate title also on {titles[title]}")
    titles[title] = rel
    md = re.search(r'<meta name="description" content="(.*?)"', src); desc = html.unescape(md.group(1)) if md else ""
    if not is404:
        if not (70 <= len(desc) <= 155): fail(rel, f"check 3: description length {len(desc)} (want 70-155)")
        if desc in descs: fail(rel, f"check 3: duplicate description also on {descs[desc]}")
        descs[desc] = rel
    else:
        if 'name="robots" content="noindex"' not in src: fail(rel, "check 3: 404 page must carry noindex")

    # 4. canonical
    mc = re.search(r'<link rel="canonical" href="(.*?)"', src)
    if not is404:
        if not mc: fail(rel, "check 4: canonical missing")
        elif mc.group(1) != HOST + url: fail(rel, f"check 4: canonical {mc.group(1)} != {HOST + url}")

    # 5. Open Graph
    if not is404:
        og = dict(re.findall(r'<meta property="(og:[a-z:_]+)" content="(.*?)"', src))
        for k in ("og:type", "og:site_name", "og:locale", "og:title", "og:description", "og:url", "og:image", "og:image:width", "og:image:height", "og:image:alt"):
            if k not in og: fail(rel, f"check 5: missing {k}")
        if og.get("og:url") and og["og:url"] != HOST + url: fail(rel, "check 5: og:url differs from canonical")
        if og.get("og:title") and html.unescape(og["og:title"]) != title: fail(rel, "check 5: og:title differs from <title>")
        if og.get("og:image"):
            f = rel_file(og["og:image"].replace(HOST, ""))
            if not (isinstance(f, Path) and f.exists()): fail(rel, f"check 5: og:image file missing {og['og:image']}")
        if 'name="twitter:card"' not in src: fail(rel, "check 5: twitter:card missing")

    # 6. JSON-LD
    blocks = []
    for chunk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try: blocks.append(json.loads(chunk))
        except Exception as e: fail(rel, f"check 6: JSON-LD does not parse: {e}")
    nodes = []
    for b in blocks: nodes.extend(b.get("@graph", [b]) if isinstance(b, dict) else [])
    types = {}
    for n in nodes:
        t = n.get("@type"); t = t if isinstance(t, list) else [t]
        for tt in t: types.setdefault(tt, []).append(n)
    if not is404:
        if "LocalBusiness" not in types: fail(rel, "check 6: no LocalBusiness node")
        else:
            lb = types["LocalBusiness"][0]
            need = ["name", "url", "telephone", "address"] + (["image", "openingHoursSpecification", "sameAs", "areaServed", "email"] if rel == "index.html" else [])
            for k in need:
                if k not in lb: fail(rel, f"check 6: LocalBusiness missing {k}")
            if lb.get("telephone") != "+15862224809": fail(rel, "check 6: LocalBusiness telephone is not the E.164 number")
            if lb.get("@id") != HOST + "/#business": fail(rel, "check 6: LocalBusiness @id must be /#business on every page")
        if rel != "index.html" and "BreadcrumbList" not in types: fail(rel, "check 6: BreadcrumbList missing on a sub-page")
        for svc in types.get("Service", []):
            if svc.get("provider", {}).get("@id") != HOST + "/#business": fail(rel, "check 6: Service.provider must reference /#business")
        for faq in types.get("FAQPage", []):
            ld_pairs = [(" ".join(q.get("name", "").split()), " ".join(q.get("acceptedAnswer", {}).get("text", "").split())) for q in faq.get("mainEntity", [])]
            if ld_pairs != c.faq:
                fail(rel, f"check 6: FAQPage JSON-LD ({len(ld_pairs)} Q) does not match the visible <details> FAQ ({len(c.faq)} Q)")
                for i, (a, b) in enumerate(zip(ld_pairs, c.faq)):
                    if a != b: fail(rel, f"check 6: FAQ item {i+1} differs: ld={a[0][:40]!r}/{a[1][:40]!r} vs page={b[0][:40]!r}/{b[1][:40]!r}")
        if c.faq and "FAQPage" not in types: fail(rel, "check 6: visible FAQ without FAQPage JSON-LD")

    # 7. images
    for tag, a, in_main in c.tags:
        if tag != "img": continue
        s = a.get("src", "")
        if "alt" not in a: fail(rel, f"check 7: <img> without alt: {s}")
        if not a.get("width") or not a.get("height"): fail(rel, f"check 7: <img> without width/height: {s}")
        if "decoding" not in a: fail(rel, f"check 7: <img> without decoding: {s}")
        if s.startswith("data:"): continue
        if in_main and a.get("fetchpriority") != "high" and a.get("loading") != "lazy":
            fail(rel, f"check 7: below-fold <img> without loading=lazy: {s}")
        if a.get("fetchpriority") == "high" and a.get("loading") == "lazy": fail(rel, f"check 7: hero image is lazy: {s}")

    # 8/17. links and assets resolve
    for tag, a, _ in c.tags:
        cands = []
        if tag == "a": cands.append(a.get("href"))
        if tag in ("link",): cands.append(a.get("href"))
        if tag in ("script", "img", "source", "iframe"):
            cands.append(a.get("src"))
            for ss in (a.get("srcset"), a.get("imagesrcset")):
                if ss: cands += [x.strip().split(" ")[0] for x in ss.split(",")]
        if tag == "link" and a.get("imagesrcset"): cands += [x.strip().split(" ")[0] for x in a["imagesrcset"].split(",")]
        if tag == "form": cands.append(a.get("action"))
        for h in cands:
            if not h: continue
            if h.startswith("#"):
                if h != "#" and h[1:] not in c.ids: fail(rel, f"check 8: anchor {h} has no target id")
                continue
            f = rel_file(h)
            if f is None: continue
            if isinstance(f, str): fail(rel, f"check 8: relative path used, make it site-absolute: {h}"); continue
            if not f.exists(): fail(rel, f"check 8: broken link or asset: {h}")
            frag = h.split("#")[1] if "#" in h else None
            if frag and f.suffix == ".html":
                if f'id="{frag}"' not in f.read_text(encoding="utf-8"): fail(rel, f"check 8: fragment #{frag} not found in {f.relative_to(ROOT)}")

    # 9. zero third parties on load
    for tag, a, _ in c.tags:
        if tag == "link" and (a.get("rel") or "") in ("canonical", "alternate"): continue
        for attr in ("src", "href", "srcset", "imagesrcset"):
            v = a.get(attr)
            if not v: continue
            if tag in ("script", "img", "source", "iframe", "link", "video", "audio") and re.search(r"https?://|^//", v):
                fail(rel, f"check 9: external {tag} {attr}: {v[:80]}")
        if tag == "form" and a.get("action") != FORM_ACTION: fail(rel, f"check 9: form action must be {FORM_ACTION}")
    if re.search(r"url\(\s*['\"]?https?://", src): fail(rel, "check 9: external url() in inline CSS")

    # 10. NAP consistency
    for needle, label in ((PHONE_DISPLAY, "display phone"), (PHONE_TEL, "tel link"), (ADDRESS_1, "address line 1"), (ADDRESS_2, "address line 2"), (EMAIL, "email"), (WA_URL, "WhatsApp URL")):
        if needle not in src: fail(rel, f"check 10: {label} missing")
    for t in set(re.findall(r'href="tel:([^"]+)"', src)):
        if t != "+15862224809": fail(rel, f"check 10: stray tel: number {t}")
    for t in set(re.findall(r'href="(https://wa\.me/[^"]+)"', src)):
        if t != WA_URL: fail(rel, f"check 10: stray WhatsApp URL {t[:60]}")
    if re.search(r"4245 E Jason|85050|info@comfortluxuryrides", src): fail(rel, "check 10: old address or email leaked in")

    # 11. form shape
    if "<form" in src:
        if 'name="botcheck"' not in src: fail(rel, "check 11: honeypot missing")
        if re.search(r"<form[^>]*novalidate", src): fail(rel, "check 11: novalidate in markup (JS must set it)")
        if 'name="access_key"' not in src: fail(rel, "check 11: access_key input missing")
        if KEY_PLACEHOLDER in src:
            (fail if STRICT else warn)(rel, "check 11: Web3Forms access key is still the placeholder")
        if src.find('id="sent"') > src.find("<form"): fail(rel, "check 11: #sent panel must precede the form")
        labels = set(re.findall(r'<label for="([^"]+)"', src))
        for tag, a, _ in c.tags:
            if tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "checkbox", "submit"):
                if a.get("id") not in labels: fail(rel, f"check 11: control without label: {a.get('name')}")
        for k in ("data-sending", "data-sending-say", "data-error"):
            if k not in src: fail(rel, f"check 11: form missing {k}")
        if "/assets/js/contact.js" not in src: fail(rel, "check 11: contact.js not loaded on the form page")

    # 13. placeholders and unconfirmed claims (comments stripped above)
    for bad in ("lorem", "TODO", "{{", "XXX", "Lorem"):
        if bad in text: fail(rel, f"check 13: placeholder text {bad!r} in visible copy")
    n_conf = len(re.findall(r'data-confirm="', src))
    if n_conf: (fail if STRICT else warn)(rel, f"check 13: {n_conf} claim(s) marked data-confirm await client confirmation")

    # 14. no em dashes or en dashes
    for ch, name in (("—", "em dash"), ("–", "en dash"), ("·", "middot")):
        if ch in raw: fail(rel, f"check 14: {name} present ({raw.count(ch)})")

    # 15. language
    if not re.search(r'<html lang="en">', src): fail(rel, "check 15: <html lang=\"en\"> missing")
    if "hreflang" in src: fail(rel, "check 15: hreflang on a single-language site")

    # 16. chrome identity (aria-current normalised)
    def block(name):
        m = re.search(rf"<!-- chrome:{name} -->(.*?)<!-- /chrome:{name} -->", raw, re.S)
        return re.sub(r' aria-current="page"', "", m.group(1)) if m else None
    t, b = block("top"), block("bottom")
    if t is None or b is None: fail(rel, "check 16: chrome markers missing")
    chrome_top[rel], chrome_bottom[rel] = t, b

    # 18. preload matches hero source
    mp = re.search(r'<link rel="preload" as="image"[^>]*imagesrcset="([^"]+)"', src)
    if mp:
        ms = re.search(r'<figure class="hero__media[^"]*">.*?<source type="image/webp" srcset="([^"]+)"', src, re.S)
        if not ms: fail(rel, "check 18: image preload but no hero <source type=webp>")
        elif ms.group(1) != mp.group(1): fail(rel, "check 18: preload imagesrcset differs from the hero webp srcset")

    # 19. viewport, theme-color, noopener
    if 'name="viewport"' not in src: fail(rel, "check 19: viewport missing")
    if 'name="theme-color"' not in src: fail(rel, "check 19: theme-color missing")
    for tag, a, _ in c.tags:
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""): fail(rel, f"check 19: target=_blank without rel=noopener: {a.get('href')}")

    # 21. the wrong-city stock photo never returns
    if re.search(r"Minneapolis|Screenshot-2023", raw, re.I): fail(rel, "check 21: Minneapolis / Screenshot-2023 referenced")

    # structure basics
    for need in ('<main id="main">', 'class="skip-link"', "<header", "<footer", '<nav class="nav" aria-label="Main">'):
        if need not in src: fail(rel, f"structure: missing {need}")

# 12. sitemap, robots, hosting files
if sitemap_urls != page_urls:
    fail("sitemap.xml", f"check 12: sitemap/page mismatch. only in sitemap: {sorted(sitemap_urls - page_urls)}; only on disk: {sorted(page_urls - sitemap_urls)}")
robots = (ROOT / "robots.txt").read_text(encoding="utf-8") if (ROOT / "robots.txt").exists() else ""
if f"Sitemap: {HOST}/sitemap.xml" not in robots: fail("robots.txt", "check 12: robots.txt does not name the sitemap")
for f in (".nojekyll", "CNAME", "favicon.ico", "apple-touch-icon.png", "assets/img/og/og-default.jpg", "llms.txt", "llms-full.txt"):
    if not (ROOT / f).exists(): fail(f, "check 12: required file missing")
if (ROOT / "CNAME").exists() and (ROOT / "CNAME").read_text().strip() != "comfortluxuryrides.com": fail("CNAME", "check 12: CNAME content")

# 16. chrome identity across pages
ref = "index.html"
for rel, t in chrome_top.items():
    if t != chrome_top.get(ref): fail(rel, "check 16: chrome:top differs from index.html")
for rel, b in chrome_bottom.items():
    if b != chrome_bottom.get(ref): fail(rel, "check 16: chrome:bottom differs from index.html")

# 14. dashes in css/js too
for f in list((ROOT / "assets").rglob("*.css")) + list((ROOT / "assets").rglob("*.js")):
    t = f.read_text(encoding="utf-8")
    if "—" in t or "–" in t: fail(f.relative_to(ROOT).as_posix(), "check 14: em/en dash present")

# 20. weight budget (home): css + js + fonts + the 560 hero webp, and the plain src of every image on the page
def size(rel):
    p = ROOT / rel.lstrip("/"); return p.stat().st_size if p.exists() else 0
home = (ROOT / "index.html").read_text(encoding="utf-8")
critical = sum(size(x) for x in ("/assets/css/styles.css", "/assets/js/main.js", "/assets/fonts/cormorant-var.woff2", "/assets/fonts/inter-var.woff2", "/assets/img/black-suv-scottsdale-desert-560.webp", "/assets/img/brand/logo-badge.webp")) + len(home.encode())
imgs = sum(size(s) for s in set(re.findall(r'<img[^>]+src="([^"]+)"', home)))
if critical > 260_000: warn("index.html", f"check 20: critical weight {critical//1024} KB > 260 KB")
if imgs > 450_000: warn("index.html", f"check 20: image weight {imgs//1024} KB > 450 KB")
print(f"home critical path ~{critical//1024} KB, images (src) ~{imgs//1024} KB, pages checked: {len(pages)}")

for w in warnings: print("WARN ", w)
for f in findings: print("FAIL ", f)
print(f"{len(warnings)} warning(s)")
print("GATE PASS" if not findings else f"GATE FAIL: {len(findings)} finding(s)")
sys.exit(1 if findings else 0)

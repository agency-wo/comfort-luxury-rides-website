"""Keep the shared header/footer (the "chrome") identical on every page.

The chrome lives in every page between <!-- chrome:top --> ... <!-- /chrome:top --> and
<!-- chrome:bottom --> ... <!-- /chrome:bottom -->. index.html is the master copy.

usage:
  python _tools/sync_chrome.py           report which pages differ from index.html
  python _tools/sync_chrome.py --apply   copy the index.html chrome into every other page,
                                         re-marking aria-current="page" for that page's own nav link
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPLY = "--apply" in sys.argv
SKIP = {"_tools", "_source", "node_modules", ".git"}
pages = sorted(p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP))
master = (ROOT / "index.html").read_text(encoding="utf-8")

def block(src, name):
    m = re.search(rf"(<!-- chrome:{name} -->)(.*?)(<!-- /chrome:{name} -->)", src, re.S)
    return m

def url_of(p):
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html": return "/"
    if rel == "404.html": return None
    return "/" + rel[: -len("index.html")]

norm = lambda s: re.sub(r' aria-current="page"', "", s)
mt, mb = block(master, "top"), block(master, "bottom")
if not mt or not mb: sys.exit("index.html has no chrome markers")
top_master, bottom_master = norm(mt.group(2)), mb.group(2)

changed = 0
for p in pages:
    if p.name == "index.html" and p.parent == ROOT: continue
    src = p.read_text(encoding="utf-8")
    t, b = block(src, "top"), block(src, "bottom")
    if not t or not b:
        print("NO MARKERS", p.relative_to(ROOT)); continue
    same = norm(t.group(2)) == top_master and b.group(2) == bottom_master
    if same: continue
    changed += 1
    if not APPLY:
        print("DIFFERS   ", p.relative_to(ROOT)); continue
    url = url_of(p)
    top = top_master
    if url:
        top = top.replace(f'<a href="{url}">', f'<a href="{url}" aria-current="page">', 1)
    src = src[:t.start(2)] + top + src[t.end(2):]
    b = block(src, "bottom")
    src = src[:b.start(2)] + bottom_master + src[b.end(2):]
    p.write_text(src, encoding="utf-8", newline="\n")
    print("UPDATED   ", p.relative_to(ROOT))
print(f"{changed} page(s) {'updated' if APPLY else 'differ'}; {len(pages)} pages scanned")
sys.exit(0 if (APPLY or changed == 0) else 1)

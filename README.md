# Comfort Luxury Rides - website

Static site (HTML + CSS + JavaScript, no framework, no build step) for **Comfort Luxury Rides**,
a chauffeured luxury-SUV (black car) service in Scottsdale, Arizona. Nine pages plus a 404, one
stylesheet, three small scripts, self-hosted fonts, zero third-party requests on page load.
Built to be hosted on **GitHub Pages + Cloudflare** at `https://comfortluxuryrides.com/`.

---

## Preview locally

```powershell
cd "c:\Users\aceto\OneDrive\Desktop\web and apps\kun"
python -m http.server 8123 --bind 127.0.0.1      # then open http://127.0.0.1:8123/
```
(Port 8099 is often taken by another site's preview on this machine, so this project uses 8123.)

## Structure

```
index.html                       Home
airport-car-service/             Airport transfers (PHX, SDL, AZA, DVT) + airport FAQ
corporate-transportation/        Corporate / executive travel
event-transportation/            Games, WM Phoenix Open, Barrett-Jackson, weddings, nights out
hourly-chauffeur-service/        Private driver by the hour + FAQ
fleet/                           GMC Yukon XL Denali specs + photo gallery (lightbox)
about/                           Company, values, Ergi Janku
contact/                         Quote form (Web3Forms) + contact card
privacy/                         Privacy policy (needed because of the form)
404.html                         Not found (noindex)
assets/css/styles.css            The whole design system and every component
assets/js/main.js                Header, mobile menu, scroll reveal, WhatsApp button, back to top
assets/js/contact.js             Quote form: validation, fetch submit, success panel (works with JS off too)
assets/js/gallery.js             Fleet lightbox
assets/fonts/                    Cormorant Garamond (variable) + Inter (variable), woff2
assets/img/                      Generated WebP + JPEG renditions + manifest.json (do not edit by hand)
assets/img/brand/                Logo badge renditions     assets/img/og/og-default.jpg  share image
favicon.ico favicon-32.png apple-touch-icon.png icon-192.png
robots.txt sitemap.xml llms.txt CNAME .nojekyll
_source/originals/               Client originals (ignored by git, never deployed)
_tools/                          Image pipeline, brand/OG generators, gate, screenshots (not deployed)
```

Every page carries the same header, footer, mobile call bar and WhatsApp button between the
`<!-- chrome:top -->` and `<!-- chrome:bottom -->` markers. **`index.html` is the master copy.**
After editing the chrome in `index.html`, run `python _tools/sync_chrome.py --apply` to push it to
every other page (it re-marks each page's own nav link with `aria-current`). `python _tools/verify.py`
fails if any page drifts.

## Editing content

- **Text**: edit the page's `index.html` directly. Keep the voice: plain, concrete, no em dashes.
- **FAQ answers** appear twice on a page: once as visible `<details>` and once in the `FAQPage`
  JSON-LD in the `<head>`. Change both; `verify.py` check 6 fails if they differ.
- **Phone, address, email, WhatsApp link** appear on every page. Search and replace across all
  `*.html`, then run `verify.py` (check 10 asserts they are identical everywhere).
- **Claims awaiting client confirmation** carry `data-confirm="..."` on the element. Once the client
  confirms a claim, delete the attribute; if they deny it, rewrite the sentence. `verify.py` warns
  while any remain and `verify.py --strict` fails on them (use `--strict` before launch).

## Adding or replacing photos

1. Put the original (largest you have) in `_source/originals/`.
2. Add or edit its entry in the `M` array of `_tools/process-images.mjs` (slug, file, category, alt text,
   optional `crop`).
3. `cd _tools && npm install` (first time) then `node _tools/process-images.mjs` from the site root.
   It writes WebP + JPEG at several widths and never upscales: a 740 px original yields 740/560/400.
4. Reference the renditions in the page with `<picture>` (copy an existing block) and keep
   `width`/`height`/`alt`/`loading`.

The current originals are small (740 to 1024 px). The site is laid out so they are never stretched,
but **ask the client for originals of 2000 px or more** and re-run the pipeline; nothing else changes.
Brand assets: `python _tools/prep_brand.py` (badge + favicons), `python _tools/make_og.py` (share image).

## Quality gate

```powershell
python _tools/verify.py              # 21 checks: SEO head, JSON-LD, images, links, NAP, form, sitemap, chrome ...
python _tools/verify.py --strict     # same, but unconfirmed claims and the placeholder key fail
python _tools/contrast.py            # every colour pair used for text meets WCAG AA
python _tools/sync_chrome.py         # header/footer identical on every page
node _tools/shot.mjs http://127.0.0.1:8123/ _tools/shots/home-390.png 390 844 --full   # screenshot + overflow report
```
Lighthouse (borrowed from the MBC SRL project, not installed here):
```powershell
$env:CHROME_PATH = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
& "..\MBC SRL\_tools\node_modules\.bin\lighthouse.cmd" http://127.0.0.1:8123/ --output=html --output-path=_tools/lh/home.html --chrome-flags="--headless=new"
```
Results of the last run are in the hand-off notes at the bottom of this file.

---

## Before you publish: placeholders and facts to confirm

| What | Where | Action |
|---|---|---|
| **Web3Forms access key** | `contact/index.html`, `value="WEB3FORMS_ACCESS_KEY_PLACEHOLDER"` | Create a free key at web3forms.com **with the client's own inbox** (comfortluxuryrides@gmail.com) and paste it in. One key per client site; never reuse another site's key. Until then the form shows an error on send (the native no-JS submit also fails) |
| **Email** | every page | The site uses `comfortluxuryrides@gmail.com`. The old About page also showed `info@comfortluxuryrides.com`; confirm which inbox the client wants and replace everywhere if needed |
| **Google Business Profile link / Place ID** | `index.html` JSON-LD (`hasMap` is not set yet), footer and reviews buttons use a Maps search URL | Find the Place ID (Google Place ID finder), then add `"hasMap": "https://www.google.com/maps/place/?q=place_id:<ID>"` and `"geo"` to the LocalBusiness node, and point the review buttons at `https://search.google.com/local/writereview?placeid=<ID>` |
| **Real reviews** | `index.html`, the commented block marked `REVIEWS-PLACEHOLDER` | Paste three real reviews (first name, city, source) and remove the comment markers. Never invent reviews and never add `Review`/`AggregateRating` markup to the LocalBusiness |
| **Claims marked `data-confirm`** | all pages (`verify.py` lists the count per page) | Flight tracking, meeting point by text, FBO pickups, child seats, payment methods, cancellation terms, hourly minimum, long-distance tours, bottled water, monthly invoicing, licensed/insured wording, the owner bio sentence. Confirm each with the client, then delete the attribute or rewrite |
| **Larger photos** | `_source/originals/` | Ask for originals of 2000 px or more and a vector logo; re-run the image pipeline. The two thumbnails in the fleet gallery (garage, Old Town) are only 300 and 240 px wide |
| **Stock interiors** | corporate hero (`black-suv-rear-seat`), hourly split (`black-suv-console`) | These two are stock photos inherited from the old site. Replace with real cabin photos of the Denali when available |
| **Address** | every page + JSON-LD | `11545 N Frank Lloyd Wright Blvd, Scottsdale, AZ 85259` (confirmed with the client on 2026-08-21). Make sure the Google Business Profile shows the same address, phone and hours |

## Client preview (Cloudflare Pages)

The site is live for review at **https://comfortluxuryrides.pages.dev/** (noindex header, so search
engines ignore it). Repository: https://github.com/agency-wo/comfort-luxury-rides-website.
To refresh the preview after new commits:
```bash
STAGE=$(mktemp -d) && git archive HEAD | tar -x -C "$STAGE"   && rm -rf "$STAGE/_tools" "$STAGE/README.md" "$STAGE/.gitignore" "$STAGE/.gitattributes"   && printf '/*
  X-Robots-Tag: noindex
' > "$STAGE/_headers"   && (cd _tools && npx wrangler pages deploy "$STAGE" --project-name=comfortluxuryrides --branch=main --commit-dirty=true)
```
When the real domain goes live, either attach `comfortluxuryrides.com` to this same Cloudflare Pages
project (Custom domains, and drop the `_headers` noindex line) or use GitHub Pages as below.

## Publish: GitHub Pages + Cloudflare

1. The repository exists at `agency-wo/comfort-luxury-rides-website` (created 2026-08-21).
2. GitHub: Settings -> Pages -> Source **main / root**. Custom domain `comfortluxuryrides.com` (the `CNAME` file is already in the repo). Wait for the certificate, then tick **Enforce HTTPS**.
3. Cloudflare DNS for `comfortluxuryrides.com`:
   - `A @` -> `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME www` -> `agency-wo.github.io`
   - Start with proxy **off** (DNS only) until GitHub has issued the certificate, then turn the proxy on. SSL/TLS mode **Full**.
4. Cloudflare -> Rules -> Redirect Rules (301), so the old WordPress URLs keep their value:
   - `/about-us/` -> `/about/`
   - `/contact-us/` -> `/contact/`
   - anything else that existed on the old site (export its sitemap first: `https://comfortluxuryrides.com/wp-sitemap.xml`) -> the closest new page, or `/`
   - `www.comfortluxuryrides.com/*` -> `comfortluxuryrides.com/$1` if Cloudflare does not already do this
5. Google Search Console: add the property (if not already), submit `https://comfortluxuryrides.com/sitemap.xml`, request indexing of the home page.
6. Keep the old WordPress host for about 30 days, then cancel it once Search Console shows the new URLs indexed and the old ones redirecting.

## Google Business Profile alignment

Same name, phone, address, hours (24 hours) and website URL as the site. Primary category
"Limousine service" (or the closest the client already uses), secondary "Airport shuttle service" and
"Chauffeur service". Upload the same hero photos. Get the Place ID (see the table above) and use the
review link in follow-up messages to clients.

---

## Hand-off notes

- Design: dark-first, gold hairlines, Cormorant Garamond headings, Inter body, real Arizona photos.
  Tokens are at the top of `assets/css/styles.css`; every text colour pair is AA (`_tools/contrast.py`).
- Accessibility: skip link, landmarks, keyboard menu and lightbox, focus rings, labelled form controls
  with live-region status, reduced-motion support, 48 px tap targets, mobile call bar.
- Performance: one CSS file, deferred JS, preloaded fonts and hero image, responsive WebP + JPEG,
  lazy loading below the fold, `content-visibility` on long sections, no third-party requests.
- SEO: unique titles/descriptions, canonical, Open Graph, JSON-LD graph (LocalBusiness + Service +
  FAQPage + BreadcrumbList + Person), sitemap, robots, llms.txt, one H1 per page, keyword-led URLs.
- The gate (`_tools/verify.py`) passed with warnings only for the items in the table above.
- Lighthouse 13 on 2026-08-21 (local server, Edge headless), after the design revision: desktop
  100 / 100 / 100 / 100; throttled mobile performance 94 to 95 (LCP 2.6 to 2.7 s, CLS 0) with 100
  for accessibility, best practices and SEO. Results live in `_tools/lh/` (ignored by git).
- **Design rules that must hold.** Client photos are compositions, so they are never cropped:
  hero, split and fleet-card images keep their natural aspect ratio and are sized by their column,
  and only the fleet contact-sheet grid and the service-card thumbnails use `object-fit: cover`
  (with `--pos` per image for the focal point). On phones the hero leads with text, and the framed
  photo sits under the buttons, so the call to action is visible without scrolling.
- **Labels.** Eyebrows are plain uppercase Inter in gold: no hairline rule, no middots. The gate
  fails on `·` as well as on em and en dashes (check 14), which keeps the old style from returning.

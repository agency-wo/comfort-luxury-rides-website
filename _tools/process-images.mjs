// Comfort Luxury Rides - image pipeline.
// Reads curated originals from _source/originals, writes responsive WebP + JPEG
// renditions into /assets/img with semantic slugs, and writes /assets/img/manifest.json.
// Adapted from MBC SRL/_tools/process-images.mjs. Never upscales: every width list is
// intersected with the source width, so a 740 px original yields 740/560/400 only.
// usage: node _tools/process-images.mjs
import sharp from "sharp";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

sharp.cache(false);
const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const SRC = join(ROOT, "_source", "originals");
const OUT = join(ROOT, "assets", "img");
mkdirSync(OUT, { recursive: true });

const BG = "#0B0B0D";                      // page background: RGBA PNGs are flattened onto it
const HERO_W = [1400, 1000, 740, 560, 400];
const STD_W = [1000, 700, 480, 320];
// Optional per-item `widths` overrides both lists, for sources that do not fit the ladder.

// cat: hero | vehicle | interior | place | people | thumb | texture
// Optional `q` overrides the encode quality (already-compressed JPEG sources get a little more).
const M = [
  // crop: drops the social-app avatar bubble baked into the bottom-left corner of the source
  { slug: "black-suv-scottsdale-desert", src: "Luxury-Taxi-ARIZONA.png", cat: "hero", hero: true, crop: { left: 0, top: 0, width: 740, height: 850 },
    alt: "Black GMC Yukon XL Denali parked under the US and Arizona flags with a desert peak behind, Scottsdale" },
  { slug: "black-suv-private-jet-scottsdale-airport", src: "Luxury-Taxi-Service-in-Scottsdale-Arizona-5.jpeg", cat: "hero", hero: true, q: { webp: 78, jpeg: 84 },
    alt: "Black luxury SUV parked beside a private jet on the ramp at Scottsdale Airport" },
  { slug: "black-suv-resort-porte-cochere", src: "Taxi-Service-ARIZONA.png", cat: "hero", hero: true,
    alt: "Black luxury SUV waiting under a Spanish-tile porte-cochere with a saguaro and palm at a Scottsdale resort" },
  { slug: "black-suv-sunset-palms", src: "Luxury-Taxi-Service-ARIZONA.png", cat: "hero", hero: true,
    alt: "Side profile of a black GMC Yukon XL Denali at sunset with palm trees, Phoenix" },
  { slug: "ergi-janku-ceo", src: "Administrator-of-Company.jpeg", cat: "people", hero: true, q: { webp: 78, jpeg: 84 },
    alt: "Ergi Janku, CEO and Managing Director of Comfort Luxury Rides, in a suit beside a black SUV" },
  { slug: "black-suv-rear-seat", src: "8.png", cat: "interior",
    alt: "Rear seat of a luxury vehicle with leather headrests and seat-back screens, door open" },
  { slug: "black-suv-console", src: "10.png", cat: "interior",
    alt: "Close-up of a car centre console and climate controls" },
  { slug: "black-suv-grille", src: "Luxury-Taxi-Service-ARIZONA-USA.png", cat: "vehicle",
    alt: "Headlight and chrome grille of a black luxury car" },
  { slug: "phoenix-skyline-sunset", src: "Taxi-Service-in-Scottsdale-Arizona-1024x536.jpg", cat: "place", q: { webp: 78, jpeg: 84 }, widths: [1024, 700, 480, 320],
    alt: "Downtown Phoenix skyline at sunset with mountains behind" },
  { slug: "three-black-suvs-garage", src: "11-300x182.png", cat: "thumb",
    alt: "Three black luxury SUVs lined up in a parking garage" },
  { slug: "black-suv-old-town-scottsdale", src: "Luxury-Taxi-Service-in-Scottsdal-240x300.jpg", cat: "thumb", q: { webp: 80, jpeg: 86 },
    alt: "Black luxury SUV driving past the Sunrise Trading Post in Old Town Scottsdale" },
  { slug: "dashboard-texture", src: "arrive11-1.png", cat: "texture", q: { webp: 60, jpeg: 70 },
    alt: "" },
];

async function run() {
  const manifest = [];
  for (const item of M) {
    const widths = item.widths || (item.hero ? HERO_W : STD_W);
    const open = () => { const s = sharp(join(SRC, item.src), { failOn: "none" }).rotate(); return item.crop ? s.extract(item.crop) : s; };
    const meta = await open().toBuffer({ resolveWithObject: true }).then(r => r.info);
    const srcW = meta.width, srcH = meta.height;
    const usable = widths.filter(w => w <= srcW);
    if (usable.length === 0) usable.push(srcW);
    // keep the native width as the largest rendition when the source is smaller than the top step
    if (srcW < widths[0] && usable[0] !== srcW) usable.unshift(srcW);
    let natW = 0, natH = 0;
    for (const w of usable) {
      const pipe = open()
        .flatten({ background: BG })
        .resize({ width: w, withoutEnlargement: true })
        // the client's originals top out at 740 px, so a light unsharp pass keeps them from
        // going mushy when a 2x screen scales them up
        .sharpen({ sigma: 0.7 });
      const info = await pipe.clone().webp({ quality: item.q?.webp ?? 74 }).toFile(join(OUT, `${item.slug}-${w}.webp`));
      await pipe.clone().jpeg({ quality: item.q?.jpeg ?? 80, mozjpeg: true, progressive: true }).toFile(join(OUT, `${item.slug}-${w}.jpg`));
      if (w === usable[0]) { natW = info.width; natH = info.height; }
    }
    manifest.push({ slug: item.slug, cat: item.cat, hero: !!item.hero, widths: usable, w: natW, h: natH, alt: item.alt });
    console.log(`ok ${item.slug}  (${srcW}x${srcH} -> ${usable.join(",")})`);
  }
  writeFileSync(join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  console.log(`\nWrote manifest.json with ${manifest.length} images.`);
}
run().catch(e => { console.error(e); process.exit(1); });

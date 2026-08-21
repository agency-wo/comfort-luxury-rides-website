// Screenshot harness: node _tools/shot.mjs <url-or-file> <out.png> [width] [height] [--full] [--menu] [--y=<px>]
// Uses installed Edge via playwright-core (no browser download). --menu opens the mobile menu first.
// Reports horizontal-overflow offenders as JSON (a layout-health check, not just a picture).
// Copied from flysystem.io/tools/shot.mjs; reveal classes changed to this site's .reveal/.is-visible.
import { chromium } from "playwright-core";
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { mkdirSync } from "node:fs";

const [, , target, out, w = "1440", h = "900", ...flags] = process.argv;
const full = flags.includes("--full");
const menu = flags.includes("--menu");
const yFlag = flags.find((f) => f.startsWith("--y="));
const scrollY = yFlag ? Number(yFlag.slice(4)) : 0;
if (!target || !out) {
  console.error("usage: node _tools/shot.mjs <url-or-file> <out.png> [width] [height] [--full] [--menu]");
  process.exit(1);
}
const url = /^https?:|^file:/.test(target) ? target : pathToFileURL(resolve(target)).href;
mkdirSync(dirname(resolve(out)), { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({
  viewport: { width: Number(w), height: Number(h) },
  deviceScaleFactor: full ? 1 : 1.5,
});
await page.goto(url, { waitUntil: "networkidle" });
// content-visibility:auto sections stay unpainted in a stitched fullPage capture, so force them on for the shot
await page.addStyleTag({ content: "html { scroll-behavior: auto !important } .section, .cta-band { content-visibility: visible !important; contain-intrinsic-size: none !important }" });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => {
  document.querySelectorAll("img[loading='lazy']").forEach((img) => (img.loading = "eager"));
  document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
});
await page.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 800) {
    window.scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 40));
  }
  window.scrollTo(0, 0);
});
await page.waitForLoadState("networkidle");
await page.evaluate(() => Promise.all([...document.images].map((i) => i.decode().catch(() => {}))));
await page.waitForTimeout(400);
if (scrollY) { await page.evaluate((y) => window.scrollTo(0, y), scrollY); await page.waitForTimeout(300); }
if (menu) {
  await page.click(".nav-toggle");
  await page.waitForTimeout(600);
}
await page.screenshot({ path: out, fullPage: full, animations: "disabled" });
const overflow = await page.evaluate(() => {
  const doc = document.documentElement;
  const bad = [];
  if (doc.scrollWidth > doc.clientWidth + 1) {
    document.querySelectorAll("body *").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.right > doc.clientWidth + 1 && r.width > 0 && bad.length < 8) {
        bad.push(`${el.tagName.toLowerCase()}.${[...el.classList].join(".")} right=${Math.round(r.right)}`);
      }
    });
  }
  return { scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth, offenders: bad };
});
console.log(JSON.stringify({ out, ...overflow }));
await browser.close();

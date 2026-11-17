// 11-17 live smoke test (deploy_queue.py runs it after every push; anyone can):  node tools/smoke_live.mjs <shots dir> /path/ /path2/ ...
// Each page at 375 and 1440 px on the LIVE site (cache-busting query): HTTP status, the site's own JS errors (ad/analytics scripts are
// ignored) and sideways scroll. Saves one screenshot per width (the first page given). Exit 1 if anything failed.
import { createRequire } from 'module';
import fs from 'fs';
const require = createRequire(import.meta.url);
const PW = ['C:/Users/elift/Desktop/Eliftforlife youtube/14 failed businesses video/editor/main/node_modules/playwright',
  'C:/Users/elift/Desktop/Eliftforlife youtube/1 Elijah Westbrook/Videos/14 failed businesses video/editor/main/node_modules/playwright'];
const pw = require(PW.find(p => fs.existsSync(p)) || 'playwright');
const BASE = process.env.SMOKE_BASE || 'https://lemonindex.com', OUT = process.argv[2];
const PAGES = process.argv.slice(3);
if (!OUT || !PAGES.length) { console.log('usage: node tools/smoke_live.mjs <shots dir> /path/ ...'); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });
const THIRD = /googlesyndication|doubleclick|googletagmanager|google-analytics|gstatic|adtrafficquality|cloudflareinsights|challenges\.cloudflare|googleadservices/i;
const browser = await pw.chromium.launch({ headless: true, args: ['--disable-gpu'] });
const out = [];
for (const w of [375, 1440]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: w < 600 ? 812 : 900 }, isMobile: w < 600, hasTouch: w < 600 });
  for (const path of PAGES) {
    const page = await ctx.newPage(); const problems = [];
    page.on('pageerror', e => { const s = String(e.stack || e.message || e); if (!THIRD.test(s)) problems.push('JS: ' + String(e.message || e).slice(0, 160)); });
    try {
      const r = await page.goto(BASE + path + (path.includes('?') ? '&' : '?') + 'smoke=' + Date.now(), { waitUntil: 'load', timeout: 45000 });
      if (!r || r.status() >= 400) problems.push('HTTP ' + (r ? r.status() : 'none'));
      await page.waitForTimeout(1500);
      const m = await page.evaluate(() => { const de = document.documentElement; let wide = null;
        if (de.scrollWidth > innerWidth + 1) for (const el of document.body.querySelectorAll('*')) { const b = el.getBoundingClientRect(); if (b.right > innerWidth + 1 && b.width > 0 && (!wide || b.right > wide.r)) wide = { r: Math.round(b.right), t: el.tagName + '.' + (typeof el.className === 'string' ? el.className : '') }; }
        return { sw: de.scrollWidth, vw: innerWidth, wide, h1: (document.querySelector('h1') || {}).textContent };
      });
      if (m.sw > m.vw + 1) problems.push(`sideways scroll ${m.sw}>${m.vw} ${JSON.stringify(m.wide)}`);
      if (path === PAGES[0]) await page.screenshot({ path: `${OUT}/live_${w}.png`, fullPage: false });
      out.push({ path, w, ok: !problems.length, h1: (m.h1 || '').trim().replace(/\s+/g, ' ').slice(0, 60), problems });
    } catch (e) { out.push({ path, w, ok: false, problems: ['load: ' + String(e.message).slice(0, 120)] }); }
    await page.close();
  }
  await ctx.close();
}
await browser.close();
for (const o of out) console.log((o.ok ? 'OK  ' : 'FAIL') + ` ${o.w} ${o.path} | ${o.h1 || ''} ${o.problems.join('; ')}`);
process.exit(out.every(o => o.ok) ? 0 : 1);

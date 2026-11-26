// 11-25 leak check for the paid checklists:  node worker/store/test_leak.mjs   (after `py build.py`; add --no-docs to skip the docs/ scan)
// The paid text lives only in the private checklist folder (LEMON_CHECKLIST_SRC, default ~/Desktop/Eliftforlife youtube/3 Lemon Index/checklist)
// and in the Worker's KV. build_content.py writes every paid sentence (30+ characters: how-to steps, what good and bad look like, why it
// matters, the year notes, the unknowns, the seller questions) to <src>/store content/leak_strings.json, outside this repo.
//   Part 1: every file under docs/ (what GitHub Pages serves: HTML, JS bundles, JSON, llms.txt, sitemaps).
//   Part 2: every tracked or about-to-be-added file in this public repo (git ls-files, untracked non-ignored too) outside docs/, with JSON / Python / JS escapes undone first.
//   Part 3: the private engine (worker/store/engine.js) is gitignored and not tracked; its marker never appears in a tracked file or docs/.
// Text a free page already showed before this change is not paid by definition; the list of such strings is printed, not counted, only if it
// is also in docs/ on origin/main (PUBLIC_BEFORE=1 re-checks that). Any other hit fails.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const src = process.env.LEMON_CHECKLIST_SRC || join(homedir(), 'Desktop', 'Eliftforlife youtube', '3 Lemon Index', 'checklist');
const lsPath = join(src, 'store content', 'leak_strings.json');
if (!existsSync(lsPath)) { console.log('FAIL: no ' + lsPath + ' (run build_content.py)'); process.exit(1); }
const strings = JSON.parse(readFileSync(lsPath, 'utf8')).map(s => s.trim()).filter(s => s.length >= 30);
if (strings.length < 1000) { console.log('FAIL: only ' + strings.length + ' paid strings'); process.exit(1); }
const ENGINE_MARK = ['PRIVATE: paid content.', 'The Lemon Index offer', 'engine'].join(' ');   // in pieces, so this file doesn't match itself

// ---- many-string search: a rolling hash over the first K characters of each string, then an exact compare
const K = 30, P = 2147483647, B = 131;
let BK = 1; for (let i = 0; i < K - 1; i++) BK = (BK * B) % P;
const anchors = new Map();
for (const s of strings) { let h = 0; for (let i = 0; i < K; i++) h = (h * B + s.charCodeAt(i)) % P; const l = anchors.get(h); l ? l.push(s) : anchors.set(h, [s]); }
function find(text) {
  const hits = new Set(); if (text.length < K) return hits;
  let h = 0; for (let i = 0; i < K; i++) h = (h * B + text.charCodeAt(i)) % P;
  for (let i = 0; ; i++) {
    const l = anchors.get(h);
    if (l) for (const s of l) if (text.startsWith(s, i)) hits.add(s);
    if (i + K >= text.length) break;
    h = ((h - (text.charCodeAt(i) * BK) % P + P) % P * B + text.charCodeAt(i + K)) % P;
  }
  return hits;
}
const unesc = t => t.replace(/\\u([0-9a-fA-F]{4})/g, (_, x) => String.fromCharCode(parseInt(x, 16))).replace(/\\(["'\\/])/g, '$1').replace(/\\n/g, '\n')
  .replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&rsquo;/g, '’').replace(/&amp;/g, '&');
const scan = t => { const a = find(t); if (/\\|&[#a-z]/.test(t)) for (const s of find(unesc(t))) a.add(s); return a; };

let bad = 0;
// self-test: a paid sentence inside other text, and JSON-escaped, must both be found
const probe = strings.find(x => /["’]/.test(x)) || strings[0];
if (!scan('xx ' + probe + ' yy').has(probe) || !scan(JSON.stringify({ a: 'q ' + probe })).has(probe)) { console.log('FAIL: the matcher missed a planted string'); process.exit(1); }
const report = (where, hits) => { for (const s of hits) { bad++; if (bad <= 25) console.log('LEAK', where, JSON.stringify(s.slice(0, 90))); } };

// Part 3 first: the engine is not tracked and is ignored
const tracked = execFileSync('git', ['ls-files', '-z', '--cached', '--others', '--exclude-standard'], { cwd: root, maxBuffer: 1 << 30 }).toString().split('\0').filter(Boolean);
if (tracked.includes('worker/store/engine.js')) { bad++; console.log('LEAK worker/store/engine.js is tracked'); }
try { execFileSync('git', ['check-ignore', '-q', 'worker/store/engine.js'], { cwd: root }); } catch { bad++; console.log('LEAK worker/store/engine.js is not gitignored'); }

// Part 2: tracked files outside docs/
let n2 = 0;
for (const f of tracked) {
  if (f.startsWith('docs/') || !/\.(py|js|mjs|json|md|txt|html|css|toml|sql|ya?ml|csv|xml)$/i.test(f)) continue;
  const p = join(root, f); if (!existsSync(p) || statSync(p).size > 64 * 1024 * 1024) continue;
  const t = readFileSync(p, 'utf8'); n2++;
  if (t.includes(ENGINE_MARK)) { bad++; console.log('LEAK engine text in', f); }
  report(f, scan(t));
}
console.log(`part 2: ${strings.length} paid strings checked against ${n2} tracked files outside docs/`);

// Part 1: docs/
if (!process.argv.includes('--no-docs')) {
  let n1 = 0, bytes = 0; const t0 = Date.now();
  (function walk(d) {
    for (const f of readdirSync(d)) {
      const p = join(d, f), st = statSync(p);
      if (st.isDirectory()) { walk(p); continue; }
      if (!/\.(html|js|json|txt|xml|css|webmanifest)$/.test(f)) continue;
      const t = readFileSync(p, 'utf8'); n1++; bytes += t.length;
      if (t.includes(ENGINE_MARK)) { bad++; console.log('LEAK engine text in', p.slice(root.length)); }
      report(p.slice(root.length + 1), scan(t));
    }
  })(join(root, 'docs'));
  console.log(`part 1: ${n1} files in docs/ (${Math.round(bytes / 1048576)} MB) in ${Math.round((Date.now() - t0) / 1000)} s`);
}
console.log(bad ? `FAIL: ${bad} leaks` : 'PASS: 0 leaks');
process.exit(bad ? 1 : 0);

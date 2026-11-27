// Compare up to 4 cars (11-02 first version; 11-12 UX test: every model, EV, performance car and supercar, up to 4, Enter adds a car).
// Data: /assets/compare.json (built by ux_c.py) = {cars: [{i id, n name, b brand, u page, k kind (car|ev|perf|sc|co), a aliases,
//   y {year: [index|null, complaints, recalls, mpgLo, mpgHi, stars, topProblem, costLo, costHi, isEV, partial (2023+)]}  or  g [generation specs] (perf),
//   d default year/generation, ev {r range, c cost, e MPGe, yr, li, w, u} (EVs), w 'ev' (score = the EV page's), h note}]}
// URL: /compare/?cars=toyota-rav4-2019,bmw-m3-g80   (?c= still works: the year pages' Compare buttons use it)
(async () => {
  const root = document.getElementById('cmpx'); if (!root) return;
  let J;
  try { J = await (await fetch('/assets/compare.json?v=1112r2d')).json(); } catch (e) { root.innerHTML = '<p class="note">Couldn&#39;t load the car list. Refresh to try again.</p>'; return; }
  const C = J.cars, BY = {}, MAX = 4;
  C.forEach(c => { BY[c.i] = c; });
  const IDX = C.map((_, n) => n);
  const fold = s => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const HAY = C.map(c => { const n = fold(c.n), a = fold(c.a), b = fold(c.b); return { c, toks: (n + ' ' + a + ' ' + b).split(' '), flat: (n + ' ' + a).replace(/ /g, '') }; });
  const opts = c => c.g ? c.g.map(g => [g.id, `${g.c} · ${g.y}`]) : Object.keys(c.y).sort().reverse().map(y => [y, y]);
  const has = (c, v) => c.g ? c.g.some(g => g.id === v) : !!c.y[v];
  // "toyota-rav4-2019" / "bmw-m3-g80" / "hyundai-ioniq-5": the longest known id prefix, the rest is the year or generation
  const parse = s => {
    for (let k = s.length; k > 0; k--) {
      if (k < s.length && s[k] !== '-') continue;
      const id = s.slice(0, k), c = BY[id]; if (!c) continue;
      const v = s.slice(k + 1); return [id, v && has(c, v) ? v : String(c.d), !(v && has(c, v))];
    }
    return null;
  };
  const qp = new URLSearchParams(location.search);
  let cars = (qp.get('cars') || qp.get('c') || '').split(',').filter(Boolean).map(parse).filter(Boolean).slice(0, MAX);
  // 11-12 r2: a car linked without a year takes the first car's year when it has a full score for it (never 2025 by default)
  const y0 = cars.find(c => !c[2] && !BY[c[0]].g);
  cars = cars.map(([i, v, guess]) => { const c = BY[i]; return [i, guess && y0 && !c.g && c.y[y0[1]] && c.y[y0[1]][0] != null && !c.y[y0[1]][10] ? y0[1] : v]; });
  const save = () => { const q = cars.map(([i, v]) => `${i}-${v}`).join(','); history.replaceState(null, '', q ? `?cars=${q}` : location.pathname); };
  // 11-12 r2: the site's one set of band words (build.py band()); a 2023+ year is partial, never judged
  const word = (li, p) => li == null ? ['mid', 'No score'] : p ? ['na', 'Too new: partial score'] : li < 50 ? ['good', 'One of the most reliable'] : li < 85 ? ['good', 'Better than average'] : li <= 115 ? ['mid', 'About average'] : li < 200 ? ['bad', 'Worse than average'] : ['bad', 'Avoid'];
  const part = r => !!(r.v && r.v[10]);
  // short column names on phones: "RAV4 Hybrid" under a small "Toyota" (Carlos: "Toyot/a" split mid-word in 4 columns)
  const shortN = c => c.b && c.n.startsWith(c.b + ' ') ? c.n.slice(c.b.length + 1) : c.n;
  const KIND = { car: '', ev: 'Electric', perf: 'Performance', sc: 'Supercar', co: 'Complaints only' };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
  const rng = (a, b, u = '') => a == null ? null : (a === b || b == null ? `${a.toLocaleString()}` : `${a.toLocaleString()}–<wbr>${b.toLocaleString()}`) + u;
  const num = s => { if (s == null) return null; const m = String(s).replace(/,/g, '').match(/[\d.]+/); return m ? +m[0] : null; };
  function find(q) {
    const s = fold(q), y = (s.match(/\b(19|20)\d{2}\b/) || [''])[0], w = s.replace(/\b(19|20)\d{2}\b/, ' ').split(' ').filter(Boolean);
    if (!w.length) return [[], y];
    const hit = HAY.filter(h => w.every(x => h.toks.some(t => t.startsWith(x)) || (x.length > 2 && h.flat.includes(x))));
    hit.sort((a, b) => (fold(a.c.n).startsWith(w[0]) ? 0 : 1) - (fold(b.c.n).startsWith(w[0]) ? 0 : 1) || (a.c.k === 'co') - (b.c.k === 'co') || a.c.n.localeCompare(b.c.n));
    // 11-12 (testers: "crv", "rouge", "chevy"): the site search's matcher (lookup.js: hyphens, aliases, typos) first, when it's loaded
    const lq = window.LQ ? LQ.pick(q.replace(/\b(19|20)\d{2}\b/, ' '), IDX, n => C[n].n + ' ' + (C[n].a || '')).map(n => C[n]) : [];
    return [[...new Set([...lq, ...hit.map(h => h.c)])].slice(0, 7), y];
  }
  // 11-12 r2 (Carlos, Mitch: added cars defaulted to 2025): no typed year -> the year of the car already in the table (the page's year), else the
  // newest fully scored year (compare.json d, never a partial 2023+)
  const pick = (c, y) => { if (y && c.y && c.y[y]) return y; const y0 = cars.length && !BY[cars[0][0]].g ? cars[0][1] : ''; return (y0 && c.y && c.y[y0] && c.y[y0][0] != null) ? y0 : String(c.d); };
  function add(id, v, quiet) { if (cars.length >= MAX || cars.some(([i, w]) => i === id && w === v)) return; cars.push([id, v]); save(); draw(!quiet); }
  // 11-15 growth 4d: "Add from My cars": the cars saved with the Save buttons (localStorage li-saved, assets/saved.js), one tap each.
  // A saved model year keeps its year, a saved model the year picked on /saved/ (else the usual default), a performance car its generation.
  function myCars() {
    let a = []; try { a = JSON.parse(localStorage.getItem('li-saved') || '[]'); } catch (e) { return []; }
    const out = [], seen = new Set();
    for (const x of Array.isArray(a) ? a : []) {
      if (!x || typeof x.id !== 'string') continue;
      const id = x.u ? x.c : x.id, c = id && BY[id]; if (!c) continue;   // motorcycles aren't in the tool
      const v = c.g ? (x.sg && has(c, x.sg) ? x.sg : String(c.d)) : (x.y && c.y[x.y] ? String(x.y) : x.sy && c.y[x.sy] ? String(x.sy) : pick(c, ''));
      if (seen.has(id + '|' + v) || cars.some(([i, w]) => i === id && w === v)) continue;
      seen.add(id + '|' + v);
      const g = c.g && c.g.find(z => z.id === v);
      out.push([id, v, c.g ? `${c.n}${g ? ` (${g.c})` : ''}` : `${v} ${c.n}`]);
    }
    return out;
  }
  function search(box) {
    const q = box.querySelector('input'), out = box.querySelector('.cx-sug');
    let hits = [], yy = '';
    const show = () => {
      [hits, yy] = find(q.value);
      out.innerHTML = hits.length ? hits.map((c, n) => `<div class="cx-hit"><b>${esc(c.n)}${KIND[c.k] ? ` <small>${KIND[c.k]}</small>` : ''}</b><select data-n="${n}" aria-label="${c.g ? 'Generation' : 'Model year'} for ${esc(c.n)}">${opts(c).map(([v, l]) => `<option value="${v}"${v === pick(c, yy) ? ' selected' : ''}>${l}</option>`).join('')}</select><button type="button" data-n="${n}">Add</button></div>`).join('')
        : (q.value.trim().length > 1 ? '<p class="cx-none">No match yet. Try the model name, like &ldquo;Camry&rdquo;, &ldquo;Model 3&rdquo; or &ldquo;M3&rdquo;.</p>' : '');
      out.querySelectorAll('button').forEach(b => b.onclick = () => { const c = hits[+b.dataset.n]; add(c.i, out.querySelector(`select[data-n="${b.dataset.n}"]`).value); });
      // 11-12 r2 (Mitch: only "Add" was tappable): the whole row adds the car, except a tap on its year picker
      out.querySelectorAll('.cx-hit').forEach(h => h.onclick = e => { if (e.target.closest('select, button')) return; const b = h.querySelector('button'); if (b) b.click(); });
    };
    q.oninput = show;
    q.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); show(); if (hits[0]) { const s0 = out.querySelector('select[data-n="0"]'); add(hits[0].i, s0 ? s0.value : pick(hits[0], yy)); } } };
  }
  function row(c, v) {
    if (c.g) { const g = c.g.find(x => x.id === v) || c.g.at(-1); return { g }; }
    return { v: c.y[v] || [] };
  }
  // 11-12 round 2 (Devin): the hero pictures follow the cars being compared, and Share sends this exact set (or its ready-made match-up
  // page, which has its own preview) instead of the bare /compare/ page
  const PAGES = new Set(J.pages || []), pair = document.querySelector('.ph-pair'), shb = [...document.querySelectorAll('[data-share]')];
  const shTxt0 = shb.map(b => b.dataset.share), title0 = document.title;
  function hero(R) {
    const ims = pair ? [...pair.querySelectorAll('img')] : [];
    R.filter(r => r.c.im).slice(0, 2).forEach((r, n) => { const im = ims[n]; if (!im || im.dataset.src === r.c.im) return; im.removeAttribute('srcset'); im.src = r.c.im; im.alt = r.c.n; im.dataset.src = r.c.im; });
    const names = R.map(r => r.c.n), ids = R.map(r => r.c.i);
    const ready = R.length === 2 ? [`/compare/${ids[0]}-vs-${ids[1]}/`, `/compare/${ids[1]}-vs-${ids[0]}/`].find(u => PAGES.has(u)) : null;
    shb.forEach((b, n) => {
      if (R.length < 2) { b.dataset.share = shTxt0[n]; delete b.dataset.shareUrl; return; }
      b.dataset.share = `${names.join(' vs ')}: problems, recalls and specs side by side. Free:`;
      b.dataset.shareUrl = ready || location.pathname + location.search;
    });
    document.title = R.length >= 2 ? `${names.join(' vs ')}: Compare Side by Side | The Lemon Index` : title0;
  }
  // 11-19 v5 (Elijah, phone): the tool looks like the match-up pages: a card per car on top (picture, name, year, one Lemon bar),
  // then every line is a tap-to-open box with one bar per car under a big car-name header (green = best of these cars, red = worst)
  const IC = { 'Complaint Score': 'chart', 'Owner complaints': 'talk', 'Recalls': 'warning', 'Horsepower': 'engine', 'Torque': 'engine', '0–60 mph': 'stopwatch',
    'Top speed': 'stopwatch', 'Weight': 'scale', 'Price new': 'tag', 'Engine': 'engine', 'YouTube owner tone': 'youtube', 'MPG / MPGe': 'data',
    'Fuel economy': 'data', 'Fuel cost a year': 'tag', 'EV range': 'signpost', 'Crash test': 'car', 'Top problem': 'wrench' };
  const svg = id => `<svg class="cpl-i" width="24" height="24" aria-hidden="true" focusable="false"><use href="/assets/ic.svg?v=1#${id}"></use></svg>`;
  const AR = '<svg class="cpl-ar" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const plain = t => String(t ?? '').replace(/<small[^>]*>.*?<\/small>/g, '').replace(/<[^>]+>/g, '').replace(/&#39;/g, "'").replace(/&amp;/g, '&').trim();
  // the model page's Lemon bar, small: 0-200 so 100 sits in the middle; green < 85, gray 85-115, red > 115
  const gauge = (li, lab, part_) => { const k = part_ ? 'mid' : li < 85 ? 'good' : li > 115 ? 'bad' : 'mid';
    return `<span class="cx5-g cx5-g-${k}" style="--p:${Math.min(Math.max(li, 0), 200) / 2}%"><span class="cx5-gt" aria-hidden="true"><i class="cx5-gg"></i><i class="cx5-gm"></i><i class="cx5-gr"></i><em></em></span><span class="cx5-gn">${li}</span><small>${lab}</small></span>`; };
  const tone = yt => `<span class="cx5-g cx5-g-${yt >= 70 ? 'good' : yt < 50 ? 'bad' : 'mid'}"><span class="cx5-ft"><i style="--w:${Math.max(3, Math.min(100, yt))}%"></i></span><span class="cx5-gn">${yt}</span><small>YouTube owner tone · out of 100</small></span>`;
  if (!document.getElementById('cx5-css')) document.head.insertAdjacentHTML('beforeend', `<style id="cx5-css">
.cx5-cars { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 10px; margin: 0 0 14px; }
@media (max-width: 700px) { .cx5-cars { grid-template-columns: repeat(min(var(--n), 2), minmax(0, 1fr)); } }
.cx5-car { position: relative; display: flex; flex-direction: column; align-items: center; text-align: center; min-width: 0; padding: 14px 10px 16px; border-radius: 22px; background: #fff; box-shadow: inset 0 0 0 1px #e5e5ea; }
.cx5-car.win { box-shadow: inset 0 0 0 2px #1a8f4c; }
.cx5-car .cx-x { top: 4px; right: 8px; }
.cx5-car .cx-badge { position: static; display: inline-block; margin: 0 0 6px; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; }
.cx5-im { display: block; width: 100%; max-width: 260px; aspect-ratio: 5 / 3; height: auto; object-fit: contain; }
.cx5-r { transform: scaleX(-1); }
.cx5-car .cx-name { margin-top: 6px; padding: 0; font-size: clamp(17px, 4.4vw, 22px); font-weight: 800; letter-spacing: -.02em; overflow-wrap: normal; word-break: normal; hyphens: auto; }
.cx5-car .cx-brand { font-size: 12px; }
.cx5-car .cx-sel { margin: 8px auto 0; }
.cx5-g { display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 230px; margin-top: 12px; }
.cx5-gt { position: relative; display: flex; gap: 2px; width: 100%; height: 10px; margin-top: 8px; }
.cx5-gt i { display: block; height: 100%; }
.cx5-gg { flex: 0 0 calc(42.5% - 1px); background: #1a8f4c; border-radius: 5px 0 0 5px; }
.cx5-gm { flex: 0 0 calc(15% - 1px); background: #c9ccd1; }
.cx5-gr { flex: 1 1 auto; background: #e8141c; border-radius: 0 5px 5px 0; }
.cx5-gt em { position: absolute; top: -9px; bottom: -9px; left: var(--p); width: 4px; margin-left: -2px; border-radius: 2px; background: #1d1d1f; box-shadow: 0 0 0 2px #fff; }
.cx5-gt em::before { content: ""; position: absolute; left: 50%; top: -7px; width: 12px; height: 12px; margin-left: -6px; border-radius: 50%; background: #ffd400; border: 3px solid #1d1d1f; box-sizing: border-box; }
.cx5-ft { display: block; width: 100%; height: 12px; margin-top: 4px; border-radius: 6px; background: #ececf0; overflow: hidden; }
.cx5-ft i { display: block; width: var(--w); height: 100%; border-radius: 6px; background: #8e8e93; }
.cx5-g-good .cx5-ft i { background: #1a8f4c; } .cx5-g-bad .cx5-ft i { background: #e8141c; }
.cx5-gn { margin-top: 12px; font: 800 clamp(30px, 8vw, 44px)/1 var(--sys, Archivo, Inter, sans-serif); letter-spacing: -.03em; font-variant-numeric: tabular-nums; color: #6e6e73; }
.cx5-g-good .cx5-gn { color: #1a8f4c; } .cx5-g-bad .cx5-gn { color: #d0121a; }
.cx5-g small { margin-top: 4px; font-size: 12px; font-weight: 600; color: #6e6e73; }
.cx5-car .cx-v { margin: 8px 0 0; font-size: 13.5px; }
.cx5-pills { display: grid; gap: 10px; margin: 0 0 14px; }
.cx5-cars, .cpl.cx5-pills { max-width: 920px; margin-left: auto; margin-right: auto; }
.cx5-pills summary small { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.cx5-pills summary > span { min-width: 0; }
.cx5-duo { display: grid; grid-template-columns: repeat(min(var(--n), 2), minmax(0, 1fr)); gap: 10px; }
@media (min-width: 701px) { .cx5-duo { grid-template-columns: repeat(var(--n), minmax(0, 1fr)); } }
.cx5-dc { min-width: 0; padding: 14px 14px 12px; border-radius: 18px; background: #fff; box-shadow: inset 0 0 0 1px #e5e5ea; }
.cx5-dc h3 { margin: 0; font-size: clamp(17px, 4.6vw, 22px); font-weight: 800; letter-spacing: -.02em; line-height: 1.15; overflow-wrap: normal; hyphens: auto; }
.cx5-dc > b { display: block; margin-top: 8px; font: 800 clamp(24px, 7vw, 36px)/1.05 var(--sys, Archivo, Inter, sans-serif); letter-spacing: -.03em; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.cx5-dc > b small { font-size: 13px; font-weight: 600; letter-spacing: 0; color: #6e6e73; }
.cx5-dc > b .st { font-size: .7em; letter-spacing: -1px; white-space: nowrap; }
.cx5-dc > b a { color: inherit; }
.cx5-dc.tx > b { font-size: clamp(16px, 4.4vw, 20px); letter-spacing: -.01em; overflow-wrap: normal; hyphens: auto; }
.cx5-dt { display: block; height: 14px; margin-top: 10px; border-radius: 7px; background: #ececf0; overflow: hidden; }
.cx5-dt i { display: block; width: var(--w); height: 100%; border-radius: 7px; background: #c9ccd1; }
.cx5-dg > b { color: #1a8f4c; } .cx5-dg .cx5-dt i { background: #1a8f4c; }
.cx5-dr > b { color: #d0121a; } .cx5-dr .cx5-dt i { background: #e8141c; }
.cx5-dc > small { display: block; margin-top: 8px; font-size: 13px; line-height: 1.3; color: #6e6e73; }
</style>`);
  function draw(focus) {
    const R = cars.map(([i, v]) => ({ c: BY[i], key: v, ...row(BY[i], v) }));
    const anyEV = R.some(r => r.c.ev || (r.v && r.v[9])), anyPerf = R.some(r => r.g), anyCar = R.some(r => r.v);
    // [label, note, value fn -> [text, number for the green check], higher is better?]
    const L = [];
    if (anyCar) L.push(['Complaint Score', '100 = average car, lower is better', r => r.v ? [r.v[0] == null ? '—' : r.v[0] + (r.c.w === 'ev' ? '*' : '') + (part(r) ? ' <small>partial</small>' : ''), r.c.w === 'ev' || part(r) ? null : r.v[0]] : ['—'], false],
                       ['Owner complaints', 'to NHTSA, first 3 years (raw count, not per car sold)', r => r.v ? [r.v[1] == null ? '—' : r.v[1].toLocaleString(), null] : r.g ? [r.g.nc == null ? '—' : r.g.nc.toLocaleString(), null] : ['—'], false]);
    if (anyPerf && !anyCar) L.push(['Owner complaints', 'to NHTSA, these years (raw count)', r => r.g ? [r.g.nc == null ? '—' : r.g.nc.toLocaleString(), null] : ['—'], false]);
    L.push(['Recalls', 'that model year / generation', r => r.v ? [r.v[2] == null ? '—' : r.v[2], r.v[2]] : r.g ? [r.g.rc, r.g.rc] : ['—'], false, true]);   // [4] true: 0 is a real value (Devin: 7 recalls beat 0)
    if (anyPerf) L.push(['Horsepower', '', r => r.g ? [r.g.hp ?? '—', r.g.hp] : ['—'], true], ['Torque', 'lb-ft', r => r.g ? [r.g.tq ?? '—', num(r.g.tq)] : ['—'], true],
                        ['0–60 mph', 'seconds', r => r.g ? [r.g.z == null ? '—' : r.g.z + (r.g.zt ? ` <small class="cx-zt">${esc(r.g.zt)}</small>` : ''), num(r.g.z)] : ['—'], false], ['Top speed', '', r => r.g ? [r.g.top ?? '—', num(r.g.top)] : ['—'], true],
                        ['Weight', '', r => r.g ? [r.g.wt ?? '—', num(r.g.wt)] : ['—'], false], ['Price new', 'base, when new', r => r.g ? [r.g.p ?? '—', num(r.g.p)] : ['—'], false],
                        ['Engine', '', r => r.g ? [r.g.eu ? `<a href="${esc(r.g.eu)}">${esc(r.g.e)}</a>` : esc(r.g.e || '—'), null] : ['—'], null],
                        ['YouTube owner tone', 'out of 100', r => r.g ? [r.g.yt ?? '—', r.g.yt] : ['—'], true]);
    if (anyCar) {
      L.push([anyEV ? 'MPG / MPGe' : 'Fuel economy', 'combined, EPA', r => { if (!r.v) return ['—']; const ev = r.v[9] || r.c.ev; const s = rng(r.v[3], r.v[4]); return [s ? s + (ev ? ' MPGe' : ' mpg') : '—', ev ? null : r.v[4]]; }, true],
             ['Fuel cost a year', anyEV ? 'gas or electricity, EPA' : 'EPA estimate', r => { if (!r.v) return ['—']; const s = rng(r.v[7], r.v[8]); return [s ? '$' + s.replace('–<wbr>', '–<wbr>$') : '—', r.v[7]]; }, false]);
      if (anyEV) L.push(['EV range', 'EPA, miles', r => r.c.ev && r.c.ev.r ? [rng(r.c.ev.r[0], r.c.ev.r[1], ' mi') + (r.c.ev.yr ? ` <small>(${r.c.ev.yr})</small>` : ''), r.c.ev.r[1]] : ['—'], true]);
      L.push(['Crash test', 'NHTSA overall', r => r.v && r.v[5] ? ['<span class="st">' + '★'.repeat(r.v[5]) + '☆'.repeat(5 - r.v[5]) + '</span>', r.v[5]] : ['—'], true],
             ['Top problem', 'most-named in complaints', r => [r.v && r.v[6] ? esc(r.v[6]) : '—', null], null]);
    }
    if (R.length) L.splice(0, L.length, ...L.filter(([, , f]) => R.some(r => { const t = f(r)[0]; return t !== '—' && t !== '' && t != null; })));   // 11-12 r2 (Devin): no row that's empty for every car
    const best = L.map(([, , f, hi, zero]) => { if (hi == null) return null; const xs = R.map(r => f(r)[1]).filter(x => x != null && (zero || x !== 0)); if (xs.length < 2 || new Set(xs).size < 2) return null; return hi ? Math.max(...xs) : Math.min(...xs); });
    const scored = R.filter(r => r.v && r.v[0] != null && r.c.w !== 'ev' && !part(r)), win = scored.length >= 2 ? scored.reduce((a, c) => c.v[0] < a.v[0] ? c : a) : null;
    const worst = L.map(([, , f, hi, zero]) => { if (hi == null) return null; const xs = R.map(r => f(r)[1]).filter(x => x != null && (zero || x !== 0)); if (xs.length < 2 || new Set(xs).size < 2) return null; return hi ? Math.min(...xs) : Math.max(...xs); });
    const card = (r, n) => {
      const [cl, w] = r.v ? word(r.v[0], part(r)) : ['', KIND[r.c.k]];
      const sel = `<select class="cx-sel" data-k="${n}" aria-label="${r.g ? 'Generation' : 'Model year'}">${opts(r.c).map(([v, l]) => `<option value="${v}"${v === r.key ? ' selected' : ''}>${l}</option>`).join('')}</select>`;
      const href = r.g ? r.c.u : (r.c.u.startsWith('/cars/') && r.c.y[r.key] ? `${r.c.u}${r.key}/` : r.c.u);
      const pic = r.c.im ? `<img class="cx5-im${R.length === 2 && n === 1 ? ' cx5-r' : ''}" src="${esc(r.c.im)}" alt="${esc(r.c.n)}" width="500" height="300" decoding="async">` : '';
      const bar = r.v ? (r.v[0] == null ? '' : gauge(r.v[0], r.c.w === 'ev' ? 'EV Complaint Score*' : part(r) ? 'Partial Complaint Score' : 'Complaint Score', part(r)))
                : r.g && r.g.yt != null ? tone(r.g.yt) : '';
      return `<div class="cx5-car${win === r ? ' win' : ''}"><button class="cx-x" type="button" data-k="${n}" aria-label="Remove ${esc(r.c.n)}">×</button>${win === r ? '<p class="cx-badge">Best score <small>per car sold</small></p>' : ''}${pic}
<a class="cx-name" href="${esc(href)}" title="${esc(r.c.n)}">${shortN(r.c) !== r.c.n ? `<small class="cx-brand">${esc(r.c.b)}</small>` : ''}${esc(shortN(r.c))}</a>${sel}${bar}${r.g ? `<p class="cx-v">${esc(r.g.v)}</p>` : `<p class="cx-v ${cl}">${w}</p>`}</div>`;
    };
    const lbox = ([lab, note, f, hi], n) => {
      const vals = R.map(r => f(r)), txt = L[n][3] === null;
      const xs = vals.map(([t, x]) => x != null ? x : (txt ? null : num(plain(t))));
      const mx = Math.max(...xs.filter(x => x != null), 0) || 1;
      const cells = R.map((r, k) => {
        const [t, x] = vals[k], v = xs[k];
        const cls = best[n] != null && x === best[n] ? ' cx5-dg' : worst[n] != null && x === worst[n] ? ' cx5-dr' : '';
        const wd = lab === 'Complaint Score' ? (v ?? 0) / 2 : lab === 'Crash test' ? (v ?? 0) / 5 * 100 : (v ?? 0) / mx * 100;
        return `<div class="cx5-dc${cls}${txt ? ' tx' : ''}"><h3>${esc(shortN(r.c))}</h3><b>${t}</b>${!txt && v != null ? `<span class="cx5-dt"><i style="--w:${Math.max(3, Math.min(100, wd)).toFixed(0)}%"></i></span>` : ''}${note ? `<small>${note}</small>` : ''}</div>`;
      }).join('');
      const sub = R.map((r, k) => `${shortN(r.c)} ${plain(vals[k][0]) || '—'}`).join(' · ');
      return `<details><summary>${svg(IC[lab] || 'data')}<span><b>${lab}</b><small>${esc(sub)}</small></span>${AR}</summary><div class="cpl-b"><div class="cx5-duo">${cells}</div></div></details>`;
    };
    const notes = [];
    if (R.some(part)) notes.push('Partial = a 2023 or newer model year: under 3 years on the road, so its score can change and it never gets the check or the badge.');
    if (R.some(r => r.c.w === 'ev')) notes.push('* EV score from the electric-car page: complaints filed by the end of the year after the model year, a shorter window than the main 3-year score, so compare it with other EV scores.');
    R.filter(r => r.c.h).forEach(r => notes.push(`${esc(r.c.n)}: ${esc(r.c.h)}`));
    if (R.some(r => r.g)) notes.push('Performance specs: the generation&#39;s headline trim (see its page for every trim and source); when that trim has no 0–60 test, the quickest tested trim, named under the time. Complaint counts there are raw, not per car sold.');
    const my = cars.length < MAX ? myCars() : [];
    const myRow = my.length ? `<div class="lsv-cm"><p class="lsv-cm-h"><b>Add from My cars</b><a href="/saved/">See all</a></p><div class="lsv-cm-l">${my.slice(0, 12).map(([, , l], n) => `<button type="button" class="lsv-cm-b" data-my="${n}" aria-label="Add the ${esc(l)} to the comparison">+ ${esc(l)}</button>`).join('')}</div></div>` : '';
    const addBox = cars.length < MAX ? `<div class="cx-add"><p><b>${cars.length ? `Add a car <small>(${cars.length} of ${MAX})</small>` : 'Pick up to 4 cars'}</b></p>${myRow}<div class="cx-box"><input type="search" enterkeyhint="go" placeholder="e.g. 2019 RAV4, Model 3, M3, Ioniq 5" aria-label="Find a car to compare" autocomplete="off"><div class="cx-sug"></div></div></div>` : `<p class="cx-full">That&#39;s 4 cars, the most at once. Remove one to add another.</p>`;
    root.innerHTML = (R.length ? `<div class="cx5-cars" style="--n:${R.length}">${R.map((r, n) => card(r, n)).join('')}</div>`
      + (R.length >= 2 ? `<div class="cpl cx5-pills" style="--n:${R.length}">${L.map(lbox).join('')}</div>` : `<div class="cpl cx5-pills" style="--n:1">${L.map(lbox).join('')}</div>`) : '') + addBox
      + (R.length >= 2 ? `<p class="cx-cap">Tap a line to see every car side by side. Green = the best of these cars on that line, red = the worst. Best score = the lowest Complaint Score (complaints per car sold), not the fewest raw complaints. ${notes.join(' ')}</p>` : notes.length ? `<p class="cx-cap">${notes.join(' ')}</p>` : '');
    hero(R);
    root.querySelectorAll('.lsv-cm-b').forEach(b => b.onclick = () => { const m = my[+b.dataset.my]; if (m) add(m[0], m[1], true); });
    root.querySelectorAll('.cx-x').forEach(x => x.onclick = () => { cars.splice(+x.dataset.k, 1); save(); draw(); });
    root.querySelectorAll('.cx-sel').forEach(s => s.onchange = () => { cars[+s.dataset.k][1] = s.value; save(); draw(); });
    const box = root.querySelector('.cx-add'); if (box) { search(box); if (focus) box.querySelector('input').focus({ preventScroll: true }); }
    // 11-12 r2 (Liam: after adding a car the page sat mid-table): keep the car names in view
    if (focus && R.length) { const t = root.querySelector('.cx5-cars'); if (t && t.getBoundingClientRect().top < 0) t.scrollIntoView({ block: 'start' }); }
  }
  draw();
})();

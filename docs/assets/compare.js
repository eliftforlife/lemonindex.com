// Compare up to 4 cars (11-02 first version; 11-12 UX test: every model, EV, performance car and supercar, up to 4, Enter adds a car).
// Data: /assets/compare.json (built by ux_c.py) = {cars: [{i id, n name, b brand, u page, k kind (car|ev|perf|sc|co), a aliases,
//   y {year: [index|null, complaints, recalls, mpgLo, mpgHi, stars, topProblem, costLo, costHi, isEV]}  or  g [generation specs] (perf),
//   d default year/generation, ev {r range, c cost, e MPGe, yr, li, w, u} (EVs), w 'ev' (score = the EV page's), h note}]}
// URL: /compare/?cars=toyota-rav4-2019,bmw-m3-g80   (?c= still works: the year pages' Compare buttons use it)
(async () => {
  const root = document.getElementById('cmpx'); if (!root) return;
  let J;
  try { J = await (await fetch('/assets/compare.json?v=1112c')).json(); } catch (e) { root.innerHTML = '<p class="note">Couldn&#39;t load the car list. Refresh to try again.</p>'; return; }
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
      const v = s.slice(k + 1); return [id, v && has(c, v) ? v : String(c.d)];
    }
    return null;
  };
  const qp = new URLSearchParams(location.search);
  let cars = (qp.get('cars') || qp.get('c') || '').split(',').filter(Boolean).map(parse).filter(Boolean).slice(0, MAX);
  const save = () => { const q = cars.map(([i, v]) => `${i}-${v}`).join(','); history.replaceState(null, '', q ? `?cars=${q}` : location.pathname); };
  const word = li => li == null ? ['mid', 'No score'] : li < 50 ? ['good', 'One of the most reliable'] : li < 85 ? ['good', 'Better than average'] : li <= 115 ? ['mid', 'About average'] : li < 200 ? ['bad', 'Worse than average'] : ['bad', 'Lemon alert'];
  const KIND = { car: '', ev: 'Electric', perf: 'Performance', sc: 'Supercar', co: 'Complaints only' };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
  const rng = (a, b, u = '') => a == null ? null : (a === b || b == null ? `${a.toLocaleString()}` : `${a.toLocaleString()}–${b.toLocaleString()}`) + u;
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
  const pick = (c, y) => (y && c.y && c.y[y]) ? y : String(c.d);
  function add(id, v) { if (cars.length >= MAX || cars.some(([i, w]) => i === id && w === v)) return; cars.push([id, v]); save(); draw(true); }
  function search(box) {
    const q = box.querySelector('input'), out = box.querySelector('.cx-sug');
    let hits = [], yy = '';
    const show = () => {
      [hits, yy] = find(q.value);
      out.innerHTML = hits.length ? hits.map((c, n) => `<div class="cx-hit"><b>${esc(c.n)}${KIND[c.k] ? ` <small>${KIND[c.k]}</small>` : ''}</b><select data-n="${n}" aria-label="${c.g ? 'Generation' : 'Model year'} for ${esc(c.n)}">${opts(c).map(([v, l]) => `<option value="${v}"${v === pick(c, yy) ? ' selected' : ''}>${l}</option>`).join('')}</select><button type="button" data-n="${n}">Add</button></div>`).join('')
        : (q.value.trim().length > 1 ? '<p class="cx-none">No match yet. Try the model name, like &ldquo;Camry&rdquo;, &ldquo;Model 3&rdquo; or &ldquo;M3&rdquo;.</p>' : '');
      out.querySelectorAll('button').forEach(b => b.onclick = () => { const c = hits[+b.dataset.n]; add(c.i, out.querySelector(`select[data-n="${b.dataset.n}"]`).value); });
    };
    q.oninput = show;
    q.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); show(); if (hits[0]) { const s0 = out.querySelector('select[data-n="0"]'); add(hits[0].i, s0 ? s0.value : pick(hits[0], yy)); } } };
  }
  function row(c, v) {
    if (c.g) { const g = c.g.find(x => x.id === v) || c.g.at(-1); return { g }; }
    return { v: c.y[v] || [] };
  }
  function draw(focus) {
    const R = cars.map(([i, v]) => ({ c: BY[i], key: v, ...row(BY[i], v) }));
    const anyEV = R.some(r => r.c.ev || (r.v && r.v[9])), anyPerf = R.some(r => r.g), anyCar = R.some(r => r.v);
    // [label, note, value fn -> [text, number for the green check], higher is better?]
    const L = [];
    if (anyCar) L.push(['Lemon Index', '100 = average car, lower is better', r => r.v ? [r.v[0] == null ? '—' : r.v[0] + (r.c.w === 'ev' ? '*' : ''), r.c.w === 'ev' ? null : r.v[0]] : ['—'], false],
                       ['Owner complaints', 'to NHTSA, that year', r => r.v ? [r.v[1] == null ? '—' : r.v[1].toLocaleString(), null] : r.g ? [r.g.nc == null ? '—' : r.g.nc.toLocaleString(), null] : ['—'], false]);
    if (anyPerf && !anyCar) L.push(['Owner complaints', 'to NHTSA, these years (raw count)', r => r.g ? [r.g.nc == null ? '—' : r.g.nc.toLocaleString(), null] : ['—'], false]);
    L.push(['Recalls', 'that model year / generation', r => r.v ? [r.v[2] == null ? '—' : r.v[2], r.v[2]] : r.g ? [r.g.rc, r.g.rc] : ['—'], false]);
    if (anyPerf) L.push(['Horsepower', '', r => r.g ? [r.g.hp ?? '—', r.g.hp] : ['—'], true], ['Torque', 'lb-ft', r => r.g ? [r.g.tq ?? '—', num(r.g.tq)] : ['—'], true],
                        ['0–60 mph', 'seconds', r => r.g ? [r.g.z ?? '—', num(r.g.z)] : ['—'], false], ['Top speed', '', r => r.g ? [r.g.top ?? '—', num(r.g.top)] : ['—'], true],
                        ['Weight', '', r => r.g ? [r.g.wt ?? '—', num(r.g.wt)] : ['—'], false], ['Price new', 'base, when new', r => r.g ? [r.g.p ?? '—', num(r.g.p)] : ['—'], false],
                        ['Engine', '', r => r.g ? [r.g.eu ? `<a href="${esc(r.g.eu)}">${esc(r.g.e)}</a>` : esc(r.g.e || '—'), null] : ['—'], null],
                        ['YouTube owner tone', 'out of 100', r => r.g ? [r.g.yt ?? '—', r.g.yt] : ['—'], true]);
    if (anyCar) {
      L.push([anyEV ? 'MPG / MPGe' : 'Fuel economy', 'combined, EPA', r => { if (!r.v) return ['—']; const ev = r.v[9] || r.c.ev; const s = rng(r.v[3], r.v[4]); return [s ? s + (ev ? ' MPGe' : ' mpg') : '—', ev ? null : r.v[4]]; }, true],
             ['Fuel cost a year', anyEV ? 'gas or electricity, EPA' : 'EPA estimate', r => { if (!r.v) return ['—']; const s = rng(r.v[7], r.v[8]); return [s ? '$' + s.replace('–', '–$') : '—', r.v[7]]; }, false]);
      if (anyEV) L.push(['EV range', 'EPA, miles', r => r.c.ev && r.c.ev.r ? [rng(r.c.ev.r[0], r.c.ev.r[1], ' mi') + (r.c.ev.yr ? ` <small>(${r.c.ev.yr})</small>` : ''), r.c.ev.r[1]] : ['—'], true]);
      L.push(['Crash test', 'NHTSA overall', r => r.v && r.v[5] ? ['<span class="st">' + '★'.repeat(r.v[5]) + '☆'.repeat(5 - r.v[5]) + '</span>', r.v[5]] : ['—'], true],
             ['Top problem', 'most-named in complaints', r => [r.v && r.v[6] ? esc(r.v[6]) : '—', null], null]);
    }
    const best = L.map(([, , f, hi]) => { if (hi == null) return null; const xs = R.map(r => f(r)[1]).filter(x => x != null && x !== 0); if (xs.length < 2 || new Set(xs).size < 2) return null; return hi ? Math.max(...xs) : Math.min(...xs); });
    const scored = R.filter(r => r.v && r.v[0] != null && r.c.w !== 'ev'), win = scored.length >= 2 ? scored.reduce((a, c) => c.v[0] < a.v[0] ? c : a) : null;
    const head = (r, n) => {
      const [cl, w] = r.v ? word(r.v[0]) : ['', KIND[r.c.k]];
      const sel = `<select class="cx-sel" data-k="${n}" aria-label="${r.g ? 'Generation' : 'Model year'}">${opts(r.c).map(([v, l]) => `<option value="${v}"${v === r.key ? ' selected' : ''}>${l}</option>`).join('')}</select>`;
      const href = r.g ? r.c.u : (r.c.u.startsWith('/cars/') && r.c.y[r.key] ? `${r.c.u}${r.key}/` : r.c.u);
      return `<div class="cx-h${win === r ? ' win' : ''}">${win === r ? '<p class="cx-badge">Fewest complaints</p>' : ''}<button class="cx-x" type="button" data-k="${n}" aria-label="Remove ${esc(r.c.n)}">×</button>
<a class="cx-name" href="${esc(href)}">${esc(r.c.n)}</a>${sel}${r.g ? `<p class="cx-v">${esc(r.g.v)}</p>` : `<p class="cx-v ${cl}">${w}</p>`}</div>`;
    };
    const body = L.map(([lab, note, f], n) => `<div class="cx-rl">${lab}${note ? ` <small>${note}</small>` : ''}</div>` + R.map(r => { const [t, x] = f(r); return `<div class="cx-rv${best[n] != null && x === best[n] ? ' w' : ''}${L[n][3] === null ? ' tx' : ''}">${t}</div>`; }).join('')).join('');
    const notes = [];
    if (R.some(r => r.c.w === 'ev')) notes.push('* EV score from the electric-car page: complaints filed by the end of the year after the model year, a shorter window than the main 3-year score, so compare it with other EV scores.');
    R.filter(r => r.c.h).forEach(r => notes.push(`${esc(r.c.n)}: ${esc(r.c.h)}`));
    if (R.some(r => r.g)) notes.push('Performance specs: the generation&#39;s headline trim (see its page for every trim and source). Complaint counts there are raw, not per car sold.');
    const addBox = cars.length < MAX ? `<div class="cx-add"><p><b>${cars.length ? `Add a car <small>(${cars.length} of ${MAX})</small>` : 'Pick up to 4 cars'}</b></p><div class="cx-box"><input type="search" enterkeyhint="go" placeholder="e.g. 2019 RAV4, Model 3, M3, Ioniq 5" aria-label="Find a car to compare" autocomplete="off"><div class="cx-sug"></div></div></div>` : `<p class="cx-full">That&#39;s 4 cars, the most at once. Remove one to add another.</p>`;
    root.innerHTML = (R.length ? `<div class="cx-t" style="--n:${R.length}"><div class="cx-corner"></div>${R.map((r, n) => head(r, n)).join('')}${body}</div>` : '') + addBox
      + (R.length >= 2 ? `<p class="cx-cap">Green check = the best of these cars on that line. ${notes.join(' ')}</p>` : notes.length ? `<p class="cx-cap">${notes.join(' ')}</p>` : '');
    root.querySelectorAll('.cx-x').forEach(x => x.onclick = () => { cars.splice(+x.dataset.k, 1); save(); draw(); });
    root.querySelectorAll('.cx-sel').forEach(s => s.onchange = () => { cars[+s.dataset.k][1] = s.value; save(); draw(); });
    const box = root.querySelector('.cx-add'); if (box) { search(box); if (focus) box.querySelector('input').focus(); }
  }
  draw();
})();

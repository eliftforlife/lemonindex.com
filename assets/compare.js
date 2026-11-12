// Compare any cars (11-02, Elijah: "an easy button on your car to compare it to another one, or add multiple"). Up to 3 cars side by side.
// Data: /assets/cars.json = {id: [name, {year: [index or null, complaints, recalls, mpgLo, mpgHi, stars, topProblem]}]}. URL: /compare/?c=honda-odyssey-2008,toyota-sienna-2008
(async () => {
  const root = document.getElementById('cmpx'); if (!root) return;
  const D = await (await fetch('/assets/cars.json?v=1102')).json();
  const IDS = Object.keys(D), MAX = 3;
  const list = () => (new URLSearchParams(location.search).get('c') || '').split(',').filter(Boolean).map(s => { const m = s.match(/^(.*)-(\d{4})$/); return m && D[m[1]] && D[m[1]][1][m[2]] ? [m[1], m[2]] : null; }).filter(Boolean).slice(0, MAX);
  let cars = list();
  const save = () => { const q = cars.map(([i, y]) => `${i}-${y}`).join(','); history.replaceState(null, '', q ? `?c=${q}` : location.pathname); };
  const word = li => li == null ? ['mid', 'Not enough data'] : li < 50 ? ['good', 'One of the most reliable'] : li < 85 ? ['good', 'Better than average'] : li <= 115 ? ['mid', 'About average'] : li < 200 ? ['bad', 'Worse than average'] : ['bad', 'Lemon alert'];
  const st = n => n ? '★'.repeat(n) + '☆'.repeat(5 - n) : '—';
  function search(box) {
    const q = box.querySelector('input'), out = box.querySelector('.cx-sug');
    q.oninput = () => {
      const s = q.value.toLowerCase(), y = (s.match(/\b(19|20)\d{2}\b/) || [''])[0], w = s.replace(/\b(19|20)\d{2}\b/, ' ').split(/[^a-z0-9]+/).filter(Boolean);
      if (!w.length) { out.innerHTML = ''; return; }
      // 11-12 (testers: "crv", "rouge", "chevy"): the site search's matcher (lookup.js: hyphens, aliases, typos) when it's loaded
      const hits = (window.LQ ? LQ.pick(q.value.replace(/\b(19|20)\d{2}\b/, ' '), IDS, i => D[i][0]) : IDS.filter(i => w.every(x => D[i][0].toLowerCase().split(/[^a-z0-9]+/).some(t => t.startsWith(x))))).slice(0, 6);
      out.innerHTML = hits.map(i => { const ys = Object.keys(D[i][1]); const yy = y && D[i][1][y] ? y : ys.at(-1);
        return `<div class="cx-hit"><b>${D[i][0]}</b><select data-i="${i}">${ys.slice().reverse().map(v => `<option${v === yy ? ' selected' : ''}>${v}</option>`).join('')}</select><button type="button" data-i="${i}">Add</button></div>`; }).join('');
      out.querySelectorAll('button').forEach(b => b.onclick = () => { const sel = out.querySelector(`select[data-i="${b.dataset.i}"]`); cars.push([b.dataset.i, sel.value]); save(); draw(); });
    };
  }
  function draw() {
    const rows = cars.map(([i, y]) => ({ i, y, name: D[i][0], v: D[i][1][y] }));
    const best = (k, low) => { const vals = rows.map(r => r.v[k]).filter(x => x != null && x !== 0); if (vals.length < 2) return null; return low ? Math.min(...vals) : Math.max(...vals); };
    const b = { li: best(0, true), rec: best(2, true), mpg: best(4, false), st: best(5, false) };
    const scored = rows.filter(r => r.v[0] != null), win = scored.length >= 2 ? scored.reduce((a, c) => c.v[0] < a.v[0] ? c : a) : null;
    const card = r => { const [c, w] = word(r.v[0]); const mk = (val, bb) => bb != null && val === bb ? ' w' : '';
      return `<div class="cx-car${win === r ? ' win' : ''}">${win === r ? '<p class="cx-badge">Fewest problems</p>' : ''}<button class="cx-x" type="button" data-k="${r.i}-${r.y}" aria-label="Remove">×</button>
<a class="cx-name" href="/cars/${r.i}/${r.y}/">${r.y} ${r.name}</a><p class="cx-v ${c}">${w}</p>
<dl><dt>Lemon Index</dt><dd class="${mk(r.v[0], b.li)}">${r.v[0] ?? '—'}</dd><dt>Recalls</dt><dd class="${mk(r.v[2], b.rec)}">${r.v[2] ?? '—'}</dd>
<dt>Fuel economy</dt><dd class="${mk(r.v[4], b.mpg)}">${r.v[3] ? (r.v[3] === r.v[4] ? r.v[3] : r.v[3] + '–' + r.v[4]) + ' mpg' : '—'}</dd><dt>Crash test</dt><dd class="${mk(r.v[5], b.st)}">${st(r.v[5])}</dd>
<dt>Top problem</dt><dd>${r.v[6] || '—'}</dd></dl></div>`; };
    root.innerHTML = `<div class="cx-grid n${rows.length + (rows.length < MAX ? 1 : 0)}">${rows.map(card).join('')}${rows.length < MAX ? `<div class="cx-add"><p><b>${rows.length ? 'Add another car' : 'Pick a car'}</b></p><div class="cx-box"><input type="search" placeholder="e.g. 2015 Toyota Camry" aria-label="Find a car"><div class="cx-sug"></div></div></div>` : ''}</div>
${rows.length >= 2 ? '<p class="cx-cap">Lemon Index: 100 = average car, lower = fewer complaints. Green check = better of the cars on that line.</p>' : ''}`;
    root.querySelectorAll('.cx-x').forEach(x => x.onclick = () => { cars = cars.filter(([i, y]) => `${i}-${y}` !== x.dataset.k); save(); draw(); });
    const box = root.querySelector('.cx-add'); if (box) search(box);
  }
  draw();
})();

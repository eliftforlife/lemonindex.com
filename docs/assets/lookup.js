// The car finder (10-29): the first thing on the home page and /cars/. Type a car ("2016 pilot", "civic 2022", "f-150")
// and pick a match, or pick brand, model and year from the lists. Data: <script id="pick"> = {brand: [[name, id, [years]], ...]}.
(() => {
  const el = document.getElementById('pick'); if (!el) return;
  const P = JSON.parse(el.textContent), $ = id => document.getElementById(id);
  const ALL = Object.entries(P).flatMap(([b, ms]) => ms.map(([n, id, ys]) => ({ b, n, id, ys, k: (n + ' ' + b).toLowerCase().replace(/[^a-z0-9 ]/g, ' ') })));
  const go = (id, y) => { location.href = '/cars/' + id + '/' + (y ? y + '/' : ''); };

  // typed search: a 4-digit year anywhere picks the year, the other words have to match the model name
  const q = $('fq'), sug = $('fsug'); let hits = [], cur = -1;
  const find = s => {
    const y = +(s.match(/\b(19|20)\d{2}\b/) || [0])[0], w = s.toLowerCase().replace(/\b(19|20)\d{2}\b/, ' ').replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean);
    if (!w.length) return [];
    return ALL.filter(c => w.every(x => c.k.split(' ').some(t => t.startsWith(x)))).slice(0, 8)
      .map(c => ({ c, y: y && c.ys.includes(y) ? y : 0, miss: y && !c.ys.includes(y) ? y : 0 }));
  };
  const show = () => {
    sug.hidden = !hits.length;
    sug.innerHTML = hits.map((h, i) => `<a role="option" href="/cars/${h.c.id}/${h.y ? h.y + '/' : ''}" class="${i === cur ? 'on' : ''}"><b>${h.y ? h.y + ' ' : ''}${h.c.n}</b><small>${h.y ? 'problems and owner complaints' : h.miss ? `no ${h.miss} in our data · every year ${h.c.ys[0]}-${h.c.ys.at(-1)}` : `every year ${h.c.ys[0]}-${h.c.ys.at(-1)}`}</small></a>`).join('');
  };
  if (q) {
    q.addEventListener('input', () => { hits = find(q.value); cur = hits.length ? 0 : -1; show(); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (hits.length) { cur = (cur + (e.key === 'ArrowDown' ? 1 : -1) + hits.length) % hits.length; show(); } }
      else if (e.key === 'Enter' && hits[cur]) { e.preventDefault(); go(hits[cur].c.id, hits[cur].y); }
      else if (e.key === 'Escape') { sug.hidden = true; }
    });
    document.addEventListener('click', e => { if (!e.target.closest('.fq')) sug.hidden = true; });
    q.addEventListener('focus', () => { if (hits.length) sug.hidden = false; });
  }

  // or pick from the lists
  const b = $('lb'), m = $('lm'), y = $('ly'), g = $('lgo'); if (!b) return;
  const opt = (s, l, ph) => { s.innerHTML = `<option value="">${ph}</option>` + l.map(([v, t]) => `<option value="${v}">${t}</option>`).join(''); s.disabled = !l.length; };
  opt(b, Object.keys(P).map(k => [k, k]), 'Brand');
  b.onchange = () => { opt(m, (P[b.value] || []).map(([n, i]) => [i, n]), 'Model'); opt(y, [], 'Year'); g.disabled = true; };
  m.onchange = () => { const r = (P[b.value] || []).find(x => x[1] === m.value); opt(y, r ? r[2].slice().reverse().map(v => [v, v]) : [], 'Year (optional)'); g.disabled = !m.value; };
  y.onchange = () => { if (m.value && y.value) go(m.value, y.value); };
  g.onclick = () => { if (m.value) go(m.value, y.value); };
})();

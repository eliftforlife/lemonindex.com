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
    // 11-02 (Elijah types the year first): a year alone lists the brands that have it; year + brand lists that brand's models
    if (!w.length) return y ? Object.keys(P).filter(br => P[br].some(m => m[2].includes(y))).map(br => ({ brand: br, y })) : [];
    const brands = Object.keys(P).filter(br => br.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(' ').some(t => t.startsWith(w[0])));
    const order = c => (c.ys.includes(y) ? 0 : 1) + (brands.includes(c.b) ? 0 : 2);
    return ALL.filter(c => w.every(x => c.k.split(' ').some(t => t.startsWith(x)))).sort((p1, p2) => order(p1) - order(p2) || p1.n.localeCompare(p2.n)).slice(0, y ? 12 : 8)
      .map(c => ({ c, y: y && c.ys.includes(y) ? y : 0, miss: y && !c.ys.includes(y) ? y : 0 }));
  };
  const show = () => {
    sug.hidden = !hits.length;
    if (hits.length && hits[0].brand) { sug.innerHTML = `<p class="fhint">${hits[0].y}: pick the brand</p><div class="fbr">` + hits.map((h, i) => `<button type="button" data-b="${h.brand}" class="${i === cur ? 'on' : ''}">${h.brand}</button>`).join('') + '</div>';
      sug.querySelectorAll('[data-b]').forEach(x => x.onclick = () => { q.value = `${hits[0].y} ${x.dataset.b} `; q.focus(); hits = find(q.value); cur = hits.length ? 0 : -1; show(); }); return; }
    sug.innerHTML = hits.map((h, i) => `<a role="option" href="/cars/${h.c.id}/${h.y ? h.y + '/' : ''}" class="${i === cur ? 'on' : ''}"><b>${h.y ? h.y + ' ' : ''}${h.c.n}</b><small>${h.y ? 'problems and owner complaints' : h.miss ? `no ${h.miss} in our data · every year ${h.c.ys[0]}-${h.c.ys.at(-1)}` : `every year ${h.c.ys[0]}-${h.c.ys.at(-1)}`}</small></a>`).join('');
  };
  if (q) {
    q.addEventListener('input', () => { hits = find(q.value); cur = hits.length ? 0 : -1; show(); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (hits.length) { cur = (cur + (e.key === 'ArrowDown' ? 1 : -1) + hits.length) % hits.length; show(); } }
      else if (e.key === 'Enter' && hits[cur]) { e.preventDefault(); if (hits[cur].brand) { q.value = `${hits[cur].y} ${hits[cur].brand} `; hits = find(q.value); cur = hits.length ? 0 : -1; show(); } else go(hits[cur].c.id, hits[cur].y); }
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

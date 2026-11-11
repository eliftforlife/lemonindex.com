// The car finder (10-29): the first thing on the home page and /cars/. Type a car ("2016 pilot", "civic 2022", "f-150")
// and pick a match, or pick brand, model and year from the lists. Data: <script id="pick"> = {brand: [[name, id, [years]], ...]}.
(() => {
  const el = document.getElementById('pick'); if (!el) return;
  const P = JSON.parse(el.textContent), $ = id => document.getElementById(id);
  const lookForm = $('look'); if (lookForm) lookForm.addEventListener('submit', e => e.preventDefault());   // was an inline onsubmit (blocked by the CSP)
  // 11-02: the names people actually type ("f150", "ram 1500") for families named after the whole line
  const AK = { 'ford-f-series': ' f150 150 f250 250 f350 350 super duty', 'ram-pickup': ' 1500 2500 3500', 'chevrolet-silverado': ' 1500 2500 3500', 'gmc-sierra': ' 1500 2500 3500' };
  const ALL = Object.entries(P).flatMap(([b, ms]) => ms.map(([n, id, ys]) => ({ b, n, id, ys, k: (n + ' ' + b).toLowerCase().replace(/[^a-z0-9 ]/g, ' ') + (AK[id] || '') })));
  const go = (id, y) => { location.href = '/cars/' + id + '/' + (y ? y + '/' : ''); };

  // 11-11 (Elijah: "the buttons underneath should come in when you click the look-up box"): Brand / Model / Year / Show problems stay
  // folded (inert, not tabbable) until the box is focused, tapped or typed in; then they slide in and stay. Without JS they simply show.
  const box = $('fq'), form = $('look');
  if (box && form) {
    const open = () => { if (!form.classList.contains('fo-closed')) return; form.classList.remove('fo-closed'); form.inert = false; form.removeAttribute('aria-hidden'); box.setAttribute('aria-expanded', 'true'); };
    form.classList.add('fo-closed'); form.inert = true; form.setAttribute('aria-hidden', 'true');
    box.setAttribute('aria-controls', 'look'); box.setAttribute('aria-expanded', 'false');
    ['focus', 'pointerdown', 'input'].forEach(ev => box.addEventListener(ev, open));
  }
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
  const miss = t => { const el = document.querySelector('.fmiss'); if (el) el.textContent = t; };
  const submit = () => {   // Enter or Show problems with text in the box: go to the highlighted match (or the top one)
    hits = find(q.value); const h = hits[cur >= 0 && cur < hits.length ? cur : 0];
    if (!h) { miss("No match. Try 'Honda Civic 2016'."); return false; }
    if (h.brand) { miss(`Add the brand and model, e.g. '${h.y} Honda Civic'.`); show(); return false; }
    go(h.c.id, h.y); return true;
  };
  if (q) {
    q.addEventListener('input', () => { hits = find(q.value); cur = hits.length ? 0 : -1; show(); miss(q.value.trim() && !hits.length ? "No match. Try 'Honda Civic 2016'." : ''); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (hits.length) { cur = (cur + (e.key === 'ArrowDown' ? 1 : -1) + hits.length) % hits.length; show(); } }
      else if (e.key === 'Enter') { e.preventDefault(); if (hits[cur] && hits[cur].brand) { q.value = `${hits[cur].y} ${hits[cur].brand} `; hits = find(q.value); cur = hits.length ? 0 : -1; show(); } else if (q.value.trim()) submit(); }
      else if (e.key === 'Escape') { sug.hidden = true; }
    });
    document.addEventListener('click', e => { if (!e.target.closest('.fq')) sug.hidden = true; });
    q.addEventListener('focus', () => { if (hits.length) sug.hidden = false; });
  }

  // or pick from the lists
  // 11-10 (Elijah: "the Show problems button doesn't work"): the button now follows the typed search first (its top match), then the
  // lists; picking a year no longer jumps away on its own, so the button is the one way to go. No target -> a short hint, never a dead button.
  const b = $('lb'), m = $('lm'), y = $('ly'), g = $('lgo'); if (!b) return;
  const tip = document.createElement('p'); tip.className = 'fmiss'; tip.setAttribute('role', 'status'); tip.setAttribute('aria-live', 'polite');
  (lookForm || g).after(tip);
  const say = t => { tip.textContent = t || ''; };
  const opt = (s, l, ph) => { s.innerHTML = `<option value="">${ph}</option>` + l.map(([v, t]) => `<option value="${v}">${t}</option>`).join(''); s.disabled = !l.length; };
  opt(b, Object.keys(P).map(k => [k, k]), 'Brand');
  b.onchange = () => { opt(m, (P[b.value] || []).map(([n, i]) => [i, n]), 'Model'); opt(y, [], 'Year'); say(''); };
  m.onchange = () => { const r = (P[b.value] || []).find(x => x[1] === m.value); opt(y, r ? r[2].slice().reverse().map(v => [v, v]) : [], 'Year (optional)'); say(''); };
  y.onchange = () => say('');
  g.disabled = false;
  g.onclick = () => {
    if (q && q.value.trim()) { if (!submit()) q.focus(); return; }
    if (m.value) return go(m.value, y.value);
    say(b.value ? 'Pick a model, then press Show problems.' : 'Type a car above, or pick a brand and model.');
  };
})();

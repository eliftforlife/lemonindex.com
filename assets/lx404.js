// 11-13 navigation test (N1, problem 10: "/cars/ford-f-150/, /cars/honda/, /cars/subaru-wrx/2016/ and reversed compare URLs all 404,
// and the 404 page has no search"): the address that wasn't found becomes a search (the site's own matcher, assets/lookup.js window.LQ).
// One clear match opens on its own; otherwise the top 3 show under an open search box. Runs only on 404.html (build.py).
(() => {
  const LQ = window.LQ, box = document.getElementById('lxq'), top = document.getElementById('lxtop'), sub = document.getElementById('lxsub');
  if (!LQ || !LQ.find || !box) return;
  let p = location.pathname;
  try { p = decodeURIComponent(p); } catch (e) { /* keep it as typed */ }
  const SKIP = new Set(['cars', 'car', 'brands', 'brand', 'make', 'makes', 'compare', 'electric', 'supercars', 'engines', 'engine', 'best', 'motorcycles',
    'planes', 'advanced', 'check-engine-light', 'index', 'index.html', 'amp', 'models', 'model', 'reviews', 'review', 'reliability']);
  const parts = p.replace(/\.(html?|php|aspx?)$/i, '').split('/').filter(Boolean).filter(x => !SKIP.has(x.toLowerCase()));
  const q = parts.join(' ').replace(/-vs-/gi, ' vs ').replace(/[-_+.]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 80);
  if (!q) return;
  box.value = q;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const here = location.pathname.replace(/\/?$/, '/');
  (LQ.load ? LQ.load() : Promise.resolve()).then(() => {
    const r = LQ.find(q) || {}, items = (r.items || []).filter(h => h.u && h.u.replace(/[#?].*$/, '') !== here).slice(0, 3);
    if (!items.length) return;
    if (r.strong && !r.hint) {   // one clear match: go there (replace, so Back doesn't land on the 404 again)
      if (sub) sub.innerHTML = `Taking you to <a href="${esc(items[0].u)}">${esc(items[0].b)}</a>…`;
      location.replace(items[0].u); return;
    }
    if (!top) return;
    const sg = document.getElementById('lxqs'); if (sg) sg.hidden = true;   // the box's own list opens again when it's tapped or typed in
    top.innerHTML = `<h2>${r.pop ? 'Popular cars' : r.hint ? 'Closest matches' : 'Did you mean'}</h2>` + items.map(h => `<a href="${esc(h.u)}"><b>${esc(h.b)}</b><small>${esc(h.s || '')}</small></a>`).join('');
    top.hidden = false;
  });
})();

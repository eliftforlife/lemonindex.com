// 11-12 (Elijah: "an engine page that says all engines, you can search ..."): /engines/.
// 11-24 v6 (Elijah: "each one has its own card ... so people just click into it and get that category"): big kind-of-engine cards
// (all_engines.py, nav.ae6). A card opens that kind's panel (section.ae6-pn) in place of the cards, with a back link; the address becomes
// /engines/?type=<kind> (shareable, the back button returns to the cards). Every engine card is in the HTML (what search engines read).
// The search box keeps the cards whose name, code, layout or cars start with every typed word ("honda k20", "ls3", "camry"), shows every
// engine panel that has a match and hides the kind cards; an engine listed in two kinds shows once.
(() => {
  const g = document.getElementById('aegrid'), q = document.getElementById('aeq'), cnt = document.getElementById('aen'); if (!g || !q) return;
  const nav = g.querySelector('.ae6'), pans = [...g.querySelectorAll('.ae6-pn')];
  const fold = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9.]+/g, ' ').replace(/ \./g, ' ').trim();
  // 11-12 round 2 (fix C): data-yr "2003–07" -> [2003, 2007], so a typed year ("2017 f250") keeps only the engines built that year
  const span = t => { const m = String(t || '').match(/(\d{4})(?:\D+(\d{2,4}))?/); if (!m) return null; const a = +m[1]; let b = m[2] ? +m[2] : a; if (b < 100) b += Math.floor(a / 100) * 100; return [a, b]; };
  const cards = [...g.querySelectorAll('.aec')].map(el => ({ el, href: el.getAttribute('href') || '', k: (el.dataset.k || '').split(' '), yr: span(el.dataset.yr) }));
  const has = k => pans.some(p => p.dataset.type === k);
  let cur = 'all';
  const view = k => {   // no search: the kind cards, or one kind's panel
    cur = has(k) ? k : 'all';
    if (nav) nav.hidden = cur !== 'all';
    pans.forEach(p => { p.hidden = p.dataset.type !== cur; });
  };
  const run = () => {
    // "ram 2500 vs f250": either side; a 4-digit year filters by the years the engine was built
    const raw = fold(q.value), ym = raw.match(/\b(19|20)\d{2}\b/), yy = ym ? +ym[0] : 0;
    const sides = raw.replace(/\b(19|20)\d{2}\b/g, ' ').split(/\s(?:vs|versus|or|v)\s/).map(x => x.split(' ').filter(Boolean)).filter(x => x.length);
    const on = !!(sides.length || yy), seen = new Set(); let n = 0;
    g.classList.toggle('ae6-q', on);
    cards.forEach(c => {
      let show = true;
      if (on) {
        show = (!sides.length || sides.some(ws => ws.every(x => c.k.some(k => k.startsWith(x))))) && (!yy || !c.yr || (c.yr[0] <= yy && yy <= c.yr[1])) && !seen.has(c.href);
        if (show) { seen.add(c.href); n++; }
      }
      c.el.hidden = !show;
    });
    if (on) {
      if (nav) nav.hidden = true;
      pans.forEach(p => { p.hidden = !p.querySelector('.aec:not([hidden])'); });
    } else view(cur);
    g.querySelector('.aenone').hidden = !on || n > 0;
    cnt.innerHTML = on ? `<b>${n}</b> engine${n === 1 ? '' : 's'} match` : '';
  };
  const fromUrl = () => new URLSearchParams(location.search).get('type') || 'all';
  const smooth = () => matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
  g.addEventListener('click', e => {
    const a = e.target.closest('a[data-type]'); if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    const k = a.dataset.type; if (k !== 'all' && !has(k)) return;   // a card with its own page (Head-to-head) opens as a normal link
    e.preventDefault();
    q.value = '';
    view(k); run();
    history.pushState(null, '', k === 'all' ? location.pathname : location.pathname + '?type=' + k);
    g.scrollIntoView({ block: 'start', behavior: smooth() });
  });
  window.addEventListener('popstate', () => { view(fromUrl()); run(); });
  q.addEventListener('input', run);
  // 11-12 round 2 (Liam, Mitch: "Enter does nothing"): Enter opens the first engine shown
  q.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return; e.preventDefault();
    const c = cards.find(x => !x.el.hidden && !x.el.closest('.ae6-pn').hidden && x.el.href); if (c) location.href = c.el.href;
  });
  const p = new URLSearchParams(location.search);
  view(fromUrl());
  if (p.get('q')) q.value = p.get('q');
  run();
  if (cur !== 'all' && !p.get('q')) requestAnimationFrame(() => g.scrollIntoView({ block: 'start' }));
})();

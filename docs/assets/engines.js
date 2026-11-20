// 11-12 (Elijah: "an engine page that says all engines, you can search ..."): /engines/.
// 11-19 v5: no tabs any more. One tap-to-open box per kind of engine (all_engines.py AE_CATS); every card is in the HTML (what search engines
// read). The search box keeps the cards whose name, code, layout or cars start with every typed word ("honda k20", "ls3", "camry"), opens
// the boxes that have a match and hides the rest; an engine listed in two boxes shows once. /engines/?type=bmw opens that box.
(() => {
  const g = document.getElementById('aegrid'), q = document.getElementById('aeq'), cnt = document.getElementById('aen'); if (!g || !q) return;
  const fold = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9.]+/g, ' ').replace(/ \./g, ' ').trim();
  // 11-12 round 2 (fix C): data-yr "2003–07" -> [2003, 2007], so a typed year ("2017 f250") keeps only the engines built that year
  const span = t => { const m = String(t || '').match(/(\d{4})(?:\D+(\d{2,4}))?/); if (!m) return null; const a = +m[1]; let b = m[2] ? +m[2] : a; if (b < 100) b += Math.floor(a / 100) * 100; return [a, b]; };
  const cards = [...g.querySelectorAll('.aec')].map(el => ({ el, href: el.getAttribute('href') || '', k: (el.dataset.k || '').split(' '), yr: span(el.dataset.yr) }));
  const boxes = [...g.querySelectorAll('details.ae5-c')], auto = new Set();
  const run = () => {
    // "ram 2500 vs f250": either side; a 4-digit year filters by the years the engine was built
    const raw = fold(q.value), ym = raw.match(/\b(19|20)\d{2}\b/), yy = ym ? +ym[0] : 0;
    const sides = raw.replace(/\b(19|20)\d{2}\b/g, ' ').split(/\s(?:vs|versus|or|v)\s/).map(x => x.split(' ').filter(Boolean)).filter(x => x.length);
    const on = !!(sides.length || yy), seen = new Set(); let n = 0;
    cards.forEach(c => {
      let show = true;
      if (on) {
        show = (!sides.length || sides.some(ws => ws.every(x => c.k.some(k => k.startsWith(x))))) && (!yy || !c.yr || (c.yr[0] <= yy && yy <= c.yr[1])) && !seen.has(c.href);
        if (show) { seen.add(c.href); n++; }
      }
      c.el.hidden = !show;
    });
    boxes.forEach(d => {
      const has = !on || !!d.querySelector('.aec:not([hidden])');
      d.parentElement.hidden = !has;
      if (on && has && !d.open) { d.open = true; auto.add(d); }
      if (!on && auto.has(d)) { d.open = false; auto.delete(d); }
    });
    g.querySelector('.aenone').hidden = !on || n > 0;
    cnt.innerHTML = on ? `<b>${n}</b> engine${n === 1 ? '' : 's'} match` : '';
  };
  q.addEventListener('input', run);
  // 11-12 round 2 (Liam, Mitch: "Enter does nothing"): Enter opens the first engine shown
  q.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return; e.preventDefault();
    const c = cards.find(x => !x.el.hidden && x.el.closest('details')?.open && x.el.href); if (c) location.href = c.el.href;
  });
  const p = new URLSearchParams(location.search), t = p.get('type');
  if (t) { const d = boxes.find(b => b.dataset.type === t); if (d) d.open = true; }
  if (p.get('q')) q.value = p.get('q');
  run();
})();

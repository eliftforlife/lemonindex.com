// 11-12 (Elijah: "an engine page that says all engines, you can search, and it has the selectors like the All cars page"): /engines/.
// Every card is in the HTML (what search engines read); the tabs only hide the others and set /engines/?type=<tab>, and the search box
// keeps the cards whose name, code, layout or cars start with every typed word ("honda k20", "ls3", "camry").
(() => {
  const g = document.getElementById('aegrid'), q = document.getElementById('aeq'), cnt = document.getElementById('aen'); if (!g || !q) return;
  const T = { all: '', bmw: 'b', supercars: 's', performance: 'p', honda: 'h', soon: 'c' };
  const fold = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9.]+/g, ' ').replace(/ \./g, ' ').trim();
  const cards = [...g.querySelectorAll('.aec')].map(el => ({ el, f: el.dataset.f || 'gas', t: (el.dataset.t || '').split(' '), k: el.dataset.k.split(' '), soon: el.classList.contains('aec-soon') }));
  const N = cards.filter(c => !c.soon).length, S = cards.length - N;
  let tab = 'all', fuel = 'all';   // 11-12: + the fuel selector (?fuel=gas|diesel|hybrid|electric), combined with the tab
  const run = push => {
    const t = T[tab], w = fold(q.value).split(' ').filter(Boolean); let n = 0, s = 0;
    cards.forEach(c => { const on = (!t || c.t.includes(t)) && (fuel === 'all' || c.f === fuel) && w.every(x => c.k.some(k => k.startsWith(x))); c.el.hidden = !on; if (on) c.soon ? s++ : n++; });
    g.querySelectorAll('.aes').forEach(sec => { sec.hidden = !sec.querySelector('.aec:not([hidden])'); });
    g.querySelector('.aenone').hidden = n + s > 0;
    g.querySelectorAll('.aetabs a[data-type]').forEach(a => { if (a.dataset.type === tab) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    g.querySelectorAll('.aefuel a[data-fuel]').forEach(a => { if (a.dataset.fuel === fuel) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    const parts = (w.length || t || fuel !== 'all') ? [n ? `<b>${n}</b> engine${n === 1 ? '' : 's'}` : '', s ? `<b>${s}</b> coming soon` : ''].filter(Boolean) : [`<b>${N}</b> engines`, `<b>${S}</b> coming soon`];
    cnt.innerHTML = (parts.join(' · ') || '<b>0</b> engines') + (w.length ? ' match' : '');
    if (push) { const u = new URLSearchParams(); if (tab !== 'all') u.set('type', tab); if (fuel !== 'all') u.set('fuel', fuel); history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u : '')); }
  };
  g.querySelector('.aetabs').addEventListener('click', e => {
    const a = e.target.closest('a[data-type]'); if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault(); tab = a.dataset.type in T ? a.dataset.type : 'all'; run(true);
  });
  const F = ['all', 'gas', 'diesel', 'hybrid', 'electric'];
  g.querySelector('.aefuel')?.addEventListener('click', e => {
    const a = e.target.closest('a[data-fuel]'); if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault(); fuel = F.includes(a.dataset.fuel) ? a.dataset.fuel : 'all'; run(true);
  });
  q.addEventListener('input', () => { const had = tab !== 'all' || fuel !== 'all'; if (q.value.trim()) { tab = 'all'; fuel = 'all'; } run(had); });   // search covers every tab, like the home search
  // 11-12 round 2 (Liam, Mitch: "Enter does nothing"): Enter opens the first engine shown (a coming-soon one opens its vote sheet)
  q.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return; e.preventDefault();
    const c = cards.find(x => !x.el.hidden && !x.soon) || cards.find(x => !x.el.hidden); if (!c) return;
    if (c.soon) c.el.click(); else if (c.el.href) location.href = c.el.href;
  });
  const p = new URLSearchParams(location.search); tab = (p.get('type') || 'all') in T ? (p.get('type') || 'all') : 'all';
  if (p.get('q')) q.value = p.get('q');
  fuel = F.includes(p.get('fuel')) ? p.get('fuel') : 'all';
  run(false);
})();

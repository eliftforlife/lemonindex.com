// 11-11 (Elijah: one Cars section): the All cars / Performance / Supercars / Electric tabs on /cars/. The page's HTML has every card (the All
// view, what search engines read); a tab only hides the others, and the address becomes /cars/?type=<tab> so the view can be shared.
(() => {
  const nav = document.querySelector('.ctabs'), grid = document.querySelector('.cgrid'); if (!nav || !grid) return;
  const T = { all: '', performance: 'p', supercars: 's', electric: 'e' };
  const set = (k, push) => {
    if (!(k in T)) k = 'all';
    const t = T[k]; grid.dataset.tab = k;
    nav.querySelectorAll('a[data-type]').forEach(a => { if (a.dataset.type === k) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    grid.querySelectorAll('.mb').forEach(mb => {
      let n = 0;
      mb.querySelectorAll('.mc').forEach(c => { const on = t ? (c.dataset.t || '').split(' ').includes(t) : !c.classList.contains('mc-dup'); c.hidden = !on; if (on) n++; });
      mb.hidden = !n;
    });
    grid.querySelectorAll('.ctn[data-for]').forEach(p => { p.hidden = p.dataset.for !== k; });
    grid.querySelectorAll('[data-hide]').forEach(x => { x.hidden = !!t && x.dataset.hide.split(' ').includes(t); });
    const soon = grid.querySelector('.mb-soon'); if (soon) soon.hidden = !!t;
    if (push) history.replaceState(null, '', k === 'all' ? location.pathname : location.pathname + '?type=' + k);
  };
  nav.addEventListener('click', e => {
    const a = e.target.closest('a[data-type]'); if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault(); set(a.dataset.type, true);
  });
  set(new URLSearchParams(location.search).get('type') || location.hash.slice(1) || 'all', false);
})();

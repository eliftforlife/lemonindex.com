// 11-11 (Elijah: one Cars section): the All cars / Performance / Supercars / Electric tabs on /cars/. The page's HTML has every card (the All
// view, what search engines read); a tab only hides the others, and the address becomes /cars/?type=<tab> so the view can be shared.
// 11-13 (nav review #6): body-type tabs too (Trucks / SUVs / Cars / Minivans). A card's data-t carries its body type (tk sv cr mv) next to
// its kind (r s e p); the body tabs skip the Electric-tab twins (mc-dup) and the gray "No data yet" cards.
(() => {
  const nav = document.querySelector('.ctabs'), grid = document.querySelector('.cgrid'); if (!nav || !grid) return;
  const T = { all: '', trucks: 'tk', suvs: 'sv', cars: 'cr', minivans: 'mv', performance: 'p', supercars: 's', electric: 'e' };
  const BODY = { tk: 1, sv: 1, cr: 1, mv: 1 };
  const set = (k, push) => {
    if (!(k in T)) k = 'all';
    const t = T[k]; grid.dataset.tab = k;
    nav.querySelectorAll('a[data-type]').forEach(a => { if (a.dataset.type === k) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    grid.querySelectorAll('.mb').forEach(mb => {
      let n = 0;
      mb.querySelectorAll('.mc').forEach(c => {
        const tags = (c.dataset.t || '').split(' '), dup = c.classList.contains('mc-dup');
        const on = !t ? !dup : BODY[t] ? tags.includes(t) && !dup && !c.classList.contains('mc-nd') : tags.includes(t);
        c.hidden = !on; if (on) n++;
      });
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
  const k0 = new URLSearchParams(location.search).get('type') || location.hash.slice(1) || 'all';
  set(k0, false);
  // 11-13: a shared tab link (the menu's Trucks, Electric, Supercars) opens at the tabs, not at the search box above them
  if (k0 in T && k0 !== 'all' && !location.hash) requestAnimationFrame(() => nav.scrollIntoView({ block: 'start' }));
})();

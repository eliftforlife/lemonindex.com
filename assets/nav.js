// (11-05: the header code moved to gh.js)
// score dials (11-03): the needle swings in when the dial scrolls into view
(() => { const g = document.querySelectorAll('[data-gauge]'); if (!g.length) return;
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return g.forEach(e => e.classList.add('in'));
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .4 }); g.forEach(e => io.observe(e)); })();
// car pages (11-03 v4): the small explainer under a section moves behind an ⓘ button next to its heading. Intros that end with ':' and
// lines carrying data (stars, links that are the whole line) stay visible.
(() => {
  document.querySelectorAll('.yc').forEach(sec => {
    const h = sec.querySelector(':scope > h2'); if (!h) return;
    const caps = [...sec.querySelectorAll(':scope > .yc-cap')].filter(c => { const t = c.textContent.trim(), a = c.querySelectorAll('a');
      return !t.endsWith(':') && !c.querySelector('.stars') && !(a.length === 1 && a[0].textContent.trim() === t); });
    if (!caps.length) return;
    const b = document.createElement('button'); b.type = 'button'; b.className = 'info'; b.setAttribute('aria-expanded', 'false'); b.setAttribute('aria-label', 'What this means'); b.textContent = 'i';
    const box = document.createElement('div'); box.className = 'info-box'; box.hidden = true; caps.forEach(c => box.appendChild(c));
    const sub = h.querySelector('.h2s'); sub ? h.insertBefore(b, sub) : h.appendChild(b); h.after(box);   // next to the title, not under the gray line
    b.addEventListener('click', () => { const open = box.hidden; box.hidden = !open; b.setAttribute('aria-expanded', String(open)); });
  });
})();
// 11-14 growth plan 4d: saved cars ("My cars", browser storage only): the Save buttons, the header count and the /saved/ page
(() => { if (document.querySelector('script[src^="/assets/saved.js"]')) return;
  const s = document.createElement('script'); s.src = '/assets/saved.js?v=4'; s.defer = true; document.head.appendChild(s); })();
// 11-19 (Elijah: Electric goes under Cars): the desktop bar's Cars dropdown (build.py NAV_CARS). Click opens it; outside click, Esc,
// the More button or a link close it. Hidden below 1024 px with the rest of the bar (the phone menu lists the same pages).
(() => { const d = document.querySelector('.gh-dd'); if (!d) return; const b = d.querySelector('.gh-ddb');
  const set = o => { d.classList.toggle('open', o); b.setAttribute('aria-expanded', String(o)); };
  b.addEventListener('click', e => { e.stopPropagation(); set(!d.classList.contains('open')); });
  document.addEventListener('click', e => { if (d.classList.contains('open') && !d.contains(e.target)) set(false); }, true);
  addEventListener('keydown', e => { if (e.key === 'Escape' && d.classList.contains('open')) { set(false); b.focus(); } }); })();
// 11-24 category menu (build.py gh_header .mn): a category row shows its pages in the same panel; '< Menu' goes back; closing resets it.
(() => { const m = document.querySelector('.gh-sheet .mn'); if (!m) return; const sh = m.closest('.gh-sheet'), h = m.closest('.gh');
  const show = k => { m.classList.remove('back'); m.classList.toggle('sub', !!k); sh.classList.toggle('mn-sub', !!k);
    m.querySelectorAll('.mn-p').forEach(p => p.classList.toggle('on', p.dataset.c === k));
    m.querySelectorAll('.mn-c').forEach(b => b.setAttribute('aria-expanded', String(b.dataset.c === k)));
    sh.scrollTop = 0; };
  m.querySelectorAll('.mn-c').forEach(b => b.addEventListener('click', e => { e.stopPropagation(); show(b.dataset.c);
    const f = m.querySelector('.mn-p.on .mn-bk'); if (f) f.focus({ preventScroll: true }); }));
  m.querySelectorAll('.mn-bk').forEach(b => b.addEventListener('click', e => { e.stopPropagation(); const k = m.querySelector('.mn-p.on');
    show(''); m.classList.add('back'); const r = k && m.querySelector(`.mn-c[data-c="${k.dataset.c}"]`); if (r) r.focus({ preventScroll: true }); }));
  new MutationObserver(() => { if (!h.classList.contains('open')) { show(''); m.classList.remove('back'); } }).observe(h, { attributes: true, attributeFilter: ['class'] });
})();

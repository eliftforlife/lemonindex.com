// Top navigation on phones (11-03): keep the current page's chip in view, and tuck the header away while scrolling down
// (it comes back as soon as you scroll up, or near the top of the page).
(() => {
  const top = document.querySelector('.top'), nav = document.querySelector('.mainnav'); if (!top) return;
  const on = nav && nav.querySelector('.on'); if (on && nav.scrollWidth > nav.clientWidth) nav.scrollLeft = on.offsetLeft - 16;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let last = scrollY, tick = false;
  addEventListener('scroll', () => { if (tick) return; tick = true; requestAnimationFrame(() => {
    const y = scrollY, d = y - last; if (Math.abs(d) > 6) { top.classList.toggle('tuck', d > 0 && y > 140 && !top.contains(document.activeElement)); last = y; } tick = false; }); }, { passive: true });
})();
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

// 11-10 /images/: each group shows its first N cards (data-cap) with a "Show all" button; the search box filters every card on the page.
(() => {
  const grids = [...document.querySelectorAll('.imggrid[data-cap]')], q = document.querySelector('.imgq'), none = document.querySelector('.imgnone');
  const capOf = g => +g.dataset.cap || 24;
  const apply = () => {
    const t = (q && q.value || '').trim().toLowerCase(); let shown = 0;
    grids.forEach(g => {
      const cards = [...g.children], open = g.dataset.open === '1'; let n = 0, hits = 0;
      cards.forEach(c => { const hit = !t || c.textContent.toLowerCase().includes(t); if (hit) hits++; const on = hit && (t || open || n < capOf(g)); if (hit) n++; c.hidden = !on; if (on) shown++; });
      const sec = g.closest('section'); if (sec) sec.hidden = !!t && !hits;
      let b = g.nextElementSibling && g.nextElementSibling.classList.contains('imgmore') ? g.nextElementSibling : null;
      const more = !t && !open && cards.length > capOf(g);
      if (more && !b) { b = document.createElement('button'); b.type = 'button'; b.className = 'imgmore'; b.addEventListener('click', () => { g.dataset.open = '1'; apply(); }); g.after(b); }
      if (b) { b.hidden = !more; b.textContent = `Show all ${cards.length}`; }
    });
    if (none) none.hidden = !t || shown > 0;
  };
  if (q) q.addEventListener('input', apply);
  apply();
})();

// 11-10: filter a grid of cards by text. Markup: <input data-filter="#grid"> + <div id="grid"> cards </div> + optional <p class="cf-none" hidden>.
(() => { document.querySelectorAll('input[data-filter]').forEach(q => {
  const g = document.querySelector(q.dataset.filter); if (!g) return; const none = g.parentElement.querySelector('.cf-none');
  q.addEventListener('input', () => { const t = q.value.trim().toLowerCase(); let n = 0;
    [...g.children].forEach(c => { const on = !t || c.textContent.toLowerCase().includes(t); c.hidden = !on; if (on) n++; });
    if (none) none.hidden = n > 0; });
}); })();

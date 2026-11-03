// /data/ page (11-03): copy buttons for the credit lines (falls back to selecting the text when the clipboard is blocked).
document.addEventListener('click', e => {
  const b = e.target.closest('.cpy-b'); if (!b) return;
  const done = () => { const t = b.textContent; b.textContent = 'Copied'; setTimeout(() => (b.textContent = t), 1600); };
  const sel = () => { const c = b.parentElement.querySelector('code'); const r = document.createRange(); r.selectNodeContents(c); const s = getSelection(); s.removeAllRanges(); s.addRange(r); };
  if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.copy).then(done, sel); else sel();
});

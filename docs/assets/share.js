// "Share this car" (11-03, Elijah: let people send a car to a friend). Phones: the native share sheet (Messages, WhatsApp, IG DMs...).
// Elsewhere: a small panel with copy link, text, WhatsApp, Facebook, X, Reddit and email. Links carry ?utm_source=share so shares show in analytics.
(() => {
  const btns = document.querySelectorAll('[data-share]'); if (!btns.length) return;
  const url = () => { const u = new URL(location.href); u.search = ''; u.hash = ''; u.searchParams.set('utm_source', 'share'); return u.toString(); };
  const enc = encodeURIComponent;
  let panel;
  const close = () => { if (panel) panel.hidden = true; };
  const open = (text) => {
    const u = url(), msg = `${text} ${u}`;
    if (!panel) { panel = document.createElement('div'); panel.className = 'shr'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'Share'); document.body.appendChild(panel);
      panel.addEventListener('click', e => { if (e.target === panel) close(); }); document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); }); }
    const L = [['Text message', `sms:?&body=${enc(msg)}`], ['WhatsApp', `https://wa.me/?text=${enc(msg)}`], ['Facebook', `https://www.facebook.com/sharer/sharer.php?u=${enc(u)}`],
      ['X', `https://x.com/intent/post?text=${enc(text)}&url=${enc(u)}`], ['Reddit', `https://www.reddit.com/submit?url=${enc(u)}&title=${enc(text)}`], ['Email', `mailto:?subject=${enc(text)}&body=${enc(msg)}`]];
    panel.innerHTML = `<div class="shr-card"><button class="shr-x" aria-label="Close">×</button><p class="shr-h">Send this to a friend</p><p class="shr-t">${text.replace(/[<>&]/g, '')}</p>
<button class="btn shr-copy" type="button">Copy link</button><div class="shr-l">${L.map(([n, h]) => `<a href="${h}" target="_blank" rel="noopener">${n}</a>`).join('')}</div></div>`;
    panel.querySelector('.shr-x').onclick = close;
    const cp = panel.querySelector('.shr-copy');
    cp.onclick = async () => { try { await navigator.clipboard.writeText(u); cp.textContent = 'Copied ✓'; } catch { prompt('Copy this link:', u); } };
    panel.hidden = false; cp.focus();
  };
  btns.forEach(b => b.addEventListener('click', async () => {
    const text = b.dataset.share;
    if (navigator.share && matchMedia('(pointer: coarse)').matches) { try { await navigator.share({ title: document.title, text, url: url() }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    open(text);
  }));
})();

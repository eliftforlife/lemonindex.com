// "Keep it free" support popup (Elijah 11-02, like Blender's donate prompt). Amounts open Stripe Payment Links; nothing card-related runs on this site.
// Hidden until the links below are filled in. Shows once per 14 days, only on car/report pages, after the reader has scrolled or stayed a while.
(() => {
  const LINKS = { 5: 'https://buy.stripe.com/eVqdR84Z25u7gtC5l9gA800', 10: 'https://buy.stripe.com/8x27sK6362hV6T2fZNgA801', 15: 'https://buy.stripe.com/9B68wO636cWz6T2bJxgA802', custom: 'https://buy.stripe.com/00w28q1MQ8Gjb9ifZNgA803' };   // Stripe Payment Links: three fixed amounts + one "customer chooses what to pay"
  const KEY = 'li-support-seen', DAYS = 14;
  const ready = Object.values(LINKS).every(Boolean);
  const isReport = /^\/(cars|electric|compare)\//.test(location.pathname) && location.pathname.split('/').filter(Boolean).length >= 2;
  const qs = new URLSearchParams(location.search);
  if (!(ready || qs.has('support-preview'))) { document.querySelectorAll('.supl').forEach(b => b.hidden = true); return; }
  const seen = () => { try { return Date.now() - (+localStorage.getItem(KEY) || 0) < DAYS * 864e5; } catch { return false; } };
  const mark = () => { try { localStorage.setItem(KEY, String(Date.now())); } catch {} };
  let pick = 10;
  const box = document.createElement('div');
  box.className = 'sup'; box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'sup-h');
  box.innerHTML = `<div class="sup-card">
  <button class="sup-x" aria-label="Close">×</button>
  <p class="sup-kick">Every report here is free</p>
  <h2 id="sup-h">Buying a used car is risky. If we helped, chip in to keep it free.</h2>
  <p class="sup-sub">No paywall, no signup. Readers like you keep the lights on.</p>
  <div class="sup-amts" role="radiogroup" aria-label="Amount">
    ${[5, 10, 15].map(a => `<button role="radio" data-a="${a}" aria-checked="${a === pick}">$${a}</button>`).join('')}
    <button role="radio" data-a="custom" aria-checked="false">Other</button>
  </div>
  <a class="btn sup-go" href="#" rel="noopener" target="_blank">Chip in $10</a>
  <button class="sup-later">Maybe later</button>
  <p class="sup-fine">Secure checkout by Stripe. Support payments aren't tax-deductible and don't unlock anything.</p>
</div>`;
  document.body.appendChild(box);
  const go = box.querySelector('.sup-go');
  const sync = () => { box.querySelectorAll('[data-a]').forEach(b => b.setAttribute('aria-checked', String(String(pick) === b.dataset.a)));
    go.textContent = pick === 'custom' ? 'Choose your amount' : `Chip in $${pick}`; go.href = LINKS[pick] || '#'; };
  box.querySelectorAll('[data-a]').forEach(b => b.addEventListener('click', () => { pick = b.dataset.a === 'custom' ? 'custom' : +b.dataset.a; sync(); }));
  const close = () => { box.hidden = true; mark(); };
  box.querySelector('.sup-x').onclick = close; box.querySelector('.sup-later').onclick = close;
  box.addEventListener('click', e => { if (e.target === box) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !box.hidden) close(); });
  go.addEventListener('click', () => mark());
  sync();
  const open = () => { if (box.hidden && !seen()) { box.hidden = false; go.focus(); } };
  window.liSupport = () => { box.hidden = false; go.focus(); };   // footer "Support the Lemon Index" link
  if (qs.has('support-preview')) return open();
  if (!isReport || seen()) return;
  let t = setTimeout(open, 40000);
  addEventListener('scroll', function f() { const p = (scrollY + innerHeight) / document.documentElement.scrollHeight; if (p > .7) { clearTimeout(t); removeEventListener('scroll', f); setTimeout(open, 1200); } }, { passive: true });
})();

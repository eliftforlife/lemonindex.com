// "Keep it free" support (Elijah 11-02, like Blender's donate prompt; v2 11-03). Amounts open Stripe Payment Links; nothing card-related runs on this site.
// 1. The full sheet: on car/report pages after 15 s of reading (tab in front; value first). Then quiet for 14 days after "Maybe later", 60 after "Chip in".
// 2. The reminder (11-03, Elijah: "every 10 mins of site use another popup... keep it 100% free"): after the first sheet, every 10 minutes of
//    reading across the site a small bar slides up ("Enjoying the Lemon Index? Keep it 100% free"). Not a blocking popup: it hides itself after
//    14 s, shows at most twice a day, × snoozes it for the day, and never shows in the 60 days after someone chips in.
(() => {
  const LINKS = { 5: 'https://buy.stripe.com/eVqdR84Z25u7gtC5l9gA800', 10: 'https://buy.stripe.com/8x27sK6362hV6T2fZNgA801', 15: 'https://buy.stripe.com/9B68wO636cWz6T2bJxgA802', custom: 'https://buy.stripe.com/00w28q1MQ8Gjb9ifZNgA803' };   // Stripe Payment Links: three fixed amounts + one "customer chooses what to pay"
  const KEY = 'li-support-seen', DAYS = 14, PAID = 'li-support-paid', PAID_DAYS = 60, READ_MS = 15000;
  const RKEY = 'li-read', NUDGE_MS = 10 * 60e3, NUDGES_PER_DAY = 2;
  const ready = Object.values(LINKS).every(Boolean);
  const isReport = /^\/(cars|electric|compare)\//.test(location.pathname) && location.pathname.split('/').filter(Boolean).length >= 2;
  const qs = new URLSearchParams(location.search);
  if (!(ready || qs.has('support-preview'))) { document.querySelectorAll('.supl').forEach(b => b.hidden = true); return; }
  const get = k => { try { return localStorage.getItem(k); } catch { return null; } }, set = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  const paid = () => Date.now() - (+get(PAID) || 0) < PAID_DAYS * 864e5;
  const seen = () => Date.now() - (+get(KEY) || 0) < DAYS * 864e5 || paid();
  const mark = () => set(KEY, String(Date.now()));
  const day = new Date().toISOString().slice(0, 10);
  let pick = 10;

  // ---- the sheet (bottom sheet on phones, centered card on bigger screens)
  const box = document.createElement('div');
  box.className = 'sup'; box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'sup-h');
  box.innerHTML = `<div class="sup-card">
  <button class="sup-x" aria-label="Close">×</button>
  <div class="sup-top"><img src="/assets/icon-64.png" alt="" width="44" height="44"><span>The Lemon Index</span></div>
  <h2 id="sup-h">Keep it 100% free</h2>
  <p class="sup-sub">Every report here is free: no paywall, no signup. If it helped you dodge a lemon, chip in and keep it that way.</p>
  <div class="sup-amts" role="radiogroup" aria-label="Amount">
    ${[5, 10, 15].map(a => `<button type="button" role="radio" data-a="${a}" aria-checked="${a === pick}">$${a}</button>`).join('')}
    <button type="button" role="radio" data-a="custom" aria-checked="false">Other</button>
  </div>
  <a class="btn sup-go" href="#" rel="noopener" target="_blank">Chip in $10</a>
  <button type="button" class="sup-later">Maybe later</button>
  <p class="sup-fine"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 11V8a5 5 0 0 1 10 0v3M5 11h14v10H5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>Secure checkout by Stripe. Support isn't tax-deductible and doesn't unlock anything.</p>
</div>`;
  document.body.appendChild(box);
  const go = box.querySelector('.sup-go');
  const sync = () => { box.querySelectorAll('[data-a]').forEach(b => b.setAttribute('aria-checked', String(String(pick) === b.dataset.a)));
    go.textContent = pick === 'custom' ? 'Choose your amount →' : `Chip in $${pick} →`; go.href = LINKS[pick] || '#'; };
  box.querySelectorAll('[data-a]').forEach(b => b.addEventListener('click', () => { pick = b.dataset.a === 'custom' ? 'custom' : +b.dataset.a; sync(); }));
  const close = () => { box.classList.remove('on'); setTimeout(() => (box.hidden = true), 250); mark(); };
  box.querySelector('.sup-x').onclick = close; box.querySelector('.sup-later').onclick = close;
  box.addEventListener('click', e => { if (e.target === box) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !box.hidden) close(); });
  go.addEventListener('click', () => { mark(); set(PAID, String(Date.now())); hideNudge(); });
  sync();
  const show = () => { box.hidden = false; requestAnimationFrame(() => box.classList.add('on')); go.focus({ preventScroll: true }); };
  const open = () => { if (box.hidden && !seen()) show(); };
  window.liSupport = show;   // footer "Support the Lemon Index" link
  document.querySelectorAll('.supl').forEach(b => b.addEventListener('click', show));   // no inline onclick (CSP)

  // ---- the reminder bar
  const bar = document.createElement('div');
  bar.className = 'nud'; bar.hidden = true; bar.setAttribute('role', 'status');
  bar.innerHTML = `<img src="/assets/icon-64.png" alt="" width="36" height="36"><p><b>Enjoying the Lemon Index?</b><span>Keep it 100% free.</span></p>
<button type="button" class="btn nud-go">Chip in</button><button type="button" class="nud-x" aria-label="Not today">×</button>`;
  document.body.appendChild(bar);
  let nudgeT;
  function hideNudge() { clearTimeout(nudgeT); bar.classList.remove('on'); setTimeout(() => (bar.hidden = true), 300); }
  const nudge = () => { bar.hidden = false; requestAnimationFrame(() => bar.classList.add('on')); nudgeT = setTimeout(hideNudge, 14000); };
  bar.querySelector('.nud-go').onclick = () => { hideNudge(); show(); };
  bar.querySelector('.nud-x').onclick = () => { hideNudge(); const r = state(); r.snooze = day; save(r); };
  const state = () => { let r; try { r = JSON.parse(get(RKEY) || '{}'); } catch { r = {}; } if (r.day !== day) r = { day, ms: 0, n: 0, snooze: r.snooze }; return r; };
  const save = r => set(RKEY, JSON.stringify(r));

  if (qs.has('support-preview')) return show();
  if (qs.has('nudge-preview')) return nudge();
  // one clock for both: only time with the tab in front counts, so a background tab never pops anything
  let read = 0, last = Date.now(), r = state(), lastSave = 0;
  setInterval(() => {
    const now = Date.now(), dt = document.visibilityState === 'visible' ? now - last : 0; last = now; if (!dt) return;
    read += dt; r.ms += dt;
    if (isReport && read >= READ_MS && !seen() && box.hidden) open();
    if (get(KEY) && !paid() && r.snooze !== day && r.n < NUDGES_PER_DAY && r.ms >= NUDGE_MS * (r.n + 1) && box.hidden && bar.hidden) { r.n++; save(r); nudge(); }
    if (now - lastSave > 5000) { save(r); lastSave = now; }
  }, 500);
  addEventListener('pagehide', () => save(r));
})();

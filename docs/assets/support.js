// "Keep it free" support (Elijah 11-02, like Blender's donate prompt; v3 11-04 "ask at the aha moment", not on a timer).
// 1. Inline card right under the page's best data (the YouTube/cost section, else the year chart, else the first data section): no popup,
//    one tap to a $5 coffee. Always there, never in the way.
// 2. The full sheet only at a value moment: the reader comes back after watching a fix / price video we linked (8 s+ away). Quiet for
//    14 days after "Maybe later", 60 after "Chip in".
// 3. The reminder bar after 3 minutes of reading across the site (most visits are 2-4 min), once a day; x snoozes it for the day.
(() => {
  const LINKS = { 5: 'https://buy.stripe.com/eVqdR84Z25u7gtC5l9gA800', 10: 'https://buy.stripe.com/8x27sK6362hV6T2fZNgA801', 15: 'https://buy.stripe.com/9B68wO636cWz6T2bJxgA802', custom: 'https://buy.stripe.com/00w28q1MQ8Gjb9ifZNgA803' };   // Stripe Payment Links: three fixed amounts + one "customer chooses what to pay"
  const KEY = 'li-support-seen', DAYS = 14, PAID = 'li-support-paid', PAID_DAYS = 60;
  const RKEY = 'li-read', NUDGE_MS = 3 * 60e3, NUDGES_PER_DAY = 1;
  const ready = Object.values(LINKS).every(Boolean);
  const isReport = /^\/(cars|electric|compare)\//.test(location.pathname) && location.pathname.split('/').filter(Boolean).length >= 2;
  const qs = new URLSearchParams(location.search);
  if (!(ready || qs.has('support-preview'))) { document.querySelectorAll('.supl').forEach(b => b.hidden = true); return; }
  const get = k => { try { return localStorage.getItem(k); } catch { return null; } }, set = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  // 11-07: donors land on /thanks/ (Stripe redirect): count them as paid so nothing asks them again for 60 days
  if (location.pathname.startsWith('/thanks/')) { set(PAID, String(Date.now())); document.querySelectorAll('.supl').forEach(b => b.hidden = true); return; }
  const paid = () => Date.now() - (+get(PAID) || 0) < PAID_DAYS * 864e5;
  const seen = () => Date.now() - (+get(KEY) || 0) < DAYS * 864e5 || paid();
  const mark = () => set(KEY, String(Date.now()));
  const day = new Date().toISOString().slice(0, 10);
  let pick = 5;

  // ---- 11-04 (Elijah: "more specific to the page they're on"): the headline and the reasons follow the page
  const H1 = ( ((document.querySelector('h1') || {}).textContent || '').replace(/\s+/g, ' ').replace(/[.]\s*$/, '').trim())
    .replace(/^Is (?:the |a |an )?/i, '').replace(/\s+(?:reliable|a good car|worth it)\??$/i, '');   // 11-10: model pages' h1 became 'Is the <car> reliable?'
  const P = location.pathname;
  const CTX = (() => {
    if (/^\/cars\/[^/]+\/\d{4}\//.test(P)) return { q: `Looking at a used ${H1}?`, a: 'This report is free. Help keep it that way.', why: [`Every year of the ${H1.replace(/^\d{4} /, '')} stays free`, 'No paywall, no account, no dealer spin', 'Pays for new car data and tools'] };
    if (/^\/cars\/[^/]+\/transmission\//.test(P)) return { q: 'Checking the transmission?', a: 'Every transmission report is free.', why: ['Every model and year stays free', 'No paywall, no account', 'Pays for new car data and tools'] };
    if (/^\/cars\/[^/]+\//.test(P)) return { q: `Shopping for a ${H1}?`, a: 'Every year of it is free to check.', why: ['Every car report stays free for everyone', 'No paywall, no account needed', 'Pays for new studies, tools and videos'] };
    if (/^\/planes\/.+/.test(P)) return { q: `Researching the ${H1}?`, a: 'Plane accident data, free for everyone.', why: ['Every plane report stays free', 'Straight from NTSB records, no paywall', 'Pays for more aviation data'] };
    if (/^\/planes\//.test(P)) return { q: 'Into planes?', a: 'Every accident report here is free.', why: ['Every plane report stays free', 'Straight from NTSB records, no paywall', 'Pays for more aviation data'] };
    if (/^\/motorcycles\/.+/.test(P)) return { q: `Riding or buying a ${H1}?`, a: 'Its problems and recalls are free to check.', why: ['Every bike report stays free', 'No paywall, no account needed', 'Pays for more motorcycle data'] };
    if (/^\/motorcycles\//.test(P)) return { q: 'Shopping for a bike?', a: 'Every motorcycle report is free.', why: ['Every bike report stays free', 'No paywall, no account needed', 'Pays for more motorcycle data'] };
    if (/^\/supercars\/.+/.test(P)) return { q: `Dreaming about the ${H1}?`, a: 'Supercar specs and recalls, free.', why: ['Every supercar page stays free', 'Real recalls and EPA numbers', 'Pays for more data and videos'] };
    if (/^\/supercars\//.test(P)) return { q: 'Supercar fan?', a: 'Every spec sheet here is free.', why: ['Every supercar page stays free', 'Real recalls and EPA numbers', 'Pays for more data and videos'] };
    if (/^\/vin\//.test(P)) return { q: 'Checked a VIN?', a: 'Keep the VIN checks free.', why: ['Free VIN checks for everyone', 'No account, we don&#39;t store your VIN', 'Pays for new tools'] };
    if (/^\/car-loan-rates\//.test(P)) return { q: 'Did this save you on your loan?', a: 'Keep the rate check free.', why: ['Free tools for every car buyer', 'No account, no dealer spin', 'Pays for new tools'] };
    if (/^\/compare\//.test(P)) return { q: 'Comparing cars?', a: 'Every head-to-head is free.', why: ['Every comparison stays free', 'No paywall, no account', 'Pays for new car data and tools'] };
    if (/^\/electric\//.test(P)) return { q: 'Thinking about an EV?', a: 'Every EV report is free.', why: ['Every EV report stays free', 'No paywall, no account', 'Pays for new studies'] };
    if (/^\/brands\//.test(P)) return { q: 'Picking a brand?', a: 'Every brand report is free.', why: ['Every brand and model stays free', 'No paywall, no account', 'Pays for new studies'] };
    return { q: 'Enjoying the Lemon Index?', a: 'Keep it free and ad-free.', why: ['Every car report stays free for everyone', 'No paywall, no account needed', 'Pays for new studies, tools and videos'] };
  })();
  const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // ---- the sheet (bottom sheet on phones, centered card on bigger screens)
  const box = document.createElement('div');
  box.className = 'sup'; box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'sup-h');
  box.innerHTML = `<div class="sup-card">
  <button class="sup-x" aria-label="Close">×</button>
  <div class="sup-art" aria-hidden="true"><svg viewBox="0 0 240 132"><g fill="none" stroke-width="14"><path d="M28 118A92 92 0 0 1 58.2 49.8" stroke="#1a8f4c"/><path d="M60 48.4A92 92 0 0 1 179.9 48.4" stroke="#d2d2d7"/><path d="M181.8 49.8A92 92 0 0 1 212 118" stroke="#e8141c"/></g><g class="sup-ndl"><path d="M116 118L120 34L124 118Z"/><circle cx="120" cy="118" r="11"/><circle cx="120" cy="118" r="5" fill="#ffd400"/></g></svg>
    <p><b>$0</b>to read any report</p></div>
  <h2 id="sup-h">${esc(CTX.q)} <span>${esc(CTX.a)} Chip in if it helped.</span></h2>
  <ul class="sup-why">${CTX.why.map(w => `<li>${w}</li>`).join('')}</ul>
  <p class="sup-ads"><b>Lemon has no ads right now.</b> Donations keep it ad-free and pay for more cars, images and data.</p>
  <details class="sup-next"><summary>What donations fund next (planned)</summary><ul><li>Year-by-year images and a year slider for more cars</li><li>Engine pages for more brands (BMW is live)</li><li>A VIN report for any car</li><li>Recall alerts for your car</li><li>A Spanish version of the site</li></ul></details>
  <div class="sup-amts" role="radiogroup" aria-label="Amount">
    ${[5, 10, 15].map(a => `<button type="button" role="radio" data-a="${a}" aria-checked="${a === pick}">$${a}</button>`).join('')}
    <button type="button" role="radio" data-a="custom" aria-checked="false">Other</button>
  </div>
  <a class="btn sup-go" href="#" rel="noopener" target="_blank">Chip in $10</a>
  <button type="button" class="sup-later">Maybe later</button>
  <p class="sup-fine">Secure checkout by Stripe. Not tax-deductible; doesn't unlock anything.</p>
</div>`;
  document.body.appendChild(box);
  const go = box.querySelector('.sup-go');
  const sync = () => { box.querySelectorAll('[data-a]').forEach(b => b.setAttribute('aria-checked', String(String(pick) === b.dataset.a)));
    go.textContent = pick === 'custom' ? 'Choose your amount' : `Chip in $${pick}`; go.href = LINKS[pick] || '#'; };
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

  // ---- 1. inline "aha" card under the best data on the page
  const spot = document.querySelector('#diy') || document.querySelector('.yyears') || document.querySelector('main .yc, main section.yc');
  if (spot && !paid()) {
    const yt = !!document.querySelector('#diy');
    const card = document.createElement('aside');
    card.className = 'supc'; card.setAttribute('aria-label', 'Support the Lemon Index');
    card.innerHTML = `<img src="/assets/icon-64.png" alt="" width="40" height="40"><div class="supc-t"><b>Did this help?</b><span>${yt ? 'We went through 100+ YouTube videos and every government complaint so you don&#39;t have to.' : 'We went through every government complaint and recall so you don&#39;t have to.'} It&#39;s free, with no paywall and no ads. A $5 coffee keeps it that way and pays for more cars and data.</span></div>
<div class="supc-b"><a class="btn supc-go" href="${LINKS[5]}" target="_blank" rel="noopener">Buy us a $5 coffee</a><button type="button" class="supc-o">Other amount</button></div>`;
    spot.insertAdjacentElement('afterend', card);
    card.querySelector('.supc-go').addEventListener('click', () => { mark(); set(PAID, String(Date.now())); });
    card.querySelector('.supc-o').addEventListener('click', show);
  }
  // ---- 2. the sheet when someone comes back from a video we sent them to (the "this just saved me" moment)
  let away = 0;
  document.addEventListener('click', e => { if (e.target.closest('a.yf-v, a.yg, a.yc-h')) away = Date.now(); }, true);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && away && Date.now() - away > 8000) { away = 0; setTimeout(open, 700); } });

  // ---- the reminder bar
  const bar = document.createElement('div');
  bar.className = 'nud'; bar.hidden = true; bar.setAttribute('role', 'status');
  bar.innerHTML = `<img src="/assets/icon-64.png" alt="" width="36" height="36"><p><b>${esc(CTX.q)}</b><span>${esc(CTX.a)}</span></p>
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
  let last = Date.now(), r = state(), lastSave = 0;
  setInterval(() => {
    const now = Date.now(), dt = document.visibilityState === 'visible' ? now - last : 0; last = now; if (!dt) return;
    r.ms += dt;
    if (!paid() && r.snooze !== day && r.n < NUDGES_PER_DAY && r.ms >= NUDGE_MS * (r.n + 1) && box.hidden && bar.hidden) { r.n++; save(r); nudge(); }
    if (now - lastSave > 5000) { save(r); lastSave = now; }
  }, 500);
  addEventListener('pagehide', () => save(r));
})();

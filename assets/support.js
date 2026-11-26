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
  if (!(ready || qs.has('support-preview'))) { document.querySelectorAll('.supl').forEach(b => b.hidden = true); const _db = document.querySelector('.donbar'); if (_db) _db.remove(); return; }
  const get = k => { try { return localStorage.getItem(k); } catch { return null; } }, set = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  // ---- 11-24 (Elijah: "new donations... what made them donate? track them"): a donor's path, no personal data.
  // Each visit keeps where it came from (referrer site only), its first page and the pages read (last 12), in this browser only.
  // A click on a Stripe link saves that path + the page, spot and amount, sends GA4 'donate_click', and tags the Stripe link with a
  // random reference (client_reference_id, shows on the Stripe payment). /thanks/ then sends GA4 'donation_complete' with the same
  // reference, so each Stripe payment can be matched to the visit that led to it.
  const ga4 = (n, p, k = 0) => { try { if (window.gtag) gtag('event', n, p); else if (k < 40) setTimeout(() => ga4(n, p, k + 1), 250); } catch {} };   // ga.js loads after this script
  const JK = 'li-visit', DK = 'li-donate-from';
  let J = null; try { J = JSON.parse(get(JK) || 'null'); } catch {}
  const now = Date.now();
  if (!J || now - (J.t || 0) > 30 * 60e3) {   // a new visit after 30 quiet minutes
    let rh = ''; try { rh = document.referrer ? new URL(document.referrer).hostname : ''; } catch {}
    if (rh === location.hostname) rh = '';
    J = { s: now, ref: rh || '(direct)', land: location.pathname, utm: qs.get('utm_source') || '', n: 0, p: [] };
  }
  if (!location.pathname.startsWith('/thanks/')) { J.n++; J.p = J.p.concat(location.pathname).slice(-12); }
  J.t = now; set(JK, JSON.stringify(J));
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href^="https://buy.stripe.com/"]'); if (!a) return;
    const id = 'li' + now.toString(36) + Math.random().toString(36).slice(2, 8);
    const amt = (Object.entries(LINKS).find(([, u]) => a.href.startsWith(u)) || ['?'])[0];
    const spot = a.closest('.sup') ? 'sheet' : a.closest('.donbar') ? 'bar' : a.closest('.supl, [class^="supc"]') ? 'card' : 'other';
    try { const u = new URL(a.href); u.searchParams.set('client_reference_id', id); a.href = u.toString(); } catch {}
    const d = { id, amt, spot, page: location.pathname, t: Date.now(), ref: J.ref, land: J.land, utm: J.utm, n: J.n, mins: Math.round((Date.now() - J.s) / 6e4), p: J.p };
    set(DK, JSON.stringify(d));
    ga4('donate_click', { donate_ref: id, donate_amount: amt, donate_spot: spot, donate_page: location.pathname, visit_source: J.ref, visit_landing: J.land, visit_pages: J.n });
  }, true);
  if (location.pathname.startsWith('/thanks/')) {
    let d = null; try { d = JSON.parse(get(DK) || 'null'); } catch {}
    if (d && !d.done) {
      ga4('donation_complete', { donate_ref: d.id, donate_amount: d.amt, donate_spot: d.spot, donate_page: d.page, visit_source: d.ref, visit_landing: d.land,
        visit_pages: d.n, visit_minutes: d.mins, visit_path: d.p.join(' > ').slice(0, 99), utm_source: d.utm });
      d.done = 1; set(DK, JSON.stringify(d));
    } else if (!d) ga4('donation_complete', { donate_ref: '(unknown)' });
  }
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
    return { q: 'Enjoying the Lemon Index?', a: 'Help keep it free for everyone.', why: ['Every car report stays free for everyone', 'No paywall, no account needed', 'Pays for new studies, tools and videos'] };
  })();
  const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // ---- the sheet (bottom sheet on phones, centered card on bigger screens)
  const box = document.createElement('div');
  box.className = 'sup'; box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'sup-h');
  box.innerHTML = `<div class="sup-card">
  <button class="sup-x" aria-label="Close">×</button>
  <div class="sup-ic"><img src="/assets/icon-64.png" alt="" width="52" height="52"></div>
  <h2 id="sup-h">Support Lemon Index</h2>
  <p class="sup-lede">Every score, chart and image here is free. A few dollars keeps it that way.</p>
  <div class="sup-amts" role="radiogroup" aria-label="Amount">
    ${[5, 10, 15].map(a => `<button type="button" role="radio" data-a="${a}" aria-checked="${a === pick}">$${a}</button>`).join('')}
    <button type="button" role="radio" data-a="custom" aria-checked="false">Other</button>
  </div>
  <a class="btn sup-go" href="#" rel="noopener" target="_blank">Donate $10</a>
  <details class="sup-next"><summary>What it pays for</summary><ul><li>More cars and years</li><li>Car images and year sliders</li><li>Engine pages for more brands</li><li>VIN reports and recall alerts</li></ul></details>
  <button type="button" class="sup-later">Maybe later</button>
  <p class="sup-fine">Secure checkout by Stripe · Not tax-deductible</p>
</div>`;
  document.body.appendChild(box);
  const go = box.querySelector('.sup-go');
  const sync = () => { box.querySelectorAll('[data-a]').forEach(b => b.setAttribute('aria-checked', String(String(pick) === b.dataset.a)));
    go.textContent = pick === 'custom' ? 'Choose your amount' : `Donate $${pick}`; go.href = LINKS[pick] || '#'; };
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
  // 11-20 (Elijah: the donate box cluttered the middle of the page): one compact line at the END of the page content, never mid-page
  const main = document.querySelector('main');
  const spot = main && [...main.children].filter((e) => !/^(SCRIPT|STYLE|LINK)$/.test(e.tagName) && e.offsetHeight > 0).pop();
  if (spot && !paid()) {
        const card = document.createElement('aside');
    card.className = 'supc supc3'; card.setAttribute('aria-label', 'Support the Lemon Index');
    // 11-19 (Elijah): black card, no icon, "Support Lemon Index" (11-20 wording) + four white buttons straight to Stripe ($5 / $10 / $15 / custom)
    card.innerHTML = `<div class="supc3-t"><b>Support Lemon Index</b><small>Secure checkout by Stripe</small></div>
<div class="supc3-a">${[5, 10, 15].map(a => `<a href="${LINKS[a]}" target="_blank" rel="noopener">$${a}</a>`).join('')}<a href="${LINKS.custom}" target="_blank" rel="noopener">Custom</a></div>`;
    spot.insertAdjacentElement('afterend', card);
    card.querySelectorAll('.supc3-a a').forEach(a => a.addEventListener('click', () => { mark(); set(PAID, String(Date.now())); }));
  }
  // ---- 2. the sheet when someone comes back from a video we sent them to (the "this just saved me" moment)
  let away = 0;
  document.addEventListener('click', e => { if (e.target.closest('a.yf-v, a.yg, a.yc-h')) away = Date.now(); }, true);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && away && Date.now() - away > 8000) { away = 0; setTimeout(open, 700); } });

  // ---- the reminder bar
  const bar = document.createElement('div');
  bar.className = 'nud'; bar.hidden = true; bar.setAttribute('role', 'status');
  // 11-26 (Elijah: "Looking at BMW 3 Series reliability? Chip in" made no sense): one short line and a plain Donate button
  bar.className = 'nud nud2';
  bar.innerHTML = `<p>Like the Lemon Index?</p><button type="button" class="btn nud-go">Donate</button><button type="button" class="nud-x" aria-label="Not today">×</button>`;
  document.body.appendChild(bar);
  let nudgeT;
  function hideNudge() { clearTimeout(nudgeT); bar.classList.remove('on'); setTimeout(() => (bar.hidden = true), 300); }
  const nudge = () => { bar.hidden = false; requestAnimationFrame(() => bar.classList.add('on')); nudgeT = setTimeout(hideNudge, 14000); };
  bar.querySelector('.nud-go').onclick = () => { hideNudge(); show(); };
  bar.querySelector('.nud-x').onclick = () => { hideNudge(); const r = state(); r.snooze = day; save(r); };
  const state = () => { let r; try { r = JSON.parse(get(RKEY) || '{}'); } catch { r = {}; } if (r.day !== day) r = { day, ms: 0, n: 0, snooze: r.snooze }; return r; };
  const save = r => set(RKEY, JSON.stringify(r));

  // ---- 11-11 (Elijah): the phone donate bar at the very top (it's in the page; the head script already hid it after x / a donation)
  const DKEY = 'li-donbar-x', DBAR_DAYS = 7, db = document.querySelector('.donbar');
  if (db) {
    if (paid() || Date.now() - (+get(DKEY) || 0) < DBAR_DAYS * 864e5) db.remove();
    else {
      const ga = name => { try { if (window.gtag) gtag('event', name, { page_path: location.pathname }); } catch {} };
      db.querySelector('.donbar-go').addEventListener('click', () => ga('coming_bar_click'));   // 11-24: a link to /coming-soon/ now (that page asks for the donation)
      db.querySelector('.donbar-x').addEventListener('click', () => { ga('coming_bar_close'); set(DKEY, String(Date.now())); db.remove(); });
    }
  }
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

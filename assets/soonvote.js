// 11-12 (UX test, Tyler: "coming-soon cards do nothing when tapped"): every coming-soon card (cars, performance cars, motorcycles, engines)
// opens a small sheet: "Vote for this one" (we build the most-voted first) and an optional email to hear when its page is live.
// It goes through the site's existing feedback endpoint (lemon-survey Worker /feedback: page path + message + optional email), so there is
// no new service or account. One vote per card per browser (localStorage); the Worker rate-limits by network.
(() => {
  const cards = document.querySelectorAll('.mc-nd, .aec-soon'); if (!cards.length) return;
  const API = 'https://lemon-survey.elift08.workers.dev/feedback', KEY = 'soon-votes';
  let mine = {}; try { mine = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(mine)); } catch (e) {} };
  const nameOf = c => {
    const im = c.querySelector('img'), b = c.querySelector('b');
    const a = im && im.alt ? im.alt.replace(/,\s*(AI )?illustration$/i, '').trim() : '';
    return a || (b ? b.textContent.trim() : 'this one');
  };
  const css = document.createElement('style');
  css.textContent = '.sv-on{cursor:pointer!important}.sv-on:focus-visible{outline:2.5px solid #e9b300;outline-offset:2px}'
    + '.sv-bg{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:200;display:flex;align-items:flex-end;justify-content:center}'
    + '.sv-sh{background:#fff;color:#111;width:min(100%,460px);border-radius:22px 22px 0 0;padding:22px 20px calc(20px + env(safe-area-inset-bottom));box-shadow:0 -10px 40px rgba(0,0,0,.2);font-size:15px}'
    + '@media (min-width:700px){.sv-bg{align-items:center}.sv-sh{border-radius:22px}}'
    + '.sv-sh h2{font-size:22px;letter-spacing:-.02em;margin:0 0 6px}.sv-sh p{margin:0 0 14px;color:#4a4a50}'
    + '.sv-b{display:block;width:100%;min-height:48px;border:0;border-radius:999px;background:#111;color:#fff;font:inherit;font-weight:700;cursor:pointer}'
    + '.sv-b[disabled]{opacity:.55;cursor:default}.sv-x{background:none;color:#111;min-height:44px;margin-top:6px;font-weight:600}'
    + '.sv-row{display:flex;gap:8px;margin:12px 0 0}.sv-row input{flex:1;min-width:0;min-height:46px;border:1px solid #d2d2d7;border-radius:12px;padding:0 12px;font:inherit}'
    + '.sv-row .sv-b{width:auto;padding:0 16px;background:#ffd400;color:#111}.sv-st{min-height:20px;margin:10px 0 0!important;font-size:14px}.sv-st.bad{color:#c4141b}';
  document.head.appendChild(css);
  const send = async (msg, email) => {
    const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ page: location.pathname, message: msg, email: email || '', hp: '' }) });
    if (!r.ok) throw new Error(r.status);
  };
  let last = null;
  const open = c => {
    const nm = nameOf(c), id = nm.toLowerCase(), voted = !!mine[id]; last = c;
    const bg = document.createElement('div'); bg.className = 'sv-bg';
    bg.innerHTML = '<div class="sv-sh" role="dialog" aria-modal="true" aria-labelledby="sv-h"><h2 id="sv-h"></h2><p>Its page isn&#39;t built yet. We build the most-voted cars and engines first.</p>'
      + '<button type="button" class="sv-b sv-v"></button>'
      + '<form class="sv-row"><input type="email" placeholder="Email me when it&#39;s live (optional)" aria-label="Email (optional)" autocomplete="email"><button class="sv-b" type="submit">Notify me</button></form>'
      + '<p class="sv-st" role="status"></p><button type="button" class="sv-b sv-x">Close</button></div>';
    bg.querySelector('#sv-h').textContent = nm + ': coming soon';
    const v = bg.querySelector('.sv-v'), st = bg.querySelector('.sv-st'), f = bg.querySelector('form'), em = f.querySelector('input');
    const say = (t, bad) => { st.textContent = t; st.classList.toggle('bad', !!bad); };
    const setv = () => { v.textContent = mine[id] ? 'Voted ✓' : 'Vote for this one'; v.disabled = !!mine[id]; };
    setv(); if (voted) say('You voted for it. Thanks!');
    const close = () => { bg.remove(); document.removeEventListener('keydown', esc); if (last) last.focus(); };
    const esc = e => { if (e.key === 'Escape') close(); };
    v.addEventListener('click', async () => {
      v.disabled = true; say('Sending…');
      try { await send('Coming-soon vote: ' + nm); mine[id] = Date.now(); save(); setv(); say('Vote counted. Thanks!'); }
      catch (e) { v.disabled = false; say(String(e.message) === '429' ? 'Too many votes from this network for now. Try again later.' : 'That didn’t send. Please try again.', true); }
    });
    f.addEventListener('submit', async e => {
      e.preventDefault(); const m = em.value.trim();
      if (!m || !(em.checkValidity && em.checkValidity())) { say('Type an email first.', true); em.focus(); return; }
      say('Sending…');
      try { await send('Notify me when live: ' + nm, m); mine[id] = mine[id] || Date.now(); save(); setv(); f.hidden = true; say('Done. We’ll email you once, when its page is live.'); }
      catch (err) { say('That didn’t send. Please try again.', true); }
    });
    bg.addEventListener('click', e => { if (e.target === bg) close(); });
    bg.querySelector('.sv-x').addEventListener('click', close);
    document.addEventListener('keydown', esc);
    document.body.appendChild(bg); v.disabled ? em.focus() : v.focus();
  };
  cards.forEach(c => {
    c.classList.add('sv-on'); c.removeAttribute('aria-disabled'); c.setAttribute('role', 'button'); c.setAttribute('tabindex', '0');
    c.setAttribute('aria-haspopup', 'dialog'); c.setAttribute('aria-label', nameOf(c) + ': coming soon. Vote for it or get notified');
    c.addEventListener('click', () => open(c));
    c.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(c); } });
  });
})();

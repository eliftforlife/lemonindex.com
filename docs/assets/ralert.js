// Recall alert signup (11-14, growth plan 4a: "Get an email if your car gets a recall"). Talks to the lemon-alerts Worker.
// Mounts every [data-ra] box: year pages {y, n, f, l}, model pages {m, f, ys: {year: names}, y0}, the VIN page {y, n, f, l} (vin.js adds it
// after a lookup and calls LXRA.scan()). n = the NHTSA make/model names the site's recall list uses. Never sends a VIN.
// Also runs the /alerts/ page: #c=<token> confirms (one tap on a button), #u=<token> unsubscribes (one click, deletes the address).
// Turnstile loads only once someone starts typing; the Worker checks it when its TURNSTILE_SECRET is set.
(() => {
  const API = 'https://lemon-alerts.elift08.workers.dev', TS = '0x4AAAAAAFyhvovKDo2j0cLa';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const post = (path, body) => fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(async r => ({ status: r.status, j: await r.json().catch(() => ({})) }));
  let n = 0, tsLoad = null;
  const loadTS = () => tsLoad || (tsLoad = new Promise(res => {
    window.lxraTS = () => res(window.turnstile);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=lxraTS'; s.async = true;
    s.onerror = () => res(null); document.head.appendChild(s);
  }));

  function mount(el) {
    if (el.dataset.raOn) return;
    let d; try { d = JSON.parse(el.dataset.ra); } catch (e) { return; }
    el.dataset.raOn = '1';
    // 11-15 (growth 4c): make pages (/recalls/<make>/) send {mk, ms: [{m, f, n, ys: [years], x: {year: names}, y0}]}: a model picker first.
    // n = the NHTSA names most years use, x = the years that differ (keeps the page small).
    const MS = Array.isArray(d.ms) && d.ms.length ? d.ms : null;
    const useM = o => { const ys = {}; (o.ys || []).forEach(y => { ys[y] = (o.x && o.x[y]) || o.n; }); Object.assign(d, { m: o.m, f: o.f, ys, y0: o.y0 }); };
    if (MS) useM(MS[0]);
    const yopts = () => Object.keys(d.ys).sort((a, b) => b - a).map(y => `<option${+y === +d.y0 ? ' selected' : ''}>${esc(y)}</option>`).join('');
    const id = 'rla' + (++n), ys = d.ys ? Object.keys(d.ys).sort((a, b) => b - a) : null;
    el.innerHTML = `<form class="rla-f" novalidate aria-labelledby="${id}h"><div class="rla-ic" aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg></div>
<div class="rla-b"><p class="rla-h" id="${id}h">${MS ? `Get an email if your ${esc(d.mk)} gets a recall.` : ys ? `Get an email if your ${esc(d.m)} gets a recall.` : `Get an email if the ${esc(d.l)} gets a new recall.`}</p>
<div class="rla-in"><div class="rla-row">${MS ? `<label class="vh" for="${id}m">Model</label><select id="${id}m" class="rla-y rla-m">${MS.map((o, i) => `<option value="${i}">${esc(o.m)}</option>`).join('')}</select>` : ''}${ys ? `<label class="vh" for="${id}y">Model year</label><select id="${id}y" class="rla-y">${yopts()}</select>` : ''}
<label class="vh" for="${id}e">Your email</label><input id="${id}e" class="rla-e" type="email" name="email" maxlength="200" autocomplete="email" inputmode="email" placeholder="Your email" required>
<button class="rla-go" type="submit">Email me</button></div>
<div class="rla-hpw" aria-hidden="true"><label for="${id}w">Leave this empty</label><input id="${id}w" class="rla-hp" name="website" tabindex="-1" autocomplete="off"></div><div class="rla-ts"></div>
<p class="rla-fine">Free. We check NHTSA&#39;s recall list every week and email you only when a new recall is added. You confirm by email first; every email has a one-tap unsubscribe. <a href="/privacy/#recall-alerts">Privacy</a></p></div>
<p class="rla-st" role="status" aria-live="polite" tabindex="-1"></p></div></form>`;
    const f = el.querySelector('form'), em = f.querySelector('.rla-e'), btn = f.querySelector('.rla-go'), st = f.querySelector('.rla-st'), sel = f.querySelector('.rla-y:not(.rla-m)'), msel = f.querySelector('.rla-m'), tsBox = f.querySelector('.rla-ts');
    const say = (t, bad) => { st.innerHTML = t; st.classList.toggle('bad', !!bad); };
    let tok = '', wid = null, ts = null;
    f.addEventListener('focusin', () => {
      if (ts !== null) return; ts = false;
      loadTS().then(T => { if (!T) return; ts = T; try { wid = T.render(tsBox, { sitekey: TS, appearance: 'interaction-only', size: 'flexible', callback: t => { tok = t; }, 'expired-callback': () => { tok = ''; }, 'error-callback': () => { tok = ''; } }); } catch (e) { /* the Worker decides */ } });
    }, { once: false });
    const waitTok = async () => { for (let i = 0; i < 30 && ts && !tok; i++) await new Promise(r => setTimeout(r, 200)); return tok; };
    f.addEventListener('submit', async e => {
      e.preventDefault();
      const mail = em.value.trim();
      if (!mail || !(em.checkValidity && em.checkValidity())) { say('Type your email address first.', true); em.focus(); return; }
      const y = sel ? +sel.value : +d.y, names = sel ? d.ys[sel.value] : d.n, label = sel ? `${y} ${d.m}` : d.l;
      btn.disabled = true; say('Sending…');
      try {
        const { status, j } = await post('/signup', { email: mail, y, n: names, f: d.f || '', hp: f.querySelector('.rla-hp').value, t: await waitTok() });
        if (ts && wid !== null) { try { ts.reset(wid); } catch (x) { /* ignore */ } tok = ''; }
        if (j.ok) {
          f.classList.add('sent');
          say(j.queued ? `<b>Saved.</b> Alerts for the ${esc(label)} start in a few days. We&#39;ll email ${esc(mail)} a link to confirm first, and nothing else is sent until you tap it.`
            : `<b>Check your inbox.</b> Tap the link we sent to ${esc(mail)} to start alerts for the ${esc(label)}. Not there? Look in spam or promotions.`);
          st.focus(); return;
        }
        say({ email: 'That email doesn&#39;t look right.', max: 'That email already has alerts for 5 cars, the most we allow.', human: 'Please finish the quick human check above, then tap Email me again.',
          car: 'We couldn&#39;t match this car in NHTSA&#39;s list, so we can&#39;t watch it yet.', busy: 'We&#39;ve hit today&#39;s email limit. Please try again tomorrow.' }[j.error]
          || (status === 429 ? 'Too many tries. Please wait a minute.' : 'That didn&#39;t send. Please try again.'), true);
      } catch (x) { say('That didn&#39;t send. Check your connection and try again.', true); }
      btn.disabled = false;
    });
    sel && sel.addEventListener('change', () => { f.classList.remove('sent'); say(''); });
    msel && msel.addEventListener('change', () => { useM(MS[+msel.value] || MS[0]); sel.innerHTML = yopts(); f.classList.remove('sent'); say(''); });
  }
  const scan = () => document.querySelectorAll('[data-ra]').forEach(mount);
  window.LXRA = { scan };
  scan();

  // ---- /alerts/: confirm or unsubscribe from the link in an email. The token rides in the #hash (never sent to our host or analytics)
  // and is cleared from the address bar right away.
  const pg = document.getElementById('rla-page'); if (!pg) return;
  const m = location.hash.match(/^#([cu])=([A-Za-z0-9_-]{32})$/);
  if (location.hash) history.replaceState(null, '', location.pathname);
  const out = pg.querySelector('.rla-out'), set = h => { out.innerHTML = h; out.hidden = false; };
  if (!m) return;
  pg.querySelector('.rla-intro').hidden = true;
  const gone = '<h2>This link has expired or was already used.</h2><p>Confirm links work for 7 days. Sign up again from your car&#39;s page or the <a href="/vin/">VIN check</a>.</p>';
  if (m[1] === 'u') {
    set('<p>Unsubscribing…</p>');
    post('/unsub', { u: m[2] }).then(({ j }) => set(j.ok
      ? (j.n ? '<h2>You&#39;re unsubscribed.</h2><p>We deleted your email address and every recall alert on it. You won&#39;t get any more emails from us.</p>'
        : '<h2>You&#39;re already unsubscribed.</h2><p>Your email address isn&#39;t on our list.</p>')
      : '<h2>That didn&#39;t work.</h2><p>Please try the link again in a minute, or email <a href="mailto:hello@elijahwestbrook.com">hello@elijahwestbrook.com</a> and we&#39;ll remove you by hand.</p>'))
      .catch(() => set('<h2>That didn&#39;t work.</h2><p>Check your connection and open the link again.</p>'));
    return;
  }
  set('<p>Checking your link…</p>');
  post('/info', { c: m[2] }).then(({ j }) => {
    if (!j.name) { set(gone); return; }
    set(`<h2>Start recall alerts for the ${esc(j.name)}?</h2><p>We&#39;ll check NHTSA&#39;s recall list every week and email you only when a new recall is added.</p><p><button class="btn rla-yes" type="button">Yes, email me new recalls</button></p>`);
    const b = out.querySelector('.rla-yes');
    b.onclick = () => {
      b.disabled = true; b.textContent = 'Starting…';
      post('/confirm', { c: m[2] }).then(({ j: k }) => set(k.ok
        ? `<h2>You&#39;re set.</h2><p>We&#39;ll email you when NHTSA adds a recall for the ${esc(k.name)}.${k.n != null ? ` Right now it has ${k.n} recall${k.n === 1 ? '' : 's'} on record.` : ''} Every email has a one-click unsubscribe.</p><p><a class="btn" href="${esc(k.url)}">See its recalls and problems</a></p>`
        : gone)).catch(() => { b.disabled = false; b.textContent = 'Yes, email me new recalls'; });
    };
  }).catch(() => set('<h2>That didn&#39;t load.</h2><p>Check your connection and open the link again.</p>'));
})();

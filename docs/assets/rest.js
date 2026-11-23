// 11-23 repair estimates (#estimates, built by repair_est.py). 1) "Your shop rate": every estimate is labor hours x rate + parts
// (data-v = hours low,high,parts low,high per engine), recomputed when the rate changes and remembered in localStorage.
// 2) "What did you pay?": posts one repair bill to the lemon-survey Worker (POST /price). Stored for review; nothing shows publicly from it yet.
(() => {
  // motorcycle, supercar and plane pages (job E) carry their own default rate and their own remembered rate (data-key on the rate input)
  const R0 = document.querySelector('.rst-ri'), DEF = (R0 && +R0.defaultValue) || 140, KEY = (R0 && R0.dataset.key) || 'lemon-shop-rate', W = 'https://lemon-survey.elift08.workers.dev';
  const money = v => { v = Math.max(0, v); v = v < 1000 ? Math.round(v / 10) * 10 : Math.round(v / 50) * 50; return '$' + v.toLocaleString('en-US'); };
  const rng = (a, b) => money(a) === money(b) ? money(a) : `${money(a)}–${money(b)}`;
  const get = () => { try { return +localStorage.getItem(KEY) || 0; } catch (e) { return 0; } };
  const put = v => { try { localStorage.setItem(KEY, String(v)); } catch (e) {} };
  const apply = rate => {
    for (const li of document.querySelectorAll('.rst li[data-v]')) {   // data-v = "h0,h1,p0,p1|..." (one per engine): lowest low to highest high
      const vs = li.dataset.v.split('|').map(x => x.split(',').map(Number)), e = li.querySelector('.rst-e');
      if (e) e.textContent = rng(Math.min(...vs.map(v => v[0] * rate + v[2])), Math.max(...vs.map(v => v[1] * rate + v[3])));
    }
    for (const i of document.querySelectorAll('.rst-ri')) if (+i.value !== rate) i.value = rate;
  };
  const ok = v => v >= 40 && v <= 400;
  const saved = get(); if (ok(saved) && saved !== DEF) apply(saved);
  for (const inp of document.querySelectorAll('.rst-ri')) {
    inp.addEventListener('input', () => { const v = +inp.value; if (ok(v)) { apply(v); put(v); } });
    inp.addEventListener('change', () => { let v = +inp.value; if (!ok(v)) { v = Math.min(400, Math.max(40, v || DEF)); apply(v); put(v); } });
  }

  // ---- "What did you pay?"
  const box = document.getElementById('paid'); if (!box) return;
  const form = box.querySelector('.rst-f'), open = box.querySelector('.rst-open'), msg = box.querySelector('.rst-msg'), TS = box.dataset.ts || '';
  const say = (t, good) => { msg.textContent = t; msg.hidden = false; msg.className = 'rst-msg' + (good ? ' ok' : ''); };
  let tsReady = null, wid = null;
  const loadTs = () => { if (!TS || tsReady) return; tsReady = new Promise(res => {
    window.onRstTs = () => res(true);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onRstTs&render=explicit'; s.async = true; s.onerror = () => res(false); document.head.appendChild(s);
  }); };
  const token = async () => {
    if (!TS) return ''; loadTs(); if (!(await tsReady) || !window.turnstile) return '';
    return new Promise(res => {
      let done = false; const fin = t => { if (!done) { done = true; res(t || ''); } }; setTimeout(() => fin(''), 120000);
      if (wid === null) wid = turnstile.render(form.querySelector('.rst-ts'), { sitekey: TS, theme: 'light', size: 'flexible', appearance: 'interaction-only', execution: 'execute', callback: fin, 'error-callback': () => fin('') });
      else turnstile.reset(wid);
      turnstile.execute(wid);
    });
  };
  const show = () => { form.hidden = false; open.setAttribute('aria-expanded', 'true'); loadTs(); };
  open.addEventListener('click', () => { if (form.hidden) { show(); form.elements.repair.focus(); } else { form.hidden = true; open.setAttribute('aria-expanded', 'false'); } });
  for (const a of document.querySelectorAll('a.rst-ask')) a.addEventListener('click', () => {
    show(); const n = a.closest('li') && a.closest('li').querySelector('.rst-n'), sel = form.elements.repair;
    const txt = n ? n.childNodes[0].textContent.trim() : '';
    for (const o of sel.options) if (o.textContent === txt) sel.value = o.value;
  });
  const ERR = { repair: 'Choose the repair.', usd: 'Enter what you paid in dollars, between $20 and $30,000.', zip: 'A ZIP code is 5 digits (or leave it empty).',
    car: 'You already sent a price for this repair on this car. Thanks!', day: 'That’s the most prices for today. Come back tomorrow.', limit: 'Too many tries. Wait a minute and try again.',
    vpn: 'Prices can’t be sent from a VPN or data-center network.', human: 'The human check didn’t go through. Try again.', busy: 'We’re getting a lot of prices today. Try again tomorrow.' };
  form.addEventListener('submit', async e => {
    e.preventDefault(); const btn = form.querySelector('button[type=submit]'); msg.hidden = true;
    const f = form.elements, repair = f.repair.value, usd = Math.round(+f.usd.value), zip = f.zip.value.trim();
    if (!repair) return say(ERR.repair);
    const umax = +f.usd.max || 30000;   // planes and supercars allow bigger bills (repair_est.py XMAX)
    if (!(usd >= 20 && usd <= umax)) return say('Enter what you paid in dollars, between $20 and $' + umax.toLocaleString('en-US') + '.');
    if (zip && !/^\d{5}$/.test(zip)) return say(ERR.zip);
    btn.disabled = true; btn.textContent = 'Checking…';
    try {
      const t = await token();
      const body = { fid: box.dataset.fid, repair, usd, year: f.year && f.year.value ? +f.year.value : null, shop: f.shop.value, zip, hp: f.website.value, t };
      const r = await fetch(`${W}/price`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (j.ok) { form.hidden = true; open.hidden = true; say('Thanks! Your price is saved. Prices like yours get added to these numbers after a check.', true); }
      else say(ERR[j.error] || 'Something went wrong. Try again in a minute.');
    } catch (err) { say('Couldn’t reach the server. Check your connection and try again.'); }
    btn.disabled = false; btn.textContent = 'Send';
  });
})();

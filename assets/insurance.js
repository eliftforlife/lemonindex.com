// 11-25 /insurance/ tool (insurance_pages.py). Runs in the browser and saves nothing: picks the state's official sample driver closest to the
// visitor (same rule as insurance_pages.py _ins_pick) or shows the anchored estimate. "Add what you pay" posts to the lemon-survey Worker (/ins).
(() => {
  const root = document.querySelector('.ins[data-ins]'); if (!root) return;
  const W = 'https://lemon-survey.elift08.workers.dev';
  const form = document.getElementById('insf'), out = document.getElementById('ins-out'), add = document.getElementById('add'), af = document.getElementById('insaf');
  let D = null, P = null; const load = () => P || (P = fetch('/assets/insurance.json?v=1').then(r => r.json()).then(j => (D = j)));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = v => '$' + Math.round(v).toLocaleString('en-US');
  const AGES = ['16-17', '18-20', '21-24', '25-29', '30-39', '40-59', '60-69', '70+'];
  const ag = a => a <= 17 ? 0 : a <= 20 ? 1 : a <= 24 ? 2 : a <= 29 ? 3 : a <= 39 ? 4 : a <= 59 ? 5 : a <= 69 ? 6 : 7;
  const REC = { clean: 'a clean record', ticket: 'a ticket', accident: 'an at-fault accident', dui: 'a DUI' };
  const RECS = { clean: 'clean record', ticket: 'ticket', accident: 'accident', dui: 'DUI' };
  const CAR = { regular: 'regular car', truck: 'truck', sports: 'sports car', super: 'supercar' };
  const sel = { rec: 'clean', kind: 'regular' };

  form.querySelectorAll('.ins-c').forEach(b => b.addEventListener('click', () => {
    const g = b.dataset.rec ? 'rec' : 'kind'; sel[g] = b.dataset[g];
    form.querySelectorAll(`.ins-c[data-${g}]`).forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  }));
  const setChip = (g, v) => { const b = form.querySelector(`.ins-c[data-${g}="${v}"]`); if (b) b.click(); };

  function pick(st, age, rec, kind) {
    const gs = (st.off && st.off.groups) || []; let best = null, bs = 1e9;
    for (const g of gs) {
      const a = g.age == null ? 15 : Math.abs(g.age - age);
      const k = g.kind === kind || ((kind === 'sports' || kind === 'super') && g.kind === 'regular') ? 0 : (g.kind === 'truck' || g.kind === 'regular') ? 8 : 10;
      const s = a + (g.rec === rec ? 0 : 12) + k + (g.cpl ? 1 : 0) + (g.cov === 'full' ? 0 : 2);
      if (s < bs) { bs = s; best = g; }
    }
    return best;
  }
  const est = (st, age, rec) => st.est[ag(age)] * (rec === 'clean' ? 1 : st.rm[rec]);

  function list(g, cap) {
    const rows = g.rows.filter(r => r[0] !== 'USAA'), us = g.rows.find(r => r[0] === 'USAA'), mx = Math.max(...g.rows.map(r => r[1]), 1);
    const li = (r, n, cls) => `<li class="ins-r${cls}" title="${esc(r[2])}"><span class="ins-n">${n}</span><span class="ins-nm">${esc(r[0])}${n === '' ? '<small>Military families only</small>' : ''}</span>`
      + `<span class="ins-bar"><i style="width:${Math.max(3, r[1] / mx * 100).toFixed(0)}%"></i></span><span class="ins-p">${$(r[1])}</span></li>`;
    const capped = cap && rows.length > cap;
    return `<ol class="ins-list${capped ? ' ins-cap' : ''}">` + rows.map((r, i) => li(r, i + 1, (i ? '' : ' ins-top') + (capped && i >= cap ? ' ins-more' : ''))).join('')
      + (us ? li(us, '', ' ins-usaa') : '') + '</ol>' + (capped ? `<button type="button" class="ins-all">Show all ${rows.length} companies</button>` : '');
  }

  function render(code, age, rec, kind) {
    const st = D.states[code], m = D.meta, f = m.car[kind] || 1, e = m.err / 100;
    const you = `<p class="ins-you">${age} · ${RECS[rec]} · ${CAR[kind]} · ${esc(st.n)}</p>`;
    const carNote = kind === 'regular' ? '' : kind === 'truck'
      ? `<p class="ins-adj"><b>Truck:</b> about the same as a regular car. <span class="ins-est">Estimate</span> Car-type adjustment is our estimate.</p>`
      : `<p class="ins-adj"><b>${kind === 'super' ? 'Supercar' : 'Sports car'}:</b> expect about ${f}× these prices. <span class="ins-est">Estimate</span> Car-type adjustment is our estimate.</p>`;
    const g = pick(st, age, rec, kind);
    if (g) {
      const o = st.off, rows = g.rows.filter(r => r[0] !== 'USAA'), top = rows[0] || g.rows[0];
      const notes = [];
      if (g.rec !== rec) notes.push(`${esc(st.n)} doesn't publish prices for a driver with ${REC[rec]} near your age, so this list is for ${REC[g.rec] || esc(g.lab.split(', ')[1])}. ${rec === 'clean' ? '' : `In ${esc(st.n)}, ${REC[rec]} usually adds about ${Math.round((st.rm[rec] - 1) * 100)}% <span class="ins-est">Estimate</span>`}`);
      if (g.age != null && ag(g.age) !== ag(age)) notes.push(`No sample driver your age in ${esc(st.n)}'s guide: the closest is ${esc(g.lab.split(', ')[0].replace(/^Age/, 'age'))}. Use the order, not the price.`);
      const full = g.cov !== 'full' || o.stale || ag(g.age ?? age) !== ag(age) || g.rec !== rec;
      const places = g.nloc > 1 ? `, middle price across ${g.nloc} ${esc(st.n)} sample places` : '';
      out.innerHTML = you + `<div class="ins-card"><div class="ins-big">${notes.length ? 'Cheapest for the closest sample driver' : 'Cheapest for you'}<b>${esc(top[0])} · ${$(top[1])}/mo</b></div>`
        + (f !== 1 ? `<p class="ins-adj">For a ${CAR[kind]}: about ${$(top[1] * f)}/mo at ${esc(top[0])}. <span class="ins-est">Estimate</span> Car-type adjustment is our estimate.</p>` : (kind === 'truck' ? carNote : ''))
        + notes.map(n => `<p class="ins-adj">${n}</p>`).join('') + list(g, 10)
        + `<p class="ins-src">Source: <a href="${esc(o.url)}" rel="noopener nofollow" target="_blank">${esc(o.who)}</a>, ${esc(o.what)}. Their sample driver: ${esc(g.lab.charAt(0).toLowerCase() + g.lab.slice(1))}${places}. Your own quote will differ: use this to know who to call first.</p>`
        + (o.note ? `<p class="ins-note">${esc(o.note)}</p>` : '') + '</div>'
        + (full ? `<p class="ins-extra">Typical full-coverage price for you: about ${$(est(st, age, rec) * f)}/mo <span class="ins-est">Estimate</span></p>` : '');
      add.querySelector('.ins-open').hidden = false; af.hidden = true; add.querySelector('.ins-open').setAttribute('aria-expanded', 'false');
    } else {
      const v = est(st, age, rec) * f, lo = v * (1 - e), hi = v * (1 + e);
      const tool = st.tool ? `<p>${esc(st.n)}'s insurance department publishes its own comparison by company, which we haven't added yet: <a href="${esc(st.tool[0])}" rel="noopener nofollow" target="_blank">${esc(st.tool[1])}</a>.</p>` : '';
      out.innerHTML = you + `<div class="ins-card"><div class="ins-big">Typical price for you <span class="ins-est">Estimate</span><b>About ${$(v)}/mo</b></div>`
        + `<div class="ins-rb"><i></i></div><div class="ins-range"><span>${$(lo)}</span><span>likely range</span><span>${$(hi)}</span></div>` + carNote
        + `<p class="ins-src">${esc(st.n)} doesn't publish prices by company, so this is our estimate: the official NAIC 2024 average for ${esc(st.n)}, adjusted for your age and record. In states that do publish prices, our estimates were off by about ${m.err}% up or down, so treat it as a rough guide, not a quote.</p></div>`
        + `<div class="ins-warn"><p><b>Which company is cheapest?</b> We don't know yet for ${esc(st.n)}, and we won't guess. Every price people add below gets us closer.</p>${tool}</div>`;
      add.querySelector('.ins-open').hidden = true; af.hidden = false;
    }
    add.hidden = false; add.querySelector('.ins-stn').textContent = st.n;
    add.dataset.st = code; add.dataset.rec = rec; add.dataset.kind = kind;
    add.querySelector('.ins-for').textContent = `For: ${st.n} · ${RECS[rec]} · ${CAR[kind]} (change it above)`;
    if (!af.elements.age.value) af.elements.age.value = age;
  }

  out.addEventListener('click', e => { const b = e.target.closest('.ins-all'); if (!b) return; b.previousElementSibling.classList.add('ins-open'); b.remove(); });
  root.addEventListener('click', e => { const b = e.target.closest('.ins-all'); if (!b || out.contains(b)) return; b.previousElementSibling.classList.add('ins-open'); b.remove(); });

  async function run(scroll) {
    const code = form.elements.st.value; if (!code) { form.elements.st.focus(); return; }
    await load(); const age = +form.elements.age.value || 35;
    render(code, age, sel.rec, sel.kind);
    try { history.replaceState(null, '', `#st=${code}&age=${age}&rec=${sel.rec}&car=${sel.kind}`); } catch (e) {}
    if (scroll) out.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  form.addEventListener('submit', e => { e.preventDefault(); run(true); });

  // links like /insurance/#car=truck (car year pages) or a shared #st=NV&age=30&rec=clean&car=regular
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get('car') && CAR[h.get('car')]) setChip('kind', h.get('car'));
  if (h.get('rec') && REC[h.get('rec')]) setChip('rec', h.get('rec'));
  if (h.get('age') && +h.get('age') >= 16 && +h.get('age') <= 85) form.elements.age.value = String(Math.round(+h.get('age')));
  if (h.get('st') && form.querySelector(`option[value="${h.get('st')}"]`)) { form.elements.st.value = h.get('st'); run(false); }
  // a state page opens with its own result already in the HTML: the add box goes with that state
  if (form.dataset.st && !h.get('st')) {
    add.dataset.st = form.dataset.st; add.dataset.rec = 'clean'; add.dataset.kind = 'regular';
    const n = form.elements.st.selectedOptions[0].textContent; add.querySelector('.ins-for').textContent = `For: ${n} · clean record · regular car (change it above)`;
    if (!out.querySelector('.ins-list')) { add.querySelector('.ins-open').hidden = true; af.hidden = false; }
  }

  // ---- Add what you pay (anonymous; stored for review, never shown until Elijah decides how)
  add.querySelector('.ins-open').addEventListener('click', e => { af.hidden = false; e.currentTarget.setAttribute('aria-expanded', 'true'); e.currentTarget.hidden = true; af.elements.company.focus(); });
  const TS = af.dataset.ts; let tsReady = null, wid = null;
  const loadTs = () => { if (!TS || tsReady) return; tsReady = new Promise(res => {
    window.onInsTs = () => res(true);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onInsTs&render=explicit'; s.async = true; s.onerror = () => res(false); document.head.appendChild(s);
  }); };
  const token = async () => {
    if (!TS) return ''; loadTs(); if (!(await tsReady) || !window.turnstile) return '';
    return new Promise(res => {
      let done = false; const fin = t => { if (!done) { done = true; res(t || ''); } }; setTimeout(() => fin(''), 120000);
      if (wid === null) wid = turnstile.render(af.querySelector('.ins-ts'), { sitekey: TS, theme: 'light', size: 'flexible', appearance: 'interaction-only', execution: 'execute', callback: fin, 'error-callback': () => fin('') });
      else turnstile.reset(wid);
      turnstile.execute(wid);
    });
  };
  af.addEventListener('focusin', loadTs, { once: true });
  const msg = af.querySelector('.ins-msg');
  const say = (t, ok) => { msg.textContent = t; msg.hidden = false; msg.className = 'ins-msg ' + (ok ? 'ok' : 'bad'); };
  const ERR = { bad: 'Please check your age and state.', usd: 'Please enter what you pay per month, in dollars (20 to 3,000).', company: 'Please type the company name only.',
    car: 'Please type the car as year, make and model (no links or numbers like phone numbers).', day: 'That’s the most prices for today. Thanks!', state: 'You already added a price for this state. Thanks!',
    limit: 'Too many tries. Wait a minute and try again.', vpn: 'Prices can’t be sent from a VPN or data-center network.', human: 'The human check didn’t go through. Try again.', busy: 'We’re getting a lot of prices today. Try again tomorrow.' };
  af.addEventListener('submit', async e => {
    e.preventDefault(); msg.hidden = true;
    const st = add.dataset.st; if (!st) return say('Pick your state above first.');
    const age = Math.round(+af.elements.age.value), usd = Math.round(+af.elements.usd.value), company = af.elements.company.value.trim();
    if (!(age >= 16 && age <= 99)) return say('Please enter your age (16 to 99).');
    if (!company) return say('Please enter your insurance company.');
    if (!(usd >= 20 && usd <= 3000)) return say(ERR.usd);
    const cm = af.elements.car.value.trim().match(/^((?:19|20)\d\d)\s+(.*)$/), car = (cm ? cm[2] : af.elements.car.value).trim(), cyear = cm ? +cm[1] : null;
    const btn = af.querySelector('button[type=submit]'); btn.disabled = true; btn.textContent = 'Sending…';
    try {
      const body = { st, age, rec: add.dataset.rec || 'clean', kind: add.dataset.kind || 'regular', company, usd, cyear, car, hp: af.elements.hp.value, t: await token() };
      const r = await fetch(`${W}/ins`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (j.ok) { af.querySelectorAll('.ins-in,.ins-lock,button[type=submit]').forEach(x => { x.hidden = true; }); say('Thanks! Your price is saved anonymously. Prices like yours get added after a check.', true); }
      else say(ERR[j.error] || 'That didn’t go through. Try again in a minute.');
    } catch (x) { say('That didn’t go through. Check your connection and try again.'); }
    btn.disabled = false; btn.textContent = 'Add my price';
  });
})();

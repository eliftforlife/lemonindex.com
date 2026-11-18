// 11-18 owner opinions box (#opinions on model and year pages, built by opinions.py). Posts to the lemon-survey Worker (POST /op), which
// checks each opinion (rules + AI) and shows only approved ones. Limits live in the Worker: one per car per 30 days, 10 a day.
// The approved list is baked into the page at build time; this script also loads the newest from GET /ops so a new one shows at once.
(() => {
  const box = document.getElementById('opinions'); if (!box) return;
  const W = 'https://lemon-survey.elift08.workers.dev', fid = box.dataset.fid, car = box.dataset.car, TS = box.dataset.ts || '', Y = +box.dataset.y || 0;
  const list = box.querySelector('.opn-l'), head = box.querySelector('.opn-h'), form = box.querySelector('.opn-f'), open = box.querySelector('.opn-open'), msg = box.querySelector('.opn-msg');
  const KIND = { owner: 'Owner', former: 'Former owner', drove: 'Drove one', opinion: 'Opinion' };
  const MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const el = (t, c, txt) => { const e = document.createElement(t); if (c) e.className = c; if (txt != null) e.textContent = txt; return e; };
  const item = o => {
    const a = el('article', 'opn-i'), h = el('header'), d = new Date(o.ts);
    h.append(el('b', '', o.name || 'Anonymous'));
    const meta = [KIND[o.kind] || 'Opinion', o.year ? String(o.year) : '', o.buy === 'yes' ? 'Would buy again' : o.buy === 'no' ? 'Wouldn’t buy again' : ''].filter(Boolean).join(' · ');
    h.append(el('span', 'opn-m', meta)); const tm = el('time', '', `${MN[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`); tm.dateTime = d.toISOString().slice(0, 10); h.append(tm);
    a.append(h); for (const para of String(o.text).split(/\n+/)) a.append(el('p', '', para)); return a;
  };
  const render = ops => {
    if (!ops.length) return;
    ops = ops.slice().sort((a, b) => (Y && (b.year === Y) - (a.year === Y)) || b.ts - a.ts);
    list.replaceChildren(...ops.slice(0, 8).map(item)); head.hidden = false;
    if (ops.length > 8) { const m = el('button', 'opn-more', `Show all ${ops.length}`); m.type = 'button'; m.onclick = () => { list.replaceChildren(...ops.map(item)); }; list.append(m); }
  };
  fetch(`${W}/ops?fid=${encodeURIComponent(fid)}`).then(r => r.json()).then(j => j.ops && render(j.ops)).catch(() => {});

  // ---- form
  open.addEventListener('click', () => { form.hidden = false; open.hidden = true; form.querySelector('textarea').focus(); loadTs(); });
  const anon = form.elements.anon, nameRow = form.querySelector('.opn-name');
  const syncAnon = () => { nameRow.hidden = anon.checked; }; anon.addEventListener('change', syncAnon); syncAnon();
  const ta = form.elements.text, cnt = form.querySelector('.opn-c');
  ta.addEventListener('input', () => { cnt.textContent = `${ta.value.trim().length}/800`; });
  const say = (t, ok) => { msg.textContent = t; msg.hidden = false; msg.className = 'opn-msg' + (ok ? ' ok' : ''); };

  let tsReady = null, wid = null;
  const loadTs = () => { if (!TS || tsReady) return; tsReady = new Promise(res => {
    window.onOpTs = () => res(true);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onOpTs&render=explicit'; s.async = true; s.onerror = () => res(false); document.head.appendChild(s);
  }); };
  const token = async () => {
    if (!TS) return ''; loadTs(); if (!(await tsReady) || !window.turnstile) return '';
    return new Promise(res => {
      let done = false; const fin = t => { if (!done) { done = true; res(t || ''); } }; setTimeout(() => fin(''), 120000);
      if (wid === null) wid = turnstile.render(form.querySelector('.opn-ts'), { sitekey: TS, theme: 'light', size: 'flexible', appearance: 'interaction-only', execution: 'execute', callback: fin, 'error-callback': () => fin('') });
      else turnstile.reset(wid);
      turnstile.execute(wid);
    });
  };
  const ERR = { length: 'Please write between 20 and 800 characters.', name: 'Names can only use letters, spaces, dots, dashes and apostrophes.', car: 'You already shared an opinion on this car. One per car, please.',
    day: 'That’s 10 opinions today. Come back tomorrow.', limit: 'Too many tries. Wait a minute and try again.', vpn: 'Opinions can’t be posted from a VPN or data-center network.', human: 'The human check didn’t go through. Try again.' };
  form.addEventListener('submit', async e => {
    e.preventDefault(); const btn = form.querySelector('button[type=submit]'); msg.hidden = true;
    const text = ta.value.trim(); if (text.length < 20) return say(ERR.length);
    if (!anon.checked && !form.elements.name.value.trim()) return say('Add your name, or tick "Post as Anonymous".');
    btn.disabled = true; btn.textContent = 'Checking…';
    try {
      const t = await token();
      const body = { fid, car, text, year: form.elements.year.value || null, kind: form.elements.kind.value, buy: (form.querySelector('input[name=buy]:checked') || {}).value || '',
        anon: anon.checked, name: anon.checked ? '' : form.elements.name.value.trim(), hp: form.elements.website.value, t };
      if (body.year) body.year = +body.year;
      const r = await fetch(`${W}/op`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (j.error) say(ERR[j.error] || 'Something went wrong. Try again in a minute.');
      else if (j.status === 'approved') { form.hidden = true; say('Thanks! Your opinion is up.', true); head.hidden = false; if (j.op) list.prepend(item(j.op)); }
      else if (j.status === 'pending') { form.hidden = true; say('Thanks! It’s waiting for its check and will show within the hour if it passes.', true); }
      else say(`It wasn’t posted: ${j.reason || 'it didn’t pass review.'} You can edit it and try again.`);
    } catch (err) { say('Couldn’t reach the server. Check your connection and try again.'); }
    btn.disabled = false; btn.textContent = 'Post opinion';
  });
})();

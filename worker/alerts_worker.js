// lemon-alerts Worker (11-14, growth plan 4a): "Get an email if your car gets a recall" for lemonindex.com.
// Cloudflare Worker + D1 (binding DB -> database lemon-alerts) + a cron trigger (alerts.toml). Deploy: worker/make_alerts.py, then
// `npx.cmd --yes wrangler deploy -c alerts.toml` from worker/. Schema: alerts_schema.sql (wrangler d1 execute lemon-alerts --remote --file ...).
//
// What it stores, per alert (table subs): the email, the model year, the NHTSA make + model names (max 2, the same ones the site's
// recall lists use), the Lemon page id when we cover the model, a confirm token (cleared once used) and an unsubscribe token, plus
// timestamps and the recall campaign numbers already sent. Never a VIN, never an IP address. A per-day salted IP hash (table hits) only
// caps repeat signups and is deleted after 2 days. Unsubscribing deletes every row for that email.
//
// Double opt-in: nothing but the confirm email goes to an address until its owner taps the confirm link (lemonindex.com/alerts/#c=...).
// Every email carries a one-click unsubscribe (List-Unsubscribe + List-Unsubscribe-Post header -> POST /unsub?t=..., and a link in the body).
//
// Sending is OFF until env SEND_ENABLED = "1" (set once lemonindex.com is verified in Resend). While off, signups are saved as pending
// ("queued") and the cron sends their confirm emails once sending is on; pending rows that never get confirmed are deleted after 30 days.
//
// Routes (CORS: lemonindex.com only, except the one-click unsubscribe, which mail providers POST without an Origin):
//   POST /signup  {email, y, n: [[MAKE, MODEL]], f?, hp, t?}   -> {ok, queued}
//                 {email, cars: [{y, n, f?}, ...] (max 5), hp, t?} -> {ok, queued, cars: [{ok} | {error}]}   (11-15, the /saved/ "My cars" page:
//                 one Turnstile check, one confirm token for the whole batch, so ONE confirm email and one tap starts every car in it)
//   POST /info    {c} or {u}                                    -> {name, y, url}     (for the /alerts/ page; no email returned)
//   POST /confirm {c}                                           -> {ok, name, url}    (every pending car on that confirm token)
//   POST /unsub   {u}  or  POST /unsub?t=<u> (one-click)        -> {ok, n}
//   GET  /unsub?t=<u>                                           -> 302 to lemonindex.com/alerts/#u=<u>
// Cron (*/15): cleanup, queued confirm emails, then up to CARS_PER_RUN cars due for their weekly NHTSA check; new campaigns -> one email
// per subscriber. A daily send cap (DAILY_CAP, Resend's free plan is 100 a day across the account) holds the rest for the next run.
const CARS = __CARS__;            // Lemon page id -> model name (assets/cars.json)
const PAIRS = new Set(__PAIRS__); // NHTSA "MAKE|MODEL" pairs our pages use (data/extras_local*.json), letters and digits only
const SITE = 'https://lemonindex.com', SELF = 'https://lemon-alerts.elift08.workers.dev';
const ORIGINS = [SITE, 'https://www.lemonindex.com'];
const ADDRESS = 'The Lemon Index · Westbrook Software LLC · 4539 N 22nd St Ste R, Phoenix, AZ 85016';
const DAY = 864e5, WEEK = 7 * DAY, CARS_PER_RUN = 4, MAX_CARS_PER_EMAIL = 5;

const cors = o => ({ 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : SITE, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (o, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(o) } });
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = s => String(s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const tok = () => { const b = crypto.getRandomValues(new Uint8Array(24)); return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const tokOk = t => typeof t === 'string' && /^[A-Za-z0-9_-]{32}$/.test(t);
const on = env => env.SEND_ENABLED === '1' && !!env.RESEND_KEY;
const cap = env => +(env.DAILY_CAP || 80);
const today = () => new Date().toISOString().slice(0, 10);
async function sha(s) { const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join(''); }

// "HONDA" "CR-V" -> "Honda CR-V": words with a digit or hyphen, and short ones, stay as NHTSA writes them
const MAKES = { 'MERCEDES-BENZ': 'Mercedes-Benz', 'ALFA ROMEO': 'Alfa Romeo', 'LAND ROVER': 'Land Rover', 'ASTON MARTIN': 'Aston Martin', BMW: 'BMW', GMC: 'GMC', MINI: 'MINI', KIA: 'Kia', RAM: 'Ram', VOLKSWAGEN: 'Volkswagen' };
const tc = w => /\d|-/.test(w) || w.length <= 3 ? w : w[0] + w.slice(1).toLowerCase();
const carName = (y, names, fid) => CARS[fid] ? `${y} ${CARS[fid]}` : `${y} ${MAKES[names[0][0]] || names[0][0].split(' ').map(tc).join(' ')} ${names[0][1].split(' ').map(tc).join(' ')}`;
const carUrl = (y, fid) => CARS[fid] ? `${SITE}/cars/${fid}/${y}/` : `${SITE}/vin/`;
const nhtsaUrl = (y, names) => `https://www.nhtsa.gov/vehicle/${y}/${encodeURIComponent(names[0][0])}/${encodeURIComponent(names[0][1])}`;

// every NHTSA recall campaign for a model year (up to 2 make/model names, the way the site's recall lists are built)
async function recallsFor(y, names) {
  const out = {};
  for (const [mk, md] of names) {
    const r = await fetch(`https://api.nhtsa.gov/recalls/recallsByVehicle?make=${encodeURIComponent(mk)}&model=${encodeURIComponent(md)}&modelYear=${y}`, { headers: { 'User-Agent': 'lemonindex.com recall alerts' } });
    if (!r.ok) throw new Error('nhtsa ' + r.status);
    for (const x of ((await r.json()).results || [])) {
      const id = x.NHTSACampaignNumber; if (!id || out[id]) continue;
      out[id] = { id, part: String(x.Component || 'Recall').split(':')[0], date: x.ReportReceivedDate || '', summary: x.Summary || '', remedy: x.Remedy || '' };
    }
  }
  return out;
}

async function send(env, msgs) {   // msgs: [{to, subject, html, text, unsub?}] -> true when Resend accepted them all
  if (!msgs.length) return true;
  const day = today();
  const used = (await env.DB.prepare('SELECT n FROM sends WHERE day = ?').bind(day).first('n')) || 0;
  if (used + msgs.length > cap(env)) return false;
  const body = msgs.map(m => ({ from: env.FROM || 'Lemon Index <recalls@lemonindex.com>', to: [m.to], subject: m.subject, html: m.html, text: m.text,
    reply_to: env.REPLY_TO || 'hello@elijahwestbrook.com',
    ...(m.unsub ? { headers: { 'List-Unsubscribe': `<${SELF}/unsub?t=${m.unsub}>`, 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' } } : {}) }));
  const r = await fetch(body.length === 1 ? 'https://api.resend.com/emails' : 'https://api.resend.com/emails/batch', { method: 'POST',
    headers: { Authorization: `Bearer ${env.RESEND_KEY}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body.length === 1 ? body[0] : body) });
  if (!r.ok) { console.log('resend', r.status, (await r.text()).slice(0, 300)); return false; }
  console.log('resend ok', msgs.length, (await r.text()).slice(0, 300));   // email ids only, never addresses
  await env.DB.prepare('INSERT INTO sends (day, n) VALUES (?, ?) ON CONFLICT(day) DO UPDATE SET n = n + excluded.n').bind(day, msgs.length).run();
  return true;
}

// ---- emails: plain, light, one action each
const shell = (inner, foot) => `<!doctype html><html><body style="margin:0;background:#f5f5f7"><div style="max-width:560px;margin:0 auto;padding:28px 18px;font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#1d1d1f">
<p style="margin:0 0 18px;font-weight:700;font-size:15px">The Lemon Index</p><div style="background:#fff;border-radius:18px;padding:24px 22px">${inner}</div>
<p style="margin:18px 4px 0;font-size:13px;line-height:1.5;color:#6e6e73">${foot}</p></div></body></html>`;
const btn = (href, label) => `<p style="margin:22px 0 6px"><a href="${esc(href)}" style="display:inline-block;background:#1d1d1f;color:#fff;text-decoration:none;font-weight:700;border-radius:999px;padding:12px 24px">${esc(label)}</a></p>`;
const rowName = r => carName(r.y, JSON.parse(r.car), r.fid);
const andList = a => a.length < 2 ? (a[0] || '') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
function confirmMail(rows) {   // one row, or (11-15) every row of one /saved/ signup batch: same address, same confirm token, one email
  rows = Array.isArray(rows) ? rows : [rows];
  const row = rows[0], names = rows.map(rowName), name = andList(names), link = `${SITE}/alerts/#c=${row.ctok}`, many = rows.length > 1;
  const what = many ? 'one of these model years' : 'this model year';
  const list = many ? `<ul style="margin:12px 0 0;padding-left:20px">${names.map(n => `<li>${esc(n)}</li>`).join('')}</ul>` : '';
  return { to: row.email, subject: many ? `Confirm recall alerts for your ${rows.length} cars` : `Confirm recall alerts for your ${name}`,
    html: shell(`<h1 style="margin:0 0 10px;font-size:22px;line-height:1.25">Confirm recall alerts for ${many ? `your ${rows.length} cars` : `the ${esc(name)}`}</h1>
<p style="margin:0">Tap the button to start${many ? ' alerts for all of them' : ''}. We check the U.S. government&#39;s (NHTSA) recall list every week and email you only when a new recall is added for ${what}.</p>${list}${btn(link, 'Yes, send me recall alerts')}
<p style="margin:14px 0 0;font-size:14px;color:#6e6e73">Didn&#39;t ask for this? Ignore this email and nothing else will be sent. The link works for 7 days.</p>`,
      `You got this because someone entered this address for recall alerts on lemonindex.com.<br>${esc(ADDRESS)}`),
    text: `Confirm recall alerts for the ${name}\n\nOpen this link to start: ${link}\n\nWe check NHTSA's recall list every week and email you only when a new recall is added for ${what}.\nDidn't ask for this? Ignore this email and nothing else will be sent. The link works for 7 days.\n\n${ADDRESS}` };
}
const sentence = (s, n = 320) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 20).replace(/\s\S*$/, '') + '…' : s; };
// the defect in plain words: drop NHTSA's "X is recalling certain 2013-2023 ... vehicles." opener (same idea as rsum() in build.py)
const defect = s => { s = String(s || '').replace(/\s+/g, ' ').trim(); const t = s.replace(/^.*?\brecalling\b.*?\b(vehicles|trucks|pick-ups|pickups|cars|SUVs|equipment|tires|seats|motorcycles)\b(?:[^.]|\.(?=\d))*?(?<!\bCo)(?<!\bInc)\.(?!\d)\s*/i, ''); return sentence(t.length >= 25 ? t : s); };
const first = s => sentence((String(s || '').replace(/\s+/g, ' ').trim().match(/^.*?[a-z)]\.(?=\s|$)/) || [String(s || '')])[0], 220);
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const usDate = d => { const m = String(d || '').match(/^(\d{2})\/(\d{2})\/(\d{4})/); return m ? `${MON[+m[2] - 1]} ${+m[1]}, ${m[3]}` : ''; };
function recallMail(row, recs) {
  const names = JSON.parse(row.car), name = carName(row.y, names, row.fid), page = carUrl(row.y, row.fid), un = `${SITE}/alerts/#u=${row.utok}`;
  const part = p => p.toLowerCase().replace(/\b\w/, c => c.toUpperCase());
  const subject = recs.length === 1 ? `New recall: ${name} (${part(recs[0].part).slice(0, 40)})` : `${recs.length} new recalls: ${name}`;
  const items = recs.map(r => `<div style="border-top:1px solid #e5e5ea;padding:16px 0 4px"><p style="margin:0 0 4px;font-weight:700">${esc(part(r.part))}</p>
<p style="margin:0 0 8px;font-size:13px;color:#6e6e73">NHTSA campaign <a href="https://www.nhtsa.gov/recalls?nhtsaId=${esc(r.id)}" style="color:#0066cc">${esc(r.id)}</a>${usDate(r.date) ? ' · issued ' + esc(usDate(r.date)) : ''}</p>
<p style="margin:0 0 8px">${esc(defect(r.summary))}</p>${r.remedy ? `<p style="margin:0 0 8px"><b>Free fix:</b> ${esc(first(r.remedy))}</p>` : ''}</div>`).join('');
  return { to: row.email, unsub: row.utok, subject,
    html: shell(`<h1 style="margin:0 0 10px;font-size:22px;line-height:1.25">${recs.length === 1 ? 'A new recall' : recs.length + ' new recalls'} for the ${esc(name)}</h1>
<p style="margin:0 0 6px">NHTSA added ${recs.length === 1 ? 'this safety recall' : 'these safety recalls'} for the ${esc(name)}. A recall can cover some or all cars of a model year, so check whether it&#39;s open on yours with its VIN. Recall repairs are free at any dealer.</p>${items}
${btn('https://www.nhtsa.gov/recalls', 'Check your VIN at nhtsa.gov')}<p style="margin:10px 0 0;font-size:15px"><a href="${esc(page)}" style="color:#0066cc">Every recall and problem for the ${esc(name)} on Lemon Index</a> · <a href="${esc(nhtsaUrl(row.y, names))}" style="color:#0066cc">NHTSA&#39;s page for it</a></p>`,
      `You get this because you asked for recall alerts for the ${esc(name)} on lemonindex.com. <a href="${esc(un)}" style="color:#6e6e73">Unsubscribe</a> (one click, deletes your email).<br>${esc(ADDRESS)}`),
    text: `${recs.length === 1 ? 'A new recall' : recs.length + ' new recalls'} for the ${name}\n\nNHTSA added ${recs.length === 1 ? 'this safety recall' : 'these safety recalls'}. A recall can cover some or all cars of a model year, so check whether it's open on yours with its VIN at https://www.nhtsa.gov/recalls. Recall repairs are free at any dealer.\n\n`
      + recs.map(r => `${part(r.part)} (NHTSA ${r.id}${usDate(r.date) ? ', issued ' + usDate(r.date) : ''})\n${defect(r.summary)}${r.remedy ? '\nFree fix: ' + first(r.remedy) : ''}\nhttps://www.nhtsa.gov/recalls?nhtsaId=${r.id}`).join('\n\n')
      + `\n\nOn Lemon Index: ${page}\n\nUnsubscribe (deletes your email): ${un}\n${ADDRESS}` };
}

// ---- the 15-minute job
async function run(env) {
  const now = Date.now(), DB = env.DB;
  await DB.batch([
    DB.prepare("DELETE FROM subs WHERE status = 'pending' AND ((conf_sent IS NULL AND created < ?) OR (conf_sent IS NOT NULL AND conf_sent < ?))").bind(now - 30 * DAY, now - WEEK),
    DB.prepare('DELETE FROM hits WHERE day < ?').bind(new Date(now - 2 * DAY).toISOString().slice(0, 10)),
    DB.prepare('DELETE FROM sends WHERE day < ?').bind(new Date(now - 40 * DAY).toISOString().slice(0, 10))]);
  if (!on(env)) return { off: true };
  // 1. confirm emails for signups saved while sending was off
  const q = (await DB.prepare("SELECT * FROM subs WHERE status = 'pending' AND conf_sent IS NULL ORDER BY id LIMIT 40").all()).results;
  const grp = new Map(); q.forEach(r => { const k = r.email + '|' + r.ctok; grp.set(k, [...(grp.get(k) || []), r]); });   // a /saved/ batch = one email
  if (q.length && await send(env, [...grp.values()].map(confirmMail)))
    await DB.batch(q.map(r => DB.prepare('UPDATE subs SET conf_sent = ?, conf_n = conf_n + 1 WHERE id = ?').bind(now, r.id)));
  // 2. weekly recall check, a few cars per run
  const due = (await DB.prepare("SELECT y, car FROM subs WHERE status = 'active' AND (checked IS NULL OR checked < ?) GROUP BY y, car ORDER BY MIN(COALESCE(checked, 0)) LIMIT ?").bind(now - WEEK, CARS_PER_RUN).all()).results;
  let mailed = 0, checked = 0;
  for (const c of due) {
    let recs; try { recs = await recallsFor(c.y, JSON.parse(c.car)); } catch (e) { console.log('nhtsa failed', c.y, c.car, String(e)); continue; }
    const ids = Object.keys(recs), subs = (await DB.prepare("SELECT * FROM subs WHERE status = 'active' AND y = ? AND car = ?").bind(c.y, c.car).all()).results;
    const quiet = [], mails = [];
    for (const s of subs) {
      if (s.seen == null) { quiet.push(DB.prepare('UPDATE subs SET seen = ?, checked = ? WHERE id = ?').bind(JSON.stringify(ids), now, s.id)); continue; }
      const seen = new Set(JSON.parse(s.seen)), fresh = ids.filter(i => !seen.has(i));
      if (!fresh.length) { quiet.push(DB.prepare('UPDATE subs SET checked = ? WHERE id = ?').bind(now, s.id)); continue; }
      mails.push([s, recallMail(s, fresh.map(i => recs[i]))]);
    }
    if (quiet.length) await DB.batch(quiet);
    if (mails.length) {
      if (!(await send(env, mails.map(m => m[1])))) break;   // over the daily cap or Resend said no: these stay due for the next run
      await DB.batch(mails.map(([s]) => DB.prepare('UPDATE subs SET seen = ?, checked = ? WHERE id = ?').bind(JSON.stringify([...new Set([...JSON.parse(s.seen), ...ids])]), now, s.id)));
      mailed += mails.length;
    }
    checked++;
  }
  return { queued: q.length, checked, mailed };
}

async function realCar(y, names) {   // names our pages use pass straight away; anything else (a decoded VIN) must be a vPIC model for that year
  if (names.every(([mk, md]) => PAIRS.has(norm(mk) + '|' + norm(md)))) return true;
  if (names.length !== 1) return false;
  const [mk, md] = names[0];
  try {
    const r = await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/${encodeURIComponent(mk)}/modelyear/${y}?format=json`);
    return r.ok && ((await r.json()).Results || []).some(m => norm(m.Model_Name) === norm(md));
  } catch (e) { return false; }
}

export default {
  async scheduled(ev, env, ctx) { ctx.waitUntil(run(env).then(r => console.log('run', JSON.stringify(r)))); },
  async fetch(req, env, ctx) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url), DB = env.DB, now = Date.now();
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    // one-click unsubscribe (RFC 8058): Gmail/Yahoo POST here with no Origin; a browser opening the header link gets the page
    if (url.pathname === '/unsub' && url.searchParams.has('t')) {
      const t = url.searchParams.get('t');
      if (req.method === 'GET') return Response.redirect(`${SITE}/alerts/#u=${tokOk(t) ? t : ''}`, 302);
      if (req.method === 'POST' && !o) {
        if (tokOk(t)) { const e = await DB.prepare('SELECT email FROM subs WHERE utok = ?').bind(t).first('email'); if (e) await DB.prepare('DELETE FROM subs WHERE email = ?').bind(e).run(); }
        return new Response('Unsubscribed', { headers: { 'Content-Type': 'text/plain' } });
      }
    }
    if (!ORIGINS.includes(o)) return json(o, { error: 'origin' }, 403);
    if (req.method !== 'POST') return json(o, { error: 'not found' }, 404);
    let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
    const ip = req.headers.get('CF-Connecting-IP') || '';
    if (env.RL && !(await env.RL.limit({ key: url.pathname + ip })).success) return json(o, { error: 'limit' }, 429);

    if (url.pathname === '/signup') {
      // 11-15: one car (the signup box) or a batch of up to 5 (the /saved/ page). A batch answers per car in `cars`, in the order sent.
      const batch = Array.isArray(b.cars), list = batch ? b.cars : [{ y: b.y, n: b.n, f: b.f }];
      if (b.hp) return json(o, { ok: true, queued: !on(env), ...(batch ? { cars: list.slice(0, MAX_CARS_PER_EMAIL).map(() => ({ ok: true })) } : {}) });   // honeypot: only bots fill it in
      const email = typeof b.email === 'string' ? b.email.trim().toLowerCase() : '', maxY = new Date().getUTCFullYear() + 2;
      const clean = c => {
        if (!c || typeof c !== 'object') return null;
        const y = +c.y, names = Array.isArray(c.n) ? c.n.slice(0, 2).map(p => Array.isArray(p) ? [String(p[0] || '').trim().toUpperCase(), String(p[1] || '').trim().toUpperCase()] : null) : [];
        if (!Number.isInteger(y) || y < 1981 || y > maxY || !names.length || names.some(p => !p || !/^[A-Z0-9][A-Z0-9 .&\/-]{0,39}$/.test(p[0]) || !/^[A-Z0-9][A-Z0-9 .&\/+()-]{0,49}$/.test(p[1]))) return null;
        return { y, names, fid: typeof c.f === 'string' && CARS[c.f] ? c.f : null };
      };
      if (!/^[^@\s"<>]{1,64}@[a-z0-9.-]+\.[a-z]{2,}$/.test(email) || email.length > 200) return json(o, { error: 'email' }, 400);
      if (!list.length || list.length > MAX_CARS_PER_EMAIL) return json(o, { error: list.length ? 'max' : 'bad' }, 400);
      const cars = list.map(clean);
      if (cars.every(c => !c)) return json(o, { error: 'bad' }, 400);
      if (env.TURNSTILE_SECRET) {
        const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.t || '')); fd.append('remoteip', ip);
        const ok = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd }).then(r => r.json()).then(j => j.success).catch(() => false);
        if (!ok) return json(o, { error: 'human' }, 403);
      }
      const day = today(), ih = await sha(`${ip}|${day}|${env.SALT || 'lemon-alerts'}|alerts`);
      const nOk = cars.filter(Boolean).length;
      const hits = (await DB.prepare('INSERT INTO hits (ih, day, n) VALUES (?, ?, ?) ON CONFLICT(ih, day) DO UPDATE SET n = n + excluded.n RETURNING n').bind(ih, day, nOk).first('n')) || nOk;
      if (hits > 10) return json(o, { error: 'limit' }, 429);                               // 10 cars signed up per visitor per day
      if (((await DB.prepare('SELECT COUNT(*) n FROM subs WHERE created >= ?').bind(now - DAY).first('n')) || 0) >= 500) return json(o, { error: 'limit' }, 429);   // flood guard
      let have = (await DB.prepare('SELECT COUNT(*) n FROM subs WHERE email = ?').bind(email).first('n')) || 0;
      const ut = (await DB.prepare('SELECT utok FROM subs WHERE email = ? LIMIT 1').bind(email).first('utok')) || tok();   // one unsubscribe token per address
      const shared = tok(), res = [], rows = [];   // a batch's new rows share one confirm token
      for (const c of cars) {
        if (!c) { res.push({ error: 'bad' }); continue; }
        if (!(await realCar(c.y, c.names))) { res.push({ error: 'car' }); continue; }
        const car = JSON.stringify(c.names);
        let row = await DB.prepare('SELECT * FROM subs WHERE email = ? AND y = ? AND car = ?').bind(email, c.y, car).first();
        if (row && row.status === 'active') { res.push({ ok: true }); continue; }       // already on: same answer, no email
        if (!row) {
          if (have >= MAX_CARS_PER_EMAIL) { res.push({ error: 'max' }); continue; }    // 5 cars per address, counting the ones it already has
          row = await DB.prepare("INSERT INTO subs (email, y, car, fid, status, ctok, utok, created) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?) RETURNING *").bind(email, c.y, car, c.fid, batch ? shared : tok(), ut, now).first();
          have++;
        }
        res.push({ ok: true }); if (!rows.some(r => r.id === row.id)) rows.push(row);
      }
      const extra = batch ? { cars: res } : {};
      if (!rows.length && !res.some(r => r.ok)) { const er = res.find(r => r.error) || { error: 'bad' }; return json(o, { error: er.error, ...extra }, 400); }
      if (!on(env)) {   // saved as pending; a batch's rows (none emailed yet) all move to its token, so the cron sends them ONE confirm email
        const mv = batch ? rows.filter(r => r.ctok !== shared && !r.conf_sent) : [];
        if (mv.length) await DB.batch(mv.map(r => DB.prepare('UPDATE subs SET ctok = ? WHERE id = ?').bind(shared, r.id)));
        return json(o, { ok: true, queued: true, ...extra });
      }
      // a pending car gets at most 3 confirm emails, 10+ minutes apart; the ones due now go out together in one email on one token
      const due = rows.filter(r => r.conf_n < 3 && (!r.conf_sent || now - r.conf_sent > 6e5));
      if (due.length) {
        const t = batch ? shared : (due[0].ctok || tok());
        due.forEach(r => { r.ctok = t; });
        if (!(await send(env, [confirmMail(due)]))) return json(o, { error: 'busy' }, 503);
        await DB.batch(due.map(r => DB.prepare('UPDATE subs SET ctok = ?, conf_sent = ?, conf_n = conf_n + 1 WHERE id = ?').bind(t, now, r.id)));
      }
      return json(o, { ok: true, queued: false, ...extra });
    }
    if (url.pathname === '/info') {
      const rs = tokOk(b.c) ? (await DB.prepare("SELECT y, car, fid FROM subs WHERE ctok = ? AND status = 'pending' ORDER BY id").bind(b.c).all()).results
        : tokOk(b.u) ? [await DB.prepare('SELECT y, car, fid FROM subs WHERE utok = ? LIMIT 1').bind(b.u).first()].filter(Boolean) : [];
      if (!rs.length) return json(o, { error: 'gone' }, 404);
      return json(o, { name: andList(rs.map(rowName)), y: rs[0].y, url: carUrl(rs[0].y, rs[0].fid), cars: rs.length });
    }
    if (url.pathname === '/confirm') {
      if (!tokOk(b.c)) return json(o, { error: 'gone' }, 404);
      const rs = (await DB.prepare("SELECT * FROM subs WHERE ctok = ? AND status = 'pending' AND conf_sent > ? ORDER BY id").bind(b.c, now - WEEK).all()).results;
      if (!rs.length) return json(o, { error: 'gone' }, 404);
      const ups = [];
      let n1 = null;
      for (const r of rs) {
        let seen = null; try { seen = JSON.stringify(Object.keys(await recallsFor(r.y, JSON.parse(r.car)))); } catch (e) { /* the cron sets the baseline */ }
        if (rs.length === 1 && seen) n1 = JSON.parse(seen).length;
        ups.push(DB.prepare("UPDATE subs SET status = 'active', ctok = NULL, confirmed = ?, seen = ?, checked = ? WHERE id = ?").bind(now, seen, seen ? now : null, r.id));
      }
      await DB.batch(ups);
      return json(o, { ok: true, name: andList(rs.map(rowName)), url: carUrl(rs[0].y, rs[0].fid), n: n1, cars: rs.length });
    }
    if (url.pathname === '/unsub') {
      if (!tokOk(b.u)) return json(o, { error: 'gone' }, 404);
      const e = await DB.prepare('SELECT email FROM subs WHERE utok = ?').bind(b.u).first('email');
      if (!e) return json(o, { ok: true, n: 0 });
      const res = await DB.prepare('DELETE FROM subs WHERE email = ?').bind(e).run();
      return json(o, { ok: true, n: res.meta?.changes || 0 });
    }
    return json(o, { error: 'not found' }, 404);
  }
};

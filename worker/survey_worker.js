// "Help our site" answers for lemonindex.com (11-03). Cloudflare Worker + D1 (binding DB -> database lemon-survey).
// POST /a {qid, a, fid?, year?, page}  -> stores one anonymous tap, returns the answer counts for that question
// GET  /r?qid=&fid=&year=              -> answer counts
// GET  /v?site=lemon|bs&period=week|month|6mo|year|all|YYYY-MM   -> vote page: {counts: {qid: {answer: n}}, voters, months} (11-03)
//      votes are the vl_* / vb_* polls in data/votes.json (one vote per poll per visitor per day), counted over the chosen window.
// No accounts, no emails, no free text: only the fixed choices in Q below are accepted. A visitor is a salted daily hash of the IP
// (raw IPs are never stored); one answer per question (per car) per visitor per day, max 100 answers per visitor per day.
// POST /suggest (11-07): tool requests for the comparison pages (table tool_requests).
// POST /apply (11-07): "Want a human to help automate your business?" applications from elijahwestbrook.com/automate/.
//      This is the one route that stores contact details (name, email, optional phone): only what the person types, in its own table
//      (applications), read by Elijah in the D1 dashboard. Fixed choices are checked, free text is length-capped, max 5 per visitor per day.
// Q is generated from data/survey.json + data/votes.json by worker/make_worker.py -> survey_worker.dist.js (the uploaded file).
const Q = __Q__;
const ORIGINS = ['https://lemonindex.com', 'https://www.lemonindex.com', 'https://thebusinessstudy.com', 'https://www.thebusinessstudy.com', 'https://elijahwestbrook.com', 'https://www.elijahwestbrook.com'];
const APPLY = { size: ['Just me', '2-5', '6-20', '21-50', '51+'], hours: ['Under 5', '5-10', '10-20', '20+', 'Not sure'], budget: ['Under $500', '$500-$1,500', '$1,500-$5,000', '$5,000+', 'Not sure yet'],
  when: ['As soon as possible', 'This month', 'In the next 3 months', 'Just exploring'],
  areas: ['Content and social media', 'Ads', 'Sales and leads', 'Customer service', 'Website and SEO', 'Operations and admin', 'Money and finance', 'Hiring and team', 'Legal and compliance', 'Something else'] };
// cloud, hosting and VPN networks (by the network's own name, plus the big ones by number): votes from them are refused
const HOSTING = /amazon|aws|google cloud|google llc|microsoft|azure|digitalocean|linode|akamai|ovh|hetzner|vultr|choopa|contabo|leaseweb|m247|datacamp|cdn77|hostinger|hosting|server|data ?cent(er|re)|cloud|vpn|proxy|colocation|oracle|alibaba|tencent|scaleway|ionos|godaddy|namecheap|packethub|tzulo|quadranet|zenlayer|psychz|frantech|buyvm|g-core|gcore|nforce|worldstream|clouvider/i;
const HOSTING_ASN = new Set([16509, 14618, 15169, 396982, 8075, 14061, 63949, 20473, 16276, 24940, 51167, 60068, 9009, 212238, 136787, 202425, 13335, 31898, 45102, 132203, 62240, 46562, 53667, 21859]);
const PRE = { lemon: 'vl_', bs: 'vb_' }, DAYS = { week: 7, month: 30, '6mo': 182, year: 365 };
const CAR = new Set(Object.keys(Q).filter(k => Q[k].car));
const cors = o => ({ 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (o, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(o) } });
async function counts(env, qid, fid, year) {
  const { results } = CAR.has(qid)
    ? await env.DB.prepare('SELECT answer, COUNT(*) n FROM answers WHERE qid = ? AND fid = ? AND year = ? GROUP BY answer').bind(qid, fid, year).all()
    : await env.DB.prepare('SELECT answer, COUNT(*) n FROM answers WHERE qid = ? GROUP BY answer').bind(qid).all();
  return Object.fromEntries(results.map(r => [r.answer, r.n]));
}
// 11-07 automations: email Elijah the moment someone applies for human help or sends a tool request. Uses Resend with the
// RESEND_KEY Worker secret (Elijah adds it in the dashboard; until then nothing is sent and the forms work as before).
// Sender = the already verified send.curbdibs.com domain (internal alerts only; applicant auto-replies wait for an EW domain).
const ALERT_TO = 'hello@elijahwestbrook.com', ALERT_FROM = 'Westbrook alerts <alerts@send.curbdibs.com>';
const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
async function alertMail(env, subject, rows, replyTo) {
  if (!env.RESEND_KEY) return;
  const html = '<table style="font:14px/1.5 -apple-system,Segoe UI,Arial">' + rows.filter(([, v]) => v && String(v).length).map(([k, v]) => `<tr><td style="color:#666;padding:4px 12px 4px 0;vertical-align:top">${esc(k)}</td><td style="padding:4px 0">${esc(Array.isArray(v) ? v.join(', ') : v)}</td></tr>`).join('') + '</table>';
  try {
    await fetch('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: `Bearer ${env.RESEND_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: ALERT_FROM, to: [ALERT_TO], subject, html, ...(replyTo ? { reply_to: replyTo } : {}) }) });
  } catch (e) { /* an alert failure never breaks the form */ }
}

export default {
  async fetch(req, env, ctx) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    if (!ORIGINS.includes(o)) return json(o, { error: 'origin' }, 403);
    const fidOk = s => typeof s === 'string' && /^[a-z0-9/-]{2,40}$/.test(s), yOk = y => Number.isInteger(y) && y >= 1990 && y <= 2030;
    if (req.method === 'GET' && url.pathname === '/r') {
      const qid = url.searchParams.get('qid'), fid = url.searchParams.get('fid'), year = +url.searchParams.get('year');
      if (!Q[qid] || (CAR.has(qid) && !(fidOk(fid) && yOk(year)))) return json(o, { error: 'bad' }, 400);
      return json(o, { counts: await counts(env, qid, fid, year) });
    }
    if (req.method === 'GET' && url.pathname === '/v') {
      const pre = PRE[url.searchParams.get('site')], period = url.searchParams.get('period') || 'all';
      if (!pre || !(period === 'all' || DAYS[period] || /^20\d\d-(0[1-9]|1[0-2])$/.test(period))) return json(o, { error: 'bad' }, 400);
      const since = DAYS[period] ? new Date(Date.now() - (DAYS[period] - 1) * 864e5).toISOString().slice(0, 10) : '';
      const where = `qid LIKE '${pre}%'` + (DAYS[period] ? ' AND day >= ?' : /^20/.test(period) ? ' AND substr(day, 1, 7) = ?' : '');
      const bind = DAYS[period] ? [since] : /^20/.test(period) ? [period] : [];
      const [r1, r2, r3] = await env.DB.batch([
        env.DB.prepare(`SELECT qid, answer, COUNT(*) n FROM answers WHERE ${where} GROUP BY qid, answer`).bind(...bind),
        env.DB.prepare(`SELECT COUNT(DISTINCT ih || day) n FROM answers WHERE ${where}`).bind(...bind),
        env.DB.prepare(`SELECT DISTINCT substr(day, 1, 7) m FROM answers WHERE qid LIKE '${pre}%' ORDER BY m DESC LIMIT 24`)]);
      const counts = {}; for (const r of r1.results) (counts[r.qid] ||= {})[r.answer] = r.n;
      return json(o, { counts, voters: r2.results[0]?.n || 0, months: r3.results.map(r => r.m) });
    }
    if (req.method === 'POST' && url.pathname === '/apply') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true });                                  // hidden field only bots fill in
      const str = (v, n) => typeof v === 'string' ? v.trim().slice(0, n) : '';
      const one = (v, k) => APPLY[k].includes(v) ? v : '';
      const d = { business: str(b.business, 120), type: str(b.type, 80), site: str(b.site, 200), size: one(b.size, 'size'), hours: one(b.hours, 'hours'),
        budget: one(b.budget, 'budget'), when: one(b.when, 'when'), areas: (Array.isArray(b.areas) ? b.areas : []).filter(a => APPLY.areas.includes(a)).slice(0, 10),
        task: str(b.task, 2000), tools: str(b.tools, 400), name: str(b.name, 100), email: str(b.email, 200).toLowerCase(), phone: str(b.phone, 40), page: str(b.page, 120) };
      if (!d.name || !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(d.email) || d.task.length < 10 || !d.areas.length) return json(o, { error: 'missing' }, 400);
      const day = new Date().toISOString().slice(0, 10), raw = req.headers.get('CF-Connecting-IP') || '', salt = env.SALT || 'lemon-survey-v1';
      const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${raw}|${day}|${salt}|apply`));
      const ih = [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, ih TEXT, data TEXT, status TEXT DEFAULT 'new')").run();
      const n = await env.DB.prepare('SELECT COUNT(*) n FROM applications WHERE ih = ? AND day = ?').bind(ih, day).first('n');
      if (n >= 5) return json(o, { error: 'limit' }, 429);
      await env.DB.prepare('INSERT INTO applications (ts, day, ih, data) VALUES (?, ?, ?, ?)').bind(Date.now(), day, ih, JSON.stringify(d)).run();
      const m = alertMail(env, `New human-help application: ${d.business || d.name}`, [['Name', d.name], ['Email', d.email], ['Phone', d.phone], ['Business', d.business], ['Type', d.type], ['Website', d.site],
        ['Size', d.size], ['Hours a week', d.hours], ['Budget', d.budget], ['When', d.when], ['Areas', d.areas], ['What eats their time', d.task], ['Tools now', d.tools], ['From page', d.page]], d.email);
      if (ctx && ctx.waitUntil) ctx.waitUntil(m); else await m;
      return json(o, { ok: true });
    }
    if (req.method === 'POST' && url.pathname === '/suggest') {
      // 11-07: "we missed a tool" / "add my tool" requests from elijahwestbrook.com comparison pages. Email is optional.
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true });
      const str = (v, n) => typeof v === 'string' ? v.trim().slice(0, n) : '';
      const d = { tool: str(b.tool, 120), url: str(b.url, 300), note: str(b.note, 1000), email: str(b.email, 200).toLowerCase(), maker: b.maker === true, page: str(b.page, 120) };
      if (d.tool.length < 2 || (d.email && !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(d.email))) return json(o, { error: 'missing' }, 400);
      const day = new Date().toISOString().slice(0, 10), raw = req.headers.get('CF-Connecting-IP') || '', salt = env.SALT || 'lemon-survey-v1';
      const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${raw}|${day}|${salt}|suggest`));
      const ih = [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS tool_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, ih TEXT, data TEXT, status TEXT DEFAULT 'new')").run();
      const n = await env.DB.prepare('SELECT COUNT(*) n FROM tool_requests WHERE ih = ? AND day = ?').bind(ih, day).first('n');
      if (n >= 10) return json(o, { error: 'limit' }, 429);
      await env.DB.prepare('INSERT INTO tool_requests (ts, day, ih, data) VALUES (?, ?, ?, ?)').bind(Date.now(), day, ih, JSON.stringify(d)).run();
      const m = alertMail(env, `Tool request: ${d.tool}${d.maker ? ' (from the maker)' : ''}`, [['Tool', d.tool], ['Website', d.url], ['Note', d.note], ['Email', d.email], ['From page', d.page]], d.email || undefined);
      if (ctx && ctx.waitUntil) ctx.waitUntil(m); else await m;
      return json(o, { ok: true });
    }
    if (req.method === 'POST' && url.pathname === '/a') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      const q = Q[b.qid]; if (!q || !q.a.includes(b.a)) return json(o, { error: 'bad' }, 400);
      const car = CAR.has(b.qid); if (car && !(fidOk(b.fid) && yOk(b.year))) return json(o, { error: 'bad' }, 400);
      // 11-05 security pass: the salt lives in the Worker secret SALT (the repo is public, so a salt written here made the daily IP hashes
      // reversible), and IPv6 visitors are keyed by their /64 (one home or phone gets a whole /64, so rotating inside it no longer buys extra votes)
      const day = new Date().toISOString().slice(0, 10), raw = req.headers.get('CF-Connecting-IP') || '', salt = env.SALT || 'lemon-survey-v1';
      const ip = raw.includes(':') ? raw.split(':').slice(0, 4).join(':') + '::/64' : raw;
      const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${ip}|${day}|${salt}`));
      const ih = [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      // votes (11-03, Elijah: "avoid false votes or spam"): no data-center / VPN networks, a human check when TURNSTILE_SECRET is set,
      // and one vote per poll per visitor (IP + browser, hashed) per 7-day block instead of per day
      let vh = '';
      if (q.v) {
        const org = String(req.cf?.asOrganization || '');
        if (HOSTING.test(org) || HOSTING_ASN.has(+req.cf?.asn)) return json(o, { error: 'vpn' }, 403);
        if (env.TURNSTILE_SECRET) {
          const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.t || '')); fd.append('remoteip', raw);
          const ok = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd }).then(r => r.json()).then(j => j.success).catch(() => false);
          if (!ok) return json(o, { error: 'human' }, 403);
        }
        const wk = Math.floor(Date.now() / (7 * 864e5)), ua = req.headers.get('User-Agent') || '';
        const h7 = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${ip}|${ua}|${wk}|${salt}|vote`));
        vh = [...new Uint8Array(h7)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
        if (await env.DB.prepare('SELECT 1 FROM answers WHERE qid = ? AND ih = ? LIMIT 1').bind(b.qid, vh).first()) return json(o, { counts: await counts(env, b.qid), voted: true });
      }
      const used = await env.DB.prepare('SELECT COUNT(*) n FROM answers WHERE ih IN (?, ?) AND day = ?').bind(ih, vh || ih, day).first('n');
      if (used >= 100) return json(o, { counts: await counts(env, b.qid, b.fid, b.year), limited: true });
      const page = typeof b.page === 'string' ? b.page.slice(0, 120).replace(/[^a-z0-9/_-]/gi, '') : '';
      await env.DB.prepare('INSERT OR IGNORE INTO answers (ts, day, page, fid, year, qid, answer, ih) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
        .bind(Date.now(), day, page, car ? b.fid : null, car ? b.year : null, b.qid, b.a, vh || ih).run();
      return json(o, { counts: await counts(env, b.qid, b.fid, b.year) });
    }
    return json(o, { error: 'not found' }, 404);
  }
};

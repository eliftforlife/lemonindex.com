// "Help our site" answers for lemonindex.com (11-03). Cloudflare Worker + D1 (binding DB -> database lemon-survey).
// POST /a {qid, a, fid?, year?, page}  -> stores one anonymous tap, returns the answer counts for that question
// GET  /r?qid=&fid=&year=              -> answer counts
// No accounts, no emails, no free text: only the fixed choices in Q below are accepted. A visitor is a salted daily hash of the IP
// (raw IPs are never stored); one answer per question (per car) per visitor per day, max 40 answers per visitor per day.
// Q is generated from data/survey.json by build.py (python build.py writes worker/survey_worker.js's Q line); keep them in sync.
const Q = __Q__;
const ORIGINS = ['https://lemonindex.com', 'https://www.lemonindex.com'];
const CAR = new Set(Object.keys(Q).filter(k => Q[k].car));
const cors = o => ({ 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (o, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(o) } });
async function counts(env, qid, fid, year) {
  const { results } = CAR.has(qid)
    ? await env.DB.prepare('SELECT answer, COUNT(*) n FROM answers WHERE qid = ? AND fid = ? AND year = ? GROUP BY answer').bind(qid, fid, year).all()
    : await env.DB.prepare('SELECT answer, COUNT(*) n FROM answers WHERE qid = ? GROUP BY answer').bind(qid).all();
  return Object.fromEntries(results.map(r => [r.answer, r.n]));
}
export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    if (!ORIGINS.includes(o)) return json(o, { error: 'origin' }, 403);
    const fidOk = s => typeof s === 'string' && /^[a-z0-9/-]{2,40}$/.test(s), yOk = y => Number.isInteger(y) && y >= 1990 && y <= 2030;
    if (req.method === 'GET' && url.pathname === '/r') {
      const qid = url.searchParams.get('qid'), fid = url.searchParams.get('fid'), year = +url.searchParams.get('year');
      if (!Q[qid] || (CAR.has(qid) && !(fidOk(fid) && yOk(year)))) return json(o, { error: 'bad' }, 400);
      return json(o, { counts: await counts(env, qid, fid, year) });
    }
    if (req.method === 'POST' && url.pathname === '/a') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      const q = Q[b.qid]; if (!q || !q.a.includes(b.a)) return json(o, { error: 'bad' }, 400);
      const car = CAR.has(b.qid); if (car && !(fidOk(b.fid) && yOk(b.year))) return json(o, { error: 'bad' }, 400);
      const day = new Date().toISOString().slice(0, 10), ip = req.headers.get('CF-Connecting-IP') || '';
      const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${ip}|${day}|lemon-survey-v1`));
      const ih = [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      const used = await env.DB.prepare('SELECT COUNT(*) n FROM answers WHERE ih = ? AND day = ?').bind(ih, day).first('n');
      if (used >= 40) return json(o, { counts: await counts(env, b.qid, b.fid, b.year), limited: true });
      const page = typeof b.page === 'string' ? b.page.slice(0, 120).replace(/[^a-z0-9/_-]/gi, '') : '';
      await env.DB.prepare('INSERT OR IGNORE INTO answers (ts, day, page, fid, year, qid, answer, ih) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
        .bind(Date.now(), day, page, car ? b.fid : null, car ? b.year : null, b.qid, b.a, ih).run();
      return json(o, { counts: await counts(env, b.qid, b.fid, b.year) });
    }
    return json(o, { error: 'not found' }, 404);
  }
};

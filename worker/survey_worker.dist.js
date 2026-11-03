// "Help our site" answers for lemonindex.com (11-03). Cloudflare Worker + D1 (binding DB -> database lemon-survey).
// POST /a {qid, a, fid?, year?, page}  -> stores one anonymous tap, returns the answer counts for that question
// GET  /r?qid=&fid=&year=              -> answer counts
// No accounts, no emails, no free text: only the fixed choices in Q below are accepted. A visitor is a salted daily hash of the IP
// (raw IPs are never stored); one answer per question (per car) per visitor per day, max 40 answers per visitor per day.
// Q is generated from data/survey.json by build.py (python build.py writes worker/survey_worker.js's Q line); keep them in sync.
const Q = {"own":{"a":["Own one now","Used to","Shopping for one","No"],"car":true},"miles":{"a":["Under 50K","50–100K","100–150K","150–200K","200K+"],"car":true},"paid":{"a":["Under $5K","$5–10K","$10–15K","$15–20K","$20–30K","$30K+"],"car":true},"where":{"a":["Dealer","Private party","CarMax / Carvana","Auction","Family / friend"],"car":true},"problem":{"a":["None","Transmission","Engine","Electrical","Brakes","Suspension","AC / heat","Other"],"car":true},"bigrepair":{"a":["No","Once","2+ times"],"car":true},"again":{"a":["Yes","Maybe","No"],"car":true},"buyfrom":{"a":["Dealer","Private party","CarMax / Carvana","Auction","Family / friend"]},"ppmarket":{"a":["Facebook Marketplace","Craigslist","OfferUp","Autotrader","Cars.com","CarGurus","Word of mouth"]},"dealersite":{"a":["CarGurus","Cars.com","Autotrader","CarMax","Carvana","Dealer websites"]},"budget":{"a":["Under $5K","$5–10K","$10–15K","$15–20K","$20–30K","$30K+"]},"toomany":{"a":["75K","100K","150K","200K","Doesn't matter if maintained"]},"ppi":{"a":["Yes, paid","Yes, free","No","Didn't know you could"]},"history":{"a":["Always","Sometimes","Never"]},"matters":{"a":["Reliability","Price","Gas mileage","Safety","Looks","Resale value"]},"keep":{"a":["Under 2 years","2–4 years","5–7 years","8+ years"]},"negotiate":{"a":["Got 10%+ off","A little off","Paid asking","Paid over asking"]},"fear":{"a":["Hidden problems","Overpaying","Scams","Financing","Paperwork"]},"lemon":{"a":["No","Yes, cost me under $1K","Yes, $1–5K","Yes, $5K+"]},"pay":{"a":["Cash","Financed","Leased"]},"salvage":{"a":["Yes","If cheap enough","Never"]},"nexttype":{"a":["Sedan","SUV","Truck","Minivan","Hybrid","Electric"]},"usedev":{"a":["Yes","Maybe","No"]},"recallfree":{"a":["Yes","No"]},"advice":{"a":["YouTube","TikTok","Reddit","A mechanic","Friends / family","Consumer Reports"]},"found":{"a":["TikTok","Instagram","YouTube","Google","Reddit","A friend"]},"credit":{"a":["781+","661–780","601–660","501–600","Under 500","Not sure"]},"aprgot":{"a":["Under 5%","5–8%","8–12%","12–16%","16–20%","20%+","Paid cash"]},"down":{"a":["$0","Under $2K","$2–5K","$5–10K","$10K+","Paid cash"]},"loanfrom":{"a":["The dealer","My bank","A credit union","An online lender","Paid cash"]}};
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

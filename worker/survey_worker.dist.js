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
// POST /feedback (11-09): the feedback box at the bottom of lemonindex.com, mealmonster.app, thebusinessstudy.com and elijahwestbrook.com.
//      Stores {site, page path, message, optional email, created} in table feedback. No IPs or IP hashes are stored: the per-IP limit is the
//      FEEDBACK_RL rate-limit binding (wrangler.toml) plus an in-memory map that dies with the isolate. Read with 0 HQ/Tools/feedback.py pull.
// POST /donor-request (11-10): "What car or feature should we add next?" on lemonindex.com/thanks/ (where Stripe sends donors).
//      Stores {request (2-300 chars), page, Stripe checkout session id if the thank-you URL carried one} in table donor_requests, plus the
//      same salted daily IP hash the other routes use (only to cap repeat sends). No name or email. Not shown publicly. Max 5 per visitor per day.
// POST /price (11-23): "What did you pay?" under the repair estimates on lemonindex.com year and /repair-cost/ pages.
//      Stores {fid, year?, repair (one of the 69 repair slugs), usd (20-30,000), shop type?, the first 3 digits of the ZIP?} in table prices,
//      Job E (11-23): motorcycle, supercar and plane pages send fid 'm/<slug>', 's/<slug>' or 'p/<slug>' with their own repair slugs (XREPAIRS,
//      from data/repair_est_x.json) and a higher price cap (supercars $300,000, planes $2,000,000: overhauls).
//      status 'new'. No name, email or full ZIP. Same guards as /op: Turnstile, honeypot, no VPN/data-center networks, the edge rate limit,
//      max 5 per visitor per day, one per car + repair per visitor per 30 days, 500 a day site-wide. Not shown publicly: read with
//      GET /prices_all (no origin check, like /ops_all; without ZIP digits or hashes; the ZIP digits are read in the D1 dashboard) and folded into the owner prices after a check.
// Deploy: py make_worker.py, then `npx.cmd --yes wrangler deploy` from this folder (wrangler.toml).
// Q is generated from data/survey.json + data/votes.json by worker/make_worker.py -> survey_worker.dist.js (the uploaded file).
const Q = {"own":{"a":["Own one now","Used to","Shopping for one","No"],"car":true},"miles":{"a":["Under 50K","50–100K","100–150K","150–200K","200K+"],"car":true},"paid":{"a":["Under $5K","$5–10K","$10–15K","$15–20K","$20–30K","$30K+"],"car":true},"where":{"a":["Dealer","Private party","CarMax / Carvana","Auction","Family / friend"],"car":true},"problem":{"a":["None","Transmission","Engine","Electrical","Brakes","Suspension","AC / heat","Other"],"car":true},"bigrepair":{"a":["No","Once","2+ times"],"car":true},"again":{"a":["Yes","Maybe","No"],"car":true},"buyfrom":{"a":["Dealer","Private party","CarMax / Carvana","Auction","Family / friend"]},"ppmarket":{"a":["Facebook Marketplace","Craigslist","OfferUp","Autotrader","Cars.com","CarGurus","Word of mouth"]},"dealersite":{"a":["CarGurus","Cars.com","Autotrader","CarMax","Carvana","Dealer websites"]},"budget":{"a":["Under $5K","$5–10K","$10–15K","$15–20K","$20–30K","$30K+"]},"toomany":{"a":["75K","100K","150K","200K","Doesn't matter if maintained"]},"ppi":{"a":["Yes, paid","Yes, free","No","Didn't know you could"]},"history":{"a":["Always","Sometimes","Never"]},"matters":{"a":["Reliability","Price","Gas mileage","Safety","Looks","Resale value"]},"keep":{"a":["Under 2 years","2–4 years","5–7 years","8+ years"]},"negotiate":{"a":["Got 10%+ off","A little off","Paid asking","Paid over asking"]},"fear":{"a":["Hidden problems","Overpaying","Scams","Financing","Paperwork"]},"lemon":{"a":["No","Yes, cost me under $1K","Yes, $1–5K","Yes, $5K+"]},"pay":{"a":["Cash","Financed","Leased"]},"salvage":{"a":["Yes","If cheap enough","Never"]},"nexttype":{"a":["Sedan","SUV","Truck","Minivan","Hybrid","Electric"]},"usedev":{"a":["Yes","Maybe","No"]},"recallfree":{"a":["Yes","No"]},"advice":{"a":["YouTube","TikTok","Reddit","A mechanic","Friends / family","Consumer Reports"]},"found":{"a":["TikTok","Instagram","YouTube","Google","Reddit","A friend"]},"credit":{"a":["781+","661–780","601–660","501–600","Under 500","Not sure"]},"aprgot":{"a":["Under 5%","5–8%","8–12%","12–16%","16–20%","20%+","Paid cash"]},"down":{"a":["$0","Under $2K","$2–5K","$5–10K","$10K+","Paid cash"]},"loanfrom":{"a":["The dealer","My bank","A credit union","An online lender","Paid cash"]},"vl_chevyford":{"a":["Chevy","Ford"],"v":"lemon"},"vl_reliable":{"a":["Toyota","Honda","Lexus","Mazda","Subaru","Hyundai","Kia","Ford","Chevrolet","Nissan","Jeep","BMW","Tesla"],"v":"lemon"},"vl_never":{"a":["Nissan","Jeep","Chrysler / Dodge","Ford","Chevrolet","Volkswagen","BMW","Land Rover","Tesla","Kia / Hyundai"],"v":"lemon"},"vl_overrated":{"a":["Tesla","BMW","Mercedes-Benz","Jeep","Land Rover","Audi","Toyota","Ford"],"v":"lemon"},"vl_truckbrand":{"a":["Ford","Chevrolet","Ram","Toyota","GMC","Nissan"],"v":"lemon"},"vl_luxury":{"a":["Lexus","Acura","Genesis","BMW","Mercedes-Benz","Audi","Infiniti","Cadillac"],"v":"lemon"},"vl_suv15":{"a":["Toyota RAV4","Honda CR-V","Mazda CX-5","Subaru Forester","Hyundai Tucson","Nissan Rogue","Ford Escape","Chevy Equinox"],"v":"lemon"},"vl_sedan10":{"a":["Toyota Corolla","Honda Civic","Toyota Camry","Honda Accord","Mazda3","Hyundai Elantra","Lexus ES"],"v":"lemon"},"vl_pickup":{"a":["Ford F-150","Chevy Silverado","Ram 1500","Toyota Tacoma","Toyota Tundra","GMC Sierra","Nissan Frontier"],"v":"lemon"},"vl_minivan":{"a":["Honda Odyssey","Toyota Sienna","Chrysler Pacifica","Kia Carnival"],"v":"lemon"},"vl_ev":{"a":["Tesla Model 3","Tesla Model Y","Hyundai Ioniq 5","Kia EV6","Ford Mustang Mach-E","Chevy Bolt","Rivian R1S"],"v":"lemon"},"vl_last":{"a":["Toyota Camry","Toyota Corolla","Honda Accord","Honda Civic","Toyota 4Runner","Toyota Tacoma","Lexus ES","Ford F-150"],"v":"lemon"},"vl_civic":{"a":["2001–2005","2006–2011","2012–2015","2016–2021","2022 and newer"],"v":"lemon"},"vl_camry":{"a":["2002–2006","2007–2011","2012–2017","2018–2024","2025 and newer"],"v":"lemon"},"vl_f150":{"a":["2004–2008","2009–2014","2015–2020","2021 and newer"],"v":"lemon"},"vl_era":{"a":["1990s","2000s","2010s","2020s"],"v":"lemon"},"vl_insbest":{"a":["State Farm","GEICO","Progressive","Allstate","USAA","Liberty Mutual","Farmers","Nationwide"],"v":"lemon"},"vl_insworst":{"a":["State Farm","GEICO","Progressive","Allstate","USAA","Liberty Mutual","Farmers","Nationwide"],"v":"lemon"},"vl_inspay":{"a":["Under $100","$100–150","$150–200","$200–300","$300+"],"v":"lemon"},"vl_buyat":{"a":["CarMax","Carvana","A local dealer","Private seller","Facebook Marketplace","Auction"],"v":"lemon"},"vl_report":{"a":["Carfax","AutoCheck","A mechanic’s inspection","None of them"],"v":"lemon"},"vl_nextpower":{"a":["Gas","Hybrid","Plug-in hybrid","Electric","Diesel"],"v":"lemon"},"vl_tires":{"a":["Michelin","Goodyear","Bridgestone","Continental","Pirelli","Firestone","Cooper","General"],"v":"lemon"},"vl_oil":{"a":["The dealer","A local mechanic","Jiffy Lube","Valvoline","Take 5","Walmart / Costco","I do it myself"],"v":"lemon"},"vl_gas":{"a":["Costco","Buc-ee’s","Wawa","Sheetz","QuikTrip","Shell","Chevron","Exxon / Mobil","Speedway"],"v":"lemon"},"vb_hustle":{"a":["DoorDash / Uber Eats","Uber / Lyft","Reselling (eBay, Mercari)","Freelancing (Upwork, Fiverr)","Tutoring","Pet sitting / dog walking","YouTube / TikTok","Lawn care"],"v":"bs"},"vb_1k":{"a":["Pressure washing","Cleaning","Lawn care","Car detailing","Reselling","Vending machines","Content creation","Dropshipping"],"v":"bs"},"vb_lifeset":{"a":["$1 million today","$5,000 a month for life"],"v":"bs"},"vb_invest":{"a":["Fidelity","Vanguard","Charles Schwab","Robinhood","Webull","Cash App","I don’t invest yet"],"v":"bs"},"vb_card":{"a":["Chase Sapphire","Amex Gold","Capital One Venture","Citi Double Cash","Discover it","Apple Card","No credit card"],"v":"bs"},"vb_remote":{"a":["Fully remote","Hybrid","In the office","My own business"],"v":"bs"},"vb_4day":{"a":["Yes","No","Depends on the job"],"v":"bs"},"vb_employer":{"a":["Costco","Trader Joe’s","Chick-fil-A","Google","Apple","Amazon","Target","Starbucks"],"v":"bs"},"vb_degree":{"a":["Yes","Only for some majors","Trade school is better","No"],"v":"bs"},"vb_fastfood":{"a":["Chick-fil-A","McDonald’s","In-N-Out","Wendy’s","Taco Bell","Chipotle","Popeyes","Raising Cane’s"],"v":"bs"},"vb_franchise":{"a":["McDonald’s","Chick-fil-A","Subway","Taco Bell","Dunkin’","Crumbl","Planet Fitness","Jersey Mike’s"],"v":"bs"},"vb_grocery":{"a":["Costco","Aldi","Trader Joe’s","Walmart","H-E-B","Publix","Kroger","Whole Foods"],"v":"bs"},"vb_carrier":{"a":["Verizon","AT&T","T-Mobile","Visible","Mint Mobile","Cricket"],"v":"bs"},"vb_overpriced":{"a":["Apple","Starbucks","Stanley","Nike","Disney","Tesla","Chipotle","Supreme"],"v":"bs"},"vb_platform":{"a":["Amazon","Shopify","Etsy","TikTok Shop","eBay","Facebook Marketplace","My own website"],"v":"bs"},"vb_social":{"a":["TikTok","Instagram","YouTube","Facebook","LinkedIn","X"],"v":"bs"},"vb_bank":{"a":["Chase","Bank of America","Wells Fargo","Capital One","Mercury","Novo","A credit union"],"v":"bs"},"vb_ceo":{"a":["Jensen Huang","Tim Cook","Elon Musk","Warren Buffett","Jeff Bezos","Mark Zuckerberg","Satya Nadella"],"v":"bs"},"vb_hard":{"a":["Getting customers","Money / cash flow","Hiring","Taxes and legal","Staying consistent","Pricing"],"v":"bs"}};
const ORIGINS = ['https://lemonindex.com', 'https://www.lemonindex.com', 'https://thebusinessstudy.com', 'https://www.thebusinessstudy.com', 'https://elijahwestbrook.com', 'https://www.elijahwestbrook.com', 'https://mealmonster.app', 'https://www.mealmonster.app'];
const FB_SITE = o => ({ 'lemonindex.com': 'lemon', 'mealmonster.app': 'mm', 'thebusinessstudy.com': 'bs', 'elijahwestbrook.com': 'ew' })[o.replace(/^https:\/\/(www\.)?/, '')];
const fbHits = new Map();   // IP -> recent send times, in memory only (gone when the isolate restarts); never written anywhere
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

// 11-18 owner opinions (Elijah: "a leave-your-opinion box ... anonymous or show their name ... 10 a day, 1 per car ... AI review, then it
// displays for that car"). Table opinions. One opinion per car per visitor per 30 days, max 10 a day per visitor, 300 a day site-wide.
// Every opinion is checked by rules (no links, emails, phone numbers, VINs, swearing) and two Workers AI models (Llama Guard for safety,
// Llama 3.1 for "a real opinion about this car, no spam or personal info"); only approved ones are shown. If AI is down the opinion waits
// (status pending) and the cron retries it. Remove one by hand: UPDATE opinions SET status='removed' WHERE id=N (D1 console).
const OP_KINDS = { owner: 'Owner', former: 'Former owner', drove: 'Drove one', opinion: 'Opinion' };
const OP_BAD = /(https?:|www\.|\b[a-z0-9-]+\.(com|net|org|io|co|ly|gg|xyz|info|biz)\b|[^@\s]+@[^@\s]+\.[a-z]{2,}|\b\d{3}[-.\s)]*\d{3}[-.\s]*\d{4}\b|\b[A-HJ-NPR-Z0-9]{17}\b)/i;
const OP_SWEAR = /\b(f+u+c+k+\w*|s+h+i+t+\w*|b+i+t+c+h+\w*|c+u+n+t+\w*|n+i+g+g+\w*|f+a+g+\w*|r+e+t+a+r+d+\w*|wh+o+r+e+\w*|d+i+c+k+\w*|p+u+s+s+y+\w*|a+s+s+h+o+l+e+\w*)\b/i;
async function opReview(env, car, text) {
  if (OP_BAD.test(text)) return { status: 'rejected', reason: 'No links, emails, phone numbers or VINs, please.' };
  if (OP_SWEAR.test(text)) return { status: 'rejected', reason: 'Please keep it clean: no swearing.' };
  if (!env.AI) return { status: 'pending', reason: '' };
  try {
    const g = await env.AI.run('@cf/meta/llama-guard-3-8b', { messages: [{ role: 'user', content: text }] });
    const gr = typeof g?.response === 'string' ? g.response : JSON.stringify(g?.response || '');
    if (/unsafe/i.test(gr) || g?.response?.safe === false) return { status: 'rejected', reason: 'It didn\u2019t pass the safety check.' };
    const sys = `You moderate short opinions that visitors post about cars on a car reliability website. The page is about the ${car}. Approve only if ALL are true: it is a genuine opinion or experience about this car (or its brand, its model years, or cars like it); it is mostly English; no hate, harassment, threats, sexual content or slurs; no personal information about anyone (private names, phone, email, address, license plate, VIN); no ads, promo codes, links or spam; not gibberish or a test message; it does not accuse a named person of a crime. Negative opinions about cars, brands, dealers and repair shops are fine. Reply with JSON only: {"ok": true or false, "reason": "short reason for the visitor"}`;
    const r = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', { messages: [{ role: 'system', content: sys }, { role: 'user', content: text }], max_tokens: 80, temperature: 0 });
    const resp = typeof r?.response === 'string' ? r.response : JSON.stringify(r?.response || '');
    const m = resp.match(/\{[\s\S]*\}/); let v = null; try { v = m ? JSON.parse(m[0]) : null; } catch (e) { v = null; }
    if (!v || typeof v.ok !== 'boolean') return { status: 'pending', reason: '' };
    return v.ok ? { status: 'approved', reason: '' } : { status: 'rejected', reason: String(v.reason || 'It didn\u2019t pass review.').slice(0, 140) };
  } catch (e) { return { status: 'pending', reason: '' }; }
}
const OP_TABLE = "CREATE TABLE IF NOT EXISTS opinions (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, fid TEXT, car TEXT, year INTEGER, kind TEXT, name TEXT, text TEXT, buy TEXT, status TEXT, reason TEXT, ih TEXT, ch TEXT)";
const XREPAIRS = { m: new Set('abs-module battery belt-drive brake-caliper brake-fluid brake-pads brake-rotors cam-chain-tensioner chain-sprockets clutch clutch-hydraulics coolant-flush cvt-belt ecu engine-rebuild final-drive fork-seals fuel-injectors fuel-pump ignition-coils infotainment instrument-cluster oil-leak oil-service radiator rear-shock regulator-rectifier spark-plugs starter starter-clutch stator steering-bearings throttle-body timing-belts tire-front tire-rear top-end transmission valve-adjustment water-pump wheel-bearings wiring-harness'.split(' ')), p: new Set('ads-b alternator annual-inspection autopilot brakes caps-repack cylinder elt-battery engine-mounts engine-overhaul exhaust fuel-pump fuel-servo fuel-tank gear-retract gps-navigator gyro heli-overhaul hot-section hundred-hour ifr-cert interior magneto oil-change paint pre-buy prop-governor prop-overhaul rotor-blades spark-plugs starter tires turbine-overhaul turbocharger vacuum-pump windshield'.split(' ')), s: new Set('abs-module ac-compressor ac-condenser ac-evaporator air-suspension airbag-module alternator annual-service backup-camera ball-joints battery bcm blend-door brake-booster brakes cam-phaser cam-sensor carbon-brakes catalytic-converter clutch control-arms convertible-top crank-sensor cv-axle differential door-lock-actuator dpf driveshaft ecm egr engine-mounts engine-replacement evap exhaust-manifold fuel-injectors fuel-pump gearbox-pump head-gasket heater-core hybrid-battery ignition-coils infotainment intake-manifold lifters maf-sensor major-service master-cylinder nose-lift oil-cooler oil-pan oxygen-sensor power-steering-pump radiator rear-main-seal spark-plugs starter steering-column steering-rack sticky-interior struts tcm thermostat throttle-body tie-rods timing-belt timing-chain tipm tires torque-converter transfer-case transmission-replacement turbo valve-body valve-cover-gasket water-pump wheel-bearing window-regulator wiring-harness'.split(' ')) };   // job E: the motorcycle (m), supercar (s) and plane (p) repairs in data/repair_est_x.json
const PRICE_TABLE = "CREATE TABLE IF NOT EXISTS prices (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, fid TEXT, year INTEGER, repair TEXT, usd INTEGER, shop TEXT, zip3 TEXT, status TEXT, ih TEXT, ch TEXT)";
const REPAIRS = new Set('abs-module ac-compressor ac-condenser ac-evaporator air-suspension airbag-module alternator backup-camera ball-joints battery bcm blend-door brake-booster brakes cam-phaser cam-sensor catalytic-converter clutch control-arms crank-sensor cv-axle differential door-lock-actuator dpf driveshaft ecm egr engine-mounts engine-replacement evap fuel-injectors fuel-pump head-gasket heater-core hybrid-battery ignition-coils infotainment intake-manifold lifters maf-sensor master-cylinder oil-cooler oil-pan oxygen-sensor power-steering-pump radiator rear-main-seal spark-plugs starter steering-column steering-rack struts tcm thermostat throttle-body tie-rods timing-belt timing-chain tipm torque-converter transfer-case transmission-replacement turbo valve-body valve-cover-gasket water-pump wheel-bearing window-regulator wiring-harness'.split(' '));   // the 69 repairs in data/repair_est.json (repair_est.py)
const opPublic = r => ({ id: r.id, ts: r.ts, year: r.year || null, kind: r.kind, name: r.name || '', text: r.text, buy: r.buy || '' });

export default {
  async fetch(req, env, ctx) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    if (req.method === 'GET' && url.pathname === '/ops_all') {   // 11-18: approved opinions for the static build (build.py bakes them into the car pages)
      await env.DB.prepare(OP_TABLE).run();
      const { results } = await env.DB.prepare("SELECT * FROM opinions WHERE status = 'approved' ORDER BY ts DESC LIMIT 5000").all();
      const out = {}; for (const r of results) (out[r.fid] ||= []).push(opPublic(r));
      return new Response(JSON.stringify(out), { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    }
    if (req.method === 'GET' && url.pathname === '/prices_all') {   // 11-23: reader repair prices for the build / review (no hashes, no ZIP, day only)
      await env.DB.prepare(PRICE_TABLE).run();
      const { results } = await env.DB.prepare('SELECT id, day, fid, year, repair, usd, shop, status FROM prices ORDER BY ts DESC LIMIT 20000').all();
      return new Response(JSON.stringify(results), { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    }
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
    if (req.method === 'POST' && url.pathname === '/feedback') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true });                                  // honeypot: only bots fill it in
      const ip = req.headers.get('CF-Connecting-IP') || '', now = Date.now();
      if (env.FEEDBACK_RL && !(await env.FEEDBACK_RL.limit({ key: ip })).success) return json(o, { error: 'limit' }, 429);
      const recent = (fbHits.get(ip) || []).filter(t => now - t < 36e5);
      if (recent.length >= 10) return json(o, { error: 'limit' }, 429);
      recent.push(now); if (fbHits.size > 5000) fbHits.clear(); fbHits.set(ip, recent);
      const message = typeof b.message === 'string' ? b.message.trim() : '', email = typeof b.email === 'string' ? b.email.trim().toLowerCase() : '';
      if (message.length < 2 || message.length > 1000 || email.length > 200 || (email && !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(email))) return json(o, { error: 'bad' }, 400);
      const page = typeof b.page === 'string' ? b.page.slice(0, 200).replace(/[^a-z0-9/_.-]/gi, '') : '';
      await env.DB.prepare('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, site TEXT, page TEXT, message TEXT, email TEXT)').run();
      const day = new Date(now).toISOString().slice(0, 10);
      if (await env.DB.prepare('SELECT COUNT(*) n FROM feedback WHERE created >= ?').bind(day).first('n') >= 500) return json(o, { error: 'limit' }, 429);   // flood guard
      await env.DB.prepare('INSERT INTO feedback (created, site, page, message, email) VALUES (?, ?, ?, ?, ?)').bind(new Date(now).toISOString(), FB_SITE(o), page, message, email || null).run();
      return json(o, { ok: true });
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
    if (req.method === 'POST' && url.pathname === '/donor-request') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true });                                  // honeypot: only bots fill it in
      const ip = req.headers.get('CF-Connecting-IP') || '';
      if (env.FEEDBACK_RL && !(await env.FEEDBACK_RL.limit({ key: 'dr:' + ip })).success) return json(o, { error: 'limit' }, 429);
      const request = typeof b.request === 'string' ? b.request.trim().slice(0, 300) : '';
      const session = typeof b.session === 'string' && /^cs_(live|test)_[A-Za-z0-9]{10,200}$/.test(b.session) ? b.session : '';
      const page = typeof b.page === 'string' ? b.page.slice(0, 120).replace(/[^a-z0-9/_.-]/gi, '') : '';
      if (request.length < 2) return json(o, { error: 'missing' }, 400);
      const day = new Date().toISOString().slice(0, 10), salt = env.SALT || 'lemon-survey-v1';
      const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${ip}|${day}|${salt}|donor`));
      const ih = [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS donor_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, ih TEXT, site TEXT, request TEXT, session TEXT, page TEXT, status TEXT DEFAULT 'new')").run();
      const n = await env.DB.prepare('SELECT COUNT(*) n FROM donor_requests WHERE ih = ? AND day = ?').bind(ih, day).first('n');
      if (n >= 5) return json(o, { error: 'limit' }, 429);
      if (await env.DB.prepare('SELECT COUNT(*) n FROM donor_requests WHERE day = ?').bind(day).first('n') >= 300) return json(o, { error: 'limit' }, 429);   // flood guard
      await env.DB.prepare('INSERT INTO donor_requests (ts, day, ih, site, request, session, page) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(Date.now(), day, ih, FB_SITE(o) || '', request, session || null, page).run();
      const m = alertMail(env, `Donor request: ${request.slice(0, 60)}`, [['Request', request], ['Stripe session', session || '(none on the thank-you URL)'], ['From page', page]]);
      if (ctx && ctx.waitUntil) ctx.waitUntil(m); else await m;
      return json(o, { ok: true });
    }
    if (req.method === 'GET' && url.pathname === '/ops') {
      const fid = url.searchParams.get('fid'); if (!fidOk(fid)) return json(o, { error: 'bad' }, 400);
      await env.DB.prepare(OP_TABLE).run();
      const { results } = await env.DB.prepare("SELECT * FROM opinions WHERE fid = ? AND status = 'approved' ORDER BY ts DESC LIMIT 60").bind(fid).all();
      return json(o, { ops: results.map(opPublic) });
    }
    if (req.method === 'POST' && url.pathname === '/op') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true, status: 'pending' });                                  // honeypot: only bots fill it in
      const str = (v, n) => typeof v === 'string' ? v.replace(/\s+/g, ' ').trim().slice(0, n) : '';
      const fid = b.fid, car = str(b.car, 60), text = typeof b.text === 'string' ? b.text.replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim() : '';
      const year = b.year == null || b.year === '' ? null : +b.year, kind = OP_KINDS[b.kind] ? b.kind : 'opinion', buy = b.buy === 'yes' || b.buy === 'no' ? b.buy : '';
      const name = b.anon ? '' : str(b.name, 30);
      if (!fidOk(fid) || !car || (year !== null && !yOk(year))) return json(o, { error: 'bad' }, 400);
      if (text.length < 20 || text.length > 800) return json(o, { error: 'length' }, 400);
      if (name && !/^[\p{L}][\p{L} .'-]{1,29}$/u.test(name)) return json(o, { error: 'name' }, 400);
      const raw = req.headers.get('CF-Connecting-IP') || '', org = String(req.cf?.asOrganization || '');
      if (HOSTING.test(org) || HOSTING_ASN.has(+req.cf?.asn)) return json(o, { error: 'vpn' }, 403);
      if (env.FEEDBACK_RL && !(await env.FEEDBACK_RL.limit({ key: 'op:' + raw })).success) return json(o, { error: 'limit' }, 429);
      if (env.TURNSTILE_SECRET) {
        const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.t || '')); fd.append('remoteip', raw);
        const ok = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd }).then(r => r.json()).then(j => j.success).catch(() => false);
        if (!ok) return json(o, { error: 'human' }, 403);
      }
      const ip = raw.includes(':') ? raw.split(':').slice(0, 4).join(':') + '::/64' : raw, salt = env.SALT || 'lemon-survey-v1', day = new Date().toISOString().slice(0, 10);
      const hx = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      const ih = await hx(`${ip}|${day}|${salt}|op`), ch = await hx(`${ip}|${fid}|${Math.floor(Date.now() / (30 * 864e5))}|${salt}|opcar`);
      await env.DB.prepare(OP_TABLE).run();
      const [r1, r2, r3] = await env.DB.batch([
        env.DB.prepare('SELECT COUNT(*) n FROM opinions WHERE ih = ? AND day = ?').bind(ih, day),
        env.DB.prepare("SELECT COUNT(*) n FROM opinions WHERE ch = ? AND status != 'rejected'").bind(ch),
        env.DB.prepare('SELECT COUNT(*) n FROM opinions WHERE day = ?').bind(day)]);
      if (r1.results[0].n >= 10) return json(o, { error: 'day' }, 429);
      if (r2.results[0].n >= 1) return json(o, { error: 'car' }, 429);
      if (r3.results[0].n >= 300) return json(o, { error: 'limit' }, 429);
      const v = await opReview(env, car, text);
      const ins = await env.DB.prepare('INSERT INTO opinions (ts, day, fid, car, year, kind, name, text, buy, status, reason, ih, ch) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        .bind(Date.now(), day, fid, car, year, kind, name, text, buy, v.status, v.reason, ih, ch).run();
      const id = ins.meta?.last_row_id;
      return json(o, { ok: true, status: v.status, reason: v.reason, op: v.status === 'approved' ? { id, ts: Date.now(), year, kind, name, text, buy } : null });
    }
    if (req.method === 'POST' && url.pathname === '/price') {
      let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
      if (b.hp) return json(o, { ok: true });                                                     // honeypot: only bots fill it in
      const fid = b.fid, repair = String(b.repair || ''), usd = Math.round(+b.usd), year = b.year == null || b.year === '' ? null : +b.year;
      const shop = ['dealer', 'independent', 'chain', 'other'].includes(b.shop) ? b.shop : '', zip = String(b.zip || '').trim();
      if (!fidOk(fid) || (year !== null && !yOk(year))) return json(o, { error: 'bad' }, 400);
      const xk = /^[msp]\//.test(fid) ? fid[0] : '';
      if (!(xk ? XREPAIRS[xk].has(repair) : REPAIRS.has(repair))) return json(o, { error: 'repair' }, 400);
      if (!(usd >= 20 && usd <= ({ s: 300000, p: 2000000 }[xk] || 30000))) return json(o, { error: 'usd' }, 400);
      if (zip && !/^\d{5}$/.test(zip)) return json(o, { error: 'zip' }, 400);
      const raw = req.headers.get('CF-Connecting-IP') || '', org = String(req.cf?.asOrganization || '');
      if (HOSTING.test(org) || HOSTING_ASN.has(+req.cf?.asn)) return json(o, { error: 'vpn' }, 403);
      if (env.FEEDBACK_RL && !(await env.FEEDBACK_RL.limit({ key: 'price:' + raw })).success) return json(o, { error: 'limit' }, 429);
      if (env.TURNSTILE_SECRET) {
        const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.t || '')); fd.append('remoteip', raw);
        const ok = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd }).then(r => r.json()).then(j => j.success).catch(() => false);
        if (!ok) return json(o, { error: 'human' }, 403);
      }
      const ip = raw.includes(':') ? raw.split(':').slice(0, 4).join(':') + '::/64' : raw, salt = env.SALT || 'lemon-survey-v1', day = new Date().toISOString().slice(0, 10);
      const hx = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
      const ih = await hx(`${ip}|${day}|${salt}|price`), ch = await hx(`${ip}|${fid}|${repair}|${Math.floor(Date.now() / (30 * 864e5))}|${salt}|pricecar`);
      await env.DB.prepare(PRICE_TABLE).run();
      const [r1, r2, r3] = await env.DB.batch([
        env.DB.prepare('SELECT COUNT(*) n FROM prices WHERE ih = ? AND day = ?').bind(ih, day),
        env.DB.prepare('SELECT COUNT(*) n FROM prices WHERE ch = ?').bind(ch),
        env.DB.prepare('SELECT COUNT(*) n FROM prices WHERE day = ?').bind(day)]);
      if (r1.results[0].n >= 5) return json(o, { error: 'day' }, 429);
      if (r2.results[0].n >= 1) return json(o, { error: 'car' }, 429);
      if (r3.results[0].n >= 500) return json(o, { error: 'busy' }, 429);
      await env.DB.prepare('INSERT INTO prices (ts, day, fid, year, repair, usd, shop, zip3, status, ih, ch) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        .bind(Date.now(), day, fid, year, repair, usd, shop, zip ? zip.slice(0, 3) : '', 'new', ih, ch).run();
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
  },
  async scheduled(ev, env, ctx) {   // 11-18: opinions that waited for the AI check (status pending) get reviewed again
    await env.DB.prepare(OP_TABLE).run();
    const { results } = await env.DB.prepare("SELECT id, car, text FROM opinions WHERE status = 'pending' ORDER BY ts LIMIT 20").all();
    for (const r of results) { const v = await opReview(env, r.car, r.text); if (v.status !== 'pending') await env.DB.prepare('UPDATE opinions SET status = ?, reason = ? WHERE id = ?').bind(v.status, v.reason, r.id).run(); }
  }
};

// Tests for the lemon-store Worker without Cloudflare, Stripe or Resend (11-25):  node worker/store/test_store.mjs
// D1 = a real SQLite database (node:sqlite) loaded with schema.sql; KV and the Rate Limiting binding = small fakes; Stripe, Resend and
// Turnstile = fakes inside fetch(). Webhooks are signed here with a throwaway secret. Nothing leaves the machine.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createHmac } from 'node:crypto';
import assert from 'node:assert/strict';
import worker from './store_worker.js';
import { verifyStripe, safeEqual, form, normEmail, SITE, clearCache, clearGoal, SESSION_TTL, ROTATE_AFTER, GRACE, CHAIN_MAX, LINK_TTL, mailBody } from './store_lib.js';

const here = new URL('.', import.meta.url);
let skew = 0; const realNow = Date.now; Date.now = () => realNow() + skew * 1000;   // move the clock in seconds
const T = () => Math.floor(Date.now() / 1000);

function d1() {
  const db = new DatabaseSync(':memory:'); db.exec(readFileSync(new URL('schema.sql', here), 'utf8'));
  const stmt = (sql, a = []) => ({ bind: (...b) => stmt(sql, b), first: async () => db.prepare(sql).get(...a) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...a) }), run: async () => { const r = db.prepare(sql).run(...a); return { success: true, meta: { changes: Number(r.changes) } }; },
    _x: () => { const st = db.prepare(sql); if (/RETURNING/i.test(sql)) return { meta: { changes: st.all(...a).length } }; const r = st.run(...a); return { meta: { changes: Number(r.changes) } }; } });
  return { raw: db, prepare: sql => stmt(sql), batch: async list => { db.exec('BEGIN'); try { const out = list.map(s => s._x()); db.exec('COMMIT'); return out; } catch (e) { db.exec('ROLLBACK'); throw e; } } };
}
const kv = () => { const m = new Map(); return { m, get: async k => m.has(k) ? m.get(k) : null, put: async (k, v) => { m.set(k, v); } }; };
const rl = limit => { const c = new Map(); return { limit: async ({ key }) => { const w = Math.floor(T() / 60), k = key + '|' + w; c.set(k, (c.get(k) || 0) + 1); return { success: c.get(k) <= limit }; } }; };

// ---- catalog: 3 car gens + 1 motorcycle (not in "all")
const GENS = { 'toyota-corolla-g11': 'car', 'toyota-tacoma-g2': 'car', 'honda-civic-g10': 'car', 'honda-cbr600rr-g1': 'moto' };
const doc = g => JSON.stringify({ v: 1, id: g, name: g, checks: { a: { q: 'PAID-SECRET-' + g } } });
// a small checklist with the 2012 Tacoma's real engine inputs (prices/, costs/), for the answer screen: the numbers must match ../dealer_offer.md
const TACO = {
  v: 1, id: 'toyota-tacoma-g2', name: 'Toyota Tacoma', short: 'Tacoma', brand: 'Toyota', type: 'truck',
  money: { dealer: { mult: 1.08, add: 1500 }, miles: { per10k: [[0, 0.035], [10, 0.025], [18, 0.02]], min: 0.6, max: 1.2 }, round: 250, bands: { far: 0.85, private_cap: 0.95 }, cap: 0.98, floor: 4500,
    trims: { 'TRD Off-Road': 1.15, 'Base': 0.95 }, drive: { rwd: 0.94, '4wd': 1.06 }, cab: null, newTrims: { 'TRD Off-Road': 1.12, 'Base': 0.85 }, records: { full: 0.25, none: -0.25 },
    fees: { tax_pct: 6, title_reg: [150, 400], doc_fee: [150, 700] }, trimYears: {}, today: '2026-11-24' },
  checks: { 'u-tires-tread': { q: 'Enough tread?', prob: 'Worn tires', k: 'cost', cost: { '*': [900, 1600] }, g: 'tires', r: 1, safe: true, sys: 'tires', need: 'four new tires', fixv: 'fit new tires', how: 'PAID-HOW-TEXT' },
    'g2-body-frame': { q: 'Heavy rust on the frame?', prob: 'Heavy rust on the frame', k: 'mech', key: true, sys: 'body' },
    'u-walk-ground': { q: 'Dry ground?', prob: 'Fluid leak', k: 'mech' } },
  ys: { 2012: { ids: ['u-tires-tread', 'g2-body-frame', 'u-walk-ground'], price: { lo: 13000, hi: 16750, mi: 165000, new: 27500 },
    unk: [{ id: 'g2-frame', t: 'the frame', checks: ['g2-body-frame'], v: { '*': [3000, 9000] }, mech_only: true, if_bad: 'walk' }],
    trims: [{ t: 'Base', eng: { sedan: '2.7 L I4 2TR-FE' }, tr: 'both' }, { t: 'TRD Off-Road', eng: { sedan: '4.0 L V6' }, tr: 'both' }],
    eng2: [{ name: '2.7 L I4 2TR-FE', adj: 0.9, est: '2.7' }, { name: '4.0 L V6', adj: 1, est: '4.0' }], driveR: [{ opts: ['rwd', '4wd'], fit: null }], drives: ['rwd', '4wd'], cabs: ['Regular Cab', 'Access Cab', 'Double Cab'] } },
};
function catalogKV() {
  const K = kv(); K.m.set('index', JSON.stringify({ v: 1, gens: Object.fromEntries(Object.entries(GENS).map(([g, c]) => [g, { cat: c, name: g }])) }));
  for (const g of Object.keys(GENS)) K.m.set('gen:' + g, doc(g));
  K.m.set('gen:toyota-tacoma-g2', JSON.stringify(TACO));
  return K;
}

// ---- fake Stripe + Resend + Turnstile
const S = { sessions: {}, calls: [], mails: [], ts: [], list: [], listFail: false, goalFile: null };   // goalFile = lemonindex.com/data/support_goal.json (11-27)   // list = what GET /v1/checkout/sessions returns, newest first
let n = 0;
globalThis.fetch = async (u, opt = {}) => {
  const url = new URL(u), ok = j => new Response(JSON.stringify(j), { status: 200 });
  if (url.host === 'api.resend.com') { S.mails.push(JSON.parse(opt.body)); return ok({ id: 'm1' }); }
  if (url.host === 'challenges.cloudflare.com') { const b = new URLSearchParams(opt.body); S.ts.push(b.get('response')); return ok({ success: b.get('response') === 'ts-good', hostname: 'lemonindex.com' }); }
  if (url.host === 'lemonindex.com' && url.pathname === '/data/support_goal.json') {   // the site's goal file (renewals for /goal)
    S.goalFileCalls = (S.goalFileCalls || 0) + 1;
    if (S.goalFile === 'fail') throw new Error('network');
    return S.goalFile ? new Response(JSON.stringify(S.goalFile), { status: 200 }) : new Response('not found', { status: 404 });
  }
  assert.equal(url.host, 'api.stripe.com'); assert.equal(opt.headers.Authorization, 'Bearer rk_test_fake');
  const body = new URLSearchParams(opt.body || ''); S.calls.push({ path: url.pathname, method: opt.method, body });
  if (url.pathname === '/v1/invoices') throw new Error('the Worker must never read invoices');
  if (url.pathname === '/v1/checkout/sessions' && opt.method === 'POST') {
    const id = 'cs_test_' + 'a'.repeat(20) + (++n), meta = {};
    for (const [k, v] of body) { const m = /^metadata\[(\w+)\]$/.exec(k); if (m) meta[m[1]] = v; }
    S.sessions[id] = { id, object: 'checkout.session', url: 'https://checkout.stripe.com/c/pay/' + id, mode: body.get('mode'), metadata: meta, client_reference_id: body.get('client_reference_id'),
      status: 'open', payment_status: 'unpaid', currency: 'usd', amount_total: body.get('line_items[0][price]') === env.PRICE_ALL ? 1999 : 799, payment_intent: null };
    return ok(S.sessions[id]);
  }
  if (url.pathname === '/v1/checkout/sessions' && opt.method === 'GET') {
    assert.equal(opt.body, undefined);
    if (S.listFail) return new Response(JSON.stringify({ error: { type: 'api_error' } }), { status: 500 });
    const q = url.searchParams, lim = Number(q.get('limit')), gte = Number(q.get('created[gte]')), st = q.get('status'), after = q.get('starting_after');
    S.calls[S.calls.length - 1].query = q;
    let L = S.list.filter(x => x.created >= gte && (!st || x.status === st));
    if (after) L = L.slice(L.findIndex(x => x.id === after) + 1);
    return ok({ object: 'list', data: L.slice(0, lim), has_more: L.length > lim });
  }
  throw new Error('unexpected fetch ' + url);
};

const WH = 'whsec_test_' + 'x'.repeat(24);
const env = { DB: d1(), CONTENT: catalogKV(), RL: rl(1000), RL_AUTH: rl(1000), RL_CONTENT: rl(1000), STRIPE_SECRET_KEY: 'rk_test_fake', STRIPE_WEBHOOK_SECRET: WH,
  TOKEN_KEY: 'k'.repeat(64), EMAIL_ON: '1', RESEND_KEY: 're_fake', MAIL_FROM: 'Lemon Index <signin@lemonindex.com>', DAILY_CAP: '1000',
  PRICE_ONE: 'price_1Ufol4Bq7BOH4VFnH1px4CoI', AMOUNT_ONE: '799', PRICE_ALL: 'price_1UfolUBq7BOH4VFnO6eePeNl', AMOUNT_ALL: '1999' };
let ipn = 0;
// fake caches.default (the Cache API): honours max-age, counts puts
const CACHE = { m: new Map(), puts: 0 };
globalThis.caches = { default: {
  match: async k => { const e = CACHE.m.get(String(k)); return e && e.exp > Date.now() ? new Response(e.text) : undefined; },
  put: async (k, r) => { CACHE.puts++; const ma = /max-age=([0-9]+)/.exec(r.headers.get('Cache-Control') || ''); CACHE.m.set(String(k), { text: await r.text(), exp: Date.now() + (ma ? Number(ma[1]) : 0) * 1000 }); },
} };
async function call(method, path, { body, token, origin = SITE, headers = {}, ip, host = 'https://lemon-store.elift08.workers.dev' } = {}) {
  const h = { 'CF-Connecting-IP': ip || '10.0.' + Math.floor(++ipn / 250) + '.' + (ipn % 250), ...headers };
  if (origin) h.Origin = origin; if (token) h.Authorization = 'Bearer ' + token; if (body !== undefined) h['Content-Type'] = 'application/json';
  const r = await worker.fetch(new Request(host + path, { method, headers: h, body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)) }), env);
  let j = null; const text = await r.text(); try { j = JSON.parse(text); } catch {}
  return { s: r.status, j, h: r.headers, text };
}
const sign = (raw, t = T(), secret = WH) => `t=${t},v1=${createHmac('sha256', secret).update(`${t}.${raw}`).digest('hex')}`;
let evn = 0;
async function hook(type, object, opts = {}) {
  const id = opts.id || 'evt_test' + (++evn).toString().padStart(8, '0');
  const raw = JSON.stringify({ id, object: 'event', type, created: opts.created || T(), data: { object } });
  const r = await call('POST', '/webhook', { body: raw, origin: null, headers: { 'Stripe-Signature': opts.sig || sign(raw, opts.t) } });
  return { ...r, id, raw };
}
const linkOf = m => /#t=(lsl_[A-Za-z0-9_-]{43})/.exec(m.html)[1];
async function signin(email, { next, dev = 'dev_' + 'a'.repeat(20) + (++ipn), ip } = {}) {
  const before = S.mails.length;
  const a = await call('POST', '/auth/start', { body: { email, next }, ip }); assert.equal(a.s, 200, JSON.stringify(a.j)); assert.equal(a.j.sent, true);
  assert.equal(S.mails.length, before + 1);
  const v = await call('POST', '/auth/verify', { body: { t: linkOf(S.mails.at(-1)), dev } }); assert.equal(v.s, 200, JSON.stringify(v.j));
  return { token: v.j.token, j: v.j, dev };
}
function paidSession(id, extra = {}) { const s = S.sessions[id]; Object.assign(s, { status: 'complete', payment_status: 'paid', payment_intent: 'pi_' + id.slice(-6) }, extra); return s; }
const tables = () => JSON.stringify(['users', 'links', 'sessions', 'purchases', 'progress', 'free_devices', 'free_used', 'hits'].map(t => env.DB.raw.prepare(`SELECT * FROM ${t}`).all()));

let pass = 0; const test = async (name, f) => { await f(); pass++; console.log('ok  ', name); };

await test('stripe signature: valid, tampered, wrong secret, too old, several v1, junk', async () => {
  const raw = '{"a":1}', t = T();
  assert.equal(await verifyStripe(raw, sign(raw, t), WH), true);
  assert.equal(await verifyStripe(raw + ' ', sign(raw, t), WH), false);
  assert.equal(await verifyStripe(raw, sign(raw, t, 'whsec_other'), WH), false);
  assert.equal(await verifyStripe(raw, sign(raw, t - 301), WH), false);
  assert.equal(await verifyStripe(raw, `t=${t},v1=${'0'.repeat(64)},` + sign(raw, t).split(',')[1], WH), true);
  for (const h of ['', 'nonsense', `t=${t}`, 'v1=abc', `t=abc,v1=${'0'.repeat(64)}`]) assert.equal(await verifyStripe(raw, h, WH), false);
  assert.equal(await verifyStripe(raw, sign(raw, t), ''), false);
  assert.equal(safeEqual('abc', 'abc'), true); assert.equal(safeEqual('abc', 'abd'), false);
  assert.equal(decodeURIComponent(new URLSearchParams(form({ line_items: [{ price: 'p', quantity: 1 }] })).toString()), 'line_items[0][price]=p&line_items[0][quantity]=1');
});
await test('email normalization: Gmail dots and +tags, googlemail, case; junk refused', async () => {
  assert.equal(normEmail('J.Doe+cars@Gmail.com').ekey, 'jdoe@gmail.com'); assert.equal(normEmail('j.doe@googlemail.com').ekey, 'jdoe@gmail.com');
  assert.equal(normEmail('J.Doe+cars@Gmail.com').email, 'j.doe+cars@gmail.com');
  // account key: exact on every non-Gmail domain (alice+x@corp.com may be another person's mailbox)
  assert.equal(normEmail('j.doe+x@outlook.com').ekey, 'j.doe+x@outlook.com'); assert.equal(normEmail('Alice+x@Corp.com').ekey, 'alice+x@corp.com');
  assert.equal(normEmail('a.lice@corp.com').ekey, 'a.lice@corp.com');
  // free key: +tags merged on big providers only, never on unknown domains
  assert.equal(normEmail('j.doe+x@outlook.com').fkey, 'j.doe@outlook.com'); assert.equal(normEmail('J.Doe+cars@Gmail.com').fkey, 'jdoe@gmail.com');
  assert.equal(normEmail('alice+x@corp.com').fkey, 'alice+x@corp.com');
  assert.equal(normEmail('alice+x@corp.com').rkey, 'alice@corp.com'); assert.equal(normEmail('J.Doe+1@Gmail.com').rkey, 'jdoe@gmail.com');
  for (const e of ['', 'a', 'a@b', 'a@b.c', '@x.com', 'a b@x.com', '+x@gmail.com', 'x@-x.com', 'a"b@x.com', 'x'.repeat(65) + '@x.com', null, 5]) assert.equal(normEmail(e), null, String(e));
});
await test('no account takeover by +tag or dots on a non-Gmail domain (security fix 11-25)', async () => {
  const A = await signin('alice@corp-example.com', { next: 'honda-civic-g10' });
  assert.equal(A.j.me.email, 'alice@corp-example.com');
  for (const other of ['alice+x@corp-example.com', 'a.lice@corp-example.com']) {
    const X = await signin(other);
    assert.equal(X.j.me.email, other, 'a different mailbox gets its own account');
    assert.equal(X.j.me.free, null, 'and does not see Alice free checklist');
    assert.equal((await call('GET', '/content?gen=honda-civic-g10', { token: X.token })).s, 403);
  }
  const A2 = await signin('ALICE@corp-example.com');                         // same address, other case: her account, address unchanged
  assert.equal(A2.j.me.free, 'honda-civic-g10'); assert.equal(A2.j.me.email, 'alice@corp-example.com');
  const G = await signin('gina.buyer+one@gmail.com');                        // Gmail variants still reach one account
  const G2 = await signin('ginabuyer@googlemail.com'); assert.equal(G2.j.me.email, 'gina.buyer+one@gmail.com');
});
await test('sign-in email limit: +tag variants on any domain share one limit of 3 an hour', async () => {
  for (let i = 0; i < 3; i++) assert.equal((await call('POST', '/auth/start', { body: { email: `flood+${i}@corp-flood.com` }, ip: '203.0.113.' + (50 + i) })).s, 200);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'flood+9@corp-flood.com' }, ip: '203.0.113.60' })).s, 429);
});
await test('CORS: only https://lemonindex.com; no credentials; preflight', async () => {
  assert.equal((await call('GET', '/me', { origin: 'https://evil.example' })).s, 403);
  assert.equal((await call('GET', '/me', { origin: null })).s, 403);
  assert.equal((await call('GET', '/me', { origin: 'http://localhost:8790' })).s, 403);   // no DEV_MODE
  const o = await call('OPTIONS', '/auth/start'); assert.equal(o.s, 204); assert.equal(o.h.get('Access-Control-Allow-Origin'), SITE);
  assert.equal(o.h.get('Access-Control-Allow-Credentials'), null);
  assert.equal((await call('OPTIONS', '/me', { origin: 'https://evil.example' })).h.get('Access-Control-Allow-Origin'), SITE);
  const r = await call('GET', '/me'); assert.equal(r.s, 401); assert.equal(r.h.get('Cache-Control'), 'no-store, private'); assert.equal(r.h.get('X-Content-Type-Options'), 'nosniff');
});
await test('dev mode only on localhost: DEV_MODE on workers.dev neither opens CORS nor leaks links', async () => {
  env.DEV_MODE = '1'; env.DEV_ORIGIN = 'http://localhost:8790'; env.EMAIL_ON = '0';
  assert.equal((await call('GET', '/me', { origin: 'http://localhost:8790' })).s, 403);
  const r = await call('POST', '/auth/start', { body: { email: 'dev@example.com' } }); assert.equal(r.s, 503); assert.equal(r.j.dev_link, undefined);
  const l = await call('POST', '/auth/start', { body: { email: 'dev2@example.com' }, origin: 'http://localhost:8790', host: 'http://localhost:8787' });
  assert.equal(l.s, 200); assert.match(l.j.dev_link, /^http:\/\/localhost:8790\/account\/signin\/#t=lsl_/);
  delete env.DEV_MODE; delete env.DEV_ORIGIN; env.EMAIL_ON = '1';
});
await test('sign-in start: validation, disposable block, payload cap, same answer for every email, link is a hashed single-use fragment', async () => {
  for (const email of ['nope', '', 'a@b.c', 'x@mailinator.com', 'x@sub.yopmail.com']) assert.equal((await call('POST', '/auth/start', { body: { email } })).s, 400, email);
  assert.equal((await call('POST', '/auth/start', { body: 'not json' })).s, 400);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'a@example.com', pad: 'x'.repeat(3000) } })).s, 400);
  const r = await call('POST', '/auth/start', { body: { email: 'First@Example.com', next: 'toyota-corolla-g11' } }); assert.equal(r.s, 200); assert.deepEqual(r.j, { sent: true });
  const m = S.mails.at(-1); assert.deepEqual(m.to, ['first@example.com']); assert.match(m.subject, /^Your Lemon Index sign-in link \([0-9A-F]{6}\)$/); assert.ok(m.headers && m.headers['X-Entity-Ref-ID']); assert.equal(m.from, 'Lemon Index <signin@lemonindex.com>');
  assert.match(m.html, /https:\/\/lemonindex\.com\/account\/signin\/#t=lsl_/); assert.match(m.text, /expires in 15 minutes/);
  const tok = linkOf(m); assert.ok(!tables().includes(tok), 'raw link token stored');
  assert.equal(env.DB.raw.prepare('SELECT next FROM links ORDER BY rowid DESC LIMIT 1').get().next, 'toyota-corolla-g11');
  await call('POST', '/auth/start', { body: { email: 'x@example.com', next: '../../etc' } });
  assert.equal(env.DB.raw.prepare('SELECT next FROM links ORDER BY rowid DESC LIMIT 1').get().next, null);
});
await test('sign-in links: work once, expire after 15 minutes, junk refused', async () => {
  await call('POST', '/auth/start', { body: { email: 'once@example.com' } }); const t1 = linkOf(S.mails.at(-1));
  const v = await call('POST', '/auth/verify', { body: { t: t1 } }); assert.equal(v.s, 200); assert.match(v.j.token, /^lss_[A-Za-z0-9_-]{43}$/);
  assert.equal(v.j.me.email, 'once@example.com'); assert.equal(v.j.me.freeLeft, true);
  const again = await call('POST', '/auth/verify', { body: { t: t1 } }); assert.equal(again.s, 400); assert.equal(again.j.error, 'used');
  await call('POST', '/auth/start', { body: { email: 'late@example.com' } }); const t2 = linkOf(S.mails.at(-1));
  skew += LINK_TTL + 1; const late = await call('POST', '/auth/verify', { body: { t: t2 } }); skew -= LINK_TTL + 1;
  assert.equal(late.s, 400); assert.equal(late.j.error, 'expired');
  assert.equal((await call('POST', '/auth/verify', { body: { t: 'lsl_' + 'q'.repeat(43) } })).j.error, 'bad');
  for (const t of ['', 'abc', 'lss_' + 'q'.repeat(43), null]) assert.equal((await call('POST', '/auth/verify', { body: { t } })).s, 400);
  assert.ok(!tables().includes(v.j.token), 'raw session token stored');
});
await test('rate limits: 3 links an hour per inbox (any Gmail spelling), 10 an hour per IP, edge burst limit', async () => {
  for (const e of ['rate.me@gmail.com', 'rateme@gmail.com', 'rate.me+1@gmail.com']) assert.equal((await call('POST', '/auth/start', { body: { email: e } })).s, 200);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'r.a.t.e.m.e@googlemail.com' } })).s, 429);
  skew += 3601; assert.equal((await call('POST', '/auth/start', { body: { email: 'rateme@gmail.com' } })).s, 200); skew -= 3601;
  const ip = '192.0.2.77';
  for (let i = 0; i < 10; i++) assert.equal((await call('POST', '/auth/start', { body: { email: `ip${i}@example.com` }, ip })).s, 200, 'ip ' + i);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'ip10@example.com' }, ip })).s, 429);
  const old = env.RL_AUTH; env.RL_AUTH = rl(2);
  const ip2 = '192.0.2.78'; const rs = [];
  for (let i = 0; i < 3; i++) rs.push((await call('POST', '/auth/start', { body: { email: `b${i}@example.com` }, ip: ip2 })).s);
  assert.deepEqual(rs, [200, 200, 429]); env.RL_AUTH = old;
});
await test('turnstile: pluggable, required when TURNSTILE_ON = 1, refuses a failed token', async () => {
  env.TURNSTILE_ON = '1';
  assert.equal((await call('POST', '/auth/start', { body: { email: 'ts@example.com', ts: 'ts-good' } })).s, 503);   // on, but no secret: refuse, don't skip
  env.TURNSTILE_SECRET = '0x_fake_secret';
  assert.equal((await call('POST', '/auth/start', { body: { email: 'ts@example.com' } })).s, 403);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'ts@example.com', ts: 'ts-bad' } })).s, 403);
  assert.equal((await call('POST', '/auth/start', { body: { email: 'ts@example.com', ts: 'ts-good' } })).s, 200);
  delete env.TURNSTILE_SECRET; env.TURNSTILE_ON = '0';
});
let A, B;
await test('free checklist: claimed from the sign-up link, once per email (any spelling), once per device, then content opens', async () => {
  A = await signin('Ann.Buyer@gmail.com', { next: 'toyota-corolla-g11' });
  assert.equal(A.j.claimed, 'toyota-corolla-g11'); assert.equal(A.j.me.free, 'toyota-corolla-g11'); assert.equal(A.j.me.freeLeft, false);
  const c = await call('GET', '/content?gen=toyota-corolla-g11', { token: A.token }); assert.equal(c.s, 200); assert.equal(c.j.checks.a.q, 'PAID-SECRET-toyota-corolla-g11');
  assert.equal((await call('POST', '/free', { token: A.token, body: { gen: 'toyota-tacoma-g2', dev: A.dev } })).j.error, 'used');
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 403);
  const A2 = await signin('annbuyer+new@gmail.com');                       // same inbox, other spelling: same account, no second free one
  assert.equal(A2.j.me.free, 'toyota-corolla-g11');
  assert.equal((await call('POST', '/free', { token: A2.token, body: { gen: 'toyota-tacoma-g2', dev: 'dev_' + 'z'.repeat(20) } })).s, 409);
  B = await signin('bob@example.com');
  assert.equal((await call('POST', '/free', { token: B.token, body: { gen: 'toyota-tacoma-g2', dev: A.dev } })).j.error, 'device-used');   // same device as Ann
  assert.equal((await call('POST', '/free', { token: B.token, body: { gen: 'toyota-tacoma-g2' } })).s, 400);                              // no device id
  assert.equal((await call('POST', '/free', { token: B.token, body: { gen: 'honda-cbr600rr-g1', dev: B.dev } })).s, 404);                  // motorcycles aren't in this product
  assert.equal((await call('POST', '/free', { token: B.token, body: { gen: 'toyota-tacoma-g2', dev: B.dev } })).j.gen, 'toyota-tacoma-g2');
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: B.token })).s, 200);
});
await test('free checklist: soft limit of 3 a day per IP', async () => {
  const ip = '198.51.100.9', r = [];
  for (let i = 0; i < 4; i++) { const u = await signin(`ipfree${i}@example.com`); r.push((await call('POST', '/free', { token: u.token, ip, body: { gen: 'honda-civic-g10', dev: u.dev } })).s); }
  assert.deepEqual(r, [200, 200, 200, 429]);
});
await test('content: needs a session, the right owner, a real generation; wrong-session fetch is refused', async () => {
  assert.equal((await call('GET', '/content?gen=toyota-corolla-g11')).s, 401);
  assert.equal((await call('GET', '/content?gen=toyota-corolla-g11', { token: 'lss_' + 'x'.repeat(43) })).s, 401);
  assert.equal((await call('GET', '/content?gen=toyota-corolla-g11', { token: B.token })).s, 403);        // Bob's session, Ann's free checklist
  for (const g of ['', '../index', 'index', 'toyota', 'toyota-corolla-g11/../x']) assert.equal((await call('GET', '/content?gen=' + encodeURIComponent(g), { token: A.token })).s, 400, g);
  assert.equal((await call('GET', '/content?gen=nissan-leaf-g1', { token: A.token })).s, 404);
  const old = env.RL_CONTENT; env.RL_CONTENT = rl(3); const rs = [];
  for (let i = 0; i < 4; i++) rs.push((await call('GET', '/content?gen=toyota-corolla-g11', { token: A.token })).s);
  assert.deepEqual(rs, [200, 200, 200, 429]); env.RL_CONTENT = old;
});
let csOne, csAll;
await test('checkout: signed in only, live price ids, metadata from the server; the success redirect grants nothing', async () => {
  assert.equal((await call('POST', '/checkout', { body: { item: 'one', gen: 'toyota-tacoma-g2' } })).s, 401);
  for (const b of [{ item: 'x', gen: 'toyota-tacoma-g2' }, { item: 'one' }, { item: 'one', gen: '__proto__' }, { item: 'one', gen: 'honda-cbr600rr-g1' }, { item: 'one', gen: 'nissan-leaf-g1' }])
    assert.ok([400, 404].includes((await call('POST', '/checkout', { token: A.token, body: b })).s), JSON.stringify(b));
  assert.equal((await call('POST', '/checkout', { token: A.token, body: { item: 'one', gen: 'toyota-corolla-g11' } })).j.error, 'owned');   // her free one
  const r = await call('POST', '/checkout', { token: A.token, body: { item: 'one', gen: 'toyota-tacoma-g2', uid: 'u_evil', price: 'price_cheap' } });
  assert.equal(r.s, 200); assert.match(r.j.url, /^https:\/\/checkout\.stripe\.com\//);
  const b = S.calls.at(-1).body;
  assert.equal(b.get('mode'), 'payment'); assert.equal(b.get('line_items[0][price]'), env.PRICE_ONE); assert.equal(b.get('line_items[0][quantity]'), '1');
  assert.equal(b.get('customer_email'), 'ann.buyer@gmail.com');   // the account's own address (a sign-in link never rewrites it; Gmail variants are one inbox)
  assert.equal(b.get('metadata[site]'), 'lemon-store'); assert.equal(b.get('metadata[gen]'), 'toyota-tacoma-g2');
  assert.match(b.get('metadata[uid]'), /^u_/); assert.notEqual(b.get('metadata[uid]'), 'u_evil'); assert.equal(b.get('payment_intent_data[metadata][item]'), 'one'); assert.ok(b.get('payment_intent_data[receipt_email]'));
  assert.equal(b.get('success_url'), SITE + '/checklist/toyota-tacoma-g2/?paid=1'); assert.equal(b.get('cancel_url'), SITE + '/checklist/toyota-tacoma-g2/#paywall');
  csOne = Object.keys(S.sessions).at(-1);
  const me = await call('GET', '/me', { token: A.token }); assert.deepEqual(me.j.owned, []);                     // back from Stripe, no webhook yet: nothing
  paidSession(csOne);
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 403);
  const a = await call('POST', '/checkout', { token: B.token, body: { item: 'all', gen: 'toyota-tacoma-g2' } }); assert.equal(a.s, 200);
  assert.equal(S.calls.at(-1).body.get('line_items[0][price]'), env.PRICE_ALL); csAll = Object.keys(S.sessions).at(-1);
});
await test('checkout: 10 an hour per account', async () => {
  const u = await signin('many@example.com'); const rs = [];
  for (let i = 0; i < 11; i++) rs.push((await call('POST', '/checkout', { token: u.token, body: { item: 'one', gen: 'honda-civic-g10' } })).s);
  assert.equal(rs.filter(s => s === 200).length, 10); assert.equal(rs.at(-1), 429);
});
let evPaid;
await test('webhook: bad signature refused; paid session grants; replay and a second event for the same session change nothing', async () => {
  const s = S.sessions[csOne];
  assert.equal((await hook('checkout.session.completed', s, { sig: sign('{}') })).s, 400);
  assert.equal((await hook('checkout.session.completed', s, { t: T() - 600 })).s, 400);
  const raw = JSON.stringify({ id: 'evt_forged0001', type: 'checkout.session.completed', created: T(), data: { object: s } });
  assert.equal((await call('POST', '/webhook', { body: raw, origin: null, headers: { 'Stripe-Signature': sign(raw, T(), 'whsec_wrong') } })).s, 400);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM purchases').get().n, 0);
  evPaid = await hook('checkout.session.completed', s); assert.equal(evPaid.s, 200); assert.equal(evPaid.j.received, true);
  assert.deepEqual((await call('GET', '/me', { token: A.token })).j.owned, ['toyota-tacoma-g2']);
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 200);
  const replay = await call('POST', '/webhook', { body: evPaid.raw, origin: null, headers: { 'Stripe-Signature': sign(evPaid.raw) } });
  assert.equal(replay.s, 200); assert.equal(replay.j.duplicate, true);
  assert.equal((await hook('checkout.session.async_payment_succeeded', s)).s, 200);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM purchases').get().n, 1);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM events').get().n, 2);
});
await test('webhook: unpaid (async) session waits; wrong amount, other site, bad uid never grant; async success grants', async () => {
  const u = await signin('async@example.com');
  await call('POST', '/checkout', { token: u.token, body: { item: 'one', gen: 'honda-civic-g10' } }); const id = Object.keys(S.sessions).at(-1), s = S.sessions[id];
  Object.assign(s, { status: 'complete', payment_status: 'unpaid', payment_intent: 'pi_async1' });
  await hook('checkout.session.completed', s); assert.deepEqual((await call('GET', '/me', { token: u.token })).j.owned, []);
  for (const bad of [{ amount_total: 1 }, { currency: 'eur' }, { metadata: { ...s.metadata, site: 'ew-store' } }, { metadata: { ...s.metadata, uid: "x'; DROP TABLE users;--" } }, { mode: 'subscription' }])
    { await hook('checkout.session.async_payment_succeeded', { ...s, payment_status: 'paid', ...bad }); assert.deepEqual((await call('GET', '/me', { token: u.token })).j.owned, [], JSON.stringify(bad)); }
  await hook('checkout.session.async_payment_succeeded', { ...s, payment_status: 'paid' });
  assert.deepEqual((await call('GET', '/me', { token: u.token })).j.owned, ['honda-civic-g10']);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM users').get().n > 0, true);
});
await test('refund: a full refund revokes, a partial one does not, an old event arriving late does not undo it', async () => {
  const pi = S.sessions[csOne].payment_intent;
  await hook('charge.refunded', { object: 'charge', id: 'ch_1', payment_intent: pi, refunded: false, amount_refunded: 100 });
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 200);
  await hook('charge.refunded', { object: 'charge', id: 'ch_1', payment_intent: pi, refunded: true, amount_refunded: 799 });
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 403);
  assert.deepEqual((await call('GET', '/me', { token: A.token })).j.owned, []);
  assert.equal((await call('GET', '/content?gen=toyota-corolla-g11', { token: A.token })).s, 200);      // the free one stays
  await hook('checkout.session.completed', S.sessions[csOne], { created: T() - 100 });                      // a late copy of the paid event
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 403);
});
await test('refund that arrives before the paid event (out of order): the purchase starts refunded', async () => {
  const u = await signin('ooo@example.com');
  await call('POST', '/checkout', { token: u.token, body: { item: 'one', gen: 'toyota-tacoma-g2' } }); const id = Object.keys(S.sessions).at(-1);
  const s = paidSession(id, { payment_intent: 'pi_outoforder1' });
  await hook('charge.refunded', { object: 'charge', payment_intent: 'pi_outoforder1', refunded: true }, { created: T() });
  await hook('checkout.session.completed', s, { created: T() - 30 });
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: u.token })).s, 403);
});
await test('disputes: opened = off, won = back on, lost = stays off; a won dispute never undoes a refund', async () => {
  const u = await signin('dispute@example.com');
  await call('POST', '/checkout', { token: u.token, body: { item: 'one', gen: 'toyota-tacoma-g2' } }); const id = Object.keys(S.sessions).at(-1);
  await hook('checkout.session.completed', paidSession(id, { payment_intent: 'pi_disp1' }));
  const get = async () => (await call('GET', '/content?gen=toyota-tacoma-g2', { token: u.token })).s;
  assert.equal(await get(), 200);
  await hook('charge.dispute.created', { object: 'dispute', id: 'dp_1', charge: 'ch_9', payment_intent: 'pi_disp1', status: 'needs_response' }); assert.equal(await get(), 403);
  await hook('charge.dispute.closed', { object: 'dispute', id: 'dp_1', payment_intent: 'pi_disp1', status: 'won' }, { created: T() + 1 }); assert.equal(await get(), 200);
  await hook('charge.dispute.created', { object: 'dispute', id: 'dp_2', payment_intent: 'pi_disp1', status: 'needs_response' }, { created: T() + 2 }); assert.equal(await get(), 403);
  await hook('charge.dispute.closed', { object: 'dispute', id: 'dp_2', payment_intent: 'pi_disp1', status: 'lost' }, { created: T() + 3 }); assert.equal(await get(), 403);
  await hook('charge.dispute.closed', { object: 'dispute', id: 'dp_old', payment_intent: 'pi_disp1', status: 'won' }, { created: T() - 50 }); assert.equal(await get(), 403);   // stale
  // refunded purchase + a won dispute: stays refunded
  const pi = S.sessions[csOne].payment_intent;
  await hook('charge.dispute.closed', { object: 'dispute', payment_intent: pi, status: 'won' }, { created: T() + 10 });
  assert.equal((await call('GET', '/content?gen=toyota-tacoma-g2', { token: A.token })).s, 403);
});
await test('all cars and trucks: every car checklist, one added after the purchase too; motorcycles not included', async () => {
  await hook('checkout.session.completed', paidSession(csAll, { amount_total: 1999, payment_intent: 'pi_all1' }));
  const me = await call('GET', '/me', { token: B.token }); assert.equal(me.j.all, true);
  for (const g of ['toyota-corolla-g11', 'toyota-tacoma-g2', 'honda-civic-g10']) assert.equal((await call('GET', '/content?gen=' + g, { token: B.token })).s, 200, g);
  assert.equal((await call('GET', '/content?gen=honda-cbr600rr-g1', { token: B.token })).s, 403);
  // a checklist uploaded later
  const idx = JSON.parse(env.CONTENT.m.get('index')); idx.gens['ford-ranger-g4'] = { cat: 'car', name: 'Ford Ranger' };
  env.CONTENT.m.set('index', JSON.stringify(idx)); env.CONTENT.m.set('gen:ford-ranger-g4', doc('ford-ranger-g4')); clearCache();
  const r = await call('GET', '/content?gen=ford-ranger-g4', { token: B.token }); assert.equal(r.s, 200); assert.equal(r.j.id, 'ford-ranger-g4');
  assert.equal((await call('GET', '/content?gen=ford-ranger-g4', { token: A.token })).s, 403);
  assert.equal((await call('POST', '/checkout', { token: B.token, body: { item: 'one', gen: 'ford-ranger-g4' } })).j.error, 'owned');
});
await test('progress: saved per account and checklist, size cap, owners only, never another account’s', async () => {
  const data = { y: 2016, seller: 'p', a: { 'u-tires-tread': 'bad' } };
  assert.equal((await call('PUT', '/progress', { token: A.token, body: { gen: 'toyota-corolla-g11', data } })).s, 200);
  assert.deepEqual((await call('GET', '/progress?gen=toyota-corolla-g11', { token: A.token })).j.data, data);
  assert.equal((await call('GET', '/progress?gen=toyota-corolla-g11', { token: B.token })).j.data, null);
  assert.equal((await call('PUT', '/progress', { token: A.token, body: { gen: 'toyota-tacoma-g2', data } })).s, 403);   // refunded: not hers
  assert.equal((await call('PUT', '/progress', { token: A.token, body: { gen: 'toyota-corolla-g11', data: { x: 'y'.repeat(17000) } } })).s, 400);
  assert.equal((await call('PUT', '/progress', { token: A.token, body: { gen: 'toyota-corolla-g11', data: [1] } })).s, 400);
  assert.deepEqual((await call('GET', '/me', { token: A.token })).j.progress.map(p => p.gen), ['toyota-corolla-g11']);
});
await test('sessions: rotate after a day (old token has a short grace), expire after 7 days, chain capped at 60 days', async () => {
  const u = await signin('rot@example.com');
  assert.equal((await call('GET', '/me', { token: u.token })).j.rotate, undefined);
  skew += ROTATE_AFTER + 5;
  const r = await call('GET', '/me', { token: u.token }); assert.match(r.j.rotate.token, /^lss_/); const t2 = r.j.rotate.token;
  assert.equal((await call('GET', '/me', { token: u.token })).s, 200);                       // grace
  skew += GRACE + 1; assert.equal((await call('GET', '/me', { token: u.token })).s, 401);   // old one gone
  assert.equal((await call('GET', '/me', { token: t2 })).s, 200);
  skew += SESSION_TTL; assert.equal((await call('GET', '/me', { token: t2 })).s, 401);      // unused for 7 days
  skew -= SESSION_TTL + GRACE + 1 + ROTATE_AFTER + 5;
  const c = await signin('chain@example.com'); let tok = c.token;
  for (let d = 0; d < 70; d += 2) { skew += 2 * DAY_(); const x = await call('GET', '/me', { token: tok }); if (x.s !== 200) { assert.ok(d >= 58, 'chain ended early at day ' + d); tok = null; break; } if (x.j.rotate) tok = x.j.rotate.token; }
  assert.equal(tok, null, 'chain never ended'); skew = 0;
});
function DAY_() { return 86400; }
await test('sign out: this device, or every device; a new device signs in and gets its purchases back', async () => {
  skew = 3700;   // Bob already asked for 2 links this hour
  const p1 = await signin('bob@example.com'), p2 = await signin('bob@example.com');
  assert.equal((await call('POST', '/auth/signout', { token: p1.token, body: {} })).s, 200);
  assert.equal((await call('GET', '/me', { token: p1.token })).s, 401); assert.equal((await call('GET', '/me', { token: p2.token })).s, 200);
  await call('POST', '/auth/signout', { token: p2.token, body: { all: true } });
  assert.equal((await call('GET', '/me', { token: p2.token })).s, 401); assert.equal((await call('GET', '/me', { token: B.token })).s, 401);
  skew = 7400; const fresh = await signin('BOB@example.com'); assert.equal(fresh.j.me.all, true); assert.equal(fresh.j.me.free, 'toyota-tacoma-g2'); B = fresh;
});
await test('delete account: needs the email typed; sessions and progress go; the free checklist is not given again', async () => {
  const u = await signin('del.me@gmail.com', { next: 'honda-civic-g10' }); assert.equal(u.j.claimed, 'honda-civic-g10');
  await call('PUT', '/progress', { token: u.token, body: { gen: 'honda-civic-g10', data: { a: 1 } } });
  assert.equal((await call('POST', '/account/delete', { token: u.token, body: { confirm: 'wrong@example.com' } })).s, 400);
  assert.equal((await call('POST', '/account/delete', { token: u.token, body: { confirm: 'Del.Me@gmail.com' } })).s, 200);
  assert.equal((await call('GET', '/me', { token: u.token })).s, 401);
  assert.equal(env.DB.raw.prepare("SELECT COUNT(*) n FROM users WHERE email = 'del.me@gmail.com'").get().n, 0);
  const again = await signin('delme@gmail.com', { next: 'toyota-tacoma-g2', dev: 'dev_' + 'n'.repeat(30) });
  assert.equal(again.j.claimed, null); assert.equal(again.j.me.freeLeft, false);
});
await test('answer screen: the engine runs in the Worker, owners only; the numbers match dealer_offer.md; cleared / found a problem at runtime', async () => {
  const u = await signin('tacoma.buyer@example.com', { next: 'toyota-tacoma-g2' }); assert.equal(u.j.claimed, 'toyota-tacoma-g2');
  const car = { y: 2012, trim: 'TRD Off-Road', tr: 'auto', drive: '4wd', cab: 'Double Cab', miles: 140000, ans: { 'u-tires-tread': 'bad', 'g2-body-frame': 'ok', 'u-walk-ground': 'ok' } };
  const ask = async (s, token = u.token, gen = 'toyota-tacoma-g2') => call('POST', '/answer', { token, body: { gen, s } });
  // not signed in, someone else's session, a checklist this account doesn't own
  assert.equal((await call('POST', '/answer', { body: { gen: 'toyota-tacoma-g2', s: car } })).s, 401);
  assert.equal((await ask(car, u.token, 'honda-civic-g10')).s, 403);
  // private seller, $19,500 asked: as it is $18,100 / open $17,000; fixed first $19,300 / open $18,100; out the door $19,350-$19,600
  let r = await ask({ ...car, seller: 'private', ask: 19500 }); assert.equal(r.s, 200, r.text);
  assert.deepEqual([r.j.range, r.j.max, r.j.open, r.j.fixed, r.j.fixedOpen, r.j.otd], [[16750, 21750], 18100, 17000, 19300, 18100, [19350, 19600]]);
  assert.equal(r.j.c, 'neg'); assert.equal(r.j.unk[0].st, 'open'); assert.equal(r.j.unk[0].out, 'walk'); assert.match(r.j.for, /TRD Off-Road, 4\.0 L V6, 4WD, Double Cab, 140,000 miles/);
  assert.equal(r.j.say[1], '“It needs four new tires. As it is, I can do $17,000. If you fit new tires first, $18,100.”');
  // the mechanic cleared the frame and quoted the tires at $1,150: computed now, not stored
  r = await ask({ ...car, seller: 'private', ask: 19500, unk: { 'g2-frame': 'ok' }, quote: { 'u-tires-tread': 1150 } });
  assert.deepEqual([r.j.max, r.j.open, r.j.unk[0].st], [18200, 17100, 'ok']);
  r = await ask({ ...car, seller: 'private', ask: 19500, unk: { 'g2-frame': 'bad' } }); assert.equal(r.j.c, 'walk');
  // dealer, no asking price (and the same with $22,900 asked: the asking price never moves the ceiling)
  for (const a of [0, 22900]) {
    r = await ask({ ...car, seller: 'dealer', ask: a, tax: a ? '' : null });   // the browser sends tax: null when the box is blank
    assert.equal(r.j.fees.taxPct, 6);
    assert.deepEqual([r.j.range, r.j.max, r.j.open, r.j.fixed, r.j.fixedOpen, r.j.otd, r.j.fees.docFee], [[19750, 25000], 21200, 19900, 22400, 21100, [22750, 23550], [150, 700]]);
  }
  // junk is cleaned, not trusted: unknown check ids, values, huge numbers, a prototype key
  r = await ask({ ...car, seller: 'evil', ask: 1e12, ans: { ...car.ans, nope: 'bad', 'u-walk-ground': 'drop table' }, quote: { 'u-tires-tread': -5 }, unk: { __proto__: 'bad' } });
  assert.equal(r.s, 200); assert.equal(r.j.seller, 'private'); assert.equal(r.j.ask, null); assert.equal(r.j.max, 18100);
  assert.equal((await ask({ ...car, y: 2031 })).s, 400); assert.equal((await ask('x')).s, 400);
  assert.equal((await call('POST', '/answer', { token: u.token, body: JSON.stringify({ gen: 'toyota-tacoma-g2', s: car, pad: 'x'.repeat(30000) }) })).s, 400);
  // the checklist itself: the page gets the checks, never the price tables the engine uses
  const c = await call('GET', '/content?gen=toyota-tacoma-g2', { token: u.token }); assert.equal(c.s, 200);
  assert.equal(c.j.checks['u-tires-tread'].how, 'PAID-HOW-TEXT'); assert.deepEqual(Object.keys(c.j.money), ['fees']); assert.ok(!c.text.includes('newTrims') && !c.text.includes('"mult"'));
});
await test('nothing secret in the database or the mail: raw tokens, IPs and device ids are never stored', async () => {
  const all = tables();
  assert.ok(!all.includes(A.token) && !all.includes(B.token)); assert.ok(!/10\.0\.\d+\.\d+|192\.0\.2|198\.51/.test(all), 'an IP was stored');
  assert.ok(!all.includes(A.dev), 'a raw device id was stored');
  const m = mailBody('https://lemonindex.com/account/signin/#t="><script>'); assert.ok(!m.html.includes('"><script>'));
});
// ---- GET /goal: this month's donations (Payment Link sessions only), cached 5 min
let gid = 0;
const monthStart = () => { const d = new Date(Date.now()); return Math.floor(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000); };
const monthOf = () => new Date(Date.now()).toISOString().slice(0, 7);
const donation = (cents, extra = {}) => ({ id: 'cs_live_d' + String(++gid).padStart(12, '0'), object: 'checkout.session', status: 'complete', payment_status: 'paid', currency: 'usd',
  amount_total: cents, payment_link: 'plink_1UXW60Bq7BOH4VFnyA7cg1Z0', metadata: {}, created: Math.max(monthStart(), T() - gid), ...extra });
const listCalls = () => S.calls.filter(c => c.method === 'GET' && c.path === '/v1/checkout/sessions');
function goalReset(list, goalFile = null) { clearGoal(); CACHE.m.clear(); CACHE.puts = 0; S.calls = []; S.listFail = false; S.goalFile = goalFile; S.goalFileCalls = 0; S.list = list.sort((a, b) => b.created - a.created); }
await test('goal: sums only paid usd donations (Payment Links); checklist sales, unpaid, open and other currencies never count', async () => {
  goalReset([donation(500), donation(525), donation(575),
    donation(1999, { payment_link: null, metadata: { site: 'lemon-store', item: 'all' } }),          // checklist sales: no payment_link
    donation(799, { payment_link: null, metadata: { site: 'lemon-store', item: 'one' } }),
    donation(2000, { payment_status: 'unpaid' }), donation(3000, { status: 'open', payment_status: 'unpaid' }), donation(4000, { status: 'expired', payment_status: 'unpaid' }),
    donation(5000, { currency: 'eur' }), donation(6000, { created: monthStart() - 10 })]);             // last month
  const r = await call('GET', '/goal');
  assert.equal(r.s, 200); assert.deepEqual(r.j, { month: monthOf(), raised: 16, n: 3 });
  assert.equal(r.h.get('Access-Control-Allow-Origin'), SITE); assert.equal(r.h.get('Cache-Control'), 'public, max-age=60');
  const c = listCalls(); assert.equal(c.length, 1);
  assert.equal(c[0].query.get('limit'), '100'); assert.equal(c[0].query.get('status'), 'complete'); assert.equal(c[0].query.get('created[gte]'), String(monthStart()));
  assert.equal(CACHE.puts, 2);
});
await test('goal: whole dollars (rounded down) and every page of results (limit 100, starting_after)', async () => {
  goalReset(Array.from({ length: 250 }, () => donation(501)));
  const r = await call('GET', '/goal');
  assert.deepEqual(r.j, { month: monthOf(), raised: 1252, n: 250 });                              // 250 x $5.01 = $1252.50
  const c = listCalls(); assert.equal(c.length, 3);
  assert.equal(c[0].query.get('starting_after'), null); assert.equal(c[1].query.get('starting_after'), S.list[99].id); assert.equal(c[2].query.get('starting_after'), S.list[199].id);
});
await test('goal: cached: a second request (and a fresh Worker copy within 5 min) does not call Stripe again', async () => {
  goalReset([donation(1600)]);
  assert.equal((await call('GET', '/goal')).j.raised, 16);
  S.list.unshift(donation(10000));
  assert.equal((await call('GET', '/goal')).j.raised, 16); assert.equal(listCalls().length, 1);    // this Worker copy's memory
  clearGoal(); assert.equal((await call('GET', '/goal')).j.raised, 16); assert.equal(listCalls().length, 1);   // a new copy: the edge cache
  skew += 301; assert.equal((await call('GET', '/goal')).j.raised, 116); assert.equal(listCalls().length, 2);  // after 5 minutes: Stripe again
  clearGoal(); CACHE.m.clear();
  const many = await Promise.all([1, 2, 3, 4].map(() => call('GET', '/goal')));                      // a burst on a cold copy: one Stripe pull
  assert.ok(many.every(x => x.j.raised === 116)); assert.equal(listCalls().length, 3);
});
await test('goal: Stripe down -> the last good number (memory, then the long cache copy), else 503; origin, method and rate limit', async () => {
  goalReset([donation(1600)]);
  assert.equal((await call('GET', '/goal')).j.raised, 16);
  skew += 301; S.listFail = true;
  let r = await call('GET', '/goal'); assert.equal(r.s, 200); assert.equal(r.j.raised, 16);         // memory
  clearGoal(); r = await call('GET', '/goal'); assert.equal(r.s, 200); assert.equal(r.j.raised, 16); // the 35-day copy
  goalReset([donation(1600)]); S.listFail = true;
  r = await call('GET', '/goal'); assert.equal(r.s, 503); assert.equal(r.j.error, 'unavailable');
  S.listFail = false;
  assert.equal((await call('GET', '/goal', { origin: 'https://evil.example' })).s, 403);
  assert.equal((await call('GET', '/goal', { origin: null })).s, 403);
  assert.equal((await call('POST', '/goal', { body: {} })).s, 401);                                  // only GET is public
  const o = await call('OPTIONS', '/goal', { origin: 'https://evil.example' }); assert.equal(o.h.get('Access-Control-Allow-Origin'), SITE);
  const x = await worker.fetch(new Request('https://lemon-store.elift08.workers.dev/goal', { headers: { Origin: SITE, 'CF-Connecting-IP': '10.9.9.9' } }), { ...env, RL: rl(0) });
  assert.equal(x.status, 429);
  const nokey = await worker.fetch(new Request('https://lemon-store.elift08.workers.dev/goal', { headers: { Origin: SITE } }), { ...env, STRIPE_SECRET_KEY: '' });
  assert.equal(nokey.status, 503);
});
// ---- 11-27 donations v2: /goal + renewals from the site's goal file (never invoices), and GET /feed (names only from the NEW field label)
const NEWF = v => [{ key: 'instagramstoryshoutoutnameorhandle', label: { type: 'custom', custom: 'Name for a shout-out + thank-you wall' }, type: 'text', text: { value: v } }];
const OLDF = v => [{ key: 'instagramstoryshoutoutnameorhandle', label: { type: 'custom', custom: 'Instagram story shout-out? Name or handle' }, type: 'text', text: { value: v } }];
await test('goal: + renewals from the site goal file when its month matches; a missing, failed or junk file adds 0 and never fails', async () => {
  goalReset([donation(500), donation(1000, { mode: 'subscription', subscription: 'sub_A' })], { month: monthOf(), raised: 99, renewals: { cents: 1300, n: 2 } });
  let r = await call('GET', '/goal'); assert.equal(r.s, 200); assert.deepEqual(r.j, { month: monthOf(), raised: 28, n: 4 });
  goalReset([donation(500)], { month: '1999-01', renewals: { cents: 1300, n: 2 } }); r = await call('GET', '/goal'); assert.deepEqual(r.j, { month: monthOf(), raised: 5, n: 1 });
  goalReset([donation(500)], null); r = await call('GET', '/goal'); assert.equal(r.s, 200); assert.equal(r.j.raised, 5);          // 404
  goalReset([donation(500)], 'fail'); r = await call('GET', '/goal'); assert.equal(r.s, 200); assert.equal(r.j.raised, 5);        // network error
  goalReset([donation(500)], { month: monthOf(), renewals: { cents: 'x', n: -1 } }); r = await call('GET', '/goal'); assert.equal(r.j.raised, 5);
  goalReset([donation(500)], { month: monthOf(), renewals: { cents: 300, n: 1 } });
  await call('GET', '/goal'); skew += 61; await call('GET', '/feed'); assert.equal(S.goalFileCalls, 1);                       // the file: 10 min in memory
  assert.equal(S.calls.filter(c => c.path === '/v1/invoices').length, 0);
});
await test('feed: new donations only, newest first; a name only from the NEW label; old-label names, card names and emails never; website only for Pit Crew', async () => {
  goalReset([
    donation(500, { custom_fields: OLDF('Old Label Person'), customer_details: { name: 'CARD NAME', email: 'donor@example.com' } }),
    donation(100, { custom_fields: NEWF('  Kim   R. ') }),
    donation(1000, { mode: 'subscription', subscription: 'sub_P', custom_fields: NEWF('Pit Shop').concat([{ key: 'yourwebsiteorchannelforthesupporterswall', label: { type: 'custom', custom: 'Your website' }, text: { value: 'pitshop.example.com' } }]) }),
    donation(500, { mode: 'subscription', subscription: 'sub_R', custom_fields: NEWF('Road Rider').concat([{ key: 'yourwebsiteorchannelforthesupporterswall', text: { value: 'https://rider.example' } }]) }),
    donation(300, { mode: 'subscription', subscription: 'sub_D', custom_fields: NEWF('me@mail.com') }),
    donation(1999, { payment_link: null, metadata: { item: 'all' }, custom_fields: NEWF('Checklist Buyer') }),
    donation(700, { created: monthStart() - 5 * 86400 }),                                               // last month: listed, not counted
  ], { month: monthOf(), renewals: { cents: 1000, n: 1 } });
  const r = await call('GET', '/feed');
  assert.equal(r.s, 200); assert.equal(r.h.get('Cache-Control'), 'public, max-age=30'); assert.equal(r.h.get('Access-Control-Allow-Origin'), SITE);
  assert.equal(r.j.month, monthOf()); assert.equal(r.j.count, 6);                                   // 5 new donations this month + 1 renewal from the goal file
  const f = r.j.feed; assert.equal(f.length, 6);
  for (let i = 1; i < f.length; i++) assert.ok(f[i - 1].at >= f[i].at);
  assert.ok(f.every(x => Object.keys(x).every(k => ['amount', 'at', 'kind', 'level', 'name', 'url'].includes(k))));
  const txt = r.text; for (const bad of ['Old Label Person', 'CARD NAME', 'donor@example.com', 'me@mail.com', 'Checklist Buyer', 'rider.example', 'cs_live', 'sub_']) assert.ok(!txt.includes(bad), bad);
  assert.ok(f.some(x => x.name === 'Pit Shop' && x.level === 'pit' && x.url === 'https://pitshop.example.com/'));
  assert.ok(f.some(x => x.name === 'Kim R.' && x.amount === 1 && x.kind === 'once' && x.level === null));
  assert.ok(f.some(x => x.name === 'Road Rider' && x.level === 'road' && !('url' in x)));
  assert.ok(f.some(x => x.name === null && x.level === 'daily'));                                   // an email typed as a name: dropped
  assert.ok(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(f[0].at));
  assert.equal(S.calls.filter(c => c.path === '/v1/invoices').length, 0);
});
await test('feed: cached 60 s, then Stripe again; Stripe down -> the last good feed, else 503; origin checked', async () => {
  goalReset([donation(500)]);
  assert.equal((await call('GET', '/feed')).j.feed.length, 1);
  S.list.unshift(donation(700));
  assert.equal((await call('GET', '/feed')).j.feed.length, 1);
  skew += 61; assert.equal((await call('GET', '/feed')).j.feed.length, 2);
  skew += 61; S.listFail = true; assert.equal((await call('GET', '/feed')).j.feed.length, 2);
  goalReset([donation(500)]); S.listFail = true; assert.equal((await call('GET', '/feed')).s, 503);
  S.listFail = false; assert.equal((await call('GET', '/feed', { origin: 'https://evil.example' })).s, 403);
});
console.log(`\n${pass} tests passed`);

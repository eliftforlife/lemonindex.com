// lemon-store library (11-25; entry = store_worker.js). Paid before-you-buy checklists on lemonindex.com: email-link sign-in, one free
// checklist per email, $7.99 one car checklist (one generation), $19.99 every car and truck checklist (ones added later too; motorcycles,
// planes and dirt bikes are a separate product later). Cloudflare Worker + D1 (DB: accounts, purchases, progress) + KV (CONTENT: the paid
// checklists, uploaded by upload_content.py from the private checklist folder; never in the public repo, docs/ or any site bundle).
// Built from the ew-store Worker (elijahwestbrook-site/worker/store_lib.js): same Stripe signature check, form encoding, D1 counters.
//
// The Worker runs on *.workers.dev, a different site from lemonindex.com (GitHub Pages), so a cookie would be third-party and dropped by
// Safari / Chrome. Sign-in therefore gives a bearer token (like ew-store) that the page keeps in localStorage and sends in Authorization.
// Only its SHA-256 is stored; it expires 7 days after it was issued, is rotated (a fresh token) on use after 1 day, every sign-in chain ends
// after 60 days, and sign-out (or "sign out everywhere") deletes it server-side.
//
//   POST /auth/start  {email, next?, ts?}       -> {sent: true}: emails a single-use sign-in link (15 min). Same answer for every email.
//   POST /auth/verify {t, dev?}                  -> {token, exp, me, claimed}: redeems the link; claims the free checklist named at sign-up.
//   POST /auth/signout {all?}          (Bearer)  -> {ok}: deletes this session (all = every session of this account)
//   GET  /me                           (Bearer)  -> {email, free, freeLeft, all, owned, progress, rotate?}
//   POST /free {gen, dev}              (Bearer)  -> {ok, gen}: the one free checklist (once per email, once per device, soft per-IP limit)
//   POST /checkout {item, gen}         (Bearer)  -> {url}: a Stripe Checkout Session (the live Price ids in wrangler.toml)
//   GET  /content?gen=                 (Bearer)  -> the paid checklist JSON, only if this account owns it (no price tables: those stay here)
//   POST /answer {gen, s}              (Bearer)  -> step 10 "Your answer": the offer engine (engine.js, private) runs HERE, never in the page
//   GET  /progress?gen= | PUT /progress {gen, data} (Bearer)
//   POST /account/delete {confirm}     (Bearer)  -> {ok}: deletes the account, its sessions and progress
//   POST /webhook                      (Stripe, signed) -> the ONLY place a purchase is granted or revoked (paid / async paid / refund / dispute)
//   GET  /goal                         (public)  -> {month: 'YYYY-MM', raised: whole dollars, n}: this month's donations (+ monthly renewals),
//                                                  for the goal box on /support/ and /coming-soon/ (cached 5 min; no D1)
//   GET  /feed                         (public)  -> {month, count, feed: [{amount, at, kind, level, name, url?}]}: the latest donations on
//                                                  /support/ (cached 60 s; no D1; names only from the new shout-out field label)
//
// Secrets (wrangler secret put; never in code or logs): STRIPE_SECRET_KEY (restricted: Checkout Sessions write only), STRIPE_WEBHOOK_SECRET,
// TOKEN_KEY (32+ chars, peppers the hashes), RESEND_KEY, TURNSTILE_SECRET. Vars: wrangler.toml. Local only (.dev.vars): DEV_MODE, DEV_ORIGIN.
import { disposable } from './disposable.js';

export const SITE = 'https://lemonindex.com';
const MIN = 60, HOUR = 3600, DAY = 86400;
export const LINK_TTL = 15 * MIN, SESSION_TTL = 7 * DAY, ROTATE_AFTER = DAY, CHAIN_MAX = 60 * DAY, GRACE = 2 * MIN;
const TOK = /^lss_[A-Za-z0-9_-]{43}$/, LINK = /^lsl_[A-Za-z0-9_-]{43}$/, GEN = /^[a-z0-9]+(?:-[a-z0-9]+){0,6}-g\d{1,2}$/, DEV = /^[A-Za-z0-9_-]{16,64}$/;
const EMAIL = /^[^@\s"<>(),;:\\[\]]{1,64}@[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?)*\.[a-z]{2,24}$/;
const CATS_ALL = new Set(['car']);            // what the $19.99 'all' covers: index entries with cat 'car' (cars, SUVs, vans and pickups)
const MAX_PROGRESS = 16000;

const enc = s => new TextEncoder().encode(s);
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
const b64u = b => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const now = () => Math.floor(Date.now() / 1000);
const rand = (pre, n = 32) => { const r = new Uint8Array(n); crypto.getRandomValues(r); return pre + b64u(r); };
export const sha256 = async s => hex(await crypto.subtle.digest('SHA-256', enc(s)));
async function hmac(key, msg) { const k = await crypto.subtle.importKey('raw', enc(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']); return crypto.subtle.sign('HMAC', k, enc(msg)); }
const pep = async (env, s) => hex(await hmac(env.TOKEN_KEY, s));   // peppered hash: tokens, device ids, IPs, emails in tombstones
export function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0;
}

// Stripe-Signature: "t=<unix>,v1=<hex hmac of `${t}.${raw body}`>[,v1=...]". 5 minute tolerance. (ew-store, unchanged)
export async function verifyStripe(raw, header, secret, at = now(), tolerance = 300) {
  if (!header || !secret) return false;
  let t = ''; const v1 = [];
  for (const part of String(header).split(',')) {
    const i = part.indexOf('='); if (i < 1) continue;
    const k = part.slice(0, i).trim(), v = part.slice(i + 1).trim();
    if (k === 't') t = v; else if (k === 'v1') v1.push(v);
  }
  if (!/^\d{1,12}$/.test(t) || !v1.length || Math.abs(at - Number(t)) > tolerance) return false;
  const want = hex(await hmac(secret, `${t}.${raw}`));
  let ok = false; for (const s of v1) if (safeEqual(want, s)) ok = true;
  return ok;
}

// Two keys (security fix 11-25):
//  ekey = the ACCOUNT. The exact lowercased address, except Gmail, where Google itself delivers dots and +tags to one inbox.
//         On any other domain alice+x@corp.com may be a different person's mailbox, so it must never open alice@corp.com's account.
//  fkey = only for "one free checklist per inbox" and the per-address rate limit. Also drops +tags on the big providers that
//         deliver +tags to the base inbox. A wrong merge here only costs someone a free checklist, never access.
const GMAIL = new Set(['gmail.com', 'googlemail.com']);
const PLUS = new Set(['gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'msn.com', 'icloud.com', 'me.com', 'mac.com',
  'fastmail.com', 'proton.me', 'protonmail.com', 'pm.me', 'zoho.com']);
export function normEmail(raw) {
  const e = String(raw || '').trim().toLowerCase();
  if (e.length > 254 || !EMAIL.test(e)) return null;
  const at = e.lastIndexOf('@'), local = e.slice(0, at);
  let domain = e.slice(at + 1);
  if (!local) return null;
  let ekey = e;
  if (GMAIL.has(domain)) {
    domain = 'gmail.com';
    const g = local.split('+')[0].replace(/\./g, '');
    if (!g) return null;
    ekey = `${g}@gmail.com`;
  }
  let fkey = ekey;
  if (PLUS.has(domain)) { const b = ekey.slice(0, ekey.lastIndexOf('@')).split('+')[0]; if (b) fkey = `${b}@${domain}`; }
  // rkey = only for the per-address sign-in email limit: +tags dropped on EVERY domain, so alice+1@, alice+2@ ... can't flood one inbox
  const rb = ekey.slice(0, ekey.lastIndexOf('@')).split('+')[0];
  const rkey = rb ? `${rb}@${domain}` : ekey;
  return { email: e, ekey, fkey, rkey, domain };
}
const freeKey = (email) => { const n = normEmail(email); return n ? n.fkey : String(email || '').toLowerCase(); };

// ---- dev mode: only from .dev.vars AND only when the Worker itself is reached on localhost (a stray DEV_MODE on workers.dev does nothing)
const devOn = (env, url) => env.DEV_MODE === '1' && ['localhost', '127.0.0.1'].includes(url.hostname);
const origins = (env, url) => devOn(env, url) && env.DEV_ORIGIN ? [SITE, env.DEV_ORIGIN] : [SITE];
const cors = (env, url, o) => ({ 'Access-Control-Allow-Origin': origins(env, url).includes(o) ? o : SITE, 'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization', 'Access-Control-Max-Age': '600', 'Vary': 'Origin' });
const HDR = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store, private', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' };
function json(ctx, body, status = 200) {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), { status, headers: { ...HDR, ...cors(ctx.env, ctx.url, ctx.o) } });
}

class StripeError extends Error { constructor(status, type, code) { super('stripe'); this.status = status; this.type = type; this.code = code; } }
export function form(obj, pre = '', out = []) {                    // {a: {b: [{c: 1}]}} -> a[b][0][c]=1 (Stripe's form encoding)
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null) continue;
    const key = pre ? `${pre}[${k}]` : k;
    if (Array.isArray(v)) v.forEach((x, i) => typeof x === 'object' ? form(x, `${key}[${i}]`, out) : out.push([`${key}[]`, String(x)]));
    else if (typeof v === 'object') form(v, key, out);
    else out.push([key, String(v)]);
  }
  return out;
}
async function stripe(env, method, path, params) {
  const q = params ? new URLSearchParams(form(params)).toString() : '';
  const r = await fetch(`https://api.stripe.com/v1/${path}`, { method,
    headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`, 'Content-Type': 'application/x-www-form-urlencoded' }, body: method === 'GET' ? undefined : q });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new StripeError(r.status, j.error && j.error.type, j.error && j.error.code);
  return j;
}

// ---- rate limits: the Workers Rate Limiting binding for bursts (per 60 s, nothing stored), D1 counters for hour / day windows
async function burst(env, binding, key) {
  const rl = env[binding]; if (!rl || typeof rl.limit !== 'function') return false;
  try { const { success } = await rl.limit({ key }); return !success; } catch { return false; }
}
async function limited(env, key, max, win) {
  const t = now(), b = Math.floor(t / win), k = (await pep(env, `rl|${key}|${win}|${b}`)).slice(0, 32);
  const r = await env.DB.prepare('INSERT INTO hits (k, n, exp) VALUES (?, 1, ?) ON CONFLICT(k) DO UPDATE SET n = n + 1 RETURNING n').bind(k, (b + 1) * win).first();
  return r.n > max;
}
async function sweep(env) {                                         // ~1 in 50 writes: drop expired rows (all indexed on exp)
  if (Math.random() >= 0.02) return;
  const t = now();
  await env.DB.batch([env.DB.prepare('DELETE FROM hits WHERE exp < ?').bind(t), env.DB.prepare('DELETE FROM links WHERE exp < ?').bind(t - DAY),
    env.DB.prepare('DELETE FROM sessions WHERE exp < ?').bind(t)]);
}
const ipOf = req => req.headers.get('CF-Connecting-IP') || 'none';
const bearer = req => { const m = /^Bearer (lss_[A-Za-z0-9_-]{43})$/.exec(req.headers.get('Authorization') || ''); return m ? m[1] : null; };
async function body(req, max = 2000) {
  const len = Number(req.headers.get('Content-Length') || 0); if (len > max) return null;
  const t = await req.text(); if (t.length > max) return null;
  try { const j = JSON.parse(t || '{}'); return j && typeof j === 'object' && !Array.isArray(j) ? j : null; } catch { return null; }
}

// ---- the checklist catalog (KV "index": {gens: {id: {cat, name}}}), cached in this Worker copy: KV is never read per page view
const MEM = new Map();
async function kvGet(env, key, ttl = 300) {
  const c = MEM.get(key), t = Date.now();
  if (c && t - c.at < ttl * 1000) return c.v;
  const v = await env.CONTENT.get(key);
  if (MEM.size > 200) MEM.clear();
  MEM.set(key, { v, at: t });
  return v;
}
export function clearCache() { MEM.clear(); }
// one checklist, parsed once per Worker copy. `pub` is what the page gets: everything but the price tables (the engine's inputs)
async function genDoc(env, gen) {
  const k = 'doc:' + gen, c = MEM.get(k), t = Date.now();
  if (c && t - c.at < 600 * 1000) return c.v;
  const raw = await env.CONTENT.get('gen:' + gen); let v = null;
  if (raw) { try { const doc = JSON.parse(raw); v = { doc, pub: JSON.stringify({ ...doc, money: { fees: (doc.money || {}).fees || null } }) }; } catch { v = null; } }
  if (MEM.size > 200) MEM.clear();
  MEM.set(k, { v, at: t });
  return v;
}
// the offer engine is private (worker/store/engine.js, gitignored, copied from the private checklist folder by build_content.py)
let ENGINE = null;
export function setEngine(fn) { ENGINE = typeof fn === 'function' ? fn : null; }
const ONE = (v, set) => set.includes(v) ? v : null;
const txt = (v, n) => typeof v === 'string' && v.length <= n ? v : null;
const int = (v, lo, hi) => { if (v == null || v === '' || typeof v === 'boolean') return null; const x = Number(v); return Number.isFinite(x) && x >= lo && x <= hi ? Math.round(x) : null; };   // null and '' stay null (Number(null) is 0: a blank tax box must not mean 0% tax)
// the buyer's answers, cleaned: only known fields, only this checklist's check ids, capped sizes
function answerInput(doc, s) {
  if (!s || typeof s !== 'object' || Array.isArray(s)) return null;
  const y = String(int(s.y, 1950, 2100)); if (!doc.ys || !doc.ys[y]) return null;
  const pick = (o, max, keyOk, valOk) => { const r = {}; if (!o || typeof o !== 'object' || Array.isArray(o)) return r; let n = 0;
    for (const [k, v] of Object.entries(o)) { if (n >= max) break; if (keyOk(k) && valOk(v)) { r[k] = v; n++; } } return r; };
  const unkIds = new Set((doc.ys[y].unk || []).map(u => u.id));
  return {
    y, seller: ONE(s.seller, ['private', 'dealer']) || 'private', stype: ONE(s.stype, ['private', 'brand', 'dealer', 'lot', 'nohaggle', 'bhph']),
    trim: txt(s.trim, 60), eng: int(s.eng, 0, 9), body: txt(s.body, 30), tr: ONE(s.tr, ['auto', 'manual']), drive: ONE(s.drive, ['fwd', 'rwd', 'awd', '4wd']),
    cab: txt(s.cab, 30), miles: int(s.miles, 0, 999999), ask: int(s.ask, 0, 9999999), rec: ONE(s.rec, ['full', 'some', 'none']), tax: int(s.tax, 0, 15),
    ans: pick(s.ans, 600, k => Object.prototype.hasOwnProperty.call(doc.checks, k), v => ['ok', 'bad', 'na', 'nh'].includes(v)),
    unk: pick(s.unk, 20, k => unkIds.has(k), v => v === 'ok' || v === 'bad'),
    quote: pick(s.quote, 60, k => Object.prototype.hasOwnProperty.call(doc.checks, k) || (k.startsWith('u:') && unkIds.has(k.slice(2))), v => int(v, 1, 500000) != null),
  };
}
async function catalog(env) { const v = await kvGet(env, 'index'); try { return (v && JSON.parse(v).gens) || {}; } catch { return {}; } }

// ---- sessions
async function session(env, req) {
  const tok = bearer(req); if (!tok) return null;
  const h = await pep(env, 'session:' + tok), t = now();
  const r = await env.DB.prepare('SELECT s.hash, s.uid, s.born, s.created, s.exp, u.email, u.ekey, u.free_gen FROM sessions s JOIN users u ON u.id = s.uid WHERE s.hash = ?').bind(h).first();
  if (!r || r.exp <= t || r.born + CHAIN_MAX <= t) return null;
  return r;
}
async function newSession(env, uid, born) {
  const token = rand('lss_'), t = now(), exp = Math.min(t + SESSION_TTL, born + CHAIN_MAX);
  await env.DB.prepare('INSERT INTO sessions (hash, uid, born, created, exp) VALUES (?, ?, ?, ?, ?)').bind(await pep(env, 'session:' + token), uid, born, t, exp).run();
  return { token, exp };
}
async function rotate(env, s) {                                     // used after a day: a fresh token, the old one lives 2 more minutes
  const t = now();
  if (t - s.created < ROTATE_AFTER || s.exp - t <= GRACE) return null;
  const n = await newSession(env, s.uid, s.born);
  await env.DB.prepare('UPDATE sessions SET exp = MIN(exp, ?) WHERE hash = ?').bind(t + GRACE, s.hash).run();
  return n;
}

// What an account can open. Purchases are written only by the webhook.
async function rights(env, s) {
  const { results } = await env.DB.prepare("SELECT item, gen FROM purchases WHERE uid = ? AND status = 'active'").bind(s.uid).all();
  return { all: results.some(r => r.item === 'all'), owned: [...new Set(results.filter(r => r.item === 'one' && r.gen).map(r => r.gen))], free: s.free_gen || null };
}
const covers = (R, gen, cat) => (R.all && CATS_ALL.has(cat)) || R.owned.includes(gen) || R.free === gen;

async function freeUsed(env, ekey) { return !!(await env.DB.prepare('SELECT 1 FROM free_used WHERE ekh = ?').bind(await pep(env, 'email:' + ekey)).first()); }
// The free checklist: once per email (users.free_gen + a tombstone that outlives a deleted account), once per device, 3 a day per IP.
async function claimFree(env, s, gen, dev, ip) {
  const cat = (await catalog(env))[gen];
  if (!cat || !CATS_ALL.has(cat.cat)) return { error: 'gen', status: 404 };
  if (s.free_gen) return s.free_gen === gen ? { ok: true, gen } : { error: 'used', status: 409 };
  if (await freeUsed(env, freeKey(s.email))) return { error: 'used', status: 409 };
  if (!DEV.test(dev || '')) return { error: 'device', status: 400 };
  const dh = await pep(env, 'dev:' + dev);
  const d = await env.DB.prepare('SELECT uid FROM free_devices WHERE dev = ?').bind(dh).first();
  if (d && d.uid !== s.uid) return { error: 'device-used', status: 409 };
  if (await limited(env, 'free|' + ip, 3, DAY)) return { error: 'busy', status: 429 };
  const t = now(), ekh = await pep(env, 'email:' + freeKey(s.email));
  const res = await env.DB.batch([
    env.DB.prepare('UPDATE users SET free_gen = ?, free_at = ? WHERE id = ? AND free_gen IS NULL').bind(gen, t, s.uid),
    env.DB.prepare('INSERT OR IGNORE INTO free_used (ekh, at) VALUES (?, ?)').bind(ekh, t),
    env.DB.prepare('INSERT OR IGNORE INTO free_devices (dev, uid, at) VALUES (?, ?, ?)').bind(dh, s.uid, t),
  ]);
  const changed = res && res[0] && res[0].meta ? res[0].meta.changes : 1;
  if (!changed) return { error: 'used', status: 409 };                // a second tab claimed a different one first
  s.free_gen = gen;
  return { ok: true, gen };
}

async function me(env, s) {
  const R = await rights(env, s), used = s.free_gen ? true : await freeUsed(env, freeKey(s.email));
  const { results } = await env.DB.prepare('SELECT gen, updated FROM progress WHERE uid = ?').bind(s.uid).all();
  return { email: s.email, free: R.free, freeLeft: !used, all: R.all, owned: R.owned, progress: results.map(r => ({ gen: r.gen, updated: r.updated })) };
}

// ---- email
async function turnstileOk(env, token, ip, url) {
  if (!env.TURNSTILE_SECRET) return env.TURNSTILE_ON !== '1';     // pluggable: off until a secret exists; TURNSTILE_ON = "1" makes it required
  if (typeof token !== 'string' || !token || token.length > 2048) return false;
  const f = new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip });
  const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: f });
  const j = await r.json().catch(() => ({}));
  const hosts = devOn(env, url) ? ['lemonindex.com', 'localhost', '127.0.0.1'] : ['lemonindex.com', 'www.lemonindex.com'];
  return j.success === true && (!j.hostname || hosts.includes(j.hostname));
}
const escH = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export function mailBody(link) {
  const f = 'font:16px/1.5 -apple-system,Segoe UI,Arial,sans-serif;color:#1d1d1f';
  // 11-26 (Elijah): every link is its own email. Gmail threads same-subject mail from one sender, so an old, used link sat on top of the new one.
  // A short random code (not part of the token) makes each subject unique; X-Entity-Ref-ID (sendMail) also stops Gmail threading.
  const code = Array.from(crypto.getRandomValues(new Uint8Array(3)), b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
  return {
    subject: `Your Lemon Index sign-in link (${code})`,
    html: `<p style="${f}">Tap the button to sign in to the Lemon Index. The link works once and expires in 15 minutes.</p>`
      + `<p style="${f}"><a href="${escH(link)}" style="display:inline-block;background:#1d1d1f;color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:600">Sign in</a></p>`
      + `<p style="font:13px/1.5 -apple-system,Segoe UI,Arial,sans-serif;color:#6e6e73">If you didn’t ask for this, ignore this email. Nobody can sign in without the link.</p>`,
    text: `Sign in to the Lemon Index (works once, expires in 15 minutes):\n${link}\n\nIf you didn't ask for this, ignore this email.`,
  };
}
async function sendMail(env, to, m) {
  const r = await fetch('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: `Bearer ${env.RESEND_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: env.MAIL_FROM, to: [to], reply_to: env.REPLY_TO || undefined, subject: m.subject, html: m.html, text: m.text,
      headers: { 'X-Entity-Ref-ID': crypto.randomUUID() } }) });
  if (!r.ok) console.log('signin mail failed', r.status);
  return r.ok;
}

// ---- Stripe Checkout
const PRICES = env => ({ one: { price: env.PRICE_ONE, cents: Number(env.AMOUNT_ONE || 799) }, all: { price: env.PRICE_ALL, cents: Number(env.AMOUNT_ALL || 1999) } });
async function checkout(env, s, item, gen) {
  const P = PRICES(env)[item];
  if (!P || !/^price_[A-Za-z0-9]{8,64}$/.test(P.price || '')) return { error: 'price-not-configured', status: 503 };
  const meta = { site: 'lemon-store', item, gen: gen || '', uid: s.uid };
  const params = { mode: 'payment', line_items: [{ price: P.price, quantity: 1 }], customer_email: s.email, client_reference_id: s.uid,
    metadata: meta, payment_intent_data: { metadata: meta, receipt_email: s.email }, submit_type: 'pay',   // 11-26 (Elijah): Stripe emails a receipt
    success_url: `${SITE}/checklist/${gen}/?paid=1`, cancel_url: `${SITE}/checklist/${gen}/#paywall` };
  const cs = await stripe(env, 'POST', 'checkout/sessions', params);
  return { url: cs.url };
}

// ---- GET /goal and GET /feed: donations (11-25 goal; 11-27 donations v2: the live feed + monthly renewals).
// Donations are Stripe Payment Links on this account (one-time $5 / $10 / $15 / custom, and since 11-27 monthly $3 / $5 / $10 subscriptions),
// so they show up as Checkout Sessions with a payment_link; checklist sales are sessions this Worker creates (metadata.item, no payment_link)
// and never count. A monthly donation's first payment is its session (mode 'subscription'); every later month is a paid invoice
// (billing_reason 'subscription_cycle') of a subscription one of those sessions started.
// /goal -> {month, raised: whole dollars this month (UTC), n: payments}                                    cached 5 min
// /feed -> {month, count: people this month, feed: [{amount, at, kind, level, name, url?}] (newest 20)}    cached 60 s
// Privacy (Elijah 11-27): a name only when the donor typed it into the field whose label was "Name for a shout-out + thank-you wall" (the
// key never changed; the label each session kept decides). Names typed under the old Instagram-only label are never shown. Never the card
// name, the customer name or the email. A website only for Pit Crew ($10/mo) and only next to such a name. Same rules as stripe_feed.py.
// REFUNDS: the key can't see refunds, so a refunded donation still counts here (rare; stripe_goal.py / stripe_feed.py fix the baked copy).
// Caching: caches.default under a fixed key where the Cache API works (custom domains; on *.workers.dev it may do nothing), plus this Worker
// copy's memory. On a Stripe error the last good answer is served (memory, then a 35-day copy in the cache), else 503.
const GOAL_KEY = 'https://lemon-store.cache/goal', GOAL_LAST = 'https://lemon-store.cache/goal-last', GOAL_TTL = 300, GOAL_PAGES = 50;
const FEED_KEY = 'https://lemon-store.cache/feed', FEED_LAST = 'https://lemon-store.cache/feed-last', FEED_TTL = 60, FEED_N = 20, SUB_DAYS = 400;
const NAME_KEY = 'instagramstoryshoutoutnameorhandle', NAME_LABEL = 'name for a shout-out', URL_KEY = 'yourwebsiteorchannelforthesupporterswall';
const MEMO = new Map();                                              // cache key -> {mem: {body, at}, run}: one Stripe pull at a time per Worker copy
export function clearGoal() { MEMO.clear(); }
const edgeCache = () => (typeof caches !== 'undefined' && caches && caches.default) || null;
async function cacheGet(key) { const c = edgeCache(); if (!c) return null; try { const r = await c.match(key); return r ? await r.text() : null; } catch { return null; } }
async function cachePut(key, body, ttl) {
  const c = edgeCache(); if (!c) return;
  try { await c.put(key, new Response(body, { headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${ttl}` } })); } catch {}
}
const monthOf = at => {
  const d = new Date(at);
  return { start: Math.floor(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000), month: `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}` };
};
const isDonation = s => !!(s && s.status === 'complete' && s.payment_status === 'paid' && String(s.currency).toLowerCase() === 'usd' && s.payment_link
  && Number.isInteger(s.amount_total) && s.amount_total > 0);
const idOf2 = x => (x && typeof x === 'object' ? x.id : x) || null;
async function list(env, path, params, pages = GOAL_PAGES) {      // every object of a Stripe list (100 a page, newest first)
  const out = []; let after = null;
  for (let page = 0; page < pages; page++) {
    const q = new URLSearchParams({ limit: '100', ...params });
    if (after) q.set('starting_after', after);
    const j = await stripe(env, 'GET', `${path}?${q.toString()}`);
    const l = Array.isArray(j.data) ? j.data : [];
    out.push(...l);
    if (!j.has_more || !l.length) break;
    after = l[l.length - 1].id;
  }
  return out;
}
const invSub = i => idOf2(i.subscription || (((i.parent || {}).subscription_details) || {}).subscription);
async function renewals(env, subs, since) {                       // paid renewal invoices of the monthly donation subscriptions
  if (!subs.size) return [];                                       // (no monthly donor yet: no invoice call at all)
  const l = await list(env, 'invoices', { status: 'paid', 'created[gte]': String(since) });
  return l.filter(i => i && i.billing_reason === 'subscription_cycle' && String(i.currency).toLowerCase() === 'usd' && Number.isInteger(i.amount_paid)
    && i.amount_paid > 0 && subs.has(invSub(i)) && !(i.created < since));
}
async function donations(env, at, pages = GOAL_PAGES) {           // the last SUB_DAYS of donation sessions + this month's renewals, newest first
  const { start, month } = monthOf(at);
  const ses = (await list(env, 'checkout/sessions', { 'created[gte]': String(start - SUB_DAYS * 86400), status: 'complete' }, pages)).filter(isDonation);
  const bySub = new Map(ses.filter(s => s.subscription).map(s => [idOf2(s.subscription), s]));
  const ren = await renewals(env, new Set(bySub.keys()), start);
  const items = ses.map(s => ({ t: s.created, cents: s.amount_total, kind: s.mode === 'subscription' ? 'monthly' : 'once', who: idOf2(s.subscription) || s.id, s }))
    .concat(ren.map(i => ({ t: i.created, cents: i.amount_paid, kind: 'monthly', who: invSub(i), s: bySub.get(invSub(i)) })))
    .sort((a, b) => b.t - a.t);
  return { start, month, items };
}
export async function goalTotal(env, at = Date.now()) {
  const { start, month, items } = await donations(env, at);
  const mine = items.filter(x => x.t >= start);
  return { month, raised: Math.floor(mine.reduce((a, x) => a + x.cents, 0) / 100), n: mine.length };
}
export function cleanName(v) {
  if (typeof v !== 'string') return null;
  v = v.replace(/\s+/g, ' ').trim().slice(0, 40).trim();
  if (!v || /\S+@\S+\.\w{2,}/.test(v) || v.replace(/\D/g, '').length >= 7) return null;
  return v;
}
export function cleanUrl(v) {
  if (typeof v !== 'string' || !v.trim()) return null;
  v = v.trim(); if (!/^https?:\/\//i.test(v)) v = 'https://' + v;
  try { const u = new URL(v); return /^https?:$/.test(u.protocol) && u.hostname.includes('.') && !u.username && !u.password && v.length <= 200 ? u.href : null; }
  catch { return null; }
}
const field = (s, key) => (s && Array.isArray(s.custom_fields) ? s.custom_fields : []).find(f => f && f.key === key);
export function donorName(s) {                                    // only from the name field with the NEW label
  const f = field(s, NAME_KEY); if (!f) return null;
  const lab = String(((f.label || {}).custom) || '').trim().toLowerCase();
  return lab.startsWith(NAME_LABEL) ? cleanName((f.text || {}).value) : null;
}
const levelOf = d => d >= 10 ? 'pit' : d >= 5 ? 'road' : 'daily';
const iso = t => new Date(t * 1000).toISOString().replace(/\.\d{3}Z$/, 'Z');
export async function feedList(env, at = Date.now()) {
  const { start, month, items } = await donations(env, at, 20);
  const count = new Set(items.filter(x => x.t >= start).map(x => x.who)).size;   // one per monthly subscription, one per one-time checkout
  const feed = items.slice(0, FEED_N).map(x => {
    const level = x.kind === 'monthly' ? levelOf(x.cents / 100) : null, name = donorName(x.s);
    const o = { amount: x.cents % 100 ? x.cents / 100 : Math.floor(x.cents / 100), at: iso(x.t), kind: x.kind, level, name };
    if (level === 'pit' && name) { const f = field(x.s, URL_KEY), u = f && cleanUrl((f.text || {}).value); if (u) o.url = u; }
    return o;
  });
  return { month, count, feed };
}
async function memo(key, last, ttl, fn, ectx) {
  const t = Date.now(); let m = MEMO.get(key); if (!m) MEMO.set(key, m = { mem: null, run: null });
  if (m.mem && t - m.mem.at < ttl * 1000) return m.mem.body;
  const hit = await cacheGet(key);
  if (hit) { m.mem = { body: hit, at: t }; return hit; }
  if (!m.run) m.run = (async () => {
    try {
      const body = JSON.stringify(await fn(t));
      m.mem = { body, at: Date.now() };
      const w = Promise.all([cachePut(key, body, ttl), cachePut(last, body, 35 * 86400)]);
      if (ectx && typeof ectx.waitUntil === 'function') ectx.waitUntil(w); else await w;
      return body;
    } finally { m.run = null; }
  })();
  try { return await m.run; }
  catch (e) {
    console.log(key.split('/').pop() + ': stripe', e instanceof StripeError ? `${e.status} ${e.type || ''} ${e.code || ''}` : (e && e.name) || 'error');
    const retry = t - Math.max(0, ttl - 60) * 1000;                // keep serving the last answer; try Stripe again in a minute
    if (m.mem) { m.mem.at = retry; return m.mem.body; }
    const l = await cacheGet(last);
    if (l) { m.mem = { body: l, at: retry }; return l; }
    return null;
  }
}
const goal = (env, ectx) => memo(GOAL_KEY, GOAL_LAST, GOAL_TTL, t => goalTotal(env, t), ectx);
const feed = (env, ectx) => memo(FEED_KEY, FEED_LAST, FEED_TTL, t => feedList(env, t), ectx);

// ---- routes
async function route(ctx) {
  const { req, env, url } = ctx, p = url.pathname, m = req.method, ip = ipOf(req);
  if (p !== '/auth/signout' && await burst(env, 'RL', 'ip:' + ip)) return json(ctx, { error: 'busy' }, 429);   // signing out always works

  if (m === 'GET' && p === '/goal') {                               // public: no session, no D1
    if (!env.STRIPE_SECRET_KEY) return json(ctx, { error: 'not-configured' }, 503);
    const g = await goal(env, ctx.ectx);
    if (!g) return json(ctx, { error: 'unavailable' }, 503);
    const r = json(ctx, g); r.headers.set('Cache-Control', 'public, max-age=60'); return r;
  }

  if (m === 'GET' && p === '/feed') {                               // public: no session, no D1 (11-27 donations v2)
    if (!env.STRIPE_SECRET_KEY) return json(ctx, { error: 'not-configured' }, 503);
    const f = await feed(env, ctx.ectx);
    if (!f) return json(ctx, { error: 'unavailable' }, 503);
    const r = json(ctx, f); r.headers.set('Cache-Control', 'public, max-age=30'); return r;
  }

  if (m === 'POST' && p === '/auth/start') {
    if (await burst(env, 'RL_AUTH', 'auth:' + ip)) return json(ctx, { error: 'busy' }, 429);
    const b = await body(req); if (!b) return json(ctx, { error: 'bad' }, 400);
    const n = normEmail(b.email); if (!n) return json(ctx, { error: 'email' }, 400);
    if (disposable(n.domain)) return json(ctx, { error: 'disposable' }, 400);
    const next = typeof b.next === 'string' && GEN.test(b.next) ? b.next : null;
    if (env.TURNSTILE_ON === '1' && !env.TURNSTILE_SECRET) return json(ctx, { error: 'not-configured' }, 503);
    if (!(await turnstileOk(env, b.ts, ip, url))) return json(ctx, { error: 'turnstile' }, 403);
    if (await limited(env, 'ai|' + ip, 10, HOUR) || await limited(env, 'ae|' + n.rkey, 3, HOUR)) return json(ctx, { error: 'busy' }, 429);
    const mailOn = env.EMAIL_ON === '1' && env.RESEND_KEY && env.MAIL_FROM;
    if (mailOn && await limited(env, 'mail|day', Number(env.DAILY_CAP || 60), DAY)) return json(ctx, { error: 'busy' }, 429);
    const t = now(), token = rand('lsl_');
    await env.DB.prepare('INSERT INTO links (hash, ekey, email, next, exp, created) VALUES (?, ?, ?, ?, ?, ?)').bind(await pep(env, 'link:' + token), n.ekey, n.email, next, t + LINK_TTL, t).run();
    await sweep(env);
    const link = `${SITE}/account/signin/#t=${token}`;              // a fragment: never sent to a server, never in logs or Referer
    if (mailOn) { await sendMail(env, n.email, mailBody(link)); return json(ctx, { sent: true }); }
    if (devOn(env, url)) return json(ctx, { sent: true, dev_link: (env.DEV_ORIGIN || SITE) + `/account/signin/#t=${token}` });
    return json(ctx, { sent: false, error: 'email-off' }, 503);
  }

  if (m === 'POST' && p === '/auth/verify') {
    if (await limited(env, 'av|' + ip, 30, HOUR)) return json(ctx, { error: 'busy' }, 429);
    const b = await body(req); if (!b || !LINK.test(b.t || '')) return json(ctx, { error: 'bad' }, 400);
    const h = await pep(env, 'link:' + b.t), t = now();
    const L = await env.DB.prepare('UPDATE links SET used_at = ? WHERE hash = ? AND used_at IS NULL AND exp > ? RETURNING ekey, email, next').bind(t, h, t).first();
    if (!L) {
      const x = await env.DB.prepare('SELECT used_at, exp FROM links WHERE hash = ?').bind(h).first();
      return json(ctx, { error: !x ? 'bad' : x.used_at ? 'used' : 'expired' }, 400);
    }
    const u = await env.DB.prepare('INSERT INTO users (id, ekey, email, created, seen) VALUES (?, ?, ?, ?, ?) ON CONFLICT(ekey) DO UPDATE SET seen = excluded.seen RETURNING id, email, free_gen')
      .bind(rand('u_', 16), L.ekey, L.email, t, t).first();
    const ses = await newSession(env, u.id, t);
    const s = { uid: u.id, email: u.email, ekey: L.ekey, free_gen: u.free_gen };   // the account's own stored address, never the link's
    let claimed = null;
    if (L.next && !u.free_gen && typeof b.dev === 'string') { const c = await claimFree(env, s, L.next, b.dev, ip); if (c.ok) claimed = c.gen; }
    return json(ctx, { token: ses.token, exp: ses.exp, next: L.next, claimed, me: await me(env, s) });
  }

  // everything below needs a session
  const s = await session(env, req);
  if (!s) return json(ctx, { error: 'signin' }, 401);

  if (m === 'POST' && p === '/auth/signout') {
    const b = await body(req) || {};
    if (b.all === true) await env.DB.prepare('DELETE FROM sessions WHERE uid = ?').bind(s.uid).run();
    else await env.DB.prepare('DELETE FROM sessions WHERE hash = ?').bind(s.hash).run();
    return json(ctx, { ok: true });
  }
  if (m === 'GET' && p === '/me') {
    const out = await me(env, s), r = await rotate(env, s);
    if (r) out.rotate = r;
    return json(ctx, out);
  }
  if (m === 'POST' && p === '/free') {
    const b = await body(req); if (!b || !GEN.test(b.gen || '')) return json(ctx, { error: 'bad' }, 400);
    const c = await claimFree(env, s, b.gen, b.dev, ip);
    return c.ok ? json(ctx, c) : json(ctx, { error: c.error }, c.status);
  }
  if (m === 'POST' && p === '/checkout') {
    const b = await body(req); if (!b) return json(ctx, { error: 'bad' }, 400);
    const item = b.item, gen = b.gen;
    if (!(item === 'one' || item === 'all') || !GEN.test(gen || '')) return json(ctx, { error: 'item' }, 400);
    const cat = (await catalog(env))[gen];
    if (!cat || !CATS_ALL.has(cat.cat)) return json(ctx, { error: 'gen' }, 404);
    if (await limited(env, 'co|' + ip, 10, HOUR) || await limited(env, 'cou|' + s.uid, 10, HOUR)) return json(ctx, { error: 'busy' }, 429);
    const R = await rights(env, s);
    if (R.all || (item === 'one' && covers(R, gen, cat.cat))) return json(ctx, { error: 'owned' }, 409);
    const c = await checkout(env, s, item, gen);
    return c.url ? json(ctx, c) : json(ctx, { error: c.error }, c.status);
  }
  if (m === 'GET' && p === '/content') {
    const gen = url.searchParams.get('gen') || '';
    if (!GEN.test(gen)) return json(ctx, { error: 'bad' }, 400);
    if (await burst(env, 'RL_CONTENT', 'c:' + s.uid) || await limited(env, 'ct|' + s.uid, 200, DAY)) return json(ctx, { error: 'busy' }, 429);
    const cat = (await catalog(env))[gen];
    if (!cat) return json(ctx, { error: 'gen' }, 404);
    if (!covers(await rights(env, s), gen, cat.cat)) return json(ctx, { error: 'not-owned' }, 403);
    const g = await genDoc(env, gen);
    if (!g) return json(ctx, { error: 'gen' }, 404);
    return json(ctx, g.pub);
  }
  if (m === 'POST' && p === '/answer') {
    const b = await body(req, 24000); if (!b || !GEN.test(b.gen || '')) return json(ctx, { error: 'bad' }, 400);
    if (await burst(env, 'RL_CONTENT', 'a:' + s.uid) || await limited(env, 'an|' + s.uid, 400, HOUR)) return json(ctx, { error: 'busy' }, 429);
    const cat = (await catalog(env))[b.gen];
    if (!cat) return json(ctx, { error: 'gen' }, 404);
    if (!covers(await rights(env, s), b.gen, cat.cat)) return json(ctx, { error: 'not-owned' }, 403);
    if (!ENGINE) return json(ctx, { error: 'engine-off' }, 503);
    const g = await genDoc(env, b.gen); if (!g) return json(ctx, { error: 'gen' }, 404);
    const S = answerInput(g.doc, b.s); if (!S) return json(ctx, { error: 'bad' }, 400);
    const r = ENGINE(g.doc, S);
    return r && !r.error ? json(ctx, r) : json(ctx, { error: 'bad' }, 400);
  }
  if (p === '/progress' && (m === 'GET' || m === 'PUT')) {
    if (m === 'GET') {
      const gen = url.searchParams.get('gen') || ''; if (!GEN.test(gen)) return json(ctx, { error: 'bad' }, 400);
      const r = await env.DB.prepare('SELECT data, updated FROM progress WHERE uid = ? AND gen = ?').bind(s.uid, gen).first();
      return json(ctx, { gen, data: r ? JSON.parse(r.data) : null, updated: r ? r.updated : null });
    }
    const b = await body(req, MAX_PROGRESS + 200);
    if (!b || !GEN.test(b.gen || '') || !b.data || typeof b.data !== 'object' || Array.isArray(b.data)) return json(ctx, { error: 'bad' }, 400);
    const data = JSON.stringify(b.data); if (data.length > MAX_PROGRESS) return json(ctx, { error: 'too-big' }, 413);
    const cat = (await catalog(env))[b.gen];
    if (!cat || !covers(await rights(env, s), b.gen, cat.cat)) return json(ctx, { error: 'not-owned' }, 403);
    if (await limited(env, 'pg|' + s.uid, 600, HOUR)) return json(ctx, { error: 'busy' }, 429);
    const t = now();
    await env.DB.prepare('INSERT INTO progress (uid, gen, data, updated) VALUES (?, ?, ?, ?) ON CONFLICT(uid, gen) DO UPDATE SET data = excluded.data, updated = excluded.updated').bind(s.uid, b.gen, data, t).run();
    return json(ctx, { ok: true, updated: t });
  }
  if (m === 'POST' && p === '/account/delete') {
    const b = await body(req);
    if (!b || typeof b.confirm !== 'string' || b.confirm.trim().toLowerCase() !== s.email) return json(ctx, { error: 'confirm' }, 400);
    await env.DB.batch([env.DB.prepare('DELETE FROM sessions WHERE uid = ?').bind(s.uid), env.DB.prepare('DELETE FROM progress WHERE uid = ?').bind(s.uid),
      env.DB.prepare('DELETE FROM free_devices WHERE uid = ?').bind(s.uid), env.DB.prepare('DELETE FROM users WHERE id = ?').bind(s.uid)]);
    return json(ctx, { ok: true });            // purchases keep only Stripe ids (for refunds and disputes); the free tombstone is a peppered hash
  }
  return json(ctx, { error: 'not-found' }, 404);
}

// ---- webhook: verified, idempotent per event id, the only writer of purchases
const idOf = x => typeof x === 'string' ? x : (x && x.id) || null;
function grantStmts(env, o, at) {
  const meta = o.metadata || {}, P = PRICES(env)[meta.item];
  if (meta.site !== 'lemon-store' || !P || !/^cs_(test|live)_[A-Za-z0-9]{10,200}$/.test(o.id || '')) return [];
  if (o.mode !== 'payment' || o.payment_status !== 'paid' || String(o.currency).toLowerCase() !== 'usd' || o.amount_total !== P.cents) {
    if (o.payment_status === 'paid') console.log('webhook: paid session that does not match the price', meta.item);
    return [];
  }
  const uid = String(meta.uid || o.client_reference_id || ''); if (!/^u_[A-Za-z0-9_-]{10,40}$/.test(uid)) return [];
  const gen = meta.item === 'one' ? String(meta.gen || '') : null; if (meta.item === 'one' && !GEN.test(gen)) return [];
  const pi = idOf(o.payment_intent), t = now();
  return [env.DB.prepare(`INSERT OR IGNORE INTO purchases (session_id, uid, item, gen, payment_intent, amount, currency, status, created, updated, ev_at)
      VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'usd', COALESCE((SELECT status FROM pi_state WHERE pi = ?5), 'active'), ?7, ?7, ?8)`).bind(o.id, uid, meta.item, gen, pi, o.amount_total, t, at)];
}
function stateStmts(env, pi, status, at, onlyFrom) {
  if (!pi) return [];
  const t = now(), w = onlyFrom ? ` AND status = '${onlyFrom}'` : '';
  return [
    env.DB.prepare(`INSERT INTO pi_state (pi, status, ev_at) VALUES (?1, ?2, ?3) ON CONFLICT(pi) DO UPDATE SET status = excluded.status, ev_at = excluded.ev_at
      WHERE excluded.ev_at >= pi_state.ev_at${onlyFrom ? ` AND pi_state.status = '${onlyFrom}'` : ''}`).bind(pi, status, at),
    env.DB.prepare(`UPDATE purchases SET status = ?1, updated = ?2, ev_at = ?3 WHERE payment_intent = ?4 AND (ev_at IS NULL OR ev_at <= ?3)${w}`).bind(status, t, at, pi),
  ];
}
async function webhook(req, env) {
  const raw = await req.text();
  if (raw.length > 512 * 1024 || !(await verifyStripe(raw, req.headers.get('Stripe-Signature'), env.STRIPE_WEBHOOK_SECRET))) return new Response('bad signature', { status: 400 });
  let ev; try { ev = JSON.parse(raw); } catch { return new Response('bad json', { status: 400 }); }
  if (!ev || typeof ev.id !== 'string' || !/^evt_[A-Za-z0-9_]{6,80}$/.test(ev.id)) return new Response('bad event', { status: 400 });
  const ok = (x = {}) => new Response(JSON.stringify({ received: true, ...x }), { headers: { 'Content-Type': 'application/json' } });
  if (await env.DB.prepare('SELECT 1 FROM events WHERE id = ?').bind(ev.id).first()) return ok({ duplicate: true });
  const o = (ev.data && ev.data.object) || {}, at = Number(ev.created) || now();
  let st = [];
  if (ev.type === 'checkout.session.completed' || ev.type === 'checkout.session.async_payment_succeeded') st = grantStmts(env, o, at);
  else if (ev.type === 'charge.refunded') { if (o.refunded === true) st = stateStmts(env, idOf(o.payment_intent), 'refunded', at); }   // full refunds only
  else if (ev.type === 'charge.dispute.created') st = stateStmts(env, idOf(o.payment_intent), 'disputed', at);
  else if (ev.type === 'charge.dispute.closed') {
    if (o.status === 'won' || o.status === 'warning_closed') st = stateStmts(env, idOf(o.payment_intent), 'active', at, 'disputed');   // back on only if the dispute took it
    else st = stateStmts(env, idOf(o.payment_intent), 'disputed', at);                                                                  // lost: stays off
  }
  st.push(env.DB.prepare('INSERT INTO events (id, type, at) VALUES (?, ?, ?)').bind(ev.id, String(ev.type || '').slice(0, 80), now()));
  try { await env.DB.batch(st); }
  catch (e) { if (/UNIQUE|constraint/i.test(String(e && e.message))) return ok({ duplicate: true }); throw e; }   // the same event, delivered twice at once
  clearCache();
  return ok();
}

export const handler = {
  async fetch(req, env, ectx) {
    const url = new URL(req.url), o = req.headers.get('Origin') || '', ctx = { req, env, url, o, ectx };
    try {
      if (url.pathname === '/webhook' && req.method === 'POST') return await webhook(req, env);   // server to server: no Origin, signature instead
      if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, url, o) });
      if (!origins(env, url).includes(o)) return json(ctx, { error: 'origin' }, 403);
      if (!env.TOKEN_KEY || env.TOKEN_KEY.length < 32 || !env.DB || !env.CONTENT) return json(ctx, { error: 'not-configured' }, 503);
      if ((url.pathname === '/checkout') && !env.STRIPE_SECRET_KEY) return json(ctx, { error: 'not-configured' }, 503);
      return await route(ctx);
    } catch (e) {
      console.log('error', url.pathname, e instanceof StripeError ? `stripe ${e.status} ${e.type || ''} ${e.code || ''}` : (e && e.name) || 'error');
      if (url.pathname === '/webhook') return new Response('retry', { status: 500 });
      return json(ctx, { error: 'server' }, e instanceof StripeError && e.status < 500 ? 400 : 502);
    }
  },
};

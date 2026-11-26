-- lemon-store D1 schema (11-25). Apply: npx wrangler d1 execute lemon-store --remote --file schema.sql   (--local for wrangler dev)
-- Stored per person: the email (to send sign-in links and receipts), purchases (Stripe ids only, no card data) and checklist progress.
-- No names, no addresses, no IP addresses (rate-limit keys are SHA-256 hashes that expire within a day).
-- users.ekey = the account key: the exact lowercased email (Gmail: dots and +tags removed, since Google sends those to one inbox).
-- Other domains are never merged: alice+x@corp.com can be someone else's mailbox. The free-checklist limit uses a looser key (free_used).
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, ekey TEXT NOT NULL UNIQUE, email TEXT NOT NULL, free_gen TEXT, free_at INTEGER,
  created INTEGER NOT NULL, seen INTEGER NOT NULL);
-- sign-in links: SHA-256 of the raw token only; single use (used_at), 15-minute expiry. next = the free checklist asked for at sign-up.
CREATE TABLE IF NOT EXISTS links (hash TEXT PRIMARY KEY, ekey TEXT NOT NULL, email TEXT NOT NULL, next TEXT, exp INTEGER NOT NULL,
  used_at INTEGER, created INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS links_exp ON links (exp);
-- sessions: SHA-256 of the bearer token. born = first sign-in of this chain (absolute cap), exp = this token's own expiry.
-- Rotation writes a new row and gives the old one a short grace exp (two tabs refreshing at once both keep working).
CREATE TABLE IF NOT EXISTS sessions (hash TEXT PRIMARY KEY, uid TEXT NOT NULL, born INTEGER NOT NULL, created INTEGER NOT NULL, exp INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS sessions_uid ON sessions (uid);
CREATE INDEX IF NOT EXISTS sessions_exp ON sessions (exp);
-- purchases: one row per paid Checkout Session (the idempotency key). item = 'one' (gen = that checklist) or 'all' (every car and truck
-- checklist, including ones added later). status: active | refunded | disputed. Only the webhook writes here.
CREATE TABLE IF NOT EXISTS purchases (session_id TEXT PRIMARY KEY, uid TEXT NOT NULL, item TEXT NOT NULL, gen TEXT, payment_intent TEXT,
  amount INTEGER NOT NULL, currency TEXT NOT NULL, status TEXT NOT NULL, created INTEGER NOT NULL, updated INTEGER NOT NULL, ev_at INTEGER);
CREATE INDEX IF NOT EXISTS purchases_uid ON purchases (uid);
CREATE INDEX IF NOT EXISTS purchases_pi ON purchases (payment_intent);
-- refund / dispute state per payment intent, kept even when that event arrives before checkout.session.completed (out-of-order delivery)
CREATE TABLE IF NOT EXISTS pi_state (pi TEXT PRIMARY KEY, status TEXT NOT NULL, ev_at INTEGER NOT NULL);
-- Stripe event ids already applied (webhook replay / retry = no-op)
CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, type TEXT NOT NULL, at INTEGER NOT NULL);
-- one free checklist per device (a random id the browser keeps; hashed). Soft limit: some leakage is accepted (Elijah 11-25).
CREATE TABLE IF NOT EXISTS free_devices (dev TEXT PRIMARY KEY, uid TEXT NOT NULL, at INTEGER NOT NULL);
-- the free checklist was used by this inbox: an HMAC (peppered hash) of the free key (ekey with +tags dropped on big providers), kept when the account is deleted so
-- delete + sign up again doesn't give a second free checklist. Not reversible without the Worker's TOKEN_KEY.
CREATE TABLE IF NOT EXISTS free_used (ekh TEXT PRIMARY KEY, at INTEGER NOT NULL);
-- checklist answers, one row per person and checklist (JSON, size-capped by the Worker)
CREATE TABLE IF NOT EXISTS progress (uid TEXT NOT NULL, gen TEXT NOT NULL, data TEXT NOT NULL, updated INTEGER NOT NULL, PRIMARY KEY (uid, gen));
-- rate-limit counters for windows longer than the Rate Limiting binding's 60 s (k = hash of key + window)
CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER NOT NULL, exp INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS hits_exp ON hits (exp);

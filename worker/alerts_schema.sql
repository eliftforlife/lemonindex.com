-- lemon-alerts D1 schema (11-14, growth plan 4a). Apply: npx.cmd --yes wrangler d1 execute lemon-alerts --remote --file alerts_schema.sql -c alerts.toml
CREATE TABLE IF NOT EXISTS subs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  y INTEGER NOT NULL,                 -- model year
  car TEXT NOT NULL,                  -- JSON [[MAKE, MODEL], ...]: NHTSA names, max 2 (never a VIN)
  fid TEXT,                           -- Lemon page id when we cover the model
  status TEXT NOT NULL DEFAULT 'pending',   -- pending | active (unsubscribing deletes the rows)
  ctok TEXT,                          -- confirm token, cleared once confirmed
  utok TEXT NOT NULL,                 -- unsubscribe token (one per address)
  created INTEGER NOT NULL, conf_sent INTEGER, conf_n INTEGER NOT NULL DEFAULT 0, confirmed INTEGER,
  seen TEXT,                          -- JSON list of NHTSA campaign numbers already known/sent
  checked INTEGER,                    -- last NHTSA check (ms)
  UNIQUE (email, y, car));
CREATE INDEX IF NOT EXISTS subs_ctok ON subs (ctok);
CREATE INDEX IF NOT EXISTS subs_utok ON subs (utok);
CREATE INDEX IF NOT EXISTS subs_due ON subs (status, checked);
CREATE INDEX IF NOT EXISTS subs_email ON subs (email);
CREATE TABLE IF NOT EXISTS hits (ih TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY (ih, day));   -- salted daily IP hash, deleted after 2 days
CREATE TABLE IF NOT EXISTS sends (day TEXT PRIMARY KEY, n INTEGER NOT NULL);   -- emails sent per day (daily cap)

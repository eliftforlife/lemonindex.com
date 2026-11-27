# stripe_feed.py (11-27, donations v2): the "Latest donations" feed, this month's donor count and the supporters wall on /support/,
# from Stripe -> data/support_feed.json. Build-time, like stripe_goal.py (same READ-only key, same donation rule: paid Checkout Sessions
# from a donate Payment Link; checklist sales have no payment_link and never count), plus paid renewal invoices of monthly donations.
#
# Privacy (Elijah 11-27): a donor's name shows ONLY when they typed it into the field whose label they saw was "Name for a shout-out +
# thank-you wall" (NAME_LABEL; the key stays SHOUT_KEY, so the label each session kept decides). Names typed under the old label
# ("Instagram story shout-out? Name or handle") agreed to an Instagram story only and are never shown: those donors are "Someone".
# Never the card name, the customer name or the email. Same rule as the lemon-store Worker's GET /feed.
#
# Usage: py stripe_feed.py          -> writes the file if anything changed, prints counts only
#        py stripe_feed.py --dry    -> prints counts, writes nothing
import json, re, sys, datetime, pathlib, urllib.parse
from stripe_goal import _key, donation_sessions, renewals

OUT = pathlib.Path(__file__).with_name('data') / 'support_feed.json'
SHOUT_KEY = 'instagramstoryshoutoutnameorhandle'   # the name field's key on every donate link (its label changed 11-27, the key didn't)
NAME_LABEL = 'name for a shout-out'   # the new label starts with this (case-insensitive): "Name for a shout-out + thank-you wall"
URL_KEY = 'yourwebsiteorchannelforthesupporterswall'   # Pit Crew link only: "Your website or channel (for the supporters wall)"
LEVELS = ((10, 'pit'), (5, 'road'), (3, 'daily'))   # monthly $ -> wall group (names live in assets/support.js MONTHLY_NAMES)
FEED_N, ACTIVE_DAYS = 20, 40   # newest donations in the feed; a monthly donor stays on the wall while a payment is under 40 days old
_EMAIL = re.compile(r'\S+@\S+\.\w{2,}')


def _field(c, key):
    if not key: return None
    for f in c.get('custom_fields') or []:
        if f.get('key') == key: return ((f.get('text') or {}).get('value') or '').strip() or None
    return None


def _name(c):
    """the donor's shout-out name, only if the field they filled in carried the NEW label (else None = 'Someone')"""
    for f in c.get('custom_fields') or []:
        lab = str(((f.get('label') or {}).get('custom')) or '').strip().lower()
        if f.get('key') == SHOUT_KEY and lab.startswith(NAME_LABEL): return clean_name(((f.get('text') or {}).get('value') or '').strip())
    return None


def clean_name(v):
    """the shout-out text as typed, trimmed; None for blank, an email address or a phone number"""
    if not v: return None
    v = re.sub(r'\s+', ' ', v).strip()[:40]
    if not v or _EMAIL.search(v) or len(re.sub(r'\D', '', v)) >= 7: return None
    return v


def clean_url(v):
    """an http(s) link with a real host, else None"""
    if not v: return None
    v = v.strip()
    if not re.match(r'^https?://', v, re.I): v = 'https://' + v
    try: u = urllib.parse.urlsplit(v)
    except ValueError: return None
    if u.scheme.lower() not in ('http', 'https') or '.' not in (u.hostname or '') or len(v) > 200 or u.username or u.password: return None
    return v


def level(dollars):
    return next((g for amt, g in LEVELS if dollars >= amt), 'daily')


def _iso(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def build(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc).timestamp()
    key = _key()
    ses = donation_sessions(key)
    by_sub = {c['subscription']: c for c in ses if c.get('subscription')}
    ren = renewals(key, set(by_sub), 0)
    items = []   # (created, cents, kind, sub id or None, session)
    for c in ses: items.append((c['created'], c.get('amount_total') or 0, 'monthly' if c.get('mode') == 'subscription' else 'once', c.get('subscription'), c))
    new = sorted(items, key=lambda x: -x[0])   # 11-27: the feed = new donations only (a renewal isn't one); same as the Worker's /feed
    for i in ren: s = i.get('subscription') or (((i.get('parent') or {}).get('subscription_details') or {}).get('subscription')); items.append((i['created'], i.get('amount_paid') or 0, 'monthly', s, by_sub[s]))
    items.sort(key=lambda x: -x[0])

    feed = [{'amount': cents / 100 if cents % 100 else cents // 100, 'at': _iso(t), 'kind': kind,
             'level': level(cents / 100) if kind == 'monthly' else None, 'name': _name(c)}
            for t, cents, kind, _, c in new[:FEED_N]]
    # people this month: one per monthly subscription, one per one-time checkout (no emails or names are read for this)
    count = len({sub or c['id'] for t, _, _, sub, c in items if t >= start})

    wall = {'pit': [], 'road': [], 'daily': [], 'once': []}
    anon = dict.fromkeys(wall, 0)
    seen = {g: set() for g in wall}
    last = {}   # monthly sub -> its newest payment (cents, time)
    for t, cents, kind, sub, c in items:
        if kind == 'monthly' and sub not in last: last[sub] = (cents, t)
    for sub, (cents, t) in last.items():
        if now.timestamp() - t > ACTIVE_DAYS * 86400: continue
        c, g = by_sub[sub], level(cents / 100)
        n = _name(c)
        if not n: anon[g] += 1; continue
        if n.lower() in seen[g]: continue
        seen[g].add(n.lower())
        e = {'name': n}
        if g == 'pit' and clean_url(_field(c, URL_KEY)): e['url'] = clean_url(_field(c, URL_KEY))
        wall[g].append(e)
    for t, cents, kind, sub, c in items:
        if kind != 'once': continue
        n = _name(c)
        if not n: anon['once'] += 1; continue
        if n.lower() in seen['once']: continue
        seen['once'].add(n.lower()); wall['once'].append({'name': n})
    return {'month': now.strftime('%Y-%m'), 'count': count, 'feed': feed, 'wall': wall, 'anon': anon}


if __name__ == '__main__':
    d = build()
    print(f"{d['month']}: {d['count']} donor(s) this month, {len(d['feed'])} in the feed, wall "
          + ', '.join(f'{g} {len(v)} named + {d["anon"][g]} unnamed' for g, v in d['wall'].items()))
    if '--dry' in sys.argv: sys.exit(0)
    old = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
    new = json.dumps(d, ensure_ascii=False, indent=1) + '\n'
    if old == new: print('unchanged'); sys.exit(0)
    OUT.write_text(new, encoding='utf-8'); print('written', OUT)

# stripe_goal.py (11-24): this month's Lemon donations from Stripe -> data/support_goal.json (the goal box on /support/ and /coming-soon/).
# Key: Elijah's restricted READ-only key for the Lemon Index Stripe account, in C:/Users/elift/.stripe.txt (never print it).
# Counts paid Payment Link (donation) Checkout Sessions created this month (UTC), USD only, plus (11-27 donations v2) the paid renewal
# invoices of monthly donations (subscriptions started from a donate Payment Link). Prints only totals.
# Usage: py stripe_goal.py            -> writes the file if the number changed, prints the total
#        py stripe_goal.py --dry      -> prints, writes nothing
import json, sys, datetime, urllib.request, urllib.parse, pathlib

KEY_FILE = pathlib.Path.home() / '.stripe.txt'
OUT = pathlib.Path(__file__).with_name('data') / 'support_goal.json'


def _key():
    k = KEY_FILE.read_text(encoding='utf-8-sig').strip()
    if not k.startswith(('rk_live_', 'sk_live_')): sys.exit('stripe key file does not hold a live key')
    return k


def _get(path, params, key):
    req = urllib.request.Request('https://api.stripe.com/v1/' + path + '?' + urllib.parse.urlencode(params),
                                 headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)


def _all(path, params, key):
    """every object of a Stripe list endpoint (follows has_more)"""
    after = None
    while True:
        p = dict(params, limit=100)
        if after: p['starting_after'] = after
        page = _get(path, p, key)
        yield from page['data']
        if not page.get('has_more') or not page['data']: return
        after = page['data'][-1]['id']


def donation_sessions(key, since=0):
    # 11-25: donations only = paid Checkout Sessions from a Payment Link (the donate links). Checklist sales (sessions the store creates,
    # no payment_link) never count. Same rule as the lemon-store Worker's GET /goal, which keeps the box live between builds.
    # A monthly donation's FIRST payment is its session (mode 'subscription'); later months are renewal invoices (renewals()).
    p = {'status': 'complete'}
    if since: p['created[gte]'] = int(since)
    return [c for c in _all('checkout/sessions', p, key)
            if c.get('payment_link') and c.get('payment_status') == 'paid' and c.get('currency') == 'usd']


def _inv_sub(i):
    """the subscription id of an invoice (old API versions: invoice.subscription; newer: invoice.parent.subscription_details)"""
    s = i.get('subscription') or (((i.get('parent') or {}).get('subscription_details') or {}).get('subscription'))
    return s.get('id') if isinstance(s, dict) else s


def renewals(key, subs, since=0):
    """paid renewal invoices (billing_reason subscription_cycle) of the monthly donation subscriptions in `subs`"""
    if not subs: return []
    p = {'status': 'paid'}
    if since: p['created[gte]'] = int(since)
    return [i for i in _all('invoices', p, key)
            if i.get('billing_reason') == 'subscription_cycle' and i.get('currency') == 'usd' and _inv_sub(i) in subs]


def month_total(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
    key = _key()
    month = donation_sessions(key, start.timestamp())
    cents, n = sum(c.get('amount_total') or 0 for c in month), len(month)
    subs = {c['subscription'] for c in donation_sessions(key) if c.get('subscription')}   # every monthly donation ever started
    ren = renewals(key, subs, start.timestamp())
    rc = sum(i.get('amount_paid') or 0 for i in ren)
    cents += rc; n += len(ren)
    return start.strftime('%Y-%m'), cents // 100, n, {'cents': rc, 'n': len(ren)}


if __name__ == '__main__':
    month, dollars, n, ren = month_total()
    print(f'{month}: ${dollars} from {n} donation(s), of which {ren["n"]} monthly renewal(s)')
    if '--dry' in sys.argv: sys.exit(0)
    # 11-27: 'renewals' = this month's monthly-renewal invoices on their own. The build serves this file at /data/support_goal.json, and the
    # lemon-store Worker (whose key reads Checkout Sessions only, never invoices) adds them to its live session total for /goal.
    new = {'month': month, 'raised': dollars, 'renewals': ren}
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    if all(old.get(k) == new[k] for k in new): print('unchanged'); sys.exit(0)
    if old.get('month') and old.get('month') != month: new['last'] = {'month': old['month'], 'raised': old.get('raised', 0)}
    OUT.write_text(json.dumps(new) + '\n', encoding='utf-8'); print('written', OUT)

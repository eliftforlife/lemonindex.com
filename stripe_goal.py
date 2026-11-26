# stripe_goal.py (11-24): this month's Lemon donations from Stripe -> data/support_goal.json (the goal box on /support/ and /coming-soon/).
# Key: Elijah's restricted READ-only key for the Lemon Index Stripe account, in C:/Users/elift/.stripe.txt (never print it).
# Counts paid Payment Link (donation) Checkout Sessions created this month (UTC), USD only. Prints only totals.
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


def month_total(now=None):
    # 11-25: donations only = paid Checkout Sessions from a Payment Link (the donate links). Checklist sales (sessions the store creates,
    # no payment_link) never count. Same rule as the lemon-store Worker's GET /goal, which keeps the box live between builds.
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
    key, cents, n, after = _key(), 0, 0, None
    while True:
        p = {'limit': 100, 'created[gte]': int(start.timestamp()), 'status': 'complete'}
        if after: p['starting_after'] = after
        page = _get('checkout/sessions', p, key)
        for c in page['data']:
            if c.get('payment_link') and c.get('payment_status') == 'paid' and c.get('currency') == 'usd':
                cents += c.get('amount_total') or 0; n += 1
        if not page.get('has_more'): break
        after = page['data'][-1]['id']
    return start.strftime('%Y-%m'), cents // 100, n


if __name__ == '__main__':
    month, dollars, n = month_total()
    print(f'{month}: ${dollars} from {n} donation(s)')
    if '--dry' in sys.argv: sys.exit(0)
    new = {'month': month, 'raised': dollars}
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    if old.get('month') == new['month'] and old.get('raised') == new['raised']: print('unchanged'); sys.exit(0)
    if old.get('month') and old.get('month') != month: new['last'] = {'month': old['month'], 'raised': old.get('raised', 0)}
    OUT.write_text(json.dumps(new) + '\n', encoding='utf-8'); print('written', OUT)

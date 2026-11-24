# 11-24 (Elijah: "push live and build price box"): "What it's worth" on every car year page (#price-guide, Overview tab) and a
# year-by-year table on supercar pages. Private-seller and dealer price ranges for 4 mileage brackets, from data/price_est.json
# (data_price_est.py). AI estimates, labelled as such on the box: never listings, sales or an appraisal. A bracket far from the
# year's typical miles shows "Rare" instead of a number. Years with measured listing prices (data/prices.json, the F-150 "What to
# pay" table) keep that table and skip this box.
import html, json, os, re
E = lambda s: html.escape(str(s), quote=True)
HERE = os.path.dirname(os.path.abspath(__file__))
_D = None
def _data():
    global _D
    if _D is None:
        p = os.path.join(HERE, 'data', 'price_est.json')
        _D = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'m': {}, 'brackets': []}
        q = os.path.join(HERE, 'data', 'prices.json')
        _D['measured'] = json.load(open(q, encoding='utf-8')) if os.path.exists(q) else {}
    return _D
LABELS = ['0–50K', '50–100K', '100–150K', '150K+']
LO = [0, 50_000, 100_000, 150_000]
CSS = '<link rel="stylesheet" href="/assets/pricebox.css?v=3">'
def _m(v): return f'${v:,}'
def _rng(a, b): return f'{_m(a)}–{b:,}'
def _mi(v): return f'{round(v / 1000):,}K' if v >= 1000 else f'{v:,}'
def _cur(mi): return max(i for i, lo in enumerate(LO) if mi >= lo)
NOTE = ('Lemon Index estimates (AI, {d}), not listings, sales records or an appraisal. Average condition, clean title, automatic, '
        'each range at the middle of its mileage band (150K+ at about 175K). Dealer = what a lot typically asks; a private sale is usually lower. '
        'Check local listings and get an inspection before you buy.')

def year_block(fid, y, car):
    D = _data(); M = D['m'].get(fid); r = M and M['y'].get(str(y))
    if not r: return ''
    if str(y) in (D['measured'].get(fid) or {}): return ''
    mi, bk = r[:2]; cur = _cur(mi)
    if not any(bk): return ''
    rows = ''
    for i, b in enumerate(bk):
        tag = ' <small class="pg-t">most common</small>' if i == cur else ''
        if b: rows += f'<tr{" class=pg-cur" if i == cur else ""}><td>{LABELS[i]} mi{tag}</td><td class="num" data-l="Private seller">{_rng(b[0], b[1])}</td><td class="num" data-l="Dealer">{_rng(b[2], b[3])}</td></tr>'
        else: rows += f'<tr class="pg-rare"><td>{LABELS[i]} mi</td><td colspan="2">Rare for a {y}</td></tr>'
    mk = f' Priced for: {E(M["mk"])}.' if M.get('mk') else ''
    return (f'<section class="yc ypg" id="price-guide">{CSS}<h2>What a {y} {E(car)} is worth</h2>'
            f'<p class="yf-s">Fair price by mileage, in U.S. dollars. Most {y}s have about {_mi(mi)} miles.{mk}</p>'
            f'<div class="tw"><table class="price pgt pgy"><thead><tr><th>Miles</th><th>Private seller</th><th>Dealer</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="yc-cap">{NOTE.format(d=E(D.get("date", "")))}</p></section>')

SNOTE = ('Lemon Index estimates (AI, {d}), not listings, auction results or an appraisal. Average condition, clean title, the version named above, '
         'at the mileage band that holds the typical miles for each year. Dealer = what a lot typically asks. Rare specs, special editions and very low miles sell higher; '
         'get a pre-purchase inspection from a specialist before you buy.')
def super_block(slug, car):
    D = _data(); M = D['m'].get(slug)
    if not M or not M['y']: return ''
    ys = sorted(M['y'], key=int, reverse=True)
    def row(y):
        mi, bk = M['y'][y][:2]; i = _cur(mi); b = bk[i] or next((x for x in bk if x), None)
        if not b: return ''
        return f'<tr><td>{y}</td><td class="num">{_mi(mi)}</td><td class="num">{_rng(b[0], b[1])}</td><td class="num">{_rng(b[2], b[3])}</td></tr>'
    head = '<thead><tr><th>Year</th><th>Typical miles</th><th>Private seller</th><th>Dealer</th></tr></thead>'
    top = ''.join(row(y) for y in ys[:6]); rest = ''.join(row(y) for y in ys[6:])
    if not top: return ''
    mk = f' Priced for: {E(M["mk"])}.' if M.get('mk') else ''
    more = f'<details class="pg-more"><summary>Older years ({len(ys) - 6})</summary><div class="tw"><table class="price pgt">{head}<tbody>{rest}</tbody></table></div></details>' if rest else ''
    return (f'<section class="yc ypg" id="price-guide">{CSS}<h2>What a {E(car)} is worth</h2>'
            f'<p class="yf-s">Fair price at each year&#39;s typical mileage, in U.S. dollars. Exotics lose value faster per mile than normal cars, so low miles matter more.{mk}</p>'
            f'<div class="tw"><table class="price pgt">{head}<tbody>{top}</tbody></table></div>{more}'
            f'<p class="yc-cap">{SNOTE.format(d=E(D.get("date", "")))}</p></section>')

# ---- 11-24 (Elijah: "a button on all car pages: find a car for your budget, the top 10 most reliable for price ranges like 5k 10k"):
# budget ranges for /budget/ (budget_pages.py), placed by the private-seller price at the year's typical miles (the middle of its range)
BUDGETS = [('5k', 0, 5000, 'Under $5,000'), ('10k', 5000, 10000, '$5,000 to $10,000'), ('15k', 10000, 15000, '$10,000 to $15,000'),
           ('20k', 15000, 20000, '$15,000 to $20,000'), ('25k', 20000, 25000, '$20,000 to $25,000'), ('30k', 25000, 30000, '$25,000 to $30,000'),
           ('40k', 30000, 40000, '$30,000 to $40,000'), ('50k', 40000, 50000, '$40,000 to $50,000')]
def at_price(fid, y):
    """[private lo, hi, dealer lo, hi] at the year's typical miles, or None"""
    M = _data()['m'].get(fid); r = M and M['y'].get(str(y))
    return r[2] if r and len(r) > 2 and r[2] else None
def budget_of(fid, y):
    a = at_price(fid, y)
    if not a: return None
    mid = (a[0] + a[1]) / 2
    return next((k for k, lo, hi, _ in BUDGETS if lo <= mid < hi), None)
def budget_href(fid=None, y=None):
    k = budget_of(fid, y) if fid and y else None
    return '/budget/' + (f'#b={k}' if k else '')

# 'Find a car for your budget' row, first in the Overview list of every /cars/<model>/ and /cars/<model>/<year>/ page (build.py page(), after the date hash)
_BUD_CAR = re.compile(r'^/cars/([^/]+(?:/[a-z]+)?)/(?:(\d{4})/)?$')
_BUD_G1 = re.compile(r'<div class="cpl-grp cpl-g1[^"]*">')
_BUD_ROW = ('<section class="cpl-sec cpl-pan" id="p-budget"><div class="cpl"><a class="cpl-a sb-go" href="{h}"><svg aria-hidden="true" class="cpl-i" focusable="false" height="24" width="24">'
            '<use href="/assets/ic.svg?v=1#tag"></use></svg><span><b>Find a car for your budget</b></span><svg aria-hidden="true" class="cpl-ar" fill="none" height="18" stroke="currentColor" '
            'stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" viewbox="0 0 24 24" width="18"><path d="m9 6 6 6-6 6"></path></svg></a></div></section>')
def budget_hook(path, doc):
    m = _BUD_CAR.match(path)
    if not m or 'id="p-budget"' in doc: return doc
    g = _BUD_G1.search(doc)
    if not g: return doc
    fid, y = m.group(1), m.group(2)
    return doc[:g.end()] + _BUD_ROW.format(h=budget_href(fid, int(y)) if y else '/budget/') + doc[g.end():]


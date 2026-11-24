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
def at_price(fid, y):
    """[private lo, hi, dealer lo, hi] at the year's typical miles, or None"""
    M = _data()['m'].get(fid); r = M and M['y'].get(str(y))
    return r[2] if r and len(r) > 2 and r[2] else None
# 11-24 v2: /budget/ tiers (budget_pages.py, data_picks.py): (set, page key, picks.json key, label, lo, hi)
BUD_TIERS_ALL = [('reg', 'u5', 'u5', 'Under $5,000', 0, 5000), ('reg', '5to10', '5-10', '$5,000 to $10,000', 5000, 10000),
                 ('reg', '10to20', '10-20', '$10,000 to $20,000', 10000, 20000), ('reg', '20up', '20+', 'Over $20,000', 20000, 10 ** 9),
                 ('super', 'u100', 'u100', 'Under $100,000', 0, 100000), ('super', '100to200', '100-200', '$100,000 to $200,000', 100000, 200000),
                 ('super', '200up', '200+', 'Over $200,000', 200000, 10 ** 9)]
_SEG = None
def seg_of(fid):
    """car / suv / truck / minivan (family_rates.csv + cars_new.json), or None"""
    global _SEG
    if _SEG is None:
        import csv
        idf = lambda n: n.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')
        _SEG = {idf(r['family']): r['segment'] for r in csv.DictReader(open(os.path.join(HERE, 'data', 'family_rates.csv'), encoding='utf-8'))}
        q = os.path.join(HERE, 'data', 'cars_new.json')
        if os.path.exists(q): _SEG.update({c['id']: c['segment'] for c in json.load(open(q, encoding='utf-8'))})
    s = _SEG.get(fid); return s if s in ('car', 'suv', 'truck', 'minivan') else None
def budget_of(fid, y):
    a = at_price(fid, y)
    if not a: return None
    mid = (a[0] + a[1]) / 2
    return next((k for st, k, _, _, lo, hi in BUD_TIERS_ALL if st == 'reg' and lo <= mid < hi), None)
def budget_href(fid=None, y=None):
    """the car's own type and the budget its price (private, typical miles) falls in"""
    t = seg_of(fid) if fid else None; k = budget_of(fid, y) if fid and y else None
    h = '&'.join(x for x in ((f't={t}' if t else ''), (f'b={k}' if k else '')) if x)
    return '/budget/' + (f'#{h}' if h else '')

# 'Find a car for your budget' row, first in the Overview list of every /cars/<model>/ and /cars/<model>/<year>/ page (build.py page(), after the date hash)
_BUD_CAR = re.compile(r'^/cars/([^/]+(?:/[a-z]+)?)/(?:(\d{4})/)?$')
_BUD_G1 = re.compile(r'<div class="cpl-grp cpl-g1[^"]*">')
# 11-24 Eli pass: search icon (the tag icon is already the 'What it's worth' row); the <style> makes the link sit flat in the inset group like the
# rows under it (no underline, no own box: the shared .cpl-ins rules only reach a .cpl-a that is a direct child, and this one is wrapped in a section)
_BUD_ROW = ('<section class="cpl-sec cpl-pan" id="p-budget"><style>#p-budget .cpl>.cpl-a,#p-budget .cpl>.cpl-a:hover{{text-decoration:none;color:inherit;box-shadow:none;'
            'border-radius:18px 18px 0 0}}#p-budget .cpl>.cpl-a{{background:transparent}}#p-budget .cpl>.cpl-a:hover{{background:#ebebee}}'
            '.cpl-ins>#p-budget:only-child .cpl>.cpl-a{{border-radius:18px}}</style><div class="cpl"><a class="cpl-a sb-go" href="{h}"><svg aria-hidden="true" class="cpl-i" focusable="false" height="24" width="24">'
            '<use href="/assets/ic.svg?v=1#search"></use></svg><span><b>Find a car for your budget</b></span><svg aria-hidden="true" class="cpl-ar" fill="none" height="18" stroke="currentColor" '
            'stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" viewbox="0 0 24 24" width="18"><path d="m9 6 6 6-6 6"></path></svg></a></div></section>')
def budget_hook(path, doc):
    m = _BUD_CAR.match(path)
    if not m or 'id="p-budget"' in doc: return doc
    g = _BUD_G1.search(doc)
    if not g: return doc
    fid, y = m.group(1), m.group(2)
    return doc[:g.end()] + _BUD_ROW.format(h=budget_href(fid, int(y) if y else None)) + doc[g.end():]


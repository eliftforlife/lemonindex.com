# 11-23 repair cost estimates (money plan m33, Elijah approved showing them): the repair-estimate dataset (data/repair_est.json, made by
# data_repair_est.py from 3 Lemon Index/data/repair_est/scored/) on the year pages (#estimates, in the Repairs & costs box) and on the
# /repair-cost/ pages. Every number comes from that file:
#   - estimate = labor hours x the visitor's shop rate (default $140/h, an input on the page, remembered in localStorage) + parts
#   - "What owners paid" (the middle half of this generation's owner bills) is the main number only where the scoring says owner bills lead
#   - the confidence band (High / Medium / Low) shows with every number; Hidden rows show no number, only "Not enough data yet"
# Plus the "What did you pay?" box: repair + price (+ optional ZIP and shop type), posted to the lemon-survey Worker (POST /price), stored for
# review and later folded into the owner prices (owner_prices.py's reader source). Nothing shows publicly from it until then.
# CSS assets/rest.css, JS assets/rest.js (rate input + the form), both linked from the blocks themselves.
import html, json, os, re
E = lambda s: html.escape(str(s), quote=True)
HERE = os.path.dirname(os.path.abspath(__file__))
_D = None
def _data():
    global _D
    if _D is None:
        p = os.path.join(HERE, 'data', 'repair_est.json')
        _D = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'gens': {}, 'names': {}, 'rate': 140}
        _D['by'] = {}
        for gid, g in _D['gens'].items(): _D['by'].setdefault(g['m'], []).append(gid)
        # how often owners name a bill for each repair across every car (data/repair_pages.json): the order repairs are listed in
        rp = os.path.join(HERE, 'data', 'repair_pages.json'); cnt = {}
        if os.path.exists(rp):
            for pt in json.load(open(rp, encoding='utf-8')).get('pts', []): cnt[pt[0]] = cnt.get(pt[0], 0) + 1
        _D['pop'] = cnt
    return _D
ALIAS = {'kia-k5': 'kia-optima'}   # the 2021+ Optima pages became the K5 (k5_split.py); the dataset keeps them under the Optima's generation
RATE = lambda: _data()['rate']
TS_KEY = '0x4AAAAAAFyhvovKDo2j0cLa'   # the site's public Turnstile key (same as the opinions box)
CSS = '<link rel="stylesheet" href="/assets/rest.css?v=2">'
JS = '<script src="/assets/rest.js?v=2" defer></script>'
BAND = {'H': ('High', 'hi'), 'M': ('Medium', 'md'), 'L': ('Low', 'lo')}
LABEL = ('Estimate: labor hours × your shop rate + parts. Owner prices are mostly dealer bills from NHTSA complaints.')
HOW = ('<p>Labor hours and parts prices are AI estimates (written by Claude for each generation, for an independent shop with quality aftermarket parts), '
       'checked against the repair bills owners reported. Confidence says how well owner bills back the number: <b>High</b> = many owner bills that agree, '
       '<b>Medium</b> = some owner bills, <b>Low</b> = an estimate with few or no owner bills behind it. With too little to go on we show no number. '
       'Where this generation&#39;s owner bills are strong (or far from the estimate), what owners paid is the main number: those are mostly dealer bills '
       'that owners named in complaints to NHTSA, so they often run higher than an independent shop. Not a quote: prices vary by shop, region, parts and miles.</p>')

def money(v):
    v = max(0, v); v = round(v / 10) * 10 if v < 1000 else round(v / 50) * 50
    return f'${v:,.0f}'
def rng(a, b): return money(a) if money(a) == money(b) else f'{money(a)}–{money(b)}'

def gen_for(fid, y):
    D = _data(); fid = ALIAS.get(fid, fid)
    for gid in D['by'].get(fid, []):
        g = D['gens'][gid]
        if g['y'][0] <= y <= g['y'][1]: return gid
    return None
def gens_of(fid):
    D = _data(); return sorted(D['by'].get(ALIAS.get(fid, fid), []), key=lambda gid: D['gens'][gid]['y'][0])
def gen_label(gid):
    g = _data()['gens'][gid]; a, b = g['sy']; return f'{a}–{b}' if a != b else str(a)

def _span(rows, rate):
    """the estimate range across the given rows (engines): lowest low to highest high"""
    return min(r[1] * rate + r[3] for r in rows), max(r[2] * rate + r[4] for r in rows)
def _rows(gid, slug, head=None):
    """[<li>] for one repair of one generation. Several engines = one line whose estimate covers all of them (the owner bills are counted
    per generation, not per engine). head: escaped html that names the line (default: the repair name)"""
    D = _data(); g = D['gens'][gid]; rows = g['r'].get(slug) or []
    if not rows: return []
    head = head if head is not None else E(D['names'].get(slug, slug))
    ok = [r for r in rows if r[5] != 'X']
    if not ok:
        return [f'<li class="rst-x"><span class="rst-n">{head}</span><span class="rst-v"><a href="#paid" class="rst-ask">Not enough data yet — tell us what you paid</a></span></li>']
    if len(ok) < len(rows) or len(rows) > 1:
        eng = [E(g['e'].get(r[0]) or 'other engines') for r in ok]
        head += f'<small>{len(ok)} engines: {", ".join(eng)}</small>' if len(ok) > 1 else f'<small>{eng[0]}</small>'
    w = min(ok, key=lambda r: r[6])   # the band shown is the weakest one in the range
    bl, bc = BAND[w[5]]
    chip = f'<i class="rst-b rst-{bc}" title="Confidence {w[6]}/100">{bl}</i>'
    data = ' data-v="' + '|'.join(f'{r[1]},{r[2]},{r[3]},{r[4]}' for r in ok) + '"'
    lo, hi = _span(ok, RATE()); t = f'<span class="rst-n">{head}</span>'
    o = next((r for r in ok if r[7] == 'o' and r[8]), None)
    if o:
        return [f'<li class="rst-o"{data}>{t}<span class="rst-v"><b>{rng(o[10], o[11])}</b>{chip}'
                f'<small>What owners paid (middle half of {o[8]} bills, mostly dealers) · estimate at your rate <em class="rst-e">{rng(lo, hi)}</em></small></span></li>']
    return [f'<li{data}>{t}<span class="rst-v"><b class="rst-e">{rng(lo, hi)}</b>{chip}</span></li>']

def rate_input(uid):
    return (f'<div class="rst-rate"><label for="rst-r-{uid}">Your shop rate</label><span class="rst-in">$<input id="rst-r-{uid}" class="rst-ri" type="number" inputmode="numeric" '
            f'min="40" max="400" step="5" value="{RATE()}" aria-describedby="rst-l-{uid}">/hour</span></div>')
def legend(uid):
    return (f'<p class="rst-l" id="rst-l-{uid}">{LABEL}</p>')

def price_box(fid, car, y=None, years=(), slugs=(), preset=None):
    """'What did you pay?' (collapsed until tapped): repair + price, optional year / ZIP / shop type, posted to the Worker"""
    D = _data(); names = D['names']
    opts = ''.join(f'<option value="{E(s)}"{" selected" if s == preset else ""}>{E(names[s])}</option>'
                   for s in sorted(slugs or names, key=lambda s: names.get(s, s)) if s in names)
    yopt = ('<option value="">Model year</option>' + ''.join(f'<option value="{v}"{" selected" if v == y else ""}>{v}</option>' for v in sorted(years, reverse=True))) if years else ''
    return (f'<div class="rst-paid" id="paid" data-fid="{E(fid)}" data-car="{E(car)}" data-ts="{TS_KEY}">'
            f'<button class="rst-open" type="button" aria-expanded="false"><b>What did you pay?</b><span>Tell us your repair bill. It makes these numbers better.</span></button>'
            f'<form class="rst-f" hidden novalidate>'
            f'<label>Repair<select name="repair" required><option value="">Choose the repair</option>{opts}</select></label>'
            f'<label>What you paid (parts + labor, USD)<span class="rst-in">$<input name="usd" type="number" inputmode="numeric" min="20" max="30000" step="1" required></span></label>'
            + (f'<label>Model year<select name="year">{yopt}</select></label>' if yopt else '')
            + '<label>Where<select name="shop"><option value="">Shop type (optional)</option><option value="dealer">Dealer</option><option value="independent">Independent shop</option>'
              '<option value="chain">Chain shop</option><option value="other">Other</option></select></label>'
              '<label>ZIP code (optional)<input name="zip" type="text" inputmode="numeric" maxlength="5" pattern="[0-9]{5}" autocomplete="postal-code"></label>'
              '<input class="rst-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><div class="rst-ts"></div>'
              '<p class="rst-rules">Only the repair, the price and the first 3 digits of your ZIP are kept. No name or email. One per repair per car.</p>'
              '<button class="btn" type="submit">Send</button></form><p class="rst-msg" hidden aria-live="polite"></p></div>')

def year_block(fid, y, car):
    """#estimates for a year page: the 8 repairs owners name most, then every other one in a fold"""
    D = _data(); gid = gen_for(fid, y)
    if not gid: return ''
    g = D['gens'][gid]; pop = D['pop']
    slugs = sorted(g['r'], key=lambda s: (-pop.get(s, 0), D['names'].get(s, s)))
    shown = [s for s in slugs if any(r[5] != 'X' for r in g['r'][s])]
    if len(shown) < 3: return ''
    top = shown[:8]; rest = [s for s in slugs if s not in top]
    li = lambda ss: ''.join(h for s in ss for h in _rows(gid, s))
    uid = re.sub(r'[^a-z0-9]', '', gid)
    return (f'<section class="yc yfx rst" id="estimates">{CSS}<h2>What repairs should cost</h2>'
            f'<p class="yf-s">Estimates for the {E(gen_label(gid))} {E(car)}, for one repair at an independent shop.</p>'
            + rate_input(uid) + f'<ul class="rst-list">{li(top)}</ul>'
            + (f'<details class="rst-more"><summary>All {len(slugs)} repairs</summary><ul class="rst-list">{li(rest)}</ul></details>' if rest else '')
            + legend(uid) + f'<details class="rst-how"><summary>How these estimates work</summary>{HOW}</details>'
            + price_box(fid, car, y, [v for v in range(g['sy'][0], g['sy'][1] + 1)], slugs) + JS + '</section>')

def model_repair_block(slug, fid, car, ylink=None):
    """/repair-cost/<repair>/<model>/: the estimate for each generation of this model. The h2 sits outside the section so the
    page's compact boxes (cp5_hook.py groups by top-level h2) give it a box of its own"""
    D = _data(); gids = [gid for gid in gens_of(fid) if D['gens'][gid]['r'].get(slug)]
    if not gids: return ''
    uid = re.sub(r'[^a-z0-9]', '', slug + fid)
    lis = ''.join(h for gid in reversed(gids) for h in _rows(gid, slug, E(gen_label(gid))))
    if 'data-v' not in lis: return ''
    return (f'<h2 id="estimates">Estimated cost by model year</h2><section class="rst">{CSS}'
            f'<p class="yf-s">One {E(D["names"].get(slug, slug).lower())} job on each {E(car)} generation, at an independent shop.</p>'
            + rate_input(uid) + f'<ul class="rst-list rst-gens">{lis}</ul>' + legend(uid)
            + f'<details class="rst-how"><summary>How these estimates work</summary>{HOW}</details>'
            + price_box(fid, car, None, [v for gid in gids for v in range(D['gens'][gid]['sy'][0], D['gens'][gid]['sy'][1] + 1)], [slug], slug) + JS + '</section>')

def hub_block(slug, name_of, url_of, limit=20):
    """/repair-cost/<repair>/: the estimate on the most popular generations (queue order: sales, searches and Search Console views)"""
    D = _data(); out = []
    for gid, g in sorted(D['gens'].items(), key=lambda t: t[1].get('i', 9999)):
        rows = g['r'].get(slug) or []
        if not rows or g['m'] not in name_of or all(r[5] == 'X' for r in rows): continue
        out.append(gid)
        if len(out) >= limit: break
    if len(out) < 5: return ''
    uid = re.sub(r'[^a-z0-9]', '', slug)
    def head(gid):
        g = D['gens'][gid]; nm = E(f'{gen_label(gid)} {name_of[g["m"]]}'); u = url_of(g['m'], g['sy'][1])
        return f'<a href="{E(u)}">{nm}</a>' if u else nm
    lis = ''.join(h for gid in out for h in _rows(gid, slug, head(gid)))
    return (f'<h2 id="estimates">Estimated cost on popular cars</h2><section class="rst">{CSS}'
            f'<p class="yf-s">One {E(D["names"].get(slug, slug).lower())} job at an independent shop, on {len(out)} of the most popular car generations we cover.</p>'
            + rate_input(uid) + f'<ul class="rst-list rst-gens">{lis}</ul>' + legend(uid)
            + f'<details class="rst-how"><summary>How these estimates work</summary>{HOW}</details>' + JS + '</section>')

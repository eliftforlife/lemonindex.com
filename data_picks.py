# 11-24 (Elijah: "make a best under 5k 5 car list, a best 5-10k list, a best over 10k list ... 15 private party then 15 dealer, so 30
# per car group like suv, truck, sedan; performance and supercar get their own money ranges; backed by YouTube score, Lemon score and price;
# by generation, like 2007-2009, so they can hunt for it in their area; these get the checklists first").
# Data only (no pages): data/picks.json + "3 Lemon Index/Best for the price picks.md" for review.
#   Run: py -X utf8 data_picks.py
# A pick is a run of consecutive model years inside one generation where every year is scored, average or better (Lemon Index <= 100,
# 15K+ sold) and its price at typical miles (middle of the AI estimate) fits the tier. Score = 60% reliability (100 - Lemon Index of the run,
# sold-weighted) + 40% YouTube buyer score (yt_scores.json, 33-68 scaled to 0-100) + up to 6 points for a longer run (easier to find).
# Each model appears once per list (its best run). Supercars: no NHTSA score, so YouTube + price only, one pick per model.
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'data')
SITE = r'C:\Users\elift\Code\lemonindex-site'
OUTMD = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\Best for the price picks.md'
sys.path.insert(0, HERE); import year_slider as YSL   # generation of every model year (ai_year_images + ai_gen_images)

J = lambda p: json.load(open(p, encoding='utf-8'))
YEARS = J(os.path.join(D, 'years.json')) + J(os.path.join(D, 'years_new.json'))
SEG = {r['family']: r['segment'] for r in csv.DictReader(open(os.path.join(D, 'family_rates.csv'), encoding='utf-8'))}
SEG.update({c['name']: c['segment'] for c in J(os.path.join(D, 'cars_new.json'))})
PRICE = J(os.path.join(D, 'price_est.json'))['m']
YT = J(os.path.join(D, 'yt_scores.json'))
SKIP = {'chevrolet-express', 'gmc-savana', 'ford-e-series', 'ford-transit', 'ford-transit-connect', 'mercedes-benz-sprinter', 'ram-promaster',
        'ram-promaster-city', 'nissan-nv', 'nissan-nv200'}   # work vans: fleet-sold, complaints per car run unrealistically low
MIN_SOLD = 15000
GROUPS = [('car', 'Cars (sedans, hatchbacks, coupes)'), ('suv', 'SUVs'), ('truck', 'Trucks'), ('minivan', 'Minivans')]
TIERS = [('u5', 'Under $5,000', 0, 5000), ('5-10', '$5,000 to $10,000', 5000, 10000), ('10-20', '$10,000 to $20,000', 10000, 20000), ('20+', 'Over $20,000', 20000, 10 ** 9)]
TOP = 5
TWINS = [('chevrolet-silverado', 'gmc-sierra'), ('chevrolet-s-10', 'gmc-sonoma'), ('chevrolet-tahoe', 'gmc-yukon'), ('chevrolet-suburban', 'gmc-yukon-xl'),
         ('chevrolet-colorado', 'gmc-canyon'), ('dodge-grand-caravan', 'chrysler-town-and-country'), ('ford-escape', 'mazda-tribute')]
NAME = {f['id']: f['name'] for f in YEARS}


def mid(lo, hi): return (lo + hi) / 2
def ytn(s): return max(0, min(100, (s - 33) / 35 * 100))


def year_rows(f):
    """scored, priced years: {y: dict(li, sold, gen, p, d, mi, yt)}"""
    out = {}; P = (PRICE.get(f['id']) or {}).get('y', {}); G = YSL.AIY.get(f['id']) or {}; Y = YT.get(f['id']) or {}
    for v in f['years']:
        y = v['y']; li = v.get('li')
        ok = li is not None and ((y >= 2010 and not v.get('early')) or v.get('n', 0) >= 20)
        if not ok or v.get('early') or v.get('low') or (v.get('sold') or 0) < MIN_SOLD: continue
        r = P.get(str(y)); g = (G.get(str(y)) or {}).get('gen')
        if not r or len(r) < 3 or not r[2] or not g: continue
        a = r[2]; t = Y.get(str(y)) or {}
        out[y] = dict(li=li, sold=v['sold'], gen=g, p=mid(a[0], a[1]), d=mid(a[2], a[3]), a=a, mi=r[0], yt=t.get('score'))
    return out


def runs(rows, key, lo, hi):
    """maximal runs of consecutive years, same generation, li <= 100, price (key) in [lo, hi)"""
    ys = sorted(y for y, r in rows.items() if r['li'] <= 100 and lo <= r[key] < hi)
    cur = []
    for y in ys:
        if cur and (y != cur[-1] + 1 or rows[y]['gen'] != rows[cur[-1]]['gen']): yield cur; cur = []
        cur.append(y)
    if cur: yield cur


def score_run(f, rows, ys):
    R = [rows[y] for y in ys]; sold = sum(r['sold'] for r in R)
    li = sum(r['li'] * r['sold'] for r in R) / sold
    yts = [r['yt'] for r in R if r['yt'] is not None]
    myt = [d['score'] for d in (YT.get(f['id']) or {}).values() if isinstance(d, dict) and d.get('score') is not None]
    yt = sum(yts) / len(yts) if yts else (sum(myt) / len(myt) if myt else None)
    s = 0.6 * (100 - li) + 0.4 * (ytn(yt) if yt is not None else 50) + min(6, 2 * (len(ys) - 1))
    return dict(id=f['id'], name=f['name'], y0=ys[0], y1=ys[-1], gen=R[0]['gen'], li=round(li), yt=round(yt) if yt is not None else None,
                yt_src='years' if yts else ('model' if yt is not None else 'none'), sold=sold, score=round(s, 1),
                p=[min(r['a'][0] for r in R), max(r['a'][1] for r in R)], d=[min(r['a'][2] for r in R), max(r['a'][3] for r in R)],
                mi=[min(r['mi'] for r in R), max(r['mi'] for r in R)])


def regular():
    out = {}
    for g, _ in GROUPS:
        fams = [f for f in YEARS if SEG.get(f['name']) == g and f['id'] not in SKIP]
        rowsby = {f['id']: year_rows(f) for f in fams}
        for key, kn in (('p', 'private'), ('d', 'dealer')):
            for tk, tl, lo, hi in TIERS:
                best = {}
                for f in fams:
                    for ys in runs(rowsby[f['id']], key, lo, hi):
                        c = score_run(f, rowsby[f['id']], ys)
                        if c['sold'] < 40000: continue   # too few on the road to hunt for
                        if f['id'] not in best or c['score'] > best[f['id']]['score']: best[f['id']] = c
                for a, b in TWINS:   # badge twins (same vehicle): keep the better one, name the other
                    if a in best and b in best:
                        keep, drop = (a, b) if best[a]['score'] >= best[b]['score'] else (b, a)
                        best[keep]['twin'] = NAME[drop]; del best[drop]
                out[f'{g}|{kn}|{tk}'] = sorted(best.values(), key=lambda c: -c['score'])[:TOP]
    return out


def supercars():
    S = J(os.path.join(SITE, 'data', 'super_yt.json')); out = []
    for k, ys in S.items():
        slug = k[6:]; P = (PRICE.get(slug) or {}).get('y', {})
        rows = [(int(y), d['score'], P.get(y)) for y, d in ys.items() if isinstance(d, dict) and d.get('score') is not None]
        rows = [(y, s, r) for y, s, r in rows if r and len(r) > 2 and r[2]]
        if not rows: continue
        out.append((slug, rows))
    return out


def super_lists(tiers):
    res = {}
    for key, kn in ((0, 'private'), (2, 'dealer')):
        for tk, tl, lo, hi in tiers:
            best = []
            for slug, rows in supercars():
                R = [(y, s, r) for y, s, r in rows if lo <= mid(r[2][key], r[2][key + 1]) < hi]
                if not R: continue
                R.sort(); yt = sum(s for _, s, _ in R) / len(R)
                best.append(dict(id=slug, y0=R[0][0], y1=R[-1][0], yt=round(yt), score=round(ytn(yt), 1),
                                 p=[min(r[2][0] for *_, r in R), max(r[2][1] for *_, r in R)], d=[min(r[2][2] for *_, r in R), max(r[2][3] for *_, r in R)]))
            res[f'super|{kn}|{tk}'] = sorted(best, key=lambda c: -c['score'])[:TOP]
    return res


SUPER_TIERS = [('u100', 'Under $100,000', 0, 100000), ('100-200', '$100,000 to $200,000', 100000, 200000), ('200+', 'Over $200,000', 200000, 10 ** 9)]


def money(a): return f'${a[0]:,}–{a[1]:,}'


def yrs(c): return str(c['y0']) if c['y0'] == c['y1'] else f"{c['y0']}–{c['y1']}"


if __name__ == '__main__':
    L = regular(); L.update(super_lists(SUPER_TIERS))
    SN = {s['name']: s for s in J(os.path.join(SITE, 'data', 'supercars.json'))}
    json.dump({'date': '2026-11-24', 'lists': L}, open(os.path.join(D, 'picks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    gens = {}
    for k, cs in L.items():
        for c in cs: gens.setdefault((c['id'], c.get('gen') or 'all', c['y0'] if k.startswith('super') else c.get('gen')), set()).add(k)
    SL = {re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-'): n for n in SN}
    def mis(c): a, b = round(c['mi'][0] / 1000), round(c['mi'][1] / 1000); return f'{a}K' if a == b else f'{a}–{b}K'
    md = ['# Best for the price: picks for review (11-24)', '',
          'Per group: 5 best picks under $5K, $5–10K, $10–20K and over $20K, once by private-seller price and once by dealer price (40 per group). '
          'A pick is a run of years in one generation, all scored average or better on the Lemon Index (100 = average car, lower = fewer complaints). '
          'Score = 60% reliability + 40% YouTube buyer score + a small bonus for a longer run. Prices are our AI estimates at the typical miles for those years (November 2026).', '']
    for g, gl in GROUPS:
        md += [f'## {gl}', '']
        for kn in ('private', 'dealer'):
            for tk, tl, *_ in TIERS:
                cs = L[f'{g}|{kn}|{tk}']
                md += [f'**{tl} ({kn} price)**', '', '| # | Pick | Generation | Lemon Index | YouTube | Private | Dealer | Typical miles |', '|---|---|---|---|---|---|---|---|']
                md += [f"| {i} | {yrs(c)} {c['name']}{' (same as ' + c['twin'] + ')' if c.get('twin') else ''} | {c['gen']} | {c['li']} | {c['yt'] if c['yt'] is not None else '–'}{'*' if c['yt_src'] == 'model' else ''} | {money(c['p'])} | {money(c['d'])} | {mis(c)} |"
                       for i, c in enumerate(cs, 1)] or ['| – | none fit | | | | | | |']
                md += ['']
    md += ['## Supercars (no complaint data: YouTube buyer score + price only)', '',
           'Years are the run that fits the price, not split by generation yet (some models span two generations, e.g. the 911 Turbo/GT3 997 and 991).', '']
    for kn in ('private', 'dealer'):
        for tk, tl, *_ in SUPER_TIERS:
            cs = L[f'super|{kn}|{tk}']
            md += [f'**{tl} ({kn} price)**', '', '| # | Pick | YouTube | Private | Dealer |', '|---|---|---|---|---|']
            md += [f"| {i} | {yrs(c)} {SL.get(c['id'], c['id'])} | {c['yt']} | {money(c['p'])} | {money(c['d'])} |" for i, c in enumerate(cs, 1)] or ['| – | none fit | | | |']
            md += ['']
    md += ['## Performance cars', '', 'Not ranked yet: only 30 of 183 have prices and 2 have YouTube scores (their pulls are queued last). Needs a price run for the other 153.', '',
           '\\* YouTube score of the whole model (no videos scored for those exact years).', '']
    ug = {(c['id'], c.get('gen') or f"{c['y0']}") for cs in L.values() for c in cs}
    md.insert(4, f'**{len(ug)} distinct generations across all lists** = the checklist build list.\n')
    open(OUTMD, 'w', encoding='utf-8').write('\n'.join(md))
    print(len(L), 'lists;', len(ug), 'distinct generations ->', OUTMD)

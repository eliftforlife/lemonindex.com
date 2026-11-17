# 11-17 F-150 split (visitor request + data fix, REQUESTED CARS BRIEF 11-15): the F-150 page (/cars/ford-f-series/) counted the whole F-Series
# family (families.py: F-150, F-250, F-350, F-450, SD, Lightning BEV), so in some model years most of its complaints were Super Duty trucks
# (2019: 84% of first-3-year complaints, 2017: 78%). The Super Duty already has its own page (/cars/ford-super-duty/, hd_pages.py).
# This script recounts the F-150 page's numbers from the F-150's OWN NHTSA model names only ('F-150', 'F-150 HYBRID'). Left out: F-250/F-350/
# F-450 (+ SD / SUPER DUTY), 'F SUPER DUTY', the ambiguous pre-2010 'F SERIES' filings and the 'F-150 LIGHTNING BEV' (its own EV page).
# No score: Ford reports F-150 and Super Duty U.S. sales together as "F-Series" (no F-150-only sales figure exists in Ford's releases, Wikipedia
# or GoodCarBadCar), so the F-150 becomes complaints-only, like the Super Duty. The study's whole-line "Ford F-Series" row (data/family_rates.csv)
# is unchanged: complaints and sales of the same line, so it stays valid as an F-Series number, and the F-150 page says it isn't the F-150's.
# Same rules as data_years.py (3-year window, model years 2000-2025, quotes) and data_extras_local.py (all complaints for sev / miles / names).
#   usage: py -X utf8 data_f150_split.py   -> data/f150_split.json (+ prints before/after per year)
import collections, json, os, random, re, sqlite3, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
DB = os.path.join(LEMON, 'data', 'complaints.db')
FID, FAM = 'ford-f-series', 'Ford F-Series'
F150 = {'F-150', 'F-150 HYBRID'}
SD = re.compile(r'F-(250|350|450)( SD| SUPER DUTY)?|F SUPER DUTY')
FAMRX = re.compile(r'F-(150|250|350|450)( SD| SUPER DUTY| HYBRID| LIGHTNING( BEV)?| RAPTOR)?|F SUPER DUTY|F SERIES')
Y0, Y1, WINDOW, MAX_MILES = 2000, 2025, 3, 400_000
src = open(os.path.join(HERE, 'data_years.py'), encoding='utf-8').read()
g = {}
exec(src[src.index('PART = {'):src.index('part = lambda')], g); PART = g['PART']
part = lambda c: PART.get(c, c.lower().replace('/', ' / '))
sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib'))
from families import FAMILIES
g = dict(re=re, FAMILIES=FAMILIES)
exec(src[src.index('BAD = re.compile'):src.index('def quotes')], g); BAD, clean = g['BAD'], g['clean']

con = sqlite3.connect(DB)
tot, totsd, totfam = collections.Counter(), collections.Counter(), collections.Counter()
comp, ids = collections.defaultdict(collections.Counter), collections.defaultdict(lambda: collections.defaultdict(list))
sev, names, miles = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), collections.defaultdict(list)
cat = collections.defaultdict(collections.Counter)
cmiles, cn = collections.defaultdict(lambda: collections.defaultdict(list)), collections.defaultdict(collections.Counter)
for odino, model, year, ldate, comps, crash, fire, injured, deaths, towed, mi in con.execute(
        f"SELECT odino, model, year, ldate, comps, crash, fire, injured, deaths, towed, miles FROM complaints WHERE make='FORD' AND year BETWEEN {Y0} AND {Y1}"):
    if not FAMRX.fullmatch(model or ''): continue
    win = bool(ldate and int(ldate[:4]) <= year + WINDOW)
    if win: totfam[year] += 1
    if SD.fullmatch(model): totsd[year] += win; continue
    if model not in F150: continue
    s = sev[year]; s['total'] += 1; s['crash'] += crash == 'Y'; s['fire'] += fire == 'Y'; s['towed'] += towed == 'Y'
    s['injured'] += (injured or 0) > 0; s['deaths'] += (deaths or 0) > 0; names[year][('FORD', model)] += 1
    ok = mi is not None and 0 < mi <= MAX_MILES
    if ok: miles[year].append(mi)
    cs = {c.split(':')[0].strip() for c in (comps or '').split(' | ')}
    for c in cs:
        if c and not c.startswith('UNKNOWN'):
            cn[year][c] += 1
            if ok: cmiles[year][c].append(mi)
    if not win: continue
    tot[year] += 1
    for c in cs:
        c = c or 'UNKNOWN'; comp[year][c] += 1; ids[year][c].append(odino)
    for a in {part(c) for c in cs if c and c not in ('UNKNOWN OR OTHER', 'UNKNOWN')}: cat[year][a] += 1   # 11-17 rule: once per problem area

def quotes(year, top):
    pool = list(dict.fromkeys(o for c in top for o in ids[year][c])); random.Random(f'{FAM}{year}').shuffle(pool)
    out, seen = [], set()
    for o in pool[:400]:
        row = con.execute('SELECT descr FROM rows WHERE odino=? AND descr IS NOT NULL LIMIT 1', (o,)).fetchone()
        if not row: continue
        t = clean(row[0])
        if not (50 <= len(t) <= 230) or BAD.search(t) or t[:40] in seen: continue
        if re.search(r'\bf-?\s?[2-5][05]0\b|super ?duty|power ?stroke|diesel|lightning', t, re.I): continue   # a quote that names another truck
        seen.add(t[:40]); out.append({'odi': o, 'text': t})
        if len(out) == 3: break
    return out

def spread(v):
    v = sorted(v); qs = statistics.quantiles(v, n=4) if len(v) >= 4 else [v[0], statistics.median(v), v[-1]]
    return int(round(qs[0], -2)), int(round(statistics.median(v), -2)), int(round(qs[2], -2))

before = {v['y']: v for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8')) if f['id'] == FID for v in f['years']}
years, extras = {}, {}
for y in range(Y0, Y1 + 1):
    if not (tot[y] or sev[y]['total']): continue
    cs = [(c, k) for c, k in comp[y].most_common() if c not in ('UNKNOWN OR OTHER', 'UNKNOWN')]
    n = tot[y] or 1
    years[str(y)] = dict(n=tot[y], n_sd=totsd[y], n_fam=totfam[y], parts=[[c, round(100 * k / n)] for c, k in sorted(cat[y].items(), key=lambda x: (-x[1], x[0]))[:5]], quotes=quotes(y, [c for c, _ in cs[:2]]))
    e = {'sev': dict(sev[y]), 'names': [[mk, md, k] for (mk, md), k in names[y].most_common(4)]}
    if len(miles[y]) >= 5:
        lo, med, hi = spread(miles[y]); e['miles'] = {'median': med, 'p25': lo, 'p75': hi, 'n': len(miles[y])}
    rows = []
    for c, _ in cn[y].most_common():
        v = cmiles[y][c]
        if len(v) < 5: continue
        lo, med, hi = spread(v); rows.append([part(c), med, lo, hi, len(v)])
        if len(rows) == 5: break
    if rows: e['comps'] = rows
    extras[str(y)] = e
out = dict(note='F-150 only (NHTSA models F-150, F-150 HYBRID); no score: Ford reports F-150 and Super Duty sales together as F-Series',
           models=sorted(F150), years=years, extras=extras,
           before={str(y): dict(li=v.get('li'), n=v['n'], sold=v.get('sold'), early=bool(v.get('early'))) for y, v in before.items()})
json.dump(out, open(os.path.join(HERE, 'data', 'f150_split.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('year  before(li, n F-Series)  after(n F-150)  Super Duty n  SD share')
for y in sorted(set(years) | {str(k) for k in before}):
    b = before.get(int(y)) or {}; a = years.get(y) or {}
    print(y, b.get('li'), b.get('n'), '->', a.get('n'), a.get('n_sd'), f"{round(100 * a.get('n_sd', 0) / max(1, a.get('n_fam', 0)))}%")

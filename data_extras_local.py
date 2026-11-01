# Builds data/extras_local.json from the local NHTSA complaints database (10-31: Elijah asked for more data per car page).
#   usage: py data_extras_local.py
# Per family and model year, using the same family matching and model-year codes as data_years.py:
#   - miles:  when problems show up. Median odometer reading of all complaints, plus per problem area (top 5 areas with
#             at least 5 readings): median, 25th and 75th percentile. Readings of 0 or over 400,000 are ignored.
#   - sev:    how serious. Complaints that report a crash, a fire, an injury, a death, or that the car was towed.
#   - names:  the NHTSA make/model names behind the family that year (data_fetch_api.py uses them for recalls and ratings).
# Unlike the Lemon Index score, these use every complaint for the model year (no 3-year window): failures at high mileage
# come years later, and a window would hide them.
import ast, json, os, re, sqlite3, statistics, sys
from collections import Counter, defaultdict
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib'))
from families import FAMILIES
import mysales

HERE = os.path.dirname(os.path.abspath(__file__))
Y0, Y1, MAX_MILES = 2000, 2022, 400_000
# Reuse data_years.py's tables (old NHTSA model names, problem-area names) without running it.
_src = ast.parse(open(os.path.join(HERE, 'data_years.py'), encoding='utf-8').read())
_lit = {t.targets[0].id: ast.literal_eval(t.value) for t in _src.body
        if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name) and t.targets[0].id in ('OLD_NAMES', 'PART')}
OLD_NAMES, PART = _lit['OLD_NAMES'], _lit['PART']
part = lambda c: PART.get(c, c.lower().replace('/', ' / '))
idof = lambda f: f.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')

pats = [(f, set(mk.split('|')), re.compile(rx)) for f, mk, rx, _, _ in FAMILIES]
old_pats = [(f, mk, re.compile(rx.pattern + ('|' + OLD_NAMES[f] if f in OLD_NAMES else ''))) for f, mk, rx in pats]

miles = defaultdict(list)                        # (fam, year) -> all readings
comp_miles = defaultdict(lambda: defaultdict(list))
comp_n = defaultdict(Counter)
sev = defaultdict(Counter)
names = defaultdict(Counter)
con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
q = f'SELECT make, model, year, crash, fire, injured, deaths, towed, miles, comps FROM complaints WHERE year BETWEEN {Y0} AND {Y1}'
for make, model, year, crash, fire, injured, deaths, towed, mi, comps in con.execute(q):
    fam = next((f for f, mk, rx in (old_pats if year < 2010 else pats) if make in mk and rx.fullmatch(model)), None)
    if fam is None: continue
    key = (fam, mysales.code(fam, year))
    names[key][(make, model)] += 1
    s = sev[key]
    s['total'] += 1
    s['crash'] += crash == 'Y'; s['fire'] += fire == 'Y'; s['towed'] += towed == 'Y'
    s['injured'] += (injured or 0) > 0; s['deaths'] += (deaths or 0) > 0
    ok = mi is not None and 0 < mi <= MAX_MILES
    if ok: miles[key].append(mi)
    for c in {c.split(':')[0].strip() for c in (comps or '').split(' | ')}:
        if not c or c.startswith('UNKNOWN'): continue
        comp_n[key][c] += 1
        if ok: comp_miles[key][c].append(mi)

def spread(v):
    v = sorted(v)
    qs = statistics.quantiles(v, n=4) if len(v) >= 4 else [v[0], statistics.median(v), v[-1]]
    return int(round(qs[0], -2)), int(round(statistics.median(v), -2)), int(round(qs[2], -2))

out = defaultdict(dict)
for (fam, year), s in sev.items():
    entry = {'sev': dict(s), 'names': [[mk, md, n] for (mk, md), n in names[(fam, year)].most_common(4)]}
    if len(miles[(fam, year)]) >= 5:
        lo, med, hi = spread(miles[(fam, year)])
        entry['miles'] = {'median': med, 'p25': lo, 'p75': hi, 'n': len(miles[(fam, year)])}
    rows = []
    for c, _ in comp_n[(fam, year)].most_common():
        v = comp_miles[(fam, year)][c]
        if len(v) < 5: continue
        lo, med, hi = spread(v)
        rows.append([part(c), med, lo, hi, len(v)])
        if len(rows) == 5: break
    if rows: entry['comps'] = rows
    out[idof(fam)][year] = entry
json.dump(out, open(os.path.join(HERE, 'data', 'extras_local.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out), 'families,', sum(len(v) for v in out.values()), 'model years,',
      sum(1 for v in out.values() for e in v.values() if 'comps' in e), 'with mileage by problem area -> data/extras_local.json')

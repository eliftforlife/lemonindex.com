# 11-12 round 2 (Carlos: "rav4 hybrid" opens the RAV4 page, which never says what the hybrid saves on a 60-mile commute): gas vs hybrid,
# from the EPA, for every model we cover that's sold both ways.
#   usage: py -X utf8 data_hybrid_split.py     -> data/hybrid_split.json
# EPA (fueleconomy.gov, the same cached API and model matching as data_fetch_api.py): per model year, each version's EPA type (atvType:
# Hybrid / Plug-in Hybrid / EV / regular), combined mpg range and yearly fuel cost range. A model is listed when at least one year has both a
# gas and a hybrid version. EPA's yearly fuel cost assumes 15,000 miles a year (55% city, 45% highway) at EPA's current fuel prices, so
# cost per mile = fuelCost08 / 15,000; the page's commute line is that arithmetic.
# NHTSA complaints can't be split by version (owners mostly file under the base name), so the pages say the score covers both.
import json, os, re, sys, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'data_fetch_api.py'), encoding='utf-8').read(); src = src[:src.index('# ---------- run ----------')]
API = {'__file__': os.path.join(HERE, 'data_fetch_api.py')}
exec(compile(src, 'data_fetch_api.py', 'exec'), API)
get, fe_pattern, fe_make, norm, MAKES, LOCAL, idof = API['get'], API['fe_pattern'], API['fe_make'], API['norm'], API['MAKES'], API['LOCAL'], API['idof']

OTHER = re.compile(r'CROSS|CX50|ROGUESPORT|FCEV|FUELCELL')   # another model the prefix match catches (Corolla Cross, CX-50, Rogue Sport), or a fuel-cell car
FULL = re.compile(r'hybrid|hev|\d{3}h|e-?tron|4xe|energi|prime|plug-?in|phev|e-hybrid', re.I)   # a full or plug-in hybrid by name (not a mild-hybrid gas engine)
def kind(v):
    t = (v.get('atvType') or '').lower()
    if 'plug' in t: return 'phev'
    if 'hybrid' in t: return 'hybrid'
    if t == 'ev': return None
    if (v.get('fuelType1') or '').lower().startswith(('electric', 'hydrogen')): return None
    return 'gas'

def year_split(fam, year):
    pat, cars = fe_pattern(fam), []
    for mk in MAKES[fam]:
        menu = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={year}&make={urllib.parse.quote(fe_make(mk))}') or {}
        items = menu.get('menuItem') or []
        for m in (items if isinstance(items, list) else [items]):
            if not pat.match(norm(m['value'])) or OTHER.search(norm(m['value'])): continue
            opts = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year={year}&make={urllib.parse.quote(fe_make(mk))}&model={urllib.parse.quote(m["value"])}') or {}
            o = opts.get('menuItem') or []
            for x in (o if isinstance(o, list) else [o])[:6]:
                v = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/{x["value"]}')
                if v and str(v.get('comb08', '')).isdigit() and int(v['comb08']) > 0: cars.append(v)
    row = {}
    for k in ('gas', 'hybrid', 'phev'):
        vs = [v for v in cars if kind(v) == k]
        if not vs: continue
        comb = [int(v['comb08']) for v in vs]; cost = [int(v['fuelCost08']) for v in vs if str(v.get('fuelCost08', '')).isdigit() and int(v['fuelCost08']) > 0]
        row[k] = {'comb': [min(comb), max(comb)], 'cost': [min(cost), max(cost)] if cost else None,
                  'versions': sorted({v.get('model', '') for v in vs})[:6], 'n': len(vs)}
    for k in ('hybrid', 'phev'):   # 11-12: mild hybrids (BMW 540i, Mercedes EQ Boost) are gas cars to a buyer: only versions sold as a hybrid count
        if row.get(k) and not any(FULL.search(n) for n in row[k]['versions']): del row[k]
    return row if row.get('gas') and (row.get('hybrid') or row.get('phev')) else None

out = {}
for fam in sorted(MAKES):
    fid = idof(fam)
    if fid not in LOCAL: continue
    ys = {}
    for y in sorted(LOCAL[fid]):
        if int(y) < 2004: continue
        try: r = year_split(fam, int(y))
        except Exception as e: print('fail', fid, y, e); continue
        if r: ys[y] = r
    if ys:
        out[fid] = {'name': fam, 'years': ys}
        print(fid, ' '.join(f'{y}:{r["gas"]["comb"]}/{(r.get("hybrid") or r.get("phev"))["comb"]}' for y, r in ys.items()), flush=True)
json.dump({'source': 'https://www.fueleconomy.gov/', 'miles_per_year': 15000, 'models': out}, open(os.path.join(HERE, 'data', 'hybrid_split.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))
print(len(out), 'models with gas + hybrid versions')

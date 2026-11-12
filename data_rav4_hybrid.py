# 11-12 (UX test, Dan: "rav4 hybrid" -> "No match", and the 2021 RAV4 page shows one "2.5L 4-cyl" at 28-40 mpg): the RAV4 Hybrid split out
# as far as the public data allows.
#   usage: py -X utf8 data_rav4_hybrid.py     -> data/rav4_hybrid.json
#   EPA (fueleconomy.gov, the same cached API as data_fetch_api.py): the gas, Hybrid and Prime (plug-in) versions of each model year
#     separately: combined mpg, yearly fuel cost, engine
#   NHTSA (3 Lemon Index/data/complaints.db): owners file almost every RAV4 complaint under "RAV4" whatever the version, so the complaint
#     counts and the score can't be split. What we can show honestly: complaints filed under "RAV4 HYBRID" / "RAV4 PRIME" by name, and the
#     share of all RAV4 complaints that name the hybrid system (NHTSA's HYBRID PROPULSION SYSTEM component)
import json, os, re, sqlite3, sys, urllib.parse
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'data_fetch_api.py'), encoding='utf-8').read(); src = src[:src.index('# ---------- run ----------')]
API = {'__file__': os.path.join(HERE, 'data_fetch_api.py')}
src = src.replace("LOCAL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))", 'LOCAL = {}')
exec(compile(src, 'data_fetch_api.py', 'exec'), API)
get = API['get']
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
Y0, Y1 = 2016, 2025   # the RAV4 Hybrid's first U.S. model year is 2016
def kind(model):
    m = model.upper()
    return 'prime' if 'PRIME' in m or 'PLUG-IN' in m else 'hybrid' if 'HYBRID' in m else None if 'EV' in m.split() else 'gas'
out = {'years': {}, 'source': 'https://www.fueleconomy.gov/', 'note': ''}
for y in range(Y0, Y1 + 1):
    menu = (get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={y}&make=Toyota') or {}).get('menuItem') or []
    menu = menu if isinstance(menu, list) else [menu]
    by = defaultdict(list)
    for m in menu:
        if not re.match(r'RAV4', m['value'], re.I): continue
        k = kind(m['value'])
        if not k: continue
        o = (get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year={y}&make=Toyota&model={urllib.parse.quote(m["value"])}') or {}).get('menuItem') or []
        for x in (o if isinstance(o, list) else [o])[:6]:
            v = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/{x["value"]}')
            if v and str(v.get('comb08', '')).isdigit(): by[k].append(v)
    row = {}
    for k, vs in by.items():
        comb = [int(v['comb08']) for v in vs if int(v['comb08']) > 0]; cost = [int(v['fuelCost08']) for v in vs if str(v.get('fuelCost08', '')).isdigit() and int(v['fuelCost08']) > 0]
        eng = sorted({f"{float(v['displ']):.1f}L {v['cylinders']}-cyl" + (' hybrid' if k != 'gas' else '') for v in vs if v.get('displ') not in (None, '', '0', '0.0')})
        ev_range = sorted({int(v['rangeA']) for v in vs if k == 'prime' and str(v.get('rangeA', '')).replace('.', '').isdigit() and float(v['rangeA']) > 0}) if k == 'prime' else []
        row[k] = {'comb': [min(comb), max(comb)], 'cost': [min(cost), max(cost)] if cost else None, 'engines': eng, 'versions': sorted({v.get('model', '') for v in vs}), 'n': len(vs)}
        if ev_range: row[k]['ev_miles'] = [ev_range[0], ev_range[-1]]
    if row.get('hybrid'): out['years'][str(y)] = row
# NHTSA: what can and can't be split
con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
named, hyb, tot = Counter(), Counter(), Counter()
for model, year, comps in con.execute("SELECT model, year, comps FROM complaints WHERE make='TOYOTA' AND model LIKE 'RAV4%' AND year BETWEEN ? AND ?", (Y0, Y1)):
    k = kind(model)
    if not k: continue
    tot[year] += 1
    if k != 'gas': named[(year, k)] += 1
    if 'HYBRID PROPULSION SYSTEM' in (comps or ''): hyb[year] += 1
for y in range(Y0, Y1 + 1):
    r = out['years'].get(str(y))
    if r: r['nhtsa'] = {'all': tot[y], 'filed_hybrid': named[(y, 'hybrid')], 'filed_prime': named[(y, 'prime')], 'hybrid_system': hyb[y]}
out['note'] = ('NHTSA complaints: owners file almost every RAV4 complaint under "RAV4", whichever version they own, so the RAV4 score covers gas, '
               'Hybrid and Prime together. Counts are every complaint for the model year (all dates).')
json.dump(out, open(os.path.join(HERE, 'data', 'rav4_hybrid.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for y, r in out['years'].items(): print(y, {k: (v['comb'], v['engines']) for k, v in r.items() if k != 'nhtsa'}, r.get('nhtsa'))
